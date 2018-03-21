#!/usr/bin/python

from optparse import OptionParser
import os
import sys
import subprocess
import traceback

owl_files = None

parser = OptionParser()
parser.header = {}
parser.add_option('-i', '--input', action='store', dest='input', type='string', help='Top directory')

(options, args) = parser.parse_args()

if not options.input:
    print 'ERROR: Missing Top directory'
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

for filename in owl_files:
    print 'Parsing: "%s"' % filename
    try:
        args = ['%s/parse_owl_file.py' % top_directory, '--file', '%s' % filename, '--output', '%s' % sql_directory]
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
        
sys.exit(0)

