begin;
set search_path = "Common", etl_util;

alter table "Common"."Gene" add column if not exists "Ensembl_Symbol" text;

insert into "Common"."Gene_Type"("Name") select distinct type_of_gene from gene_info on conflict do nothing;
insert into "Common"."Chromosome"("Name", "Species") select distinct chromosome, species from gene_info where chromosome is not null and species is not null on conflict do nothing;

with url_table as (
   select d.geneid,
          string_agg(d.db || ': ' || '[' || d.xref || '](' ||  d.url || ')', ', ' order by d.db, d.xref) links
  from dbxrefs d group by d.geneid
)
update "Common"."Gene" o set
   "NCBI_Symbol" = g.symbol,
   "MGI_Symbol" = m.xref,
   "Ensembl_Symbol" = e.xref,
   "Synonyms" = array_to_string(regexp_split_to_array(g.synonyms, '\\|') || regexp_split_to_array(g.other_designations, '\\|'), ', '),
   "Description" = g.description,
   "Gene_Type" = g.type_of_gene,
   "Species" = g.species,
   "Chromosome" = g.chromosome,
   "Location" = g.map_location,
   "NCBI_Date" = g.data_source_date,
   "External_Links" = 'NCBI: [' || g.geneid::text || '](https://www.ncbi.nlm.nih.gov/gene/' || g.geneid::text || '), ' || url.links
from gene_info g
left join dbxrefs m on m.geneid = g.geneid and m.db = 'MGI'
left join dbxrefs e on e.geneid = g.geneid and e.db = 'Ensembl'
left join url_table url on url.geneid = g.geneid
where g.geneid = o."NCBI_GeneID";

insert into "Gene" (
   "NCBI_GeneID",
   "NCBI_Symbol",
   "MGI_Symbol",
   "Ensembl_Symbol",
   "Synonyms",
   "Description",
   "Gene_Type",
   "Species",
   "Chromosome",
   "Location",
   "NCBI_Date",
   "External_Links"
   )
with url_table as (
   select d.geneid,
          string_agg(d.db || ': ' || '[' || d.xref || '](' ||  d.url || ')', ', ' order by d.db, d.xref) links
  from dbxrefs d group by d.geneid
)
select distinct
   g.geneid,
   g.symbol,
   m.xref,
   e.xref,
   array_to_string(regexp_split_to_array(g.synonyms, '\\|') || regexp_split_to_array(g.other_designations, '\\|'), ', '),
   g.description,
   g.type_of_gene,
   g.species,
   g.chromosome,
   g.map_location,
   g.data_source_date,
   'NCBI: [' || g.geneid::text || '](https://www.ncbi.nlm.nih.gov/gene/' || g.geneid::text || '), ' || url.links
from gene_info g
left join dbxrefs m on m.geneid = g.geneid and m.db = 'MGI'
left join dbxrefs e on e.geneid = g.geneid and e.db = 'Ensembl'
left join url_table url on url.geneid = g.geneid
where not exists (select 1 from "Common"."Gene" o where o."NCBI_GeneID" = g.geneid);

commit;
create index if not exists "Gene_Ensembl_Symbol_idx" on "Common"."Gene"("Ensembl_Symbol");
analyze "Common"."Gene";

\copy "Common"."Gene" to '/var/scratch/gene_etl/new_data/gene.csv' with csv header
\copy "Common"."Chromosome" to '/var/scratch/gene_etl/new_data/chromosome.csv' with csv header
\copy (select "Name" from "Common"."Gene_Type" g where not exists (select 1 from "Common".original_gene_type o where o."Name" = g."Name")) to '/var/scratch/gene_etl/new_data/gene_type.csv' with csv header
