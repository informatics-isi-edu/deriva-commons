BEGIN;

DROP TABLE "vocabulary"."age" CASCADE;
DROP TABLE "vocabulary"."equipment_model" CASCADE;
DROP TABLE "vocabulary"."experiment_type" CASCADE;
DROP TABLE "vocabulary"."icd10_code" CASCADE;
DROP TABLE "vocabulary"."icd10_diagnosis" CASCADE;
DROP TABLE "vocabulary"."omim_code" CASCADE;
DROP TABLE "vocabulary"."omim_diagnosis" CASCADE;
DROP TABLE "isa"."data_type" CASCADE;
DROP TABLE "isa"."human_age" CASCADE;
DROP TABLE "isa"."human_age_stage" CASCADE;
DROP TABLE "isa"."human_anatomic_source" CASCADE;
DROP TABLE "isa"."human_enhancer" CASCADE;
DROP TABLE "isa"."human_gender" CASCADE;
DROP TABLE "isa"."imaging_method" CASCADE;
DROP TABLE "isa"."instrument" CASCADE;
DROP TABLE "isa"."jax_strain" CASCADE;
DROP TABLE "isa"."mouse_age_stage" CASCADE;
DROP TABLE "isa"."mouse_anatomic_source" CASCADE;
DROP TABLE "isa"."mouse_enhancer" CASCADE;
DROP TABLE "isa"."mouse_gene" CASCADE;
DROP TABLE "isa"."mouse_genetic_background" CASCADE;
DROP TABLE "isa"."mouse_genotype" CASCADE;
DROP TABLE "isa"."mouse_mutation" CASCADE;
DROP TABLE "isa"."mouse_theiler_stage" CASCADE;
DROP TABLE "isa"."organism" CASCADE;
DROP TABLE "isa"."specimen" CASCADE;
DROP TABLE "isa"."zebrafish_age_stage" CASCADE;
DROP TABLE "isa"."zebrafish_anatomic_source" CASCADE;
DROP TABLE "isa"."zebrafish_genotype" CASCADE;
DROP TABLE "isa"."zebrafish_mutation" CASCADE;

-- update ermrest
TRUNCATE _ermrest.data_version;
TRUNCATE _ermrest.model_version;
SELECT _ermrest.model_change_event();


COMMIT;
