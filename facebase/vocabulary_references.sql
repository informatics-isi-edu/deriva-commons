-- begin transaction

BEGIN;

CREATE OR REPLACE FUNCTION data_commons.make_facebase_references(schema_name name, table_name name, column_name name, vocabulary_schema name, vocabulary_table name, vocabulary_id name, vocabulary_dbxref name) RETURNS BOOLEAN AS $$
DECLARE
   cvterm_name name = vocabulary_table || '_terms';
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
		ADD CONSTRAINT %I_%I_fkey FOREIGN KEY (%I) REFERENCES "Vocabulary".%I(dbxref)',
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
		ADD CONSTRAINT %I_%I_fkey FOREIGN KEY (%I) REFERENCES "Vocabulary".%I(dbxref)',
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

ALTER TABLE vocabulary.anatomy DROP CONSTRAINT anatomy_species_fkey;
ALTER TABLE vocabulary.chromatin_modifier DROP CONSTRAINT chromatin_modifier_species_fkey;
ALTER TABLE vocabulary.gender DROP CONSTRAINT gender_species_fkey;
ALTER TABLE vocabulary.gene DROP CONSTRAINT gene_species_fkey;
ALTER TABLE vocabulary.genotype DROP CONSTRAINT genotype_species_fkey;
ALTER TABLE vocabulary.mutation DROP CONSTRAINT mutation_species_fkey;
ALTER TABLE vocabulary.origin DROP CONSTRAINT origin_species_fkey;
ALTER TABLE vocabulary.stage DROP CONSTRAINT stage_species_fkey;
ALTER TABLE vocabulary.strain DROP CONSTRAINT strain_species_fkey;
ALTER TABLE vocabulary.theiler_stage DROP CONSTRAINT theiler_stage_species_fkey;
ALTER TABLE vocabulary.transcription_factor DROP CONSTRAINT transcription_factor_species_fkey;


ALTER TABLE isa.dataset_human_age DROP CONSTRAINT dataset_human_age_human_age_fkey;
ALTER TABLE isa.dataset_human_age ADD CONSTRAINT dataset_human_age_human_age_fkey FOREIGN KEY (human_age) REFERENCES isa.human_age(term) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE isa.imaging DROP CONSTRAINT imaging_equipment_model_fkey;
ALTER TABLE isa.imaging ADD CONSTRAINT imaging_equipment_model_fkey FOREIGN KEY (equipment_model) REFERENCES isa.instrument(term) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE isa.dataset_mouse_theiler_stage DROP CONSTRAINT dataset_mouse_theiler_stage_mouse_theiler_stage_fkey;
ALTER TABLE isa.dataset_mouse_theiler_stage ADD CONSTRAINT dataset_mouse_theiler_stage_mouse_theiler_stage_fkey FOREIGN KEY (mouse_theiler_stage) REFERENCES isa.mouse_theiler_stage(term) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE isa.dataset_zebrafish_mutation DROP CONSTRAINT dataset_zebrafish_mutation_zebrafish_mutation_fkey;
ALTER TABLE isa.dataset_zebrafish_mutation ADD CONSTRAINT dataset_zebrafish_mutation_zebrafish_mutation_fkey FOREIGN KEY (zebrafish_mutation) REFERENCES isa.zebrafish_mutation(term) ON UPDATE CASCADE ON DELETE RESTRICT;


SELECT data_commons.make_facebase_terms_references('vocabulary', 'anatomy', 'term', 'Vocabulary', 'anatomy');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'chemical_entities', 'name', 'Vocabulary', 'chemical_entities');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'cvnames', 'name', 'Vocabulary', 'cvnames');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'file_format', 'term', 'Vocabulary', 'file_format');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'gender', 'term', 'Vocabulary', 'gender');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'gene', 'term', 'Vocabulary', 'gene');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'gene_summary', 'name', 'Vocabulary', 'gene_summary');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'genotype', 'term', 'Vocabulary', 'genotype');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'histone_modification', 'term', 'Vocabulary', 'histone_modification');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'image_creation_device', 'term', 'Vocabulary', 'image_creation_device');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'mapping_assembly', 'term', 'Vocabulary', 'mapping_assembly');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'molecule_type', 'term', 'Vocabulary', 'molecule_type');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'mutation', 'term', 'Vocabulary', 'mutation');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'origin', 'term', 'Vocabulary', 'origin');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'output_type', 'term', 'Vocabulary', 'output_type');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'paired_end_or_single_read', 'term', 'Vocabulary', 'paired_end_or_single_read');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'phenotype', 'name', 'Vocabulary', 'phenotype');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'rnaseq_selection', 'term', 'Vocabulary', 'rnaseq_selection');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'sample_type', 'term', 'Vocabulary', 'sample_type');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'sequencing_data_direction', 'term', 'Vocabulary', 'sequencing_data_direction');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'species', 'term', 'Vocabulary', 'species');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'specimen', 'term', 'Vocabulary', 'specimen');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'stage', 'term', 'Vocabulary', 'stage');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'strain', 'term', 'Vocabulary', 'strain');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'strandedness', 'term', 'Vocabulary', 'strandedness');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'target_of_assay', 'term', 'Vocabulary', 'target_of_assay');
SELECT data_commons.make_facebase_terms_references('vocabulary', 'theiler_stage', 'term', 'Vocabulary', 'theiler_stage');

