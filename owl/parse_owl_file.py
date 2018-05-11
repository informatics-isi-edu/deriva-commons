#!/usr/bin/python

import os
import sys
import traceback
import rdflib
from optparse import OptionParser

literals_subjects = """
    SELECT DISTINCT ?s ?p ?o 
        WHERE {
            ?s ?p ?o .
        FILTER (isLiteral(?s))
        }
    ORDER BY ?s      
"""

literals_predicates = """
    SELECT DISTINCT ?s ?p ?o 
        WHERE {
            ?s ?p ?o .
        FILTER (isLiteral(?p))
        }
    ORDER BY ?p      
"""

literals_objects = """
    SELECT DISTINCT ?s ?p ?o 
        WHERE {
            ?s ?p ?o .
        FILTER (isLiteral(?o))
        }
    ORDER BY ?o      
"""

literals_terms = """
    SELECT DISTINCT ?s ?o 
        WHERE {
            ?s ?p ?o .
        FILTER (isLiteral(?o) && regex(str(?p), "preferred_name$"))
        }
    ORDER BY ?o ?s  
"""

literals_synonyms = """
    SELECT DISTINCT ?s ?o 
        WHERE {
            ?s ?p ?o .
        FILTER (isLiteral(?o) && regex(str(?p), "/synonym$"))
        }
    ORDER BY ?o      
"""

vocabularies_tables = """
DROP TABLE IF EXISTS temp.%(db)s_terms CASCADE;
CREATE TABLE temp.%(db)s_terms(
    id serial PRIMARY KEY, 
    name text, 
    subject text, 
    alternate_name text,
    accession text, 
    cv text default '%(cv)s',
    db text default '%(db)s',
    dbxref text,
    alternate_dbxref text,
    has_synonym boolean default false, 
    is_duplicate boolean default false);
ALTER TABLE temp.%(db)s_terms OWNER TO ermrest;

DROP TABLE IF EXISTS temp.%(db)s_synonyms CASCADE;
CREATE TABLE temp.%(db)s_synonyms(
    id serial PRIMARY KEY, 
    synonym text, 
    subject text, 
    name text, 
    dbxref text);
ALTER TABLE temp.%(db)s_synonyms OWNER TO ermrest;

"""

parser = OptionParser()
parser.header = {}
parser.add_option('-f', '--file', action='store', dest='file', type='string', help='OWL file name')
parser.add_option('-n', '--ontology', action='store', dest='ontology', type='string', help='Ontology name')
parser.add_option('-o', '--output', action='store', dest='output', type='string', help='Output directory')

(options, args) = parser.parse_args()

if not options.file:
    print 'ERROR: Missing input OWL file'
    sys.exit()
    
if not options.ontology:
    print 'ERROR: Missing ontology name'
    sys.exit()
    
parts = options.file.split('/')
db = parts[-1].split('.')[0]
cv = '%s_%s' % (options.ontology, db)
output = '/'.join(parts[0:-1])
    
if options.output:
    output = options.output

output_terms = '%s/%s_terms.sql' % (output, db)

g = rdflib.Graph()
g.parse(options.file)

xmlns = {}

def getShortName(name):
    ret = '%s' % name
    ret = ret.encode('utf-8')
    for key, value in xmlns.iteritems():
        if ret.startswith(value):
            ret = '%s:%s' % (key, ret[len(value):])
            return ret
    return ret

def isLiteral(value):
    try:
        int(value)
        return False
    except:
        return True

def setNamespace():
    f = open(options.file, 'r')
    line = f.readline()
    while line != '':
        line = line.strip()
        if line.startswith('<rdf:RDF '):
            line = line[len('<rdf:RDF '):]
        if line.endswith('>'):
            line = line[:-1]
        prefix = None
        if line.startswith('xmlns:'):
            prefix = 'xmlns:'
        if line.startswith('xmlns='):
            prefix = 'xmlns='
        if line.startswith('xml:'):
            prefix = 'xml:'
            line = line[0:len(line)-1]

        if prefix == 'xmlns:' or prefix == 'xml:':
            line = line[len(prefix):]
            values = line.split('=')
            xmlns[values[0]] = values[1][1:len(values[1])-1]
        elif prefix == 'xmlns=':
            line = line[len(prefix):]
            xmlns[''] = line[1:len(line)-1]
        line = f.readline() 
    f.close()
    
def insert_terms(out, qres):
    for row in qres:
        try:
            s,o = row
            alternate_name = '%s' % s.encode('utf-8').replace("'", "''")
            s = getShortName(s).replace("'", "''")
            o = getShortName(o).replace("'", "''")
            if isLiteral(o):
                if s[0] == ':':
                    accession = s[1:]
                else:
                    accession = s
                out.write("INSERT INTO temp.%s_terms(name, subject, accession, cv, db, alternate_name) VALUES('%s', '%s', '%s', '%s', '%s', '%s');\n" % (db, o, s, accession, cv, db, alternate_name))
        except:
            et, ev, tb = sys.exc_info()
            print str(et)
            print 'Exception "%s"' % str(ev)
            print '%s' % str(traceback.format_exception(et, ev, tb))
            sys.exit(1)
            
