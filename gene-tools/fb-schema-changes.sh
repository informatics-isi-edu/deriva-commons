#!/bin/sh

usage="Usage: $0 host curie_prefix

if [ $# -ne 2 ]; then
   echo $usage
   exit 1
fi

host=$1; shift
curie_prefix=$1; shift

python3 create_tables.py --host $host --skip-gene $curie_prefix
python3 fb_keys.py --config-file facebase_gene_defaults.json $host
python3 convert_fb_gene_table.py --config-file facebase_gene_defaults.json $host

cat | sudo -u ermrest psql facebasedb << EOF
update vocab.species set id = regexp_replace(id, 'NCBITAXON', 'NCBITaxon');
update vocab.species set uri = regexp_replace(id, '^NCBITaxon:', 'http://purl.obolibrary.org/obo/NCBITaxon_');
EOF
