#!/bin/sh

usage="Usage: $0 host curie-prefix"

if [ $# -ne 2 ]; then
    echo $usage
    exit 1
fi

host=$1; shift
curie=$1; shift

python3 create_tables.py \
	--config-file facebase_gene_defaults.json \
	--skip-gene --skip-species \
	$host $curie
