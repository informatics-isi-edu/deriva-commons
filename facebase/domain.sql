-- begin transaction

BEGIN;

DROP SCHEMA IF EXISTS "Vocabulary";
CREATE SCHEMA "Vocabulary" AUTHORIZATION ermrest;

CREATE OR REPLACE FUNCTION data_commons.make_facebase_domain_tables(schema_name name, base_name name) RETURNS BOOLEAN AS $$
DECLARE
   cvterm_name text = base_name || '_terms';
   path_name text = base_name || '_paths';
   rel_type_table_name name = base_name || '_relationship_types';
BEGIN
	PERFORM data_commons.make_domain_tables(schema_name, base_name, schema_name, rel_type_table_name);
	execute format('ALTER TABLE %I.%I 
		ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval(''_ermrest.rid_seq''::regclass) NOT NULL,
		ADD COLUMN "RCB" public.ermrest_rcb,
		ADD COLUMN "RMB" public.ermrest_rmb,
		ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
		ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL,
		OWNER TO ermrest',
		schema_name, cvterm_name);
		
	execute format('CREATE TRIGGER ermrest_syscols 
		BEFORE INSERT OR UPDATE ON %I.%I 
		FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()',
		schema_name, cvterm_name);
	
	execute format('ALTER TABLE %I.%I 
		ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval(''_ermrest.rid_seq''::regclass) NOT NULL,
		ADD COLUMN "RCB" public.ermrest_rcb,
		ADD COLUMN "RMB" public.ermrest_rmb,
		ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
		ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL,
		OWNER TO ermrest',
		schema_name, path_name);
		
	execute format('CREATE TRIGGER ermrest_syscols 
		BEFORE INSERT OR UPDATE ON %I.%I 
		FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()',
		schema_name, path_name);
	
	execute format('ALTER TABLE %I.%I 
		ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval(''_ermrest.rid_seq''::regclass) NOT NULL,
		ADD COLUMN "RCB" public.ermrest_rcb,
		ADD COLUMN "RMB" public.ermrest_rmb,
		ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
		ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL,
		OWNER TO ermrest',
		schema_name, rel_type_table_name);
		
	execute format('CREATE TRIGGER ermrest_syscols 
		BEFORE INSERT OR UPDATE ON %I.%I 
		FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()',
		schema_name, rel_type_table_name);
		
	RETURN TRUE;
END 
$$ language plpgsql;

SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'anatomy');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'chemical_entities');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'cvnames');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'file_format');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'gender');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'gene');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'gene_summary');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'genotype');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'histone_modification');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'image_creation_device');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'mapping_assembly');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'molecule_type');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'mutation');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'origin');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'output_type');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'paired_end_or_single_read');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'phenotype');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'rnaseq_selection');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'sample_type');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'sequencing_data_direction');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'species');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'specimen');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'stage');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'strain');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'strandedness');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'target_of_assay');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'theiler_stage');
SELECT data_commons.make_facebase_domain_tables('Vocabulary', 'data_type');


CREATE OR REPLACE FUNCTION data_commons.load_facebase_domain_tables(schema_name name, base_name name) RETURNS BOOLEAN AS $$
DECLARE
   cvterm_name text = base_name || '_terms';
BEGIN
	execute format('INSERT INTO %I.%I(dbxref, dbxref_unversioned, cv, name, definition, is_obsolete, is_relationshiptype, synonyms, alternate_dbxrefs) 
		SELECT dbxref, dbxref_unversioned, cv, name, definition, is_obsolete, is_relationshiptype, synonyms, alternate_dbxrefs from data_commons.cvterm 
		WHERE name IN (SELECT name FROM temp.%I)',
	schema_name, cvterm_name, base_name);
	RETURN TRUE;
END 
$$ language plpgsql;

SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'anatomy');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'chemical_entities');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'cvnames');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'file_format');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'gender');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'gene');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'gene_summary');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'genotype');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'histone_modification');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'image_creation_device');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'mapping_assembly');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'molecule_type');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'mutation');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'origin');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'output_type');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'paired_end_or_single_read');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'phenotype');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'rnaseq_selection');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'sample_type');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'sequencing_data_direction');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'species');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'specimen');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'stage');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'strain');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'strandedness');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'target_of_assay');
SELECT data_commons.load_facebase_domain_tables('Vocabulary', 'theiler_stage');

-- update ermrest
TRUNCATE _ermrest.data_version;
TRUNCATE _ermrest.model_version;
SELECT _ermrest.model_change_event();


COMMIT;

