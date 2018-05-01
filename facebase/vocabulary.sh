#!/bin/bash

# The script will be executed as root
# $1 is the facebase database name
# $2 is the facebase top directory

LOAD_OCDM=${LOAD_OCDM:-false}


rm -f "$2"/out.log
rm -f "$2"/err.log
rm -f "$2"/err_domain.log

# Drop the non referred vocabulary tables

echo "Dropping the non referred vocabulary tables..."

su -c "psql \"$1\"" - postgres < "$2"/clean_up.sql > "$2"/out.log 2>"$2"/err.log

if [ $? != 0 ]
  then
    echo "Failure Dropping the non referred vocabulary tables."
    exit 1
  fi

# Load the data_commons schema

echo "Loading the data_commons schema..."

su -c "psql \"$1\"" - postgres < "$2"/data_commons.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the data_commons schema."
    exit 1
  fi

# Load the public functions

echo "Loading the public functions..."

su -c "psql \"$1\"" - postgres < "$2"/00_common_functions.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the public functions."
    exit 1
  fi

# Add the ermrest system columns

echo "Adding the ermrest system columns..."

su -c "psql \"$1\"" - postgres < "$2"/data_commons_ermrest.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Adding the ermrest system columns."
    exit 1
  fi

# Get the facebase and uberon terms

echo "Getting the facebase and uberon terms..."

su -c "psql -v ON_ERROR_STOP=1 \"$1\"" - postgres < "$2"/uberon.sql > "$2"/out.log 2>"$2"/err.log

if [ $? != 0 ]
  then
    echo "Failure Getting the facebase and uberon terms."
    exit 1
  fi


#==== ADD switch so we don't load OCDM terms to the cvterms table ... 
if ${LOAD_OCDM}
then 

# Load the aeo terms

echo "Loading the aeo terms..."

su -c "psql \"$1\"" - postgres < "$2"/aeo.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the aeo terms."
    exit 1
  fi

# Load the cet terms

echo "Loading the cet terms..."

su -c "psql \"$1\"" - postgres < "$2"/cet.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the cet terms."
    exit 1
  fi

# Load the chm3o terms

echo "Loading the chm3o terms..."

su -c "psql \"$1\"" - postgres < "$2"/chm3o.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the chm3o terms."
    exit 1
  fi

# Load the chmmo terms

echo "Loading the chmmo terms..."

su -c "psql \"$1\"" - postgres < "$2"/chmmo.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the chmmo terms."
    exit 1
  fi

# Load the chmo terms

echo "Loading the chmo terms..."

su -c "psql \"$1\"" - postgres < "$2"/chmo.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the chmo terms."
    exit 1
  fi

# Load the cho terms

echo "Loading the cho terms..."

su -c "psql \"$1\"" - postgres < "$2"/cho.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the cho terms."
    exit 1
  fi

# Load the chzmo terms

echo "Loading the chzmo terms..."

su -c "psql \"$1\"" - postgres < "$2"/chzmo.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the chzmo terms."
    exit 1
  fi

# Load the cmmo terms

echo "Loading the cmmo terms..."

su -c "psql \"$1\"" - postgres < "$2"/cmmo.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the cmmo terms."
    exit 1
  fi

# Load the cmo terms

echo "Loading the cmo terms..."

su -c "psql \"$1\"" - postgres < "$2"/cmo.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the cmo terms."
    exit 1
  fi

# Load the cpo terms

echo "Loading the cpo terms..."

su -c "psql \"$1\"" - postgres < "$2"/cpo.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the cpo terms."
    exit 1
  fi

# Load the czo terms

echo "Loading the czo terms..."

su -c "psql \"$1\"" - postgres < "$2"/czo.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the czo terms."
    exit 1
  fi

# Load the ocdm terms

echo "Loading the ocdm terms..."

su -c "psql \"$1\"" - postgres < "$2"/ocdm.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the ocdm terms."
    exit 1
  fi

fi

# ==========

# Load the data_commons with the OCDM terms

echo "Loading the data_commons with the OCDM terms..."

su -c "psql \"$1\"" - postgres < "$2"/data_commons_ocdm.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the data_commons with the OCDM terms."
    exit 1
  fi

# Load the data_commons with the facebase terms not present into the ontology

echo "Loading the data_commons with the facebase terms not present into the ontology..."

su -c "psql \"$1\"" - postgres < "$2"/local_ocdm.sql > "$2"/out.log 2>"$2"/err.log

if [ -s "$2"/err.log ]
  then
    echo "Failure Loading the data_commons with the facebase terms not present into the ontology."
    exit 1
  fi

# Creating the Vocabulary for the OCDM domain

echo "Creating the Vocabulary for the OCDM domain..."

su -c "psql -v ON_ERROR_STOP=1 \"$1\"" - postgres < "$2"/domain.sql > "$2"/out.log 2>"$2"/err.log

if [ $? != 0 ]
  then
    echo "Check the \"$2\"/err.log file to see if there are just warnings."
    exit 1
  fi

# Creating the references to the Vocabulary tables

echo "Creating the references to the Vocabulary tables..."

su -c "psql -v ON_ERROR_STOP=1 \"$1\"" - postgres < "$2"/vocabulary_references.sql > "$2"/out.log 2>"$2"/err.log

if [ $? != 0 ]
  then
    echo "Check the \"$2\"/err.log file to see if there are just warnings."
    exit 1
  fi

# Adding the sort_key column for the stage vocabulary table

echo "Adding the sort_key column for the stage vocabulary table..."

su -c "psql -v ON_ERROR_STOP=1 \"$1\"" - postgres < "$2"/stage_terms.sql > "$2"/out.log 2>"$2"/err.log

if [ $? != 0 ]
  then
    echo "Check the \"$2\"/err.log file to see if there are just warnings."
    exit 1
  fi

rm -f "$2"/out.log
rm -f "$2"/err.log