SELECT data_commons.make_facebase_terms_references('isa', 'data_type', 'term', 'Vocabulary', 'data_type');
SELECT data_commons.make_facebase_terms_references('isa', 'human_age', 'term', 'Vocabulary', 'human_age');
SELECT data_commons.make_facebase_terms_references('isa', 'human_age_stage', 'term', 'Vocabulary', 'age_stage');
SELECT data_commons.make_facebase_terms_references('isa', 'human_anatomic_source', 'term', 'Vocabulary', 'anatomic_source');
SELECT data_commons.make_facebase_terms_references('isa', 'human_enhancer', 'term', 'Vocabulary', 'enhancer');
SELECT data_commons.make_facebase_terms_references('isa', 'human_gender', 'term', 'Vocabulary', 'gender');
SELECT data_commons.make_facebase_terms_references('isa', 'instrument', 'term', 'Vocabulary', 'instrument');
SELECT data_commons.make_facebase_terms_references('isa', 'mouse_age_stage', 'term', 'Vocabulary', 'age_stage');
SELECT data_commons.make_facebase_terms_references('isa', 'mouse_anatomic_source', 'term', 'Vocabulary', 'anatomic_source');
SELECT data_commons.make_facebase_terms_references('isa', 'mouse_enhancer', 'term', 'Vocabulary', 'enhancer');
SELECT data_commons.make_facebase_terms_references('isa', 'mouse_gene', 'term', 'Vocabulary', 'gene');
SELECT data_commons.make_facebase_terms_references('isa', 'mouse_genetic_background', 'term', 'Vocabulary', 'mouse_genetic_background');
SELECT data_commons.make_facebase_terms_references('isa', 'mouse_genotype', 'term', 'Vocabulary', 'genotype');
SELECT data_commons.make_facebase_terms_references('isa', 'mouse_mutation', 'term', 'Vocabulary', 'mutation');
SELECT data_commons.make_facebase_terms_references('isa', 'mouse_theiler_stage', 'term', 'Vocabulary', 'theiler_stage');
SELECT data_commons.make_facebase_terms_references('isa', 'organism', 'term', 'Vocabulary', 'organism');
SELECT data_commons.make_facebase_terms_references('isa', 'zebrafish_age_stage', 'term', 'Vocabulary', 'age_stage');
SELECT data_commons.make_facebase_terms_references('isa', 'zebrafish_anatomic_source', 'term', 'Vocabulary', 'anatomic_source');
SELECT data_commons.make_facebase_terms_references('isa', 'zebrafish_genotype', 'term', 'Vocabulary', 'genotype');
SELECT data_commons.make_facebase_terms_references('isa', 'zebrafish_mutation', 'term', 'Vocabulary', 'mutation');

-- vocabulary.anatomy
SELECT data_commons.make_facebase_references('viz', 'volume', 'anatomy', 'vocabulary', 'anatomy', 'id', 'term');
SELECT data_commons.make_facebase_references('viz', 'mesh', 'anatomy', 'vocabulary', 'anatomy', 'id', 'term');
SELECT data_commons.make_facebase_references('viz', 'landmark', 'anatomy', 'vocabulary', 'anatomy', 'id', 'term');
SELECT data_commons.make_facebase_references('viz', 'model', 'anatomy', 'vocabulary', 'anatomy', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'sample', 'anatomy', 'vocabulary', 'anatomy', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample', 'anatomy', 'vocabulary', 'anatomy', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'clinical_assay', 'anatomy', 'vocabulary', 'anatomy', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'imaging_data', 'anatomy', 'vocabulary', 'anatomy', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample_summary', 'anatomy', 'vocabulary', 'anatomy', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'imaging', 'anatomy', 'vocabulary', 'anatomy', 'id', 'term');

