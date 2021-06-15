#! /bin/bash

usage="$0 gene_info_file"

if [ $# -ne 1 ]; then
    echo $usage
    exit 1
fi

file=$1

if [[ $file =~ .gz ]]; then
    gunzip $file
    file=`basename -s .gz $file`
fi

cat <<EOF
create schema if not exists raw;
set search_path = raw;

create table if not exists species_map (
  taxon_id integer primary key,
  species_name text not null unique
);

truncate table species_map;

\copy species_map(taxon_id, species_name) from 'species_map.csv' with csv header

create table if not exists db_url_prefixes (
    db text primary key,
    pre_species_prefix text,
    space_replacement text,
    post_species_prefix text
);

truncate table db_url_prefixes;

\copy db_url_prefixes(db, pre_species_prefix, space_replacement, post_species_prefix) from 'db_prefixes.csv' with csv header

create table if not exists raw.gene_info (
    tax_id integer,
     geneid integer primary key,
     symbol text,
     locustag text,
     synonyms text,
     dbxrefs text,
     chromosome text,
     map_location text,
     description text,
     type_of_gene text,
     symbol_from_nomenclature_authority text,
     full_name_from_nomenclature_authority text,
     nomenclature_status text,
     other_designations text,
     modification_date text,
     feature_type text,
     species_name text);

truncate table raw.gene_info;
\copy gene_info(tax_id, geneid, symbol, locustag, synonyms, dbxrefs, chromosome, map_location, description, type_of_gene, symbol_from_nomenclature_authority, full_name_from_nomenclature_authority, nomenclature_status, other_designations, modification_date, feature_type) from '$file' with csv header delimiter E'\t'
EOF


for a in symbol locustag synonyms dbxrefs chromosome map_location description type_of_gene symbol_from_nomenclature_authority full_name_from_nomenclature_authority nomenclature_status other_designations; do
    cat<<EOF
update gene_info set $a = trim($a);
update gene_info set $a = null where $a in ('', '-');
EOF
done

cat <<EOF
update gene_info gi set species_name = m.species_name from species_map m
  where m.taxon_id = gi.tax_id;

create table if not exists raw.dbxrefs (
   geneid integer not null,
   db text not null,
   xref text not null,
   url text,
   primary key(geneid, db, xref)
);

truncate table raw.dbxrefs;

insert into raw.dbxrefs (geneid, db, xref, url)
with dbx as (
  select geneid, species_name, regexp_split_to_table(dbxrefs, '\|') dbxref from gene_info
  ),
dbr as (
   select geneid,
          species_name,
          regexp_replace(dbxref, '^([^:]*):.*$', '\1') db,
          regexp_replace(dbxref, '^[^:]*:(.*)', '\1') xref
   from dbx
)
select distinct
   d.geneid,
   d.db,
   d.xref,
   case
      when x.post_species_prefix is null then
           x.pre_species_prefix || d.xref
      else
           x.pre_species_prefix || regexp_replace(d.species_name, ' ', coalesce(x.space_replacement, '+')) ||
           x.post_species_prefix || d.xref
   end
   from dbr d
   left join db_url_prefixes x on x.db = d.db
;

analyze gene_info;
analyze dbxrefs;
EOF
