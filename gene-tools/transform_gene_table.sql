begin;
create schema if not exists transformed;

set search_path = transformed, raw;

create table if not exists transformed."Gene_Type" (
    "Name" text primary key
);
truncate table transformed."Gene_Type";

create table if not exists transformed."Chromosome" (
   "Name" text not null,
   "Species" text not null,
   unique ("Name", "Species")
);
truncate table transformed."Chromosome";

create table if not exists transformed."Gene" (
    "ID" text primary key,
    "URI" text not null unique,
    "Name" text not null,
    "Description" text,
    "Gene_Type" text not null,
    "Species" text not null,
    "Chromosome" text,
    "Location" text,
    "Source_Date" text,
    "Synonyms" text[],
    "Reference_URL" text
);
truncate table transformed."Gene";

create table if not exists transformed."Gene_Alternate_ID" (
     "Gene" text not null,
     "Alternate_ID" text not null,
     "Alternate_Ontology" text not null,
     "Reference_URL" text,
     unique("Gene", "Alternate_ID")
);
truncate table transformed."Gene_Alternate_ID";


insert into transformed."Gene_Type"("Name") select distinct type_of_gene from gene_info on conflict do nothing;
insert into transformed."Chromosome"("Name", "Species") select distinct chromosome, 'NCBITaxon:' || tax_id from gene_info where chromosome is not null and tax_id is not null on conflict do nothing;

insert into "Gene" (
   "ID",
   "URI",
   "Name",
   "Description",
   "Synonyms",
   "Gene_Type",
   "Species",
   "Chromosome",
   "Location",
   "Source_Date",
   "Reference_URL"
   ) select
      'NCBI_Gene:' || g.geneid,
      'https://ncbi.nlm.nih.gov/gene/' || g.geneid,
       g.symbol,
       g.description,
       array_cat(string_to_array(g.synonyms, '|'), string_to_array(g.other_designations, '|')),
       g.type_of_gene,
       'NCBITaxon:' || g.tax_id,
       g.chromosome,
       g.map_location,
       g.modification_date,
      'https://ncbi.nlm.nih.gov/gene/' || g.geneid
    from raw.gene_info g
    on conflict ("ID") do update set
       "Name" = EXCLUDED."Name",
       "Description" = EXCLUDED."Description",
       "Synonyms" = EXCLUDED."Synonyms",
       "Gene_Type" = EXCLUDED."Gene_Type",
       "Species" = EXCLUDED."Species",
       "Chromosome" = EXCLUDED."Chromosome",
       "Location" = EXCLUDED."Location",
       "Source_Date" = EXCLUDED."Source_Date"    
;

insert into transformed."Gene_Alternate_ID" (
   "Gene",
   "Alternate_ID",
   "Alternate_Ontology"
   ) select
   'NCBI_Gene:' || geneid,
    xref,
    db
from raw.dbxrefs;
commit;
analyze transformed."Gene";