-- vocabulary.chemical_entities
SELECT data_commons.make_facebase_references('isa', 'image_staining', 'stain', 'vocabulary', 'chemical_entities', 'id', 'name');

-- vocabulary.cvnames

-- vocabulary.file_format
SELECT data_commons.make_facebase_references('legacy', 'file', 'file_format', 'vocabulary', 'file_format', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'track_file', 'file_format', 'vocabulary', 'file_format', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'imaging_data', 'file_type', 'vocabulary', 'file_format', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'sequencing_data', 'file_type', 'vocabulary', 'file_format', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'processed_data', 'file_type', 'vocabulary', 'file_format', 'id', 'term');

-- vocabulary.gender
SELECT data_commons.make_facebase_references('isa', 'biosample', 'gender', 'vocabulary', 'gender', 'id', 'term');

-- vocabulary.gene
SELECT data_commons.make_facebase_references('isa', 'sample', 'gene', 'vocabulary', 'gene', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample', 'gene', 'vocabulary', 'gene', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'clinical_assay', 'gene', 'vocabulary', 'gene', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample_summary', 'gene', 'vocabulary', 'gene', 'id', 'term');

-- vocabulary.gene_summary
SELECT data_commons.make_facebase_references('isa', 'dataset', 'gene_summary', 'vocabulary', 'gene_summary', 'id', 'name');

-- vocabulary.genotype
SELECT data_commons.make_facebase_references('isa', 'sample', 'genotype', 'vocabulary', 'genotype', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample', 'genotype', 'vocabulary', 'genotype', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'clinical_assay', 'genotype', 'vocabulary', 'genotype', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample_summary', 'genotype', 'vocabulary', 'genotype', 'id', 'term');

-- vocabulary.histone_modification
SELECT data_commons.make_facebase_references('isa', 'experiment', 'histone_modification', 'vocabulary', 'histone_modification', 'id', 'term');

-- vocabulary.image_creation_device
SELECT data_commons.make_facebase_references('isa', 'imaging_data', 'device', 'vocabulary', 'image_creation_device', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'imaging', 'device', 'vocabulary', 'image_creation_device', 'id', 'term');

-- vocabulary.mapping_assembly
SELECT data_commons.make_facebase_references('isa', 'processed_data', 'mapping_assembly', 'vocabulary', 'mapping_assembly', 'id', 'term');

-- vocabulary.molecule_type
SELECT data_commons.make_facebase_references('isa', 'experiment', 'molecule_type', 'vocabulary', 'molecule_type', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'assay', 'molecule_type', 'vocabulary', 'molecule_type', 'id', 'term');

-- vocabulary.mutation
SELECT data_commons.make_facebase_references('isa', 'biosample', 'mutation', 'vocabulary', 'mutation', 'id', 'term');

-- vocabulary.origin
SELECT data_commons.make_facebase_references('isa', 'biosample', 'origin', 'vocabulary', 'origin', 'id', 'term');

-- vocabulary.output_type
SELECT data_commons.make_facebase_references('isa', 'processed_data', 'output_type', 'vocabulary', 'output_type', 'id', 'term');

-- vocabulary.paired_end_or_single_read
SELECT data_commons.make_facebase_references('isa', 'sequencing_data', 'paired_end_or_single_read', 'vocabulary', 'paired_end_or_single_read', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'assay', 'paired_end_or_single_read', 'vocabulary', 'paired_end_or_single_read', 'id', 'term');

-- vocabulary.phenotype
SELECT data_commons.make_facebase_references('isa', 'sample', 'phenotype', 'vocabulary', 'phenotype', 'id', 'name');
SELECT data_commons.make_facebase_references('isa', 'biosample', 'phenotype', 'vocabulary', 'phenotype', 'id', 'name');
SELECT data_commons.make_facebase_references('isa', 'clinical_assay', 'phenotype', 'vocabulary', 'phenotype', 'id', 'name');
-- SELECT data_commons.make_facebase_references('isa', 'dataset_phenotype', 'phenotype', 'vocabulary', 'phenotype', 'id', 'name');
SELECT data_commons.make_facebase_references('isa', 'biosample_summary', 'phenotype', 'vocabulary', 'phenotype', 'id', 'name');

-- vocabulary.rnaseq_selection
SELECT data_commons.make_facebase_references('isa', 'experiment', 'rnaseq_selection', 'vocabulary', 'rnaseq_selection', 'id', 'term');

-- vocabulary.sample_type
SELECT data_commons.make_facebase_references('isa', 'assay', 'sample_type', 'vocabulary', 'sample_type', 'id', 'term');

