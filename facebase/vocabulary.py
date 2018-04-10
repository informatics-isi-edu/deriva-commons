#!/usr/bin/python

import sys
import traceback
import json
from deriva.core import ErmrestCatalog, AttrDict
from deriva.core.ermrest_model import builtin_types, Table, Column, Key, ForeignKey

def main(servername, credentialsfilename, catalog, output, target):
    
    data_commons_ontologies = ['uberon', 'anatomical_structure', 'uberon/phenoscape-anatomy']
    
    ocdm_sub_ontologies = [
                           'aeo',
                           'cet',
                           'chm3o',
                           'chmmo',
                           'chmo',
                           'cho',
                           'chzmo',
                           'cmmo',
                           'cmo',
                           'cpo',
                           'czmo',
                           'czo',
                           'ocdm'
                           ]
    
    set_pair_end = """
CREATE OR REPLACE FUNCTION isa.set_pair_end() RETURNS TRIGGER AS $$
DECLARE
BEGIN
    IF NEW.paired IS NULL THEN
       NEW.paired = CASE WHEN NEW.filename ilike '%_R1.fastq.gz' OR NEW.filename ilike '%_1.fastq.gz' OR
                              NEW.filename ilike '%_R2.fastq.gz' OR NEW.filename ilike '%_2.fastq.gz' THEN
                     (SELECT dbxref FROM "vocab".paired_end_or_single_read WHERE term='Paired-end')
                    ELSE
                     (SELECT dbxref FROM "vocab".paired_end_or_single_read WHERE term='Single-end')
                    END;
    END IF;

    RETURN NEW;

END
$$ language plpgsql;
    """
    make_temp_functions = """
DROP SCHEMA IF EXISTS temp;
CREATE SCHEMA temp AUTHORIZATION ermrest;

CREATE TABLE temp.terms_iri(name text PRIMARY KEY, dbxref text, iri text);
ALTER TABLE temp.terms_iri OWNER TO ermrest;

CREATE OR REPLACE FUNCTION temp.set_iri(schema_name name, table_name name, column_name name) RETURNS BOOLEAN AS $$
DECLARE
BEGIN
    BEGIN
        execute format('INSERT INTO temp.terms_iri(name, iri) SELECT %I AS name, iri AS iri FROM %I.%I WHERE iri IS NOT NULL AND iri != '''' ON CONFLICT DO NOTHING', column_name, schema_name, table_name);
    EXCEPTION WHEN OTHERS THEN
    END;
    RETURN TRUE;
END
$$ language plpgsql;

CREATE OR REPLACE FUNCTION temp.make_temp_tables_annotations(schema_name name, base_name name) RETURNS BOOLEAN AS $$
DECLARE
BEGIN
    execute format('INSERT INTO _ermrest. model_table_annotation(schema_name, table_name, annotation_uri, annotation_value) 
        VALUES(''%I'',''%I'',''tag:isrd.isi.edu,2016:visible-columns'', ''{"*":["name","cv"]}'')',
        schema_name, base_name);
        
    RETURN TRUE;
END 
$$ language plpgsql;

CREATE OR REPLACE FUNCTION temp.make_facebase_temp_tables(schema_name name, base_name name) RETURNS BOOLEAN AS $$
DECLARE
BEGIN
    execute format('ALTER TABLE %I.%I 
        ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval(''_ermrest.rid_seq''::regclass) NOT NULL,
        ADD COLUMN "RCB" public.ermrest_rcb,
        ADD COLUMN "RMB" public.ermrest_rmb,
        ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
        ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL,
        OWNER TO ermrest',
        schema_name, base_name);
        
    execute format('CREATE TRIGGER ermrest_syscols 
        BEFORE INSERT OR UPDATE ON %I.%I 
        FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()',
        schema_name, base_name);
    
    RETURN TRUE;
END 
$$ language plpgsql;

CREATE TABLE temp.owl_terms(cv text, name text, PRIMARY KEY (name));
ALTER TABLE temp.owl_terms OWNER TO ermrest;
CREATE TABLE temp.owl_predicates(predicate text, PRIMARY KEY (predicate));
ALTER TABLE temp.owl_predicates OWNER TO ermrest;
CREATE TABLE temp.terms(name text, cv text, PRIMARY KEY (name));
ALTER TABLE temp.terms OWNER TO ermrest;
CREATE TABLE temp.ocdm(name text, cv text DEFAULT 'ocdm', PRIMARY KEY (name));
ALTER TABLE temp.ocdm OWNER TO ermrest;
CREATE TABLE temp.facebase(name text, cv text DEFAULT 'facebase', PRIMARY KEY (name));
ALTER TABLE temp.facebase OWNER TO ermrest;
    """

    dataset_functions = """
CREATE OR REPLACE FUNCTION data_commons.make_dataset_tables(schema_name name, table_name name, column_name name) RETURNS BOOLEAN AS $$
DECLARE
BEGIN
    execute format('CREATE TABLE %I.%I (
        dataset_id bigint NOT NULL,
        %I text NOT NULL,
        "RID" public.ermrest_rid DEFAULT nextval(''_ermrest.rid_seq''::regclass) NOT NULL,
        "RCB" public.ermrest_rcb,
        "RMB" public.ermrest_rmb,
        "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
        "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
        )',
        schema_name, table_name, column_name);
        
    execute format('ALTER TABLE ONLY %I.%I FORCE ROW LEVEL SECURITY', schema_name, table_name);
    execute format('ALTER TABLE ONLY %I.%I OWNER TO ermrest', schema_name, table_name);
    execute format('COMMENT ON COLUMN %I.%I."RID" IS ''System-generated unique row ID.''', schema_name, table_name);
    execute format('COMMENT ON COLUMN %I.%I."RCB" IS ''System-generated row created by user provenance.''', schema_name, table_name);
    execute format('COMMENT ON COLUMN %I.%I."RMB" IS ''System-generated row modified by user provenance.''', schema_name, table_name);
    execute format('COMMENT ON COLUMN %I.%I."RCT" IS ''System-generated row creation timestamp.''', schema_name, table_name);
    execute format('COMMENT ON COLUMN %I.%I."RMT" IS ''System-generated row modification timestamp''', schema_name, table_name);
    execute format('ALTER TABLE ONLY %I.%I
        ADD CONSTRAINT "%I_RID_key" UNIQUE ("RID")', schema_name, table_name, table_name);
    execute format('ALTER TABLE ONLY %I.%I
        ADD CONSTRAINT %I_pkey PRIMARY KEY (dataset_id, %I)', schema_name, table_name, table_name, column_name);
    execute format('CREATE INDEX %I__pgtrgm_idx ON %I.%I USING gin ((((COALESCE((dataset_id)::text, ''''::text) || '' ''::text) || COALESCE(%I, ''''::text))) public.gin_trgm_ops)', table_name, schema_name, table_name, column_name);
    execute format('CREATE INDEX %I__tsvector_idx ON %I.%I USING gin (to_tsvector(''english''::regconfig, ((COALESCE((dataset_id)::text, ''''::text) || '' ''::text) || COALESCE(%I, ''''::text))))', table_name, schema_name, table_name, column_name);
    execute format('CREATE INDEX %I_dataset_id_idx ON %I.%I USING btree (dataset_id)', table_name, schema_name, table_name);
    execute format('CREATE INDEX %I_dataset_id_pgtrgm_idx ON %I.%I USING gin (((dataset_id)::text) public.gin_trgm_ops)', table_name, schema_name, table_name);
    execute format('CREATE INDEX %I_%I_idx ON %I.%I USING btree (%I)', table_name, column_name, schema_name, table_name, column_name);
    execute format('CREATE INDEX %I_%I_pgtrgm_idx ON %I.%I USING gin (%I public.gin_trgm_ops)', table_name, column_name, schema_name, table_name, column_name);
    execute format('CREATE TRIGGER ermrest_syscols BEFORE INSERT OR UPDATE ON %I.%I FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()', schema_name, table_name);
    execute format('ALTER TABLE ONLY %I.%I
        ADD CONSTRAINT %I_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES isa.dataset(id) ON UPDATE CASCADE ON DELETE CASCADE', schema_name, table_name, table_name);
    execute format('ALTER TABLE ONLY %I.%I
        ADD CONSTRAINT %I_%I_fkey FOREIGN KEY (%I) REFERENCES vocab.%I_terms(dbxref)', schema_name, table_name, table_name, column_name, column_name, column_name);
        
    RETURN TRUE;
END 
$$ language plpgsql;
    """
    
    domain_functions = """
DROP SCHEMA IF EXISTS "vocab";
CREATE SCHEMA "vocab" AUTHORIZATION ermrest;

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

    """
    
    references_functions = """
CREATE OR REPLACE FUNCTION data_commons.make_facebase_references(schema_name name, table_name name, column_name name, vocabulary_schema name, vocabulary_table name, vocabulary_id name, vocabulary_dbxref name, vocabulary_domain name) RETURNS BOOLEAN AS $$
DECLARE
   cvterm_name name = vocabulary_domain || '_terms';
   term text;
BEGIN
    execute format('ALTER TABLE %I.%I 
        DROP CONSTRAINT IF EXISTS %I_%I_fkey',
        schema_name, table_name, table_name, column_name);
    
    execute format('ALTER TABLE %I.%I 
        ALTER COLUMN %I TYPE text',
        schema_name, table_name, column_name);
    
    execute format('UPDATE  %I.%I T1 SET %I=(SELECT %I FROM %I.%I T2 WHERE to_number(T1.%I, ''999999'') = T2.%I)',
        schema_name, table_name, column_name, vocabulary_dbxref, vocabulary_schema, vocabulary_table, column_name, vocabulary_id);
    
    execute format('ALTER TABLE %I.%I 
        ADD CONSTRAINT %I_%I_fkey FOREIGN KEY (%I) REFERENCES "vocab".%I(dbxref)',
        schema_name, table_name, table_name, column_name, column_name, cvterm_name);
        
    RETURN TRUE;
END 
$$ language plpgsql;

CREATE OR REPLACE FUNCTION data_commons.make_dataset_references(schema_name name, table_name name, column_name name, vocabulary_table name) RETURNS BOOLEAN AS $$
DECLARE
   cvterm_name name = vocabulary_table || '_terms';
   term text;
BEGIN
    execute format('ALTER TABLE %I.%I 
        DROP CONSTRAINT IF EXISTS %I_%I_fkey',
        schema_name, table_name, table_name, column_name);
    
    execute format('ALTER TABLE %I.%I 
        ADD CONSTRAINT %I_%I_fkey FOREIGN KEY (%I) REFERENCES "vocab".%I(dbxref)',
        schema_name, table_name, table_name, column_name, column_name, cvterm_name);
        
    RETURN TRUE;
END 
$$ language plpgsql;

CREATE OR REPLACE FUNCTION data_commons.make_facebase_terms_references(schema_name name, table_name name, column_name name, vocabulary_schema name, vocabulary_table name) RETURNS BOOLEAN AS $$
DECLARE
   cvterm_name name = vocabulary_table || '_terms';
BEGIN
    execute format('UPDATE  %I.%I T1 SET %I=(SELECT dbxref FROM %I.%I T2 WHERE T2.name = T1.%I LIMIT 1)',
        schema_name, table_name, column_name, vocabulary_schema, cvterm_name, column_name);
    
    execute format('ALTER TABLE %I.%I 
        ADD CONSTRAINT %I_%I_fkey FOREIGN KEY (%I) REFERENCES %I.%I(dbxref)',
        schema_name, table_name, table_name, column_name, column_name, vocabulary_schema, cvterm_name);
        
    RETURN TRUE;
END 
$$ language plpgsql;

    """
    
    common_functions = """
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
SELECT _ermrest.model_change_event();


COMMIT;

    """
    data_commons_ermrest = """
-- begin transaction

BEGIN;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cv"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cv" 
    ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
    ADD COLUMN "RCB" public.ermrest_rcb,
    ADD COLUMN "RMB" public.ermrest_rmb,
    ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
    ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvterm"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvterm" 
    ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
    ADD COLUMN "RCB" public.ermrest_rcb,
    ADD COLUMN "RMB" public.ermrest_rmb,
    ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
    ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvterm_dbxref"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvterm_dbxref" 
    ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
    ADD COLUMN "RCB" public.ermrest_rcb,
    ADD COLUMN "RMB" public.ermrest_rmb,
    ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
    ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvterm_relationship"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvterm_relationship" 
    ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
    ADD COLUMN "RCB" public.ermrest_rcb,
    ADD COLUMN "RMB" public.ermrest_rmb,
    ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
    ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvtermpath"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvtermpath" 
    ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
    ADD COLUMN "RCB" public.ermrest_rcb,
    ADD COLUMN "RMB" public.ermrest_rmb,
    ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
    ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvtermprop"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvtermprop" 
    ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
    ADD COLUMN "RCB" public.ermrest_rcb,
    ADD COLUMN "RMB" public.ermrest_rmb,
    ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
    ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvtermsynonym"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvtermsynonym" 
    ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
    ADD COLUMN "RCB" public.ermrest_rcb,
    ADD COLUMN "RMB" public.ermrest_rmb,
    ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
    ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."db"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."db" 
    ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
    ADD COLUMN "RCB" public.ermrest_rcb,
    ADD COLUMN "RMB" public.ermrest_rmb,
    ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
    ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."dbxref"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."dbxref" 
    ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
    ADD COLUMN "RCB" public.ermrest_rcb,
    ADD COLUMN "RMB" public.ermrest_rmb,
    ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
    ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."domain_registry"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."domain_registry" 
    ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
    ADD COLUMN "RCB" public.ermrest_rcb,
    ADD COLUMN "RMB" public.ermrest_rmb,
    ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
    ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."relationship_types"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."relationship_types" 
    ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
    ADD COLUMN "RCB" public.ermrest_rcb,
    ADD COLUMN "RMB" public.ermrest_rmb,
    ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
    ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;


-- update ermrest
SELECT _ermrest.model_change_event();


COMMIT;

    """
    
    data_commons_ocdm_prefix = """
-- begin transaction

BEGIN;

DROP TRIGGER IF EXISTS cvterm_generate_dbxref ON data_commons.cvterm;
DROP TRIGGER IF EXISTS cvterm_insert_trigger ON data_commons.cvterm;

CREATE TRIGGER cvterm_generate_dbxref BEFORE INSERT ON data_commons.cvterm FOR EACH ROW EXECUTE PROCEDURE data_commons.cvterm_generate_dbxref('facebase');
CREATE TRIGGER cvterm_insert_trigger AFTER INSERT ON data_commons.cvterm FOR EACH ROW EXECUTE PROCEDURE data_commons.cvterm_add('facebase');

    """
    
    data_commons_ocdm_suffix = """
-- commit transaction

INSERT INTO data_commons.cvterm (cv, name) SELECT cv, name FROM temp.owl_terms;
INSERT INTO temp.ocdm (cv, name) SELECT cv, name FROM temp.owl_terms WHERE name NOT IN (SELECT name FROM temp.uberon) AND name IN (SELECT name FROM temp.terms);
UPDATE temp.terms T1 SET cv = (SELECT cv FROM temp.ocdm T2 WHERE T1.name = T2.name) WHERE name IN (SELECT name FROM temp.ocdm);


-- update ermrest
SELECT _ermrest.model_change_event();


COMMIT;

    """
    local_ocdm_prefix = """
-- begin transaction

BEGIN;


INSERT INTO temp.facebase (name) SELECT DISTINCT name FROM temp.terms WHERE name NOT IN (SELECT name FROM data_commons.cvterm);

    """
    
    local_ocdm_suffix = """
INSERT INTO data_commons.cvterm (cv, name) SELECT cv, name FROM temp.facebase ON CONFLICT DO NOTHING;

UPDATE temp.terms T1 SET cv = (SELECT cv FROM temp.facebase T2 WHERE T1.name = T2.name) WHERE name IN (SELECT name FROM temp.facebase);

-- update ermrest
SELECT _ermrest.model_change_event();


COMMIT;

    """
    
    """
    Duplicate Foreign Keys constraints
    """
    duplicate_constraints = {'isa': {'dataset_zebrafish_anatomic_source': ['dataset_zebrafish_anatomic_source_zebrafish_anatomic_source_fke']}}
    
    """
    Triggers
    """
    triggers = {'isa': {'biosample': [
                                      {'populate_biosample_summary': 'BEFORE INSERT OR UPDATE ON isa.biosample FOR EACH ROW EXECUTE PROCEDURE isa.update_biosample_summary()'},
                                      {'populate_experiment_biosample_summary': 'AFTER UPDATE ON isa.biosample FOR EACH ROW EXECUTE PROCEDURE isa.update_experiment_biosample_summary()'}
                                      ],
                        'sequencing_data': [
                                            {'populate_paired': 'BEFORE INSERT OR UPDATE ON isa.sequencing_data FOR EACH ROW EXECUTE PROCEDURE isa.set_pair_end()'},
                                            {'populate_read': 'BEFORE INSERT OR UPDATE ON isa.sequencing_data FOR EACH ROW EXECUTE PROCEDURE isa.set_sequencing_read()'}
                                            ]
                        }
                }
    
    """
    Views
    """
    isa_imaging_compact_view = """
 SELECT i."RID",
    i."RCB",
    i."RCT",
    i."RMB",
    i."RMT",
    i.replicate,
    i.filename,
    i.url,
    to_jsonb(ARRAY( SELECT row_to_json(thumbnail_row.*) AS row_to_json
           FROM ( SELECT t.filename,
                    t.url,
                    t.caption
                   FROM isa.thumbnail t
                  WHERE t.thumbnail_of = i."RID"::bigint) thumbnail_row)) AS thumbnails,
    i.byte_count,
    i.file_type,
    i.md5,
    i.submitted_on
   FROM isa.imaging_data i;
    """
    
    views = {'isa': {'imaging_compact': isa_imaging_compact_view}}

    
    """
    Terms mapped to the ontologies.
    """
    mapped_terms = {
                     'Adult': 'adult',
                     'Auditory Capsule': 'Auditory capsule',
                     'Cleft palate': 'oropharyngeal choana',
                     'Female': 'female organism',
                     'Human': 'human',
                     'Male': 'male organism',
                     'Maxilla defects': 'Maxilla defect',
                     'Mouse': 'mouse',
                     'Nasal suture': 'nasal suture',
                     'Neural Crest': 'Neural crest',
                     'Taenia Marginalis Anterior': 'taenia marginalis anterior',
                     'Taenia Marginalis Posterior': 'taenia marginalis posterior',
                     'Tooth defects': 'Tooth defect',
                     'Trigeminal v': 'Trigeminal V',
                     'Ts17 ectoderm of frontonasal process': 'TS17 ectoderm of frontonasal process',
                     'Ts19 ectoderm of frontonasal process': 'TS19 ectoderm of frontonasal process',
                     'Ts21 ectoderm of frontonasal process': 'TS21 ectoderm of frontonasal process',
                     'Zebrafish': 'zebrafish'
                    }
    """
    The vocabulary tables from the "vocabulary" schema.
    """
    vocabulary_tables = [
                     'age',
                     'anatomy',
                     'equipment_model',
                     'experiment_type',
                     'file_extension',
                     'file_format',
                     'gender',
                     'gene',
                     'genotype',
                     'histone_modification',
                     'icd10_code',
                     'icd10_diagnosis',
                     'image_creation_device',
                     'mapping_assembly',
                     'molecule_type',
                     'mutation',
                     'omim_code',
                     'omim_diagnosis',
                     'origin',
                     'output_type',
                     'paired_end_or_single_read',
                     'phenotype',
                     'rnaseq_selection',
                     'sample_type',
                     'species',
                     'specimen',
                     'stage',
                     'strain',
                     'strandedness',
                     'target_of_assay',
                     'theiler_stage'
                     ]
    
    """
    The vocabulary tables from the "isa" schema.
    """
    isa_tables = [
                  'data_type',
                  'experiment_type',
                  'human_age',
                  'human_age_stage',
                  'human_anatomic_source',
                  'human_enhancer',
                  'human_gender',
                  'imaging_method',
                  'instrument',
                  'jax_strain',
                  'mouse_age_stage',
                  'mouse_anatomic_source',
                  'mouse_enhancer',
                  'mouse_gene',
                  'mouse_genetic_background',
                  'mouse_genotype',
                  'mouse_mutation',
                  'mouse_theiler_stage',
                  'organism',
                  'specimen',
                  'zebrafish_age_stage',
                  'zebrafish_anatomic_source',
                  'zebrafish_genotype',
                  'zebrafish_mutation'
                  ]
    
    """
    The vocabulary tables from the "vocab" schema.
    """
    domain_tables = [
                     'anatomy',
                     'data_type',
                     'enhancer',
                     'experiment_type',
                     'file_format',
                     'gender',
                     'gene',
                     'genotype',
                     'histone_modification',
                     'human_age',
                     'image_creation_device',
                     'instrument',
                     'mapping_assembly',
                     'molecule_type',
                     'mouse_genetic_background',
                     'mutation',
                     'organism',
                     'origin',
                     'output_type',
                     'paired_end_or_single_read',
                     'phenotype',
                     'rnaseq_selection',
                     'species',
                     'specimen',
                     'stage',
                     'strain',
                     'strandedness',
                     'target_of_assay'
                     ]
        
    
    """
    The dictionary with the merged vocabularies.
    """
    union_vocabularies = {'gender': {'vocabulary': ['gender'], 'isa': ['human_gender']},
                          'gene': {'vocabulary': ['gene'], 'isa': ['mouse_gene']},
                          'genotype': {'vocabulary': ['genotype'], 'isa': ['mouse_genotype', 'zebrafish_genotype']},
                          'mutation': {'vocabulary': ['mutation'], 'isa': ['mouse_mutation', 'zebrafish_mutation']},
                          'stage': {'vocabulary': ['stage', 'theiler_stage'], 'isa': ['human_age_stage', 'mouse_age_stage', 'mouse_theiler_stage', 'zebrafish_age_stage']},
                          'anatomy': {'vocabulary': ['anatomy'], 'isa': ['human_anatomic_source', 'mouse_anatomic_source', 'zebrafish_anatomic_source']},
                          'enhancer': {'isa': ['human_enhancer', 'mouse_enhancer']},
                          'species': {'vocabulary': ['species'], 'isa': ['organism']}
                          }

    """
    The dictionary with the merged vocabularies.
    """
    union_dataset = {'gender': ['human_gender'],
                      'gene': ['mouse_gene'],
                      'genotype': ['mouse_genotype', 'zebrafish_genotype'],
                      'mutation': ['mouse_mutation', 'zebrafish_mutation'],
                      'stage': ['human_age_stage', 'mouse_age_stage', 'mouse_theiler_stage', 'zebrafish_age_stage'],
                      'anatomy': ['human_anatomic_source', 'mouse_anatomic_source', 'zebrafish_anatomic_source'],
                      'enhancer': ['human_enhancer', 'mouse_enhancer']
                      }

    """
    The dictionary for mapping values.
    """
    mapping_terms = [{'table': 'isa.organism',
                      'column': 'term',
                      'mappings': {'Mouse': 'Mus musculus',
                                   'Zebrafish': 'Danio rerio',
                                   'Chimpanzee': 'Pan troglodytes',
                                   'Human': 'Homo sapiens'
                                   }
                      }
                     ]
    
    """
    The dictionary with the "Referenced by:" tables of the "vocab" schema.
    """
    domain_references = {}
    
    """
    The dictionary with the "introspection" of the vocabulary tables.
    Each table in the schema contains the "foreign_keys" and the "references"
    """
    vocabulary_relations = {'vocabulary': {}, 'isa': {}}
    
    """
    The dictionary that contains the vocabulary tables that have no "Referenced by:".
    """
    vocabulary_orphans = {'vocabulary': [], 'isa': []}
    
    """
    The dictionary that contains the column name used as a term in the vocabulary tables.
    Valid values are "term" or "name".
    """
    vocabulary_term_name = {'vocabulary': {}, 'isa': {}}
    
    """
    The list of the generated tables in the "vocab" schema.
    """    
    vocabulary_domains = []
    
    """
    The list of the generated tables in the "vocab" schema.
    """    
    temporary_tables = {'vocabulary': [], 'isa': []}
    
    def is_term_reference(goal, schema_name, table_name, column_name, constraint_name):
        """
        Check if a constraint is a foreign key to a vocabulary term.
        """
        if schema_name not in ['vocabulary', 'isa'] or table_name not in vocabulary_orphans[schema_name]:
            table = goal.table(schema_name, table_name)
            for foreign_key in table.foreign_keys:
                if len(foreign_key.foreign_key_columns) == 1:
                    foreign_key_column = foreign_key.foreign_key_columns[0]
                    referenced_column = foreign_key.referenced_columns[0]
                    schema, constraint = foreign_key.names[0]
                    if constraint == constraint_name and column_name == referenced_column['column_name']:
                        return True
        return False
    
    def get_term_reference(goal, schema_name, table_name, constraint_name):
        """
        Get the reference column name for the given constraint.
        """
        if schema_name not in ['vocabulary'] or table_name not in vocabulary_orphans[schema_name]:
            table = goal.table(schema_name, table_name)
            for foreign_key in table.foreign_keys:
                if len(foreign_key.foreign_key_columns) == 1:
                    foreign_key_column = foreign_key.foreign_key_columns[0]
                    referenced_column = foreign_key.referenced_columns[0]
                    schema, constraint = foreign_key.names[0]
                    if constraint == constraint_name:
                        return referenced_column['column_name']
        return None
    
    def get_refereced_by(goal, schema_name, table_name, exclude_schema=None):
        """
        Get the "Referenced by:" tables for the given schema:table.
        Exclude from the result the tables from the schema mentioned by the "exclude_schema" parameter
        """
        ret = []
        for schema in goal.schemas.values():
            for table in schema.tables.values():
                for foreign_key in table.foreign_keys:
                    if len(foreign_key.referenced_columns) == 1:
                        referenced_column = foreign_key.referenced_columns[0]
                        if referenced_column['table_name'] == table_name and referenced_column['schema_name'] == schema_name:
                            foreign_key_column = foreign_key.foreign_key_columns[0]
                            if foreign_key_column['schema_name'] != exclude_schema:
                                constraint_name = foreign_key.names[0]
                                ret.append({'foreign_key': foreign_key_column, 'constraint_name': constraint_name})
        return ret
    
    def get_foreign_keys(goal, schema_name, table_name, exclude_schema=None):
        """
        Get the Foreign Keys tables for the given schema:table.
        Exclude from the result the Foreign Keys from the schema mentioned by the "exclude_schema" parameter
        """
        ret = []
        table = goal.table(schema_name, table_name)
        for foreign_key in table.foreign_keys:
            if len(foreign_key.foreign_key_columns) == 1:
                foreign_key_column = foreign_key.foreign_key_columns[0]
                referenced_column = foreign_key.referenced_columns[0]
                if referenced_column['schema_name'] != exclude_schema:
                    constraint_name = foreign_key.names[0]
                    ret.append({'foreign_key': foreign_key_column, 'constraint_name': constraint_name})
        return ret
    
    def print_domain_references():
        """
        Print the "Referenced by:" tables for the domain tables.
        """
        for table in domain_tables:
            print table
            for reference in domain_references[table]:
                print '\t%s' % reference
                
    def set_domain_references(goal):
        """
        Set the "Referenced by:" tables for the domain tables.
        Exclude from the result the tables from the domain tables
        """
        for table in domain_tables:
            domain_references[table] = get_refereced_by(goal, 'vocab', '%s_terms' % table, 'vocab')

        #print_domain_references()
                
    def collect_domain_references(goal):
        """
        Generate the SQL script to collect the usage of the domain terms.
        """
        set_domain_references(goal)
        out = file('%s/collect_used_terms.sql' % output, 'w')
        out.write('BEGIN;\n')
        out.write('\n')
        
        out.write('DROP SCHEMA IF EXISTS "temp_vocabularies" CASCADE;\n')
        out.write('CREATE SCHEMA "temp_vocabularies" AUTHORIZATION ermrest;')
        out.write('\n\n')
        
        for table in domain_tables:
            if len(domain_references[table]) == 0:
                out.write('CREATE TABLE "temp_vocabularies"."%s_terms_used" (name text PRIMARY KEY);\n' % table)
                out.write('ALTER TABLE "temp_vocabularies"."%s_terms_used" OWNER TO ermrest;\n' % table)
                out.write('\n')
                out.write('CREATE TABLE "temp_vocabularies"."%s_terms_not_used" (name text PRIMARY KEY);\n' % table)
                out.write('ALTER TABLE "temp_vocabularies"."%s_terms_not_used" OWNER TO ermrest;\n' % table)
                out.write('\n')
                continue
                
            out.write('CREATE TABLE "temp_vocabularies"."%s_terms_used" AS\n' % table)
            queries = []
            for reference in domain_references[table]:
                foreign_key = reference['foreign_key']
                schema_name = foreign_key['schema_name']
                table_name = foreign_key['table_name']
                column_name = foreign_key['column_name']
                queries.append('SELECT DISTINCT T1.name FROM  "vocab"."%s_terms" T1 JOIN "%s"."%s" T2 ON T1.dbxref = T2.%s' % (table, schema_name, table_name, column_name))
            out.write('\nUNION\n'.join(queries))
            out.write('\n;\n\n')
            out.write('ALTER TABLE "temp_vocabularies"."%s_terms_used" OWNER TO ermrest;\n' % table)
            out.write('ALTER TABLE "temp_vocabularies"."%s_terms_used" ADD PRIMARY KEY (name);\n' % table)
            out.write('\n')
            out.write('CREATE TABLE "temp_vocabularies"."%s_terms_not_used" AS\n' % table)
            out.write('SELECT name FROM "temp"."%s"\n' % table)
            out.write('EXCEPT\n')
            out.write('SELECT name FROM "temp_vocabularies"."%s_terms_used"\n' % table)
            out.write(';\n\n')
            out.write('ALTER TABLE "temp_vocabularies"."%s_terms_not_used" OWNER TO ermrest;\n' % table)
            out.write('ALTER TABLE "temp_vocabularies"."%s_terms_not_used" ADD PRIMARY KEY (name);\n' % table)
            out.write('\n')
            
        out.write('CREATE TABLE "temp_vocabularies"."all_terms_used" AS\n')
        queries = []
        for table in domain_tables:
            queries.append('SELECT DISTINCT name FROM  "temp_vocabularies"."%s_terms_used"' % (table))
            
        out.write('\nUNION\n'.join(queries))
        out.write('\n;\n\n')
        out.write('ALTER TABLE "temp_vocabularies"."all_terms_used" OWNER TO ermrest;\n')
        out.write('ALTER TABLE "temp_vocabularies"."all_terms_used" ADD PRIMARY KEY (name);\n')
        out.write('\n')
        
        out.write('CREATE TABLE "temp_vocabularies"."all_terms_not_used" AS\n')
        queries = []
        for table in domain_tables:
            queries.append('SELECT DISTINCT name FROM  "temp_vocabularies"."%s_terms_not_used"' % (table))
            
        out.write('\nUNION\n'.join(queries))
        out.write('\n;\n\n')
        out.write('ALTER TABLE "temp_vocabularies"."all_terms_not_used" OWNER TO ermrest;\n')
        out.write('ALTER TABLE "temp_vocabularies"."all_terms_not_used" ADD PRIMARY KEY (name);\n')
        out.write('\n')
        
        out.write('CREATE TABLE "temp_vocabularies"."all_terms" (name text PRIMARY KEY, mode text, cv text);\n\n')
        out.write('ALTER TABLE "temp_vocabularies"."all_terms" OWNER TO ermrest;\n')
        out.write('\n')
        out.write('INSERT INTO "temp_vocabularies"."all_terms" (name, mode)  SELECT name as name, \'used\' as mode FROM "temp_vocabularies"."all_terms_used";\n')
        out.write('INSERT INTO "temp_vocabularies"."all_terms" (name, mode) SELECT name as name, \'not used\' as mode FROM "temp_vocabularies"."all_terms_not_used" ON CONFLICT DO NOTHING;\n')
        out.write('\n')
        
        out.write('UPDATE "temp_vocabularies"."all_terms" T1 SET cv = (SELECT cv as cv FROM "data_commons"."cvterm" T2 WHERE T2.cv != \'facebase\' AND T2.cv != \'ocdm\' AND T1.name = T2.name LIMIT 1) WHERE T1.mode = \'used\';\n')
        out.write('UPDATE "temp_vocabularies"."all_terms" T1 SET cv = (SELECT cv as cv FROM "data_commons"."cvterm" T2 WHERE T2.cv = \'ocdm\' AND T1.name = T2.name LIMIT 1) WHERE T1.mode = \'used\' AND T1.cv IS NULL;\n')
        out.write('UPDATE "temp_vocabularies"."all_terms" T1 SET cv = (SELECT cv as cv FROM "data_commons"."cvterm" T2 WHERE T1.name = T2.name LIMIT 1) WHERE T1.mode = \'used\' AND T1.cv IS NULL;\n')
        out.write('SELECT _ermrest.model_change_event();\n')
        out.write('\n')
        
        out.write('COMMIT;\n')
        out.close()
        
        
    def set_schema_vocabularies_relations(goal, schema, tables):
        """
        Set the Foreign Keys and "Referenced by:" for the vocabulary tables of the schema.
        """
        for table in tables:
            references = get_refereced_by(goal, schema, table)
            if len(references) > 0:
                vocabulary_relations[schema][table] = {}
                vocabulary_relations[schema][table]['references'] = references
            foreign_keys = get_foreign_keys(goal, schema, table)
            if len(foreign_keys) > 0:
                if table not in vocabulary_relations[schema].keys():
                    vocabulary_relations[schema][table] = {}
                vocabulary_relations[schema][table]['foreign_keys'] = foreign_keys
        
    def print_schema_vocabularies_relations(schema, tables, out):
        """
        Print the vocabularies relations for the tables of the mentioned schema.
        """
        for table in tables:
            out.write('\n%s.%s\n' % (schema, table))
            relations = vocabulary_relations[schema].get(table, None)
            if relations != None:
                foreign_keys =  relations.get('foreign_keys', None)
                if foreign_keys != None:
                    out.write('\tForeign Keys:\n')
                    for foreign_key in foreign_keys:
                        out.write('\t\t%s\n' % foreign_key)
                references =  relations.get('references', None)
                if references != None:
                    out.write('\tRefereced By:\n')
                    for reference in references:
                        out.write('\t\t%s\n' % reference)
        
    def print_vocabularies_relations():
        """
        Print the vocabularies relations.
        """
        out = file('%s/vocabularies_tables.txt' % output, 'w')
        print_schema_vocabularies_relations('vocabulary', vocabulary_tables, out)
        out.write('\n')
        print_schema_vocabularies_relations('isa', isa_tables, out)
        out.close()
        
    def set_vocabularies_relations(goal):
        """
        Set the Foreign Keys and "Referenced by:" for the vocabulary tables.
        """
        set_schema_vocabularies_relations(goal, 'vocabulary', vocabulary_tables)
        set_schema_vocabularies_relations(goal, 'isa', isa_tables)
        print_vocabularies_relations()
        
    def has_external_referenced_by(references):
        """
        Check if it exist at least one "Referenced by:" table that does not refer a vocabulary table.
        """
        for reference in references:
            foreign_key = reference['foreign_key']
            if foreign_key['schema_name'] not in ['vocabulary', 'isa']:
                return True
            elif foreign_key['table_name'] not in vocabulary_tables and foreign_key['table_name'] not in isa_tables:
                return True
        return False
        
    def get_schema_vocabulary_orphans(schema, tables):
        """
        Get the schema tables that don't have a "Referenced by:" table other than a vocabulary table.
        """
        for table in tables:
            if vocabulary_relations[schema].get(table, None) == None or vocabulary_relations[schema][table].get('references', None) == None:
                vocabulary_orphans[schema].append(table)
            elif has_external_referenced_by(vocabulary_relations[schema][table]['references']) == False:
                vocabulary_orphans[schema].append(table)
        
    def get_vocabulary_orphans():
        """
        Get the tables that don't have a "Referenced by:" table other than a the vocabulary table.
        """
        get_schema_vocabulary_orphans('vocabulary', vocabulary_tables)
        get_schema_vocabulary_orphans('isa', isa_tables)
        
    def generate_clean_up():
        """
        Generate the clean_up.sql to drop the vocabularies orphan tables.
        """
        out = file('%s/clean_up.sql' % output, 'w')
        out.write('BEGIN;\n')
        out.write('\n')
        for mapping in mapping_terms:
            table = mapping['table']
            column = mapping['column']
            for from_value,to_value in mapping['mappings'].iteritems():
                out.write('UPDATE %s SET %s=\'%s\' WHERE %s=\'%s\';\n' % (table, column, to_value, column, from_value))
                
        out.write('\n')
        
        for table in vocabulary_orphans['vocabulary']:
            out.write('DROP TABLE "vocabulary"."%s" CASCADE;\n' % table)
        out.write('\n')
        for table in vocabulary_orphans['isa']:
            out.write('DROP TABLE "isa"."%s" CASCADE;\n' % table)
        
        out.write('\nSELECT _ermrest.model_change_event();\n')
        out.write('\n')
        
        out.write('COMMIT;\n')
        out.close()
        
    def set_vocabulary_schema_term_name(goal, schema, tables):
        """
        Set the vocabularies schema column name for the term
        """
        for table_name in tables:
            if  table_name not in vocabulary_orphans[schema]:
                table = goal.table(schema, table_name)
                column_definitions = table.column_definitions
                column_name = None
                for column_definition in column_definitions:
                    if column_definition.name == 'term':
                        column_name = 'term'
                        break
                    elif column_definition.name == 'name':
                        column_name = 'name'
                if column_name == None:
                    print 'vocab term name not found for "%s"."%s"' % (schema, table_name)
                else:
                    vocabulary_term_name[schema][table_name] = column_name
        
    def set_vocabulary_term_name(goal):
        """
        Set the vocabularies column name for the term
        """
        set_vocabulary_schema_term_name(goal, 'vocabulary', vocabulary_tables)
        set_vocabulary_schema_term_name(goal, 'isa', isa_tables)
        
    def is_in_unions(schema, table):
        """
        Check if a table is in a merged domain.
        """
        for domain in union_vocabularies.keys():
            tables = union_vocabularies[domain].get(schema, None)
            if tables != None:
                if table in tables:
                    return True
        return False
    
    def delete_not_used_terms(out):
        """
        Generate DELETE statements for the terms not used.
        """
        for table in vocabulary_tables:
            if table not in vocabulary_orphans['vocabulary']:
                references = vocabulary_relations['vocabulary'][table].get('references', None)
                if len(references) > 0:
                    term = vocabulary_term_name['vocabulary'][table]
                    queries = []
                    out.write('CREATE TABLE temp.temp_all_terms (name text PRIMARY KEY);\n')
                    out.write('ALTER TABLE temp.temp_all_terms OWNER TO ermrest;\n')
                    out.write('INSERT INTO temp.temp_all_terms(name) SELECT DISTINCT %s AS name FROM vocabulary.%s;\n' % (term, table))
                    out.write('CREATE TABLE temp.temp_used_terms (name text PRIMARY KEY);\n')
                    out.write('ALTER TABLE temp.temp_used_terms OWNER TO ermrest;\n')
                    for reference in references:
                        schema, constraint = reference['constraint_name']
                        foreign_key = reference['foreign_key']
                        schema_name = foreign_key['schema_name']
                        table_name = foreign_key['table_name']
                        column_name = foreign_key['column_name']
                        fk_column = get_term_reference(goal, '%s' % schema_name, '%s' % table_name, '%s' % constraint)
                        if schema_name not in vocabulary_orphans.keys() or table_name not in vocabulary_orphans[schema_name]:
                            queries.append('SELECT DISTINCT T1.%s FROM  "vocabulary"."%s" T1 JOIN "%s"."%s" T2 ON T1."%s" = T2.%s' % (term, table, schema_name, table_name, fk_column, column_name))
                    if len(queries) > 0:
                        out.write('INSERT INTO temp.temp_used_terms(name)\n%s\n;\n' % '\nUNION\n'.join(queries))
                        out.write('CREATE TABLE temp.temp_not_used_terms (name text PRIMARY KEY);\n')
                        out.write('ALTER TABLE temp.temp_not_used_terms OWNER TO ermrest;\n')
                        out.write('INSERT INTO temp.temp_not_used_terms(name)\nSELECT name AS name FROM temp.temp_all_terms\nEXCEPT\nSELECT name AS name FROM temp.temp_used_terms;\n')
                        out.write('DELETE FROM vocabulary.%s WHERE %s IN (SELECT name FROM temp.temp_not_used_terms);\n' % (table, term))
                        out.write('DROP TABLE temp.temp_not_used_terms;\n')
                    out.write('DROP TABLE temp.temp_all_terms;\n')
                    out.write('DROP TABLE temp.temp_used_terms;\n')
                    out.write('\n')
                
        for table in isa_tables:
            if table not in vocabulary_orphans['isa']:
                references = vocabulary_relations['isa'][table].get('references', None)
                if len(references) > 0:
                    term = vocabulary_term_name['isa'][table]
                    queries = []
                    out.write('CREATE TABLE temp.temp_all_terms (name text PRIMARY KEY);\n')
                    out.write('ALTER TABLE temp.temp_all_terms OWNER TO ermrest;\n')
                    out.write('INSERT INTO temp.temp_all_terms(name) SELECT DISTINCT %s AS name FROM isa.%s;\n' % (term, table))
                    out.write('CREATE TABLE temp.temp_used_terms (name text PRIMARY KEY);\n')
                    out.write('ALTER TABLE temp.temp_used_terms OWNER TO ermrest;\n')
                    for reference in references:
                        schema, constraint = reference['constraint_name']
                        foreign_key = reference['foreign_key']
                        schema_name = foreign_key['schema_name']
                        table_name = foreign_key['table_name']
                        column_name = foreign_key['column_name']
                        fk_column = get_term_reference(goal, '%s' % schema_name, '%s' % table_name, '%s' % constraint)
                        if schema_name not in vocabulary_orphans.keys() or table_name not in vocabulary_orphans[schema_name]:
                            queries.append('SELECT DISTINCT T1.%s FROM  "isa"."%s" T1 JOIN "%s"."%s" T2 ON T1."%s" = T2.%s' % (term, table, schema_name, table_name, fk_column, column_name))
                    if len(queries) > 0:
                        out.write('INSERT INTO temp.temp_used_terms(name)\n%s\n;\n' % '\nUNION\n'.join(queries))
                        out.write('CREATE TABLE temp.temp_not_used_terms (name text PRIMARY KEY);\n')
                        out.write('ALTER TABLE temp.temp_not_used_terms OWNER TO ermrest;\n')
                        out.write('INSERT INTO temp.temp_not_used_terms(name)\nSELECT name AS name FROM temp.temp_all_terms\nEXCEPT\nSELECT name AS name FROM temp.temp_used_terms;\n')
                        out.write('DELETE FROM isa.%s WHERE %s IN (SELECT name FROM temp.temp_not_used_terms);\n' % (table, term))
                        out.write('DROP TABLE temp.temp_not_used_terms;\n')
                    out.write('DROP TABLE temp.temp_all_terms;\n')
                    out.write('DROP TABLE temp.temp_used_terms;\n')
                    out.write('\n')
        
    def update_mapped_terms(out):
        """
        Update the terms with the values from the existing ontologies.
        """
        for table in vocabulary_tables:
            if table not in vocabulary_orphans['vocabulary']:
                term = vocabulary_term_name['vocabulary'][table]
                for name,value in mapped_terms.iteritems():
                    out.write('UPDATE vocabulary.%s SET %s = \'%s\' WHERE %s = \'%s\' AND \'%s\' NOT IN (SELECT %s FROM vocabulary.%s);\n' % (table, term, value, term, name, value, term, table))
                out.write('\n')
                
        for table in isa_tables:
            if table not in vocabulary_orphans['isa']:
                term = vocabulary_term_name['isa'][table]
                for name,value in mapped_terms.iteritems():
                    out.write('UPDATE isa.%s SET %s = \'%s\' WHERE %s = \'%s\' AND \'%s\' NOT IN (SELECT %s FROM isa.%s);\n' % (table, term, value, term, name, value, term, table))
                out.write('\n')
        
    def make_temp_schema():
        """
        Generate the "temp" schema.
        """
        out = file('%s/uberon.sql' % output, 'w')
        out.write('BEGIN;\n')
        out.write('%s\n' % make_temp_functions)
        
        delete_not_used_terms(out)
        update_mapped_terms(out)
        
        iri = []
        
        out.write('INSERT INTO temp.terms(name)\n')
        queries = []
        for table in vocabulary_tables:
            if table not in vocabulary_orphans['vocabulary']:
                column = vocabulary_term_name['vocabulary'][table]
                queries.append('SELECT DISTINCT %s AS name FROM vocabulary.%s' % (column, table))
                iri.append('SELECT temp.set_iri(\'%s\', \'%s\', \'%s\');\n' %('vocabulary', table, column))
                
        for table in isa_tables:
            if table not in vocabulary_orphans['isa']:
                column = vocabulary_term_name['isa'][table]
                queries.append('SELECT DISTINCT %s AS name FROM isa.%s' % (column, table))
                iri.append('SELECT temp.set_iri(\'%s\', \'%s\', \'%s\');\n' %('isa', table, column))
                
        out.write('\nUNION\n'.join(queries))
        out.write('\n;\n\n')
        
        for table in vocabulary_tables:
            if table not in vocabulary_orphans['vocabulary']:
                column = vocabulary_term_name['vocabulary'][table]
                table_name = table
                if table in union_vocabularies.keys():
                    table_name = 'vocabulary_%s' % table
                out.write('CREATE TABLE temp.%s AS SELECT DISTINCT %s AS name FROM vocabulary.%s;\n' % (table_name, column, table))
                out.write('ALTER TABLE temp.%s OWNER TO ermrest;\n\n' % table_name)
                temporary_tables['vocabulary'].append({
                                                       'original_name': '%s' % table,
                                                       'name': '%s' % table_name})
        
        for table in isa_tables:
            if table not in vocabulary_orphans['isa']:
                column = vocabulary_term_name['isa'][table]
                table_name = table
                if table in union_vocabularies.keys():
                    table_name = 'isa_%s' % table
                out.write('CREATE TABLE temp.%s AS SELECT DISTINCT %s AS name FROM isa.%s;\n' % (table_name, column, table))
                out.write('ALTER TABLE temp.%s OWNER TO ermrest;\n\n' % table_name)
                temporary_tables['isa'].append({
                                               'original_name': '%s' % table,
                                               'name': '%s' % table_name})
        
        out.write('\n')
        
        for domain in union_vocabularies.keys():
            queries = []
            for schema in union_vocabularies[domain].keys():
                for table in union_vocabularies[domain][schema]:
                    table_name = table
                    if table in union_vocabularies.keys():
                        table_name = '%s_%s' % (schema, table)
                    queries.append('SELECT DISTINCT name AS name FROM temp.%s' % table_name)
                    column = vocabulary_term_name[schema][table]
                    iri.append('SELECT temp.set_iri(\'%s\', \'%s\', \'%s\');\n' %(schema, table, column))
            out.write('CREATE TABLE temp.%s AS %s;\n' % (domain, ' UNION '.join(queries)))
            
        out.write('\n')
        
        out.write('CREATE TABLE temp.uberon AS\n')
        out.write('SELECT DISTINCT name,cv FROM data_commons.cvterm WHERE name IN (SELECT name FROM temp.terms);\n')
        out.write('ALTER TABLE temp.uberon OWNER TO ermrest;\n')
        out.write('\n')
        data_commons_ontologies_enclosed = []
        for ontology in data_commons_ontologies:
            data_commons_ontologies_enclosed.append('\'%s\'' % ontology)
        out.write('UPDATE temp.terms T1 SET cv = (SELECT cv FROM temp.uberon T2 WHERE T2.cv IN (%s) AND T1.name = T2.name LIMIT 1) WHERE name IN (SELECT name FROM temp.uberon);\n' % ','.join(data_commons_ontologies_enclosed))
        out.write('UPDATE temp.terms T1 SET cv = (SELECT cv FROM temp.uberon T2 WHERE T1.name = T2.name LIMIT 1) WHERE cv is NULL AND name IN (SELECT name FROM temp.uberon);\n')
        out.write('\n')
        
        for table in ['owl_terms', 'owl_predicates', 'ocdm', 'facebase', 'terms', 'uberon']:
            out.write('SELECT temp.make_facebase_temp_tables(\'temp\', \'%s\');\n' % table)
            
        out.write('\n')
        
        for table in vocabulary_tables:
            if table not in vocabulary_orphans['vocabulary']:
                table_name = table
                if table in union_vocabularies.keys():
                    table_name = 'vocabulary_%s' % table
                out.write('SELECT temp.make_facebase_temp_tables(\'temp\', \'%s\');\n' % table_name)
                
        for table in isa_tables:
            if table not in vocabulary_orphans['isa']:
                table_name = table
                if table in union_vocabularies.keys():
                    table_name = 'isa_%s' % table
                out.write('SELECT temp.make_facebase_temp_tables(\'temp\', \'%s\');\n' % table_name)
                
        out.write('\n')
        
        for table in union_vocabularies.keys():
            out.write('SELECT temp.make_facebase_temp_tables(\'temp\', \'%s\');\n' % table)
            
        out.write('\n')
        
        for table in ['ocdm', 'facebase', 'terms', 'uberon']:
            out.write('SELECT temp.make_temp_tables_annotations(\'temp\', \'%s\');\n' % table)
            
        out.write('\n')
        
        for line in iri:
            out.write('%s' % line)
            
        out.write('\n')
        out.write('\nSELECT _ermrest.model_change_event();\n')
        out.write('\n')
        
        out.write('COMMIT;\n')
        out.close()

    def get_domain_table(schema, table):
        """
        Get the "vocab" table.
        """
        for domain in union_vocabularies.keys():
            tables = union_vocabularies[domain].get(schema, None)
            if tables != None:
                if table in tables:
                    return domain
        return table
    
    def get_vocabulary_domains():
        """
        Generate the "vocab" domain tables.
        """
        for table in union_vocabularies.keys():
            vocabulary_domains.append(table)
            
        for table in vocabulary_tables:
            if is_in_unions('vocabulary', table) == False and table not in vocabulary_orphans['vocabulary']:
                vocabulary_domains.append(table)
                
        for table in isa_tables:
            if is_in_unions('isa', table) == False and table not in vocabulary_orphans['isa']:
                vocabulary_domains.append(table)
                

    def trace():
        """
        Trace the vocabulary orphans and domain tables.
        """
        print 'vocabulary orphans:'
        for orphan in vocabulary_orphans['vocabulary']:
            print '\t%s' % orphan
        print 'isa orphans:'
        for orphan in vocabulary_orphans['isa']:
            print '\t%s' % orphan
        print 'Domain Tables:'
        for domain in vocabulary_domains:
            print '\t%s' % domain
        
    def make_domain_script():
        """
        Generate the domain.sql script.
        """
        out = file('%s/domain.sql' % output, 'w')
        out.write('BEGIN;\n')
        out.write('%s\n' % domain_functions)
        out.write('\n')
        out.write('%s\n' % dataset_functions)
        out.write('\n')
        for domain in vocabulary_domains:
            out.write('SELECT data_commons.make_facebase_domain_tables(\'vocab\', \'%s\');\n' % domain)
        
        out.write('\n')
        for domain in vocabulary_domains:
            out.write('SELECT data_commons.load_facebase_domain_tables(\'vocab\', \'%s\');\n' % domain)
        
        out.write('\n')
        out.write('\nSELECT _ermrest.model_change_event();\n')
        out.write('\n')
        
        out.write('COMMIT;\n')
        out.close()
        
    def make_references_script(goal):
        """
        Generate the vocabulary vocabulary_references.sql script.
        """
        out = file('%s/vocabulary_references.sql' % output, 'w')
        out.write('BEGIN;\n')
        out.write('%s\n' % references_functions)
        out.write('\n')
        
        for schema in views.keys():
            for view in views[schema].keys():
                out.write('DROP VIEW %s.%s;\n' % (schema, view))
                        
        out.write('\n')
        
        for schema in triggers.keys():
            for table in triggers[schema].keys():
                for trigger in triggers[schema][table]:
                    for trigger_name in trigger.keys():
                        out.write('DROP TRIGGER %s ON %s.%s;\n' % (trigger_name, schema, table))
                        
        out.write('\n')
        
        for schema in duplicate_constraints.keys():
            for table in duplicate_constraints[schema].keys():
                for constraint in duplicate_constraints[schema][table]:
                    out.write('ALTER TABLE %s.%s DROP CONSTRAINT IF EXISTS %s;\n' % (schema, table, constraint))
                        
        out.write('\n')
        
        for table in vocabulary_tables:
            if table not in vocabulary_orphans['vocabulary']:
                foreign_keys = vocabulary_relations['vocabulary'][table].get('foreign_keys', None)
                if foreign_keys != None:
                    for foreign_key in foreign_keys:
                        schema, constraint = foreign_key['constraint_name']
                        out.write('ALTER TABLE vocabulary.%s DROP CONSTRAINT IF EXISTS %s;\n' % (table, constraint))
        out.write('\n')
                
        for table in isa_tables:
            if table not in vocabulary_orphans['isa']:
                references = vocabulary_relations['isa'][table].get('references', None)
                if references != None:
                    for reference in references:
                        schema, constraint = reference['constraint_name']
                        foreign_key = reference['foreign_key']
                        schema_name = foreign_key['schema_name']
                        table_name = foreign_key['table_name']
                        column_name = foreign_key['column_name']
                        term = vocabulary_term_name['isa'][table]
                        if is_term_reference(goal, schema_name, table_name, term, constraint):
                            out.write('ALTER TABLE %s.%s DROP CONSTRAINT IF EXISTS %s;\n' % (schema_name, table_name, constraint))
                            out.write('ALTER TABLE %s.%s ADD CONSTRAINT %s FOREIGN KEY (%s) REFERENCES isa.%s(%s) ON UPDATE CASCADE ON DELETE RESTRICT;\n' % (schema_name, table_name, constraint, column_name, table, term))
                            out.write('\n')
        
        out.write('\n')
        
        for table in vocabulary_tables:
            if table not in vocabulary_orphans['vocabulary']:
                references = vocabulary_relations['vocabulary'][table].get('references', None)
                if references != None:
                    for reference in references:
                        schema, constraint = reference['constraint_name']
                        foreign_key = reference['foreign_key']
                        schema_name = foreign_key['schema_name']
                        table_name = foreign_key['table_name']
                        column_name = foreign_key['column_name']
                        term = vocabulary_term_name['vocabulary'][table]
                        if is_term_reference(goal, schema_name, table_name, term, constraint):
                            out.write('ALTER TABLE %s.%s DROP CONSTRAINT IF EXISTS %s;\n' % (schema_name, table_name, constraint))
                            out.write('ALTER TABLE %s.%s ADD CONSTRAINT %s FOREIGN KEY (%s) REFERENCES vocabulary.%s(%s) ON UPDATE CASCADE ON DELETE RESTRICT;\n' % (schema_name, table_name, constraint, column_name, table, term))
                            out.write('\n')
        
        out.write('\n')
        
        for table in vocabulary_tables:
            if table not in vocabulary_orphans['vocabulary']:
                domain = get_domain_table('vocabulary', table)
                term = vocabulary_term_name['vocabulary'][table]
                out.write('SELECT data_commons.make_facebase_terms_references(\'vocabulary\', \'%s\', \'%s\', \'vocab\', \'%s\');\n' % (table, term, domain))
        
        out.write('\n')
        
        for table in isa_tables:
            if table not in vocabulary_orphans['isa']:
                domain = get_domain_table('isa', table)
                term = vocabulary_term_name['isa'][table]
                out.write('SELECT data_commons.make_facebase_terms_references(\'isa\', \'%s\', \'%s\', \'vocab\', \'%s\');\n' % (table, term, domain))
        
        out.write('\n')
        
        for table in vocabulary_tables:
            if table not in vocabulary_orphans['vocabulary']:
                references = vocabulary_relations['vocabulary'][table].get('references', None)
                term = vocabulary_term_name['vocabulary'][table]
                domain = get_domain_table('vocabulary', table)
                if references != None:
                    out.write('\n-- vocabulary.%s\n' % table)
                    for reference in references:
                        schema, constraint = reference['constraint_name']
                        foreign_key = reference['foreign_key']
                        schema_name = foreign_key['schema_name']
                        table_name = foreign_key['table_name']
                        column_name = foreign_key['column_name']
                        if schema_name != 'vocabulary':
                            fk_column = get_term_reference(goal, '%s' % schema_name, '%s' % table_name, '%s' % constraint)
                            if fk_column == 'id':
                                out.write('SELECT data_commons.make_facebase_references(\'%s\', \'%s\', \'%s\', \'vocabulary\', \'%s\', \'id\', \'%s\', \'%s\');\n' % (schema_name, table_name, column_name, table, term, domain))  
                            else:
                                out.write('SELECT data_commons.make_dataset_references(\'%s\', \'%s\', \'%s\', \'%s\');\n' % (schema_name, table_name, column_name, domain))
                                                            
        out.write('\n')
        
        for table in isa_tables:
            if table not in vocabulary_orphans['isa']:
                domain = get_domain_table('isa', table)
                references = vocabulary_relations['isa'][table].get('references', None)
                term = vocabulary_term_name['isa'][table]
                if references != None:
                    out.write('\n-- isa.%s\n' % table)
                    for reference in references:
                        schema, constraint = reference['constraint_name']
                        foreign_key = reference['foreign_key']
                        schema_name = foreign_key['schema_name']
                        table_name = foreign_key['table_name']
                        column_name = foreign_key['column_name']
                        if schema_name != 'vocabulary':
                            fk_column = get_term_reference(goal, '%s' % schema_name, '%s' % table_name, '%s' % constraint)
                            if fk_column == term:
                                out.write('SELECT data_commons.make_dataset_references(\'%s\', \'%s\', \'%s\', \'%s\');\n' % (schema_name, table_name, column_name, domain))
                            else:
                                out.write('SELECT data_commons.make_facebase_references(\'%s\', \'%s\', \'%s\', \'isa\', \'%s\', \'%s\', \'%s\', \'%s\');\n' % (schema_name, table_name, column_name, table, fk_column, term, domain))                
                                
                
        out.write('\n')
        
        for schema in views.keys():
            for view in views[schema].keys():
                out.write('CREATE VIEW %s.%s AS %s\n;\n' % (schema, view, views[schema][view]))
                        
        out.write('\n')
        
        out.write('%s\n' % set_pair_end)
        out.write('\n')
        
        for schema in triggers.keys():
            for table in triggers[schema].keys():
                for trigger in triggers[schema][table]:
                    for trigger_name, body in trigger.iteritems():
                        out.write('CREATE TRIGGER %s %s;\n' % (trigger_name, body))
                        
        out.write('\n')
        
        for dataset,tables in union_dataset.iteritems():
            out.write('SELECT data_commons.make_dataset_tables(\'isa\', \'dataset_%s\', \'%s\');\n' % (dataset, dataset))
            for table in tables:
                out.write('INSERT INTO isa.dataset_%s(dataset_id, %s, "RID", "RCB", "RMB", "RCT", "RMT") SELECT dataset_id as dataset_id, %s AS %s, "RID" as "RID", "RCB" AS "RCB", "RMB" AS "RMB", "RCT" AS "RCT", "RMT" AS "RMT" FROM isa.dataset_%s;\n' % (dataset, dataset, table, dataset, table))
            out.write('\n')
        
        out.write('\n')
        
        for table in vocabulary_tables:
            if table not in vocabulary_orphans['vocabulary']:
                out.write('DROP TABLE "vocabulary"."%s" CASCADE;\n' % table)
        out.write('\n')
        
        for table in isa_tables:
            if table not in vocabulary_orphans['isa']:
                out.write('DROP TABLE "isa"."%s" CASCADE;\n' % table)
                
        out.write('\n')
        
        for dataset,tables in union_dataset.iteritems():
            for table in tables:
                out.write('DROP TABLE "isa"."dataset_%s" CASCADE;\n' % table)
        
        out.write('\n')
        
        out.write('UPDATE temp.terms_iri T1 SET dbxref = (SELECT dbxref from data_commons.cvterm T2, temp.terms T3 where T1.name = T2.name AND T2.name = T3.name AND T2.cv = T3.cv);\n')
        out.write('INSERT INTO data_commons.dbxref(db,accession) SELECT \'URL\' AS db, iri AS accession FROM temp.terms_iri ON CONFLICT DO NOTHING;\n')
        out.write('INSERT INTO data_commons.cvterm_dbxref(cvterm, alternate_dbxref) SELECT dbxref AS cvterm, \'URL:\' || iri || \':\' AS alternate_dbxref FROM temp.terms_iri ON CONFLICT DO NOTHING;\n')
        
        out.write('\n')
        out.write('\nSELECT _ermrest.model_change_event();\n')
        out.write('\n')
        
        out.write('COMMIT;\n')
        out.close()
        
    def make_common_functions_script():
        """
        Generate the vocabulary 00_common_functions.sql script.
        """
        out = file('%s/00_common_functions.sql' % output, 'w')
        out.write('%s\n' % common_functions)
        out.close()
        
    def make_data_commons_ermrest_script():
        """
        Generate the vocabulary data_commons_ermrest.sql script.
        """
        out = file('%s/data_commons_ermrest.sql' % output, 'w')
        out.write('%s\n' % data_commons_ermrest)
        out.close()
        
    def make_data_commons_ocdm_script():
        """
        Generate the vocabulary data_commons_ocdm.sql script.
        """
        out = file('%s/data_commons_ocdm.sql' % output, 'w')
        out.write('%s\n' % data_commons_ocdm_prefix)
        out.write('\n')
        
        for cv in ocdm_sub_ontologies:
            out.write('INSERT INTO data_commons.cv (name, definition) VALUES(\'ocdm_%s\', \'Ontology of Craniofacial Development and Malformation\');\n' % cv)
            out.write('INSERT INTO data_commons.db (name, urlprefix, description) VALUES(\'ocdm_%s\', \'http://purl.org/sig/ont/ocdm\', \'Ontology of Craniofacial Development and Malformation\');\n' % cv.upper())
            
        out.write('\n')
        
        for cv in vocabulary_domains:
            out.write('INSERT INTO data_commons.cv (name, definition) VALUES(\'facebase_%s\', \'Resource for Craniofacial Researchers\');\n' % cv)
            out.write('INSERT INTO data_commons.db (name, urlprefix, description) VALUES(\'facebase_%s\', \'https://www.facebase.org/\', \'Resource for Craniofacial Researchers\');\n' % cv.upper())
            
        out.write('\n')
        
        out.write('%s\n' % data_commons_ocdm_suffix)
        out.close()
        
    def make_local_ocdm_script():
        """
        Generate the vocabulary local_ocdm.sql script.
        """
        out = file('%s/local_ocdm.sql' % output, 'w')
        out.write('%s\n' % local_ocdm_prefix)
        out.write('\n')
        
        for table in temporary_tables['vocabulary']:
            original_name = get_domain_table('vocabulary', table['original_name'])
            out.write('UPDATE temp.facebase SET cv = \'facebase_%s\' WHERE name IN (SELECT name FROM temp.%s);\n' % (original_name, table['name']))
        
        out.write('\n')
        
        for table in temporary_tables['isa']:
            original_name = get_domain_table('isa', table['original_name'])
            out.write('UPDATE temp.facebase SET cv = \'facebase_%s\' WHERE name IN (SELECT name FROM temp.%s);\n' % (original_name, table['name']))
        
        out.write('\n')
        out.write('%s\n' % local_ocdm_suffix)
        out.close()
        
    def make_facebase_terms_script():
        """
        Generate the table showing the FaceBase terms 
        together with the table they are coming from.
        """
        out = file('%s/facebase_terms.sql' % output, 'w')
        out.write('BEGIN;\n')
        out.write('\n')
        out.write('DROP SCHEMA IF EXISTS mappable CASCADE;\n')
        out.write('CREATE SCHEMA mappable AUTHORIZATION ermrest;\n')
        out.write('\n')
        out.write('CREATE TABLE mappable.cvterms (term text, schema_name text, table_name text, cv text, PRIMARY KEY (term, cv));\n')
        out.write('ALTER TABLE mappable.cvterms OWNER TO ermrest;\n')
        out.write('\n')
        for table in temporary_tables['vocabulary']:
            original_name = get_domain_table('vocabulary', table['original_name'])
            out.write('INSERT INTO mappable.cvterms (term, schema_name, table_name, cv) SELECT T1.name AS term, \'vocabulary\' AS schema_name, \'%s\' AS table_name, T2.cv AS cv FROM temp.%s T1 JOIN "vocab".%s_terms T2 ON T1.name = T2.name ON CONFLICT DO NOTHING;\n' % (original_name, table['name'], original_name))
            
        out.write('\n')
        
        for table in temporary_tables['isa']:
            original_name = get_domain_table('isa', table['original_name'])
            out.write('INSERT INTO mappable.cvterms (term, schema_name, table_name, cv) SELECT T1.name AS term, \'isa\' AS schema_name, \'%s\' AS table_name, T2.cv AS cv FROM temp.%s T1 JOIN "vocab".%s_terms T2 ON T1.name = T2.name ON CONFLICT DO NOTHING;\n' % (original_name, table['name'], original_name))
            
        out.write('\n')
        out.write('TRUNCATE _ermrest.data_version;\n')
        out.write('TRUNCATE _ermrest.model_version;\n')
        out.write('SELECT _ermrest.model_change_event();\n')
        out.write('\n')
        
        out.write('COMMIT;\n')
        out.write('\n')
        out.close()
        
    # could wrap in a deriva-qt GUI to use interactive login instead?
    credentials = json.load(open(credentialsfilename))
    catalog_number = int(catalog)
    #print credentials
    catalog = ErmrestCatalog('https', servername, catalog, credentials)
    goal = catalog.get_catalog_model()
    set_vocabularies_relations(goal)
    get_vocabulary_orphans()
    generate_clean_up()
    set_vocabulary_term_name(goal)
    make_temp_schema()
    get_vocabulary_domains()
    vocabulary_domains = sorted(vocabulary_domains)
    make_domain_script()
    make_references_script(goal)
    make_common_functions_script()
    make_data_commons_ermrest_script()
    make_data_commons_ocdm_script()
    make_local_ocdm_script()
    make_facebase_terms_script()
    
if __name__ == '__main__':
    assert len(sys.argv) >= 5, "required arguments: servername credentialsfilename catalog output [target]"
    servername = sys.argv[1]
    credentialsfilename = sys.argv[2]
    catalog = sys.argv[3]
    output = sys.argv[4]
    if len(sys.argv) == 6:
        target = sys.argv[5]
    else:
        target = 'all'
    exit(main(servername, credentialsfilename, catalog, output, target))

