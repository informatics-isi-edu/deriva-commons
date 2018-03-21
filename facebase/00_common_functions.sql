-- BEGIN transaction

BEGIN;

CREATE OR REPLACE FUNCTION public.unset_bulk_upload() RETURNS BOOLEAN AS $$
   SELECT set_config('rbk.bulk_upload', 'False', False);
   SELECT true;
$$ LANGUAGE SQL;

CREATE or REPLACE FUNCTION public.get_bulk_upload() RETURNS BOOLEAN AS $$
   SELECT lower(current_setting('rbk.bulk_upload', true)) IS NOT DISTINCT from 'true';
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

-- update ermrest
TRUNCATE _ermrest.data_version;
TRUNCATE _ermrest.model_version;
SELECT _ermrest.model_change_event();


COMMIT;

