#!/bin/bash

usage="$0 host species source_url"
hatrac_parent=/hatrac/facebase/gene_source_files
config_file=facebase_gene_defaults.json
database=facebasedb
hatrac_parent=/hatracn/facebase/gene_source_files
scratch_db=gene_etl
#import_script=import_tables.sql

# for arg in "$@"; do
#     case $arg in
# 	--import-script)
# 	    import_script=$2
# 	    shift; shift
# 	    ;;
# 	*)
# 	    break
#     esac
# done

if [ $# -ne 3 ]; then
    echo $usage
    exit 1
fi

host=$1; shift
species=$1; shift
source_url=$1; shift

eval `python3 set_shell_env.py $host $config_file`

mkdir -p $scratch_directory

# fetch the file from NCBI and store in scratch directory
# skip-hatrac here until I get hatrac write perms
raw_file=`python3 upload_gene_source_file.py \
	--scratch-directory $scratch_directory \
        --skip-hatrac \
	$host \
	$config_file \
	"$species" \
	$source_url \
	$hatrac_parent`


# generate and run script to upload raw file to scratch database
sh extract-gene-info.sh $raw_file > $scratch_directory/load_raw.sql
psql -f $scratch_directory/load_raw.sql $scratch_db

# Create a directory to hold the transformed csv files:

mkdir -p $scratch_directory/transformed

# Create versions of the gene, etc. tables in the scratch directory,
# then dump them as csv into the scratch directory
psql -f transform_gene_table.sql gene_etl

gene_type_file=$scratch_directory/transformed/gene_type.csv
psql gene_etl > $gene_type_file <<EOF
copy (
     select "Name", 'No description' as "Description", null as "Synonyms"
     from transformed."Gene_Type")
     to STDOUT with csv header;
EOF
sudo -u ermrest psql $database <<EOF
create temporary table tmp_gene_type (
   "Name" text,
   "Description" text,
   "Synonyms" text[]
   );
\copy tmp_gene_type("Name", "Description", "Synonyms") from '${gene_type_file}' with csv header
insert into "${gene_type_schema}"."${gene_type_table}"("Name", "Description", "Synonyms")
   select "Name", "Description", "Synonyms" from tmp_gene_type
   on conflict("Name") do update
   set "Description" = EXCLUDED."Description",
   "Synonyms" = EXCLUDED."Synonyms"
EOF

chrome_file=$scratch_directory/transformed/chromosme.csv
psql gene_etl > ${chrome_file} <<EOF
copy (
     select "Name", "Species" from transformed."Chromosome")
     to STDOUT with csv header;
EOF

sudo -u ermrest psql $database <<EOF
create temporary table tmp_chromosome (
   "Name" text,
   "Species" text
   );

\copy tmp_chromosome("Name", "Species") from '${chrome_file}' with csv header
insert into "${chromosome_schema}"."${chromosome_table}"("Name", "Species")
   select "Name", "Species" from tmp_chromosome c
   where exists (select 1 from "${species_schema}"."${species_table}" s
      where s.id = c."Species")
   on conflict do nothing;
EOF

gene_file=$scratch_directory/transformed/gene.csv
psql gene_etl > $gene_file <<EOF
copy (
   select "ID", "URI", "Name", "Description", "Gene_Type",
   "Species", "Chromosome", "Location", "Source_Date", "Synonyms"
    from transformed."Gene") 
    to STDOUT with csv header
EOF

sudo -u ermrest psql $database <<EOF
create temporary table tmp_gene(
   "ID" text,
   "URI" text,
   "Name" text,
   "Description" text,
   "Gene_Type" text,
   "Species" text,
   "Chromosome" text,
   "Location" text,
   "Source_Date" date,
   "Synonyms" text[]
   );
\copy tmp_gene("ID", "URI", "Name", "Description", "Gene_Type", "Species", "Chromosome", "Location", "Source_Date", "Synonyms") from '${gene_file}' with csv header
insert into "${gene_schema}"."${gene_table}"(
       "id", "uri", "name", "description",
       "Gene_Type", "Species", "Chromosome",
       "Location", "Source_Date", "synonyms")
select
       g."ID", g."URI", g."Name", g."Description",
       t."ID", g."Species", c."RID",
       g."Location", g."Source_Date", g."Synonyms"
from tmp_gene g
join "${gene_type_schema}"."${gene_type_table}" t on t."Name" = g."Gene_Type"
left join "${chromosome_schema}"."${chromosome_table}" c on c."Name" = g."Chromosome" and c."Species" = g."Species"
   where exists (select 1 from "${species_schema}"."${species_table}" s
      where s.id = g."Species")
on conflict("id") do update
  set "name" = EXCLUDED."name",
     "description" = EXCLUDED."description",
     "Gene_Type" = EXCLUDED."Gene_Type",
     "Species" = EXCLUDED."Species",
     "Chromosome" = EXCLUDED."Chromosome",
     "Location" = EXCLUDED."Location",
     "Source_Date" = EXCLUDED."Source_Date",
     "synonyms" = EXCLUDED."synonyms";
EOF

dbxref_file=$scratch_directory/transformed/alternate_id.csv
psql gene_etl > ${dbxref_file} <<EOF
copy (
     select "Gene", "Alternate_ID", "Alternate_Ontology"
     from transformed."Gene_Alternate_ID")
     to STDOUT with csv header;
EOF
	
sudo -u ermrest psql $database <<EOF
create temporary table tmp_dbxref (
   "Gene" text,
   "Alternate_ID" text,
   "Alternate_Ontology" text
   );
\copy tmp_dbxref("Gene", "Alternate_ID", "Alternate_Ontology") from '${dbxref_file}' with csv header
insert into "${dbxref_schema}"."${dbxref_table}"("Gene", "Alternate_ID", "Alternate_Ontology")
  select "Gene", "Alternate_ID", "Alternate_Ontology" from tmp_dbxref
  on conflict("Gene", "Alternate_ID") do update set "Alternate_Ontology" = EXCLUDED."Alternate_Ontology";
create temporary table db_prefix(
  db text,
  pre_species_prefix text,
  space_replacement text,
  post_species_prefix text
);

\copy db_prefix(db,pre_species_prefix,space_replacement,post_species_prefix) from 'db_prefixes.csv' with csv header
update "${dbxref_schema}"."${dbxref_table}" d
   set "Reference_URL" = 
      coalesce(m.pre_species_prefix, '') ||
      regexp_replace(d."Alternate_ID", ' ', coalesce(m.space_replacement, ''), 'g') ||
      coalesce(m.post_species_prefix, '')
   from db_prefix m where m.db = d."Alternate_Ontology";;

-- More complicated external links
update "${dbxref_schema}"."${dbxref_table}" d
   set "Reference_URL" = 'https://uswest.ensembl.org/' ||
       regexp_replace(s.name, ' ', '_', 'g') ||
       '/Gene/Summary?db=core;g=' ||
       d."Alternate_ID"
   from "${gene_schema}"."${gene_table}" g 
   join "${species_schema}"."${species_table}" s on g."Species" = s."id"
   where d."Alternate_Ontology" = 'Ensembl'
   and g."id" = d."Gene";

update "${dbxref_schema}"."${dbxref_table}" d
   set "Reference_URL" = 'http://www.imgt.org/genedb/GENElect?query=2+' ||
   d."Alternate_ID" ||
  '&species=' ||
   regexp_replace(s.name, ' ', '+', 'g')
   from "${gene_schema}"."${gene_table}" g 
   join "${species_schema}"."${species_table}" s on g."Species" = s."id"
   where d."Alternate_Ontology" = 'IMGT/GENE-DB'
   and g."id" = d."Gene";
EOF
