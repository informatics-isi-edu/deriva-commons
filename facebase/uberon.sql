-- begin transaction

BEGIN;

DROP SCHEMA IF EXISTS temp;
CREATE SCHEMA temp AUTHORIZATION ermrest;

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

INSERT INTO temp.terms(name)
SELECT DISTINCT term AS name FROM vocabulary.anatomy
UNION
SELECT DISTINCT name AS name FROM vocabulary.chemical_entities
UNION
SELECT DISTINCT name AS name FROM vocabulary.cvnames
UNION
SELECT DISTINCT term AS name FROM vocabulary.file_format
UNION
SELECT DISTINCT term AS name FROM vocabulary.gender
UNION
SELECT DISTINCT term AS name FROM vocabulary.gene
UNION
SELECT DISTINCT name AS name FROM vocabulary.gene_summary
UNION
SELECT DISTINCT term AS name FROM vocabulary.genotype
UNION
SELECT DISTINCT term AS name FROM vocabulary.histone_modification
UNION
SELECT DISTINCT term AS name FROM vocabulary.image_creation_device
UNION
SELECT DISTINCT term AS name FROM vocabulary.mapping_assembly
UNION
SELECT DISTINCT term AS name FROM vocabulary.molecule_type
UNION
SELECT DISTINCT term AS name FROM vocabulary.mutation
UNION
SELECT DISTINCT term AS name FROM vocabulary.origin
UNION
SELECT DISTINCT term AS name FROM vocabulary.output_type
UNION
SELECT DISTINCT term AS name FROM vocabulary.paired_end_or_single_read
UNION
SELECT DISTINCT name AS name FROM vocabulary.phenotype
UNION
SELECT DISTINCT term AS name FROM vocabulary.rnaseq_selection
UNION
SELECT DISTINCT term AS name FROM vocabulary.sample_type
UNION
SELECT DISTINCT term AS name FROM vocabulary.sequencing_data_direction
UNION
SELECT DISTINCT term AS name FROM vocabulary.species
UNION
SELECT DISTINCT term AS name FROM vocabulary.specimen
UNION
SELECT DISTINCT term AS name FROM vocabulary.stage
UNION
SELECT DISTINCT term AS name FROM vocabulary.strain
UNION
SELECT DISTINCT term AS name FROM vocabulary.strandedness
UNION
SELECT DISTINCT term AS name FROM vocabulary.target_of_assay
UNION
SELECT DISTINCT term AS name FROM isa.data_type
UNION
SELECT DISTINCT term AS name FROM isa.human_age
UNION
SELECT DISTINCT term AS name FROM isa.human_age_stage
UNION
SELECT DISTINCT term AS name FROM isa.human_anatomic_source
UNION
SELECT DISTINCT term AS name FROM isa.human_enhancer
UNION
SELECT DISTINCT term AS name FROM isa.human_gender
UNION
SELECT DISTINCT term AS name FROM isa.instrument
UNION
SELECT DISTINCT term AS name FROM isa.mouse_age_stage
UNION
SELECT DISTINCT term AS name FROM isa.mouse_anatomic_source
UNION
SELECT DISTINCT term AS name FROM isa.mouse_enhancer
UNION
SELECT DISTINCT term AS name FROM isa.mouse_gene
UNION
SELECT DISTINCT term AS name FROM isa.mouse_genetic_background
UNION
SELECT DISTINCT term AS name FROM isa.mouse_genotype
UNION
SELECT DISTINCT term AS name FROM isa.mouse_mutation
UNION
SELECT DISTINCT term AS name FROM isa.mouse_theiler_stage
UNION
SELECT DISTINCT term AS name FROM isa.organism
UNION
SELECT DISTINCT term AS name FROM isa.zebrafish_age_stage
UNION
SELECT DISTINCT term AS name FROM isa.zebrafish_anatomic_source
UNION
SELECT DISTINCT term AS name FROM isa.zebrafish_genotype
UNION
SELECT DISTINCT term AS name FROM isa.zebrafish_mutation
;
            
            
CREATE TABLE temp.anatomy AS SELECT DISTINCT term AS name FROM vocabulary.anatomy;
ALTER TABLE temp.anatomy OWNER TO ermrest;

