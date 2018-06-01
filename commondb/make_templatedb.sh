#!/bin/bash

# This script creates a generic 'common' template db from an existing
# instance of the facebasedb.
#
# Run this script on a facebase host to create a template from its database:
# $ sudo ./make_template [-y] SOURCEDB DESTDB DESTCAT
#
# Where,
#  SOURCEDB is 'facebasedb' by default, if left blank
#  DESTDB is 'commondb' by default, if left blank
#  DESTCAT is '8' by default, if left blank
#
# Option '-y' to answer 'yes' to all questions for optional steps.
#
# Note that DESTDB will be dropped and recreated!

if [ "$1" == "-y" ];
then
    ALLYES=1
    shift
else
    ALLYES=
fi

SOURCEDB=${1:-'facebasedb'}
DESTDB=${2:-'commondb'}
DESTCAT=${3:-'8'}
ERMRESTDIR=${ERMRESTDIR:-"/home/isrddev/ermrest"}
HOST=${HOST:-$(hostname)}
ACL_CONFIG=${ACL_CONFIG:-"$(pwd)/acl_config.json"}

function question
{
    if [ "${ALLYES}" ];
    then
        return 0
    else
        read -t 30 -n 1 -p "$1 " ans
        if [ "$ans" == "y" ];
        then
            return 0
        fi
    fi
    return 1
}

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
    cat "$1" | sed -e "s/'''FB'''/'''DC'''/g" | sed -e "s/https:\/\/www.facebase.org//g" | sed -e "s/https:\/\/dev.facebase.org//g" | sed -e "s/https:\/\/staging.facebase.org//g" | sed -e "s/facebase/commons/g" | sed -e "s/\/data\/record/\/chaise\/record/g" | sed -e "s/\/fb2\//\//g" > "$tmpfile"
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

    # hack the catalog owner acl, set to isrd-staff
    cat <<EOF | runuser -u ermrest psql "$1"
UPDATE _ermrest.known_catalog_acls
SET members = '{"https://auth.globus.org/176baec4-ed26-11e5-8e88-22000ab4b42b"}'
WHERE acl = 'owner';
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

function ermrest_deploy
{
    here=$(pwd)
    cd ${ERMRESTDIR}
    make deploy
    cd $here
}

function update_acls
{
    runuser -c "deriva-acl-config --host ${HOST} --config-file ${ACL_CONFIG} ${DESTCAT}" - "${SUDO_USER:-$USER}"
}

echo "Running ${0} with:"
echo "  SOURCEDB=${SOURCEDB}"
echo "  DESTDB=${DESTDB}"
echo "  DESTCAT=${DESTCAT}"

dropdb "$DESTDB"
createdb "$DESTDB"
dumpdb "$SOURCEDB" "$DESTDB"
purgefb "$DESTDB"
restoredb "$DESTDB"
hackdb "$DESTDB"

question "Register database ${DESTDB} as catalog ${DESTCAT} (y/n)?" \
    && registerdb "$DESTCAT" "$DESTDB"

question "Run ermrest make deploy (y/n)?" \
    && ermrest_deploy

question "Update acl configuration (y/n)?" \
    && update_acls

question "Dump final database (y/n)?" \
    && runuser -u ermrest pg_dump "${DESTDB}" > "${DESTDB}.sql"

echo "Done"

