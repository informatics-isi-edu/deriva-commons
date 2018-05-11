-- BEGIN transaction

BEGIN;

CREATE OR REPLACE FUNCTION public.unset_bulk_upload() RETURNS BOOLEAN AS $$
   SELECT set_config('rbk.bulk_upload', 'False', False);
   SELECT true;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION public.get_bulk_upload() RETURNS BOOLEAN AS $$
   SELECT lower(current_setting('rbk.bulk_upload', true)) IS NOT DISTINCT FROM 'true';
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION public.try_ermrest_data_change_event(sname name, tname name) RETURNS BOOLEAN AS $$
DECLARE
is_bulk_upload BOOLEAN;
BEGIN
   SELECT public.get_bulk_upload() INTO is_bulk_upload;
   IF NOT is_bulk_upload THEN
      BEGIN
         perform _ermrest.data_change_event(sname, tname);
         exception when others THEN
            RETURN false;
      END;
   END IF;
   RETURN true;
END
$$ language plpgsql;

CREATE OR REPLACE function data_commons.push_cvtermpath_adds() returns TRIGGER AS $$
DECLARE
   term_schema text;
   term_table text;
   path_schema text;
   path_table text;
   rel_schema text;
   rel_table text;
BEGIN
   for term_schema, term_table, path_schema, path_table, rel_schema, rel_table IN
       SELECT d.term_schema, d.term_table, d.path_schema, d.path_table, d.rel_type_schema, d.rel_type_table FROM data_commons.domain_registry d
   loop
       BEGIN
           IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN
	      execute format ('DELETE FROM %I.%I WHERE subject_dbxref = %L AND object_dbxref = %L AND type_dbxref = %L',
                 path_schema, path_table, OLD.subject_dbxref, OLD.object_dbxref, OLD.type_dbxref);
           ELSIF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
	      execute format ('INSERT into %I.%I (subject_dbxref, object_dbxref, type_dbxref, cv, pathdistance, cvtermpath_id) 
                  SELECT %L, %L, %L, %L, %s, %s
                  WHERE EXISTS (SELECT 1 FROM %I.%I WHERE dbxref = %L)
                  AND EXISTS (SELECT 1 FROM %I.%I WHERE dbxref = %L)
                  AND EXISTS (SELECT 1 FROM %I.%I WHERE cvterm_dbxref = %L)',
                 path_schema, path_table, NEW.subject_dbxref, NEW.object_dbxref, NEW.type_dbxref, NEW.cv, NEW.pathdistance, NEW.cvtermpath_id,
		 term_schema, term_table, NEW.subject_dbxref,
		 term_schema, term_table, NEW.object_dbxref,
		 rel_schema, rel_table, NEW.type_dbxref
		 );
           END IF;
--       exception when others then
--           continue;
       perform public.try_ermrest_data_change_event(term_schema, term_table);	   
       END;
   END loop;
   RETURN NEW;
END
$$ language plpgsql;

DROP TRIGGER IF EXISTS cvtermpath_push_updates_trigger ON data_commons.cvtermpath;
CREATE TRIGGER cvtermpath_push_updates_trigger  AFTER INSERT OR UPDATE OR DELETE ON data_commons.cvtermpath for each row execute PROCEDURE data_commons.push_cvtermpath_adds();

-- update ermrest
TRUNCATE _ermrest.data_version;
TRUNCATE _ermrest.model_version;
SELECT _ermrest.model_change_event();


COMMIT;

