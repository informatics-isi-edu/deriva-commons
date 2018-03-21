-- begin transaction

BEGIN;


INSERT INTO temp.facebase (name) SELECT DISTINCT name FROM temp.terms WHERE name NOT IN (SELECT name FROM data_commons.cvterm);

INSERT INTO data_commons.cvterm (cv, name) SELECT cv, name FROM temp.facebase;

UPDATE temp.terms T1 SET cv = (SELECT cv FROM temp.facebase T2 WHERE T1.name = T2.name) WHERE name IN (SELECT name FROM temp.facebase);

-- update ermrest
TRUNCATE _ermrest.data_version;
TRUNCATE _ermrest.model_version;
SELECT _ermrest.model_change_event();


COMMIT;

