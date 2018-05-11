#!/usr/bin/python

from optparse import OptionParser
import os
import stat
import sys
import subprocess
import traceback

header = """
#!/bin/bash

# The script will be executed as root
# $1 is the database name
# $2 is the top directory

# Create the "temp" schema if it does not exists

echo "Creating the temp schema..."

su -c "psql -v ON_ERROR_STOP=1 -c \\"CREATE SCHEMA IF NOT EXISTS temp AUTHORIZATION ermrest\\" \\"$1\\"" - postgres > "$2"/out.log 2>"$2"/err.log

if [ $? != 0 ]
  then
    echo "Failure Creating the temp schema."
    exit 1
  fi

"""

owl_template = """
# Load the %(db)s terms

echo "Loading the %(db)s terms..."

su -c "psql -v ON_ERROR_STOP=1 \\"$1\\"" - postgres < "$2"/%(db)s_terms.sql > "$2"/out.log 2>"$2"/err.log

if [ $? != 0 ]
  then
    echo "Failure Loading the %(db)s terms."
    exit 1
  fi


"""

owl_files = None

parser = OptionParser()
parser.header = {}
parser.add_option('-i', '--input', action='store', dest='input', type='string', help='Top directory')
parser.add_option('-n', '--ontology', action='store', dest='ontology', type='string', help='Ontology name')
parser.add_option('-c', '--config', action='store', dest='config', type='string', help='Configuration file for specifying the predicates for the terms and synonyms')

(options, args) = parser.parse_args()

if not options.input:
    print 'ERROR: Missing Top directory'
    sys.exit()
    
if not options.ontology:
    print 'ERROR: Missing Ontology name'
    sys.exit()
    
if not options.config:
    print 'ERROR: Missing configuration file.'
    sys.exit()
    
top_directory = options.input
owl_directory = '%s/owl' % (top_directory)
sql_directory = '%s/sql' % (top_directory)

def scanFiles(path):
    files = []
    for entry in os.listdir(path):
        if os.path.isfile('%s%s%s' % (path, os.sep, entry)):
            files.append('%s%s%s' % (path, os.sep, entry))
        else:
            files.extend(scanFiles('%s%s%s' % (path, os.sep, entry)))
    return files

owl_files = scanFiles(owl_directory)

out = file('%s.sh' % options.ontology, 'w')
out.write(header)

for filename in owl_files:
    print 'Parsing: "%s"' % filename
    parts = filename.split('/')
    db = parts[-1].split('.')[0]
    out.write(owl_template % dict(db=db))
    try:
        args = ['%s/parse_owl_file.py' % top_directory, '--file', '%s' % filename, '--output', '%s' % sql_directory, '--ontology', '%s' % options.ontology, '--config', '%s' % options.config]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = p.communicate()
        returncode = p.returncode
    except:
        et, ev, tb = sys.exc_info()
        print 'got unexpected exception "%s"' % str(ev)
        print '%s' % str(traceback.format_exception(et, ev, tb))
        returncode = 1
        
    if returncode != 0:
        print 'Could not execute the script for generating OWL terms.\nstdoutdata: %s\nstderrdata: %s\n' % (stdoutdata, stderrdata)
        
out.close()
os.chmod('%s.sh' % options.ontology, os.stat('%s.sh' % options.ontology).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
sys.exit(0)

