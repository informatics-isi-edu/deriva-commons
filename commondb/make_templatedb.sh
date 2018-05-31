#!/bin/bash

# This script creates a generic 'common' template db from an existing
# instance of the facebasedb.
#
# Run this script on a facebase host to create a template from its database:
# $ sudo ./make_template SOURCEDB DESTDB DESTCAT
#
# Where,
#  SOURCEDB is 'facebasedb' by default, if left blank
#  DESTDB is 'commondb' by default, if left blank
#  DESTCAT is '8' by default, if left blank
#
# Note that DESTDB will be dropped and recreated!

SOURCEDB=${1:-'facebasedb'}
DESTDB=${2:-'commondb'}
DESTCAT=${3:-'8'}
ERMRESTDIR="/home/isrddev/ermrest"

function dropdb
{
    runuser -u ermrest ~ermrest/force-disconnect.sh "$1"
    runuser -u postgres dropdb "$1"
}

function createdb
{
    runuser -c "createdb -O ermrest '$1'" - postgres
}

function dumpdb
{
    runuser -c "pg_dump -n 'public' -n '_ermrest*' -n 'data_commons' -n 'vocab' '$1'" - ermrest > "${2}-core.sql"
    runuser -c "pg_dump -s -N 'temp' -N 'public' -N '_ermrest*' -N 'data_commons' -N 'vocab' '$1'" - ermrest  > "${2}-schema-only.sql"
}

function purgefb
{
    purgefb_from "${1}-core.sql"
    purgefb_from "${1}-schema-only.sql"
}

function purgefb_from
{
    tmpfile="${1}.tmp"
    cat "$1" | sed -e "s/'''FB'''/'''DC'''/g" | sed -e "s/https:\/\/www.facebase.org//g" | sed -e "s/https:\/\/dev.facebase.org//g" | sed -e "s/https:\/\/staging.facebase.org//g" | sed -e "s/facebase/commons/g" | sed -e "s/\/data\/record/\/chaise\/record/g" > "$tmpfile"
    rm "$1"
    mv "$tmpfile" "$1"
}

function restoredb
{
    runuser -u postgres psql "$1" < "${1}-core.sql"
    runuser -u postgres psql "$1" < "${1}-schema-only.sql"
}

function hackdb
{
    # drop _ermrest_history
    cat <<EOF | runuser -u ermrest psql "$1"
DROP SCHEMA _ermrest_history CASCADE;
EOF

    # drop vocab.gene_summary
    cat <<EOF | runuser -u ermrest psql "$1"
DROP TABLE vocab.gene_summary CASCADE;
EOF

    # delete unwanted _ermrest entries
    cat <<EOF | runuser -u ermrest psql "$1"
DELETE FROM _ermrest.valuemap;
DELETE FROM _ermrest.model_modified;
DELETE FROM _ermrest.table_modified;
EOF
}

function registerdb
{
    cat <<EOF | runuser -u ermrest psql ermrest
INSERT INTO simple_registry (id, descriptor) 
VALUES ($1, '{"type": "postgres", "dbname": "$2"}')
ON CONFLICT DO NOTHING;
EOF
}

echo "Running ${0} with:"
echo "  SOURCEDB=${SOURCEDB}"
echo "  DESTDB=${DESTDB}"
echo "  DESTCAT=${DESTCAT}"
echo

dropdb "$DESTDB"
createdb "$DESTDB"
dumpdb "$SOURCEDB" "$DESTDB"
purgefb "$DESTDB"
restoredb "$DESTDB"
hackdb "$DESTDB"

read -t 30 -n 1 -p "Register database ${DESTDB} as catalog ${DESTCAT} (y/n)? " reg_ans
echo
if [ "$reg_ans" == "y" ];
then
    registerdb "$DESTCAT" "$DESTDB"
else
    echo "Skipping catalog registration..."
fi

read -t 30 -n 1 -p "Run ermrest make deploy (y/n)? " deploy_ans
echo
if [ "$deploy_ans" == "y" ];
then
    here=$(pwd)
    cd ${ERMRESTDIR}
    make deploy
    cd $here
else
    echo "Skipping make deploy..."
fi

read -t 30 -n 1 -p "Dump final database (y/n)? " dump_ans
echo
if [ "$dump_ans" == "y" ];
then
    dumpfile="${DESTDB}.sql"
    echo "Dumping ${DESTDB} to ${dumpfile}..."
    runuser -u ermrest pg_dump "${DESTDB}" > "${dumpfile}"
else
    echo "Skipping final database dump..."
fi

echo
echo "Done"