CREATE TABLE temp.chemical_entities AS SELECT DISTINCT name AS name FROM vocabulary.chemical_entities;
ALTER TABLE temp.chemical_entities OWNER TO ermrest;

CREATE TABLE temp.cvnames AS SELECT DISTINCT name AS name FROM vocabulary.cvnames;
ALTER TABLE temp.cvnames OWNER TO ermrest;

CREATE TABLE temp.file_format AS SELECT DISTINCT term AS name FROM vocabulary.file_format;
ALTER TABLE temp.file_format OWNER TO ermrest;

CREATE TABLE temp.gender AS SELECT DISTINCT term AS name FROM vocabulary.gender UNION SELECT DISTINCT term AS name FROM isa.human_gender;
ALTER TABLE temp.gender OWNER TO ermrest;

CREATE TABLE temp.gene AS SELECT DISTINCT term AS name FROM vocabulary.gene UNION SELECT DISTINCT term AS name FROM isa.mouse_gene;
ALTER TABLE temp.gene OWNER TO ermrest;

CREATE TABLE temp.gene_summary AS SELECT DISTINCT name AS name FROM vocabulary.gene_summary;
ALTER TABLE temp.gene OWNER TO ermrest;

CREATE TABLE temp.genotype AS SELECT DISTINCT term AS name FROM vocabulary.genotype UNION SELECT DISTINCT term AS name FROM isa.mouse_genotype UNION SELECT DISTINCT term AS name FROM isa.zebrafish_genotype;
ALTER TABLE temp.genotype OWNER TO ermrest;

CREATE TABLE temp.histone_modification AS SELECT DISTINCT term AS name FROM vocabulary.histone_modification;
ALTER TABLE temp.histone_modification OWNER TO ermrest;

CREATE TABLE temp.image_creation_device AS SELECT DISTINCT term AS name FROM vocabulary.image_creation_device;
ALTER TABLE temp.image_creation_device OWNER TO ermrest;

CREATE TABLE temp.mapping_assembly AS SELECT DISTINCT term AS name FROM vocabulary.mapping_assembly;
ALTER TABLE temp.mapping_assembly OWNER TO ermrest;

CREATE TABLE temp.molecule_type AS SELECT DISTINCT term AS name FROM vocabulary.molecule_type;
ALTER TABLE temp.molecule_type OWNER TO ermrest;

CREATE TABLE temp.mutation AS SELECT DISTINCT term AS name FROM vocabulary.mutation UNION SELECT DISTINCT term AS name FROM isa.mouse_mutation UNION SELECT DISTINCT term AS name FROM isa.zebrafish_mutation;
ALTER TABLE temp.mutation OWNER TO ermrest;

CREATE TABLE temp.origin AS SELECT DISTINCT term AS name FROM vocabulary.origin;
ALTER TABLE temp.origin OWNER TO ermrest;

CREATE TABLE temp.output_type AS SELECT DISTINCT term AS name FROM vocabulary.output_type;
ALTER TABLE temp.output_type OWNER TO ermrest;

CREATE TABLE temp.paired_end_or_single_read AS SELECT DISTINCT term AS name FROM vocabulary.paired_end_or_single_read;
ALTER TABLE temp.paired_end_or_single_read OWNER TO ermrest;

CREATE TABLE temp.phenotype AS SELECT DISTINCT name AS name FROM vocabulary.phenotype;
ALTER TABLE temp.phenotype OWNER TO ermrest;

