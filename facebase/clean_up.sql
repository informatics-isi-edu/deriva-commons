BEGIN;

DROP TABLE "vocabulary"."age" CASCADE;
DROP TABLE "vocabulary"."chemical_entities" CASCADE;
DROP TABLE "vocabulary"."cvnames" CASCADE;
DROP TABLE "vocabulary"."equipment_model" CASCADE;
DROP TABLE "vocabulary"."experiment_type" CASCADE;
DROP TABLE "vocabulary"."file_extension" CASCADE;
DROP TABLE "vocabulary"."icd10_code" CASCADE;
DROP TABLE "vocabulary"."icd10_diagnosis" CASCADE;
DROP TABLE "vocabulary"."omim_code" CASCADE;
DROP TABLE "vocabulary"."omim_diagnosis" CASCADE;
DROP TABLE "vocabulary"."sample_type" CASCADE;

DROP TABLE "isa"."imaging_method" CASCADE;
DROP TABLE "isa"."jax_strain" CASCADE;
DROP TABLE "isa"."specimen" CASCADE;

-- update ermrest
TRUNCATE _ermrest.data_version;
TRUNCATE _ermrest.model_version;
SELECT _ermrest.model_change_event();


COMMIT;