-- vocabulary.sequencing_data_direction
SELECT data_commons.make_facebase_references('isa', 'sequencing_data', 'direction', 'vocabulary', 'sequencing_data_direction', 'id', 'term');

-- vocabulary.species
SELECT data_commons.make_facebase_references('isa', 'sample', 'species', 'vocabulary', 'species', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample', 'species', 'vocabulary', 'species', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'clinical_assay', 'species', 'vocabulary', 'species', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample_summary', 'species', 'vocabulary', 'species', 'id', 'term');

-- vocabulary.specimen
SELECT data_commons.make_facebase_references('isa', 'sample', 'specimen', 'vocabulary', 'specimen', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample', 'specimen', 'vocabulary', 'specimen', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'clinical_assay', 'specimen', 'vocabulary', 'specimen', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample_summary', 'specimen', 'vocabulary', 'specimen', 'id', 'term');

-- vocabulary.stage
SELECT data_commons.make_facebase_references('isa', 'sample', 'stage', 'vocabulary', 'stage', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample', 'stage', 'vocabulary', 'stage', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample_summary', 'stage', 'vocabulary', 'stage', 'id', 'term');

-- vocabulary.strain
SELECT data_commons.make_facebase_references('isa', 'sample', 'strain', 'vocabulary', 'strain', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample', 'strain', 'vocabulary', 'strain', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample_summary', 'strain', 'vocabulary', 'strain', 'id', 'term');

-- vocabulary.strandedness
SELECT data_commons.make_facebase_references('isa', 'experiment', 'strandedness', 'vocabulary', 'strandedness', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'assay', 'strandednes', 'vocabulary', 'strandedness', 'id', 'term');

-- vocabulary.target_of_assay
SELECT data_commons.make_facebase_references('isa', 'experiment', 'target_of_assay', 'vocabulary', 'target_of_assay', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'assay', 'target_of_assay', 'vocabulary', 'target_of_assay', 'id', 'term');

