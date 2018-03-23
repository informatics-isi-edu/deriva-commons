-- begin transaction

BEGIN;

DROP TRIGGER IF EXISTS cvterm_generate_dbxref ON data_commons.cvterm;
DROP TRIGGER IF EXISTS cvterm_insert_trigger ON data_commons.cvterm;

CREATE TRIGGER cvterm_generate_dbxref BEFORE INSERT ON data_commons.cvterm FOR EACH ROW EXECUTE PROCEDURE data_commons.cvterm_generate_dbxref('facebase');
CREATE TRIGGER cvterm_insert_trigger AFTER INSERT ON data_commons.cvterm FOR EACH ROW EXECUTE PROCEDURE data_commons.cvterm_add('facebase');


INSERT INTO data_commons.cv (name, definition) VALUES('ocdm', 'Ontology of Craniofacial Development and Malformation');
INSERT INTO data_commons.cv (name, definition) VALUES('facebase', 'Resource for Craniofacial Researchers');

INSERT INTO data_commons.db (name, urlprefix, description) VALUES('OCDM', 'http://purl.org/sig/ont/ocdm', 'Ontology of Craniofacial Development and Malformation');
INSERT INTO data_commons.db (name, urlprefix, description) VALUES('FaceBase', 'https://www.facebase.org/', 'Resource for Craniofacial Researchers');

INSERT INTO data_commons.cvterm (cv, name) SELECT cv, name FROM temp.owl_terms;
INSERT INTO temp.ocdm (cv, name) SELECT cv, name FROM temp.owl_terms WHERE name NOT IN (SELECT name FROM temp.uberon) AND name IN (SELECT name FROM temp.terms);
UPDATE temp.terms T1 SET cv = (SELECT cv FROM temp.ocdm T2 WHERE T1.name = T2.name) WHERE name IN (SELECT name FROM temp.ocdm);


-- update ermrest
TRUNCATE _ermrest.data_version;
TRUNCATE _ermrest.model_version;
SELECT _ermrest.model_change_event();


COMMIT;