CREATE TABLE temp.rnaseq_selection AS SELECT DISTINCT term AS name FROM vocabulary.rnaseq_selection;
ALTER TABLE temp.rnaseq_selection OWNER TO ermrest;

CREATE TABLE temp.sample_type AS SELECT DISTINCT term AS name FROM vocabulary.sample_type;
ALTER TABLE temp.sample_type OWNER TO ermrest;

CREATE TABLE temp.sequencing_data_direction AS SELECT DISTINCT term AS name FROM vocabulary.sequencing_data_direction;
ALTER TABLE temp.sequencing_data_direction OWNER TO ermrest;

CREATE TABLE temp.species AS SELECT DISTINCT term AS name FROM vocabulary.species;
ALTER TABLE temp.species OWNER TO ermrest;

CREATE TABLE temp.specimen AS SELECT DISTINCT term AS name FROM vocabulary.specimen;
ALTER TABLE temp.specimen OWNER TO ermrest;

CREATE TABLE temp.stage AS SELECT DISTINCT term AS name FROM vocabulary.stage;
ALTER TABLE temp.stage OWNER TO ermrest;

CREATE TABLE temp.strain AS SELECT DISTINCT term AS name FROM vocabulary.strain;
ALTER TABLE temp.strain OWNER TO ermrest;

CREATE TABLE temp.strandedness AS SELECT DISTINCT term AS name FROM vocabulary.strandedness;
ALTER TABLE temp.strandedness OWNER TO ermrest;

CREATE TABLE temp.target_of_assay AS SELECT DISTINCT term AS name FROM vocabulary.target_of_assay;
ALTER TABLE temp.target_of_assay OWNER TO ermrest;

CREATE TABLE temp.theiler_stage AS SELECT DISTINCT term AS name FROM vocabulary.theiler_stage UNION SELECT DISTINCT term AS name FROM isa.mouse_theiler_stage;
ALTER TABLE temp.theiler_stage OWNER TO ermrest;

CREATE TABLE temp.data_type AS SELECT DISTINCT term AS name FROM isa.data_type;
ALTER TABLE temp.data_type OWNER TO ermrest;

CREATE TABLE temp.human_age AS SELECT DISTINCT term AS name FROM isa.human_age;
ALTER TABLE temp.human_age OWNER TO ermrest;

CREATE TABLE temp.age_stage AS SELECT DISTINCT term AS name FROM isa.human_age_stage UNION SELECT DISTINCT term AS name FROM isa.mouse_age_stage UNION SELECT DISTINCT term AS name FROM isa.zebrafish_age_stage;
ALTER TABLE temp.age_stage OWNER TO ermrest;

CREATE TABLE temp.anatomic_source AS SELECT DISTINCT term AS name FROM isa.human_anatomic_source UNION SELECT DISTINCT term AS name FROM isa.mouse_anatomic_source UNION SELECT DISTINCT term AS name FROM isa.zebrafish_anatomic_source;
ALTER TABLE temp.anatomic_source OWNER TO ermrest;

CREATE TABLE temp.enhancer AS SELECT DISTINCT term AS name FROM isa.human_enhancer UNION SELECT DISTINCT term AS name FROM isa.mouse_enhancer;
ALTER TABLE temp.enhancer OWNER TO ermrest;

CREATE TABLE temp.instrument AS SELECT DISTINCT term AS name FROM isa.instrument;
ALTER TABLE temp.instrument OWNER TO ermrest;

CREATE TABLE temp.mouse_genetic_background AS SELECT DISTINCT term AS name FROM isa.mouse_genetic_background;
ALTER TABLE temp.mouse_genetic_background OWNER TO ermrest;

CREATE TABLE temp.organism AS SELECT DISTINCT term AS name FROM isa.organism;
ALTER TABLE temp.organism OWNER TO ermrest;

CREATE TABLE temp.uberon AS
SELECT DISTINCT name,cv FROM data_commons.cvterm WHERE name IN (SELECT name FROM temp.terms);
ALTER TABLE temp.uberon OWNER TO ermrest;