-- vocabulary.theiler_stage
SELECT data_commons.make_facebase_references('isa', 'sample', 'theiler_stage', 'vocabulary', 'theiler_stage', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample', 'theiler_stage', 'vocabulary', 'theiler_stage', 'id', 'term');
SELECT data_commons.make_facebase_references('isa', 'biosample_summary', 'theiler_stage', 'vocabulary', 'theiler_stage', 'id', 'term');

-- isa.data_type
SELECT data_commons.make_dataset_references('isa', 'dataset_data_type', 'data_type', 'data_type');

-- isa.human_age
SELECT data_commons.make_dataset_references('isa', 'dataset_human_age', 'human_age', 'human_age');

-- isa.human_age_stage
SELECT data_commons.make_dataset_references('isa', 'dataset_human_age_stage', 'human_age_stage', 'age_stage');

-- isa.human_anatomic_source
SELECT data_commons.make_dataset_references('isa', 'dataset_human_anatomic_source', 'human_anatomic_source', 'anatomic_source');

-- isa.human_enhancer
SELECT data_commons.make_dataset_references('isa', 'dataset_human_enhancer', 'human_enhancer', 'enhancer');

-- isa.human_gender
SELECT data_commons.make_dataset_references('isa', 'dataset_human_gender', 'human_gender', 'gender');

-- isa.instrument
SELECT data_commons.make_dataset_references('isa', 'dataset_instrument', 'instrument', 'instrument');
SELECT data_commons.make_dataset_references('isa', 'imaging_data', 'equipment_model', 'instrument');
SELECT data_commons.make_dataset_references('isa', 'imaging', 'equipment_model', 'instrument');

-- isa.mouse_age_stage
SELECT data_commons.make_dataset_references('isa', 'dataset_mouse_age_stage', 'mouse_age_stage', 'age_stage');

-- isa.mouse_anatomic_source
SELECT data_commons.make_dataset_references('isa', 'dataset_mouse_anatomic_source', 'mouse_anatomic_source', 'anatomic_source');

-- isa.mouse_enhancer
SELECT data_commons.make_dataset_references('isa', 'dataset_mouse_enhancer', 'mouse_enhancer', 'enhancer');

-- isa.mouse_gene
SELECT data_commons.make_dataset_references('isa', 'dataset_mouse_gene', 'mouse_gene', 'gene');

-- isa.mouse_genetic_background
SELECT data_commons.make_dataset_references('isa', 'dataset_mouse_genetic_background', 'mouse_genetic_background', 'mouse_genetic_background');

-- isa.mouse_genotype
SELECT data_commons.make_dataset_references('isa', 'dataset_mouse_genotype', 'mouse_genotype', 'genotype');

-- isa.mouse_mutation
SELECT data_commons.make_dataset_references('isa', 'dataset_mouse_mutation', 'mouse_mutation', 'mutation');

-- isa.mouse_theiler_stage
SELECT data_commons.make_dataset_references('isa', 'dataset_mouse_theiler_stage', 'mouse_theiler_stage', 'theiler_stage');

-- isa.organism
SELECT data_commons.make_dataset_references('isa', 'dataset_organism', 'organism', 'organism');

-- isa.zebrafish_age_stage
SELECT data_commons.make_dataset_references('isa', 'dataset_zebrafish_age_stage', 'zebrafish_age_stage', 'age_stage');

-- isa.zebrafish_anatomic_source
SELECT data_commons.make_dataset_references('isa', 'dataset_zebrafish_anatomic_source', 'zebrafish_anatomic_source', 'anatomic_source');

-- isa.zebrafish_genotype
SELECT data_commons.make_dataset_references('isa', 'dataset_zebrafish_genotype', 'zebrafish_genotype', 'genotype');

-- isa.zebrafish_mutation
SELECT data_commons.make_dataset_references('isa', 'dataset_zebrafish_mutation', 'zebrafish_mutation', 'mutation');

DROP TABLE "vocabulary"."anatomy" CASCADE;
DROP TABLE "vocabulary"."chemical_entities" CASCADE;
DROP TABLE "vocabulary"."cvnames" CASCADE;
DROP TABLE "vocabulary"."file_format" CASCADE;
DROP TABLE "vocabulary"."gender" CASCADE;
DROP TABLE "vocabulary"."gene" CASCADE;
DROP TABLE "vocabulary"."gene_summary" CASCADE;
DROP TABLE "vocabulary"."genotype" CASCADE;
DROP TABLE "vocabulary"."histone_modification" CASCADE;
DROP TABLE "vocabulary"."image_creation_device" CASCADE;
DROP TABLE "vocabulary"."mapping_assembly" CASCADE;
DROP TABLE "vocabulary"."molecule_type" CASCADE;
DROP TABLE "vocabulary"."mutation" CASCADE;
DROP TABLE "vocabulary"."origin" CASCADE;
DROP TABLE "vocabulary"."output_type" CASCADE;
DROP TABLE "vocabulary"."paired_end_or_single_read" CASCADE;
DROP TABLE "vocabulary"."phenotype" CASCADE;
DROP TABLE "vocabulary"."rnaseq_selection" CASCADE;
DROP TABLE "vocabulary"."sample_type" CASCADE;
DROP TABLE "vocabulary"."sequencing_data_direction" CASCADE;
DROP TABLE "vocabulary"."species" CASCADE;
DROP TABLE "vocabulary"."specimen" CASCADE;
DROP TABLE "vocabulary"."stage" CASCADE;
DROP TABLE "vocabulary"."strain" CASCADE;
DROP TABLE "vocabulary"."strandedness" CASCADE;
DROP TABLE "vocabulary"."target_of_assay" CASCADE;
DROP TABLE "vocabulary"."theiler_stage" CASCADE;

DROP TABLE "isa"."data_type" CASCADE;
DROP TABLE "isa"."human_age" CASCADE;
DROP TABLE "isa"."human_age_stage" CASCADE;
DROP TABLE "isa"."human_anatomic_source" CASCADE;
DROP TABLE "isa"."human_enhancer" CASCADE;
DROP TABLE "isa"."human_gender" CASCADE;
DROP TABLE "isa"."instrument" CASCADE;
DROP TABLE "isa"."mouse_age_stage" CASCADE;
DROP TABLE "isa"."mouse_anatomic_source" CASCADE;
DROP TABLE "isa"."mouse_enhancer" CASCADE;
DROP TABLE "isa"."mouse_gene" CASCADE;
DROP TABLE "isa"."mouse_genetic_background" CASCADE;
DROP TABLE "isa"."mouse_genotype" CASCADE;
DROP TABLE "isa"."mouse_mutation" CASCADE;
DROP TABLE "isa"."mouse_theiler_stage" CASCADE;
DROP TABLE "isa"."organism" CASCADE;
DROP TABLE "isa"."zebrafish_age_stage" CASCADE;
DROP TABLE "isa"."zebrafish_anatomic_source" CASCADE;
DROP TABLE "isa"."zebrafish_genotype" CASCADE;
DROP TABLE "isa"."zebrafish_mutation" CASCADE;

-- update ermrest
TRUNCATE _ermrest.data_version;
TRUNCATE _ermrest.model_version;
SELECT _ermrest.model_change_event();


COMMIT;