def insert_synonyms(out, qres):
    for row in qres:
        try:
            s,o = row
            s = getShortName(s).replace("'", "''")
            o = getShortName(o).replace("'", "''")
            if isLiteral(o):
                out.write("INSERT INTO temp.%s_synonyms(synonym, subject) VALUES('%s', '%s');\n" % (db, o, s))
        except:
            print 'write error'
            
def get_all_terms(out):
    qres = g.query(literals_terms)
    insert_terms(out, qres)
    out.write('\n')
    
def get_all_synonyms(out):
    qres = g.query(literals_synonyms)
    insert_synonyms(out, qres)
    out.write('\n')
    
def join_synonyms(out):
    out.write("DELETE FROM temp.%(db)s_terms WHERE name = '';\n" % dict(db=db))
    out.write("UPDATE temp.%(db)s_synonyms T1 SET name = (SELECT name FROM temp.%(db)s_terms T2 WHERE T1.subject = T2.subject LIMIT 1);\n" % dict(db=db))
    out.write("DELETE FROM temp.%(db)s_synonyms WHERE name IS NULL;\n" % dict(db=db))
    out.write("UPDATE temp.%(db)s_terms SET has_synonym = true WHERE (name, subject) IN (SELECT name, subject FROM temp.%(db)s_synonyms);\n" % dict(db=db))
    out.write("UPDATE temp.%(db)s_terms SET is_duplicate = true WHERE name IN (SELECT name FROM temp.%(db)s_terms GROUP BY name HAVING count(*) > 1);\n" % dict(db=db))
    out.write("DELETE FROM temp.%(db)s_terms WHERE has_synonym = false AND is_duplicate = true AND name IN (SELECT name FROM temp.%(db)s_terms WHERE has_synonym = true AND is_duplicate = true);\n" % dict(db=db))
    out.write("DELETE FROM temp.%(db)s_terms T1 WHERE has_synonym = false AND is_duplicate = true AND id NOT IN (SELECT id FROM temp.%(db)s_terms T2 WHERE T2.has_synonym = false AND T2.is_duplicate = true AND T1.name = T2.name ORDER BY id LIMIT 1);\n" % dict(db=db))
    out.write("CREATE TABLE temp.temporary AS SELECT * FROM temp.%(db)s_terms T1 WHERE has_synonym = true AND is_duplicate = true AND id NOT IN (SELECT id FROM temp.%(db)s_terms T2 WHERE T2.has_synonym = true AND T2.is_duplicate = true AND T1.name = T2.name ORDER BY id LIMIT 1);\n" % dict(db=db))
    out.write("DELETE FROM temp.%(db)s_synonyms WHERE (name, subject) IN (SELECT name, subject FROM temp.temporary);\n" % dict(db=db))
    out.write("DELETE FROM temp.%(db)s_terms WHERE (name, subject) IN (SELECT name, subject FROM temp.temporary);\n" % dict(db=db))
    out.write("DROP TABLE temp.temporary;\n")
    out.write("DELETE FROM temp.%(db)s_synonyms WHERE (name, subject) NOT IN (SELECT name, subject FROM temp.%(db)s_terms);\n" % dict(db=db))
    out.write("INSERT INTO data_commons.db (name) VALUES('%s') ON CONFLICT DO NOTHING;\n" % db)
    out.write("INSERT INTO data_commons.cv (name) VALUES('%s') ON CONFLICT DO NOTHING;\n" % cv)
    out.write("UPDATE temp.%(db)s_terms SET dbxref = '%(db)s' || ':' || accession || ':';\n" % dict(db=db))
    out.write("UPDATE temp.%(db)s_terms SET alternate_dbxref = '%(db)s' || ':' || alternate_name || ':';\n" % dict(db=db))
    out.write("INSERT INTO data_commons.dbxref(db, accession) SELECT db, accession FROM temp.%(db)s_terms ON CONFLICT DO NOTHING;\n" % dict(db=db))
    out.write("INSERT INTO data_commons.dbxref(db, accession) SELECT db, alternate_name FROM temp.%(db)s_terms ON CONFLICT DO NOTHING;\n" % dict(db=db))
    out.write("INSERT INTO data_commons.cvterm(dbxref, cv, name) SELECT dbxref, cv, name FROM temp.%(db)s_terms ON CONFLICT DO NOTHING;\n" % dict(db=db))
    out.write("INSERT INTO data_commons.cvterm_dbxref(cvterm, alternate_dbxref) SELECT dbxref, alternate_dbxref FROM temp.%(db)s_terms ON CONFLICT DO NOTHING;\n" % dict(db=db))
    out.write("UPDATE temp.%(db)s_synonyms T1 SET dbxref = (SELECT dbxref FROM temp.%(db)s_terms T2 WHERE T1.subject = T2.subject AND T1.name = T2.name) ;\n" % dict(db=db))
    out.write("INSERT INTO data_commons.cvtermsynonym(dbxref, synonym) SELECT dbxref, synonym FROM temp.%(db)s_synonyms ON CONFLICT DO NOTHING;\n" % dict(db=db))
    out.write('\n')
    
setNamespace()
out = file(output_terms, 'w')
out.write("BEGIN;\n")
out.write(vocabularies_tables % dict(cv=cv, db=db))
get_all_terms(out)
get_all_synonyms(out)
join_synonyms(out)
out.write("COMMIT;\n")
out.close()
sys.exit(0)