UPDATE temp.terms T1 SET cv = (SELECT cv FROM temp.uberon T2 WHERE T1.name = T2.name LIMIT 1) WHERE name IN (SELECT name FROM temp.uberon);

SELECT temp.make_facebase_temp_tables('temp', 'owl_terms');
SELECT temp.make_facebase_temp_tables('temp', 'owl_predicates');
SELECT temp.make_facebase_temp_tables('temp', 'ocdm');
SELECT temp.make_facebase_temp_tables('temp', 'facebase');
SELECT temp.make_facebase_temp_tables('temp', 'terms');
SELECT temp.make_facebase_temp_tables('temp', 'uberon');

SELECT temp.make_facebase_temp_tables('temp', 'anatomy');
SELECT temp.make_facebase_temp_tables('temp', 'chemical_entities');
SELECT temp.make_facebase_temp_tables('temp', 'cvnames');
SELECT temp.make_facebase_temp_tables('temp', 'file_format');
SELECT temp.make_facebase_temp_tables('temp', 'gender');
SELECT temp.make_facebase_temp_tables('temp', 'gene');
SELECT temp.make_facebase_temp_tables('temp', 'gene_summary');
SELECT temp.make_facebase_temp_tables('temp', 'genotype');
SELECT temp.make_facebase_temp_tables('temp', 'histone_modification');
SELECT temp.make_facebase_temp_tables('temp', 'image_creation_device');
SELECT temp.make_facebase_temp_tables('temp', 'mapping_assembly');
SELECT temp.make_facebase_temp_tables('temp', 'molecule_type');
SELECT temp.make_facebase_temp_tables('temp', 'mutation');
SELECT temp.make_facebase_temp_tables('temp', 'origin');
SELECT temp.make_facebase_temp_tables('temp', 'output_type');
SELECT temp.make_facebase_temp_tables('temp', 'paired_end_or_single_read');
SELECT temp.make_facebase_temp_tables('temp', 'phenotype');
SELECT temp.make_facebase_temp_tables('temp', 'rnaseq_selection');
SELECT temp.make_facebase_temp_tables('temp', 'sample_type');
SELECT temp.make_facebase_temp_tables('temp', 'sequencing_data_direction');
SELECT temp.make_facebase_temp_tables('temp', 'species');
SELECT temp.make_facebase_temp_tables('temp', 'specimen');
SELECT temp.make_facebase_temp_tables('temp', 'stage');
SELECT temp.make_facebase_temp_tables('temp', 'strain');
SELECT temp.make_facebase_temp_tables('temp', 'strandedness');
SELECT temp.make_facebase_temp_tables('temp', 'target_of_assay');
SELECT temp.make_facebase_temp_tables('temp', 'theiler_stage');
SELECT temp.make_facebase_temp_tables('temp', 'data_type');
SELECT temp.make_facebase_temp_tables('temp', 'human_age');
SELECT temp.make_facebase_temp_tables('temp', 'age_stage');
SELECT temp.make_facebase_temp_tables('temp', 'anatomic_source');
SELECT temp.make_facebase_temp_tables('temp', 'enhancer');
SELECT temp.make_facebase_temp_tables('temp', 'instrument');
SELECT temp.make_facebase_temp_tables('temp', 'mouse_genetic_background');
SELECT temp.make_facebase_temp_tables('temp', 'organism');

SELECT temp.make_temp_tables_annotations('temp', 'ocdm');
SELECT temp.make_temp_tables_annotations('temp', 'facebase');
SELECT temp.make_temp_tables_annotations('temp', 'terms');
SELECT temp.make_temp_tables_annotations('temp', 'uberon');


-- update ermrest
TRUNCATE _ermrest.data_version;
TRUNCATE _ermrest.model_version;
SELECT _ermrest.model_change_event();


COMMIT;

