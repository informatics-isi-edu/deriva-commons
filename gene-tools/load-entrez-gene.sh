#! /bin/bash

cat <<EOF
begin;
set search_path = etl_util;
truncate table gene_file_versions;
\copy gene_file_versions(filename,data_source_name,data_source_url,species,data_source_date,retrieved_date) from '/var/www/bulk/etl_util/gene_file_versions.csv' with csv header
EOF

for f in $*; do
cat <<EOF
delete from entrez_gene where filename = '$f';
alter table entrez_gene alter column filename set default '$f';
\copy entrez_gene (gene_id,biotype,analysis_id,seq_region_id,seq_region_start,seq_region_end,seq_region_strand,display_xref_id,"source",status,description,is_current,canonical_transcript_id,stable_id,version,entrez_created_date,entrez_modified_date) from '$f' with csv delimiter E'\t'
alter table entrez_gene alter column filename set default null;
update entrez_gene g 
  set species=f.species, data_source_name=f.data_source_name,
      data_source_date = f.data_source_date, retrieved_date=f.retrieved_date
  from gene_file_versions f where f.filename = g.filename
  and g.filename = '$f';

EOF
done

cat <<EOF
analyze entrez_gene;
commit;
EOF



