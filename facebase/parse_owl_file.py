#!/usr/bin/python

import os
import sys
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

parser = OptionParser()
parser.header = {}
parser.add_option('-f', '--file', action='store', dest='file', type='string', help='OWL file name')
parser.add_option('-o', '--output', action='store', dest='output', type='string', help='Output directory')

(options, args) = parser.parse_args()

if not options.file:
    print 'ERROR: Missing input OWL file'
    sys.exit()
    
parts = options.file.split('/')
cv = parts[-1].split('.')[0]
output = '/'.join(parts[0:-1])
    
if options.output:
    output = options.output

output = '%s/%s.sql' % (output, cv)

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
    
def insert_results(out, qres, literal):
    for row in qres:
        try:
            s,p,o = row
            s = getShortName(s).replace("'", "''")
            p = getShortName(p).replace("'", "''")
            o = getShortName(o).replace("'", "''")
            if isLiteral(o):
                out.write("INSERT INTO temp.owl_terms(cv, name) VALUES('%s', '%s') ON CONFLICT DO NOTHING;\n" % ('ocdm_%s' % cv, o))
                out.write("INSERT INTO temp.owl_predicates(predicate) VALUES('%s') ON CONFLICT DO NOTHING;\n" % (p))
        except:
            print 'write error'
            
def get_all_literals():
    out = file(output, 'w')
    out.write("BEGIN;\n")
    """
    qres = g.query(literals_subjects)
    insert_results(out, qres, 'subjects')
    qres = g.query(literals_predicates)
    insert_results(out, qres, 'predicates')
    """
    qres = g.query(literals_objects)
    insert_results(out, qres, 'objects')
    out.write("COMMIT;\n")
    out.close()
    
setNamespace()
get_all_literals()
sys.exit(0)

