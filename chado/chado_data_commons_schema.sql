begin;
create schema data_commons;

create table if not exists data_commons.domain_registry(
   id serial primary key,
   term_schema text not null,
   term_table text not null,
   rel_type_schema text not null,
   rel_type_table text not null,
   path_schema text not null,
   path_table text not null,
   unique(term_schema, term_table)
);   


create table data_commons.db (
  name text primary key,
  description text,
  urlprefix text,
  url text
  );

create table data_commons.cv (
  name text primary key,
  definition text
);

create table data_commons.dbxref (
  name text primary key,
  db text not null references data_commons.db(name) deferrable,
  accession text not null,
  version text not null default '',
  description text,
  unique(db, accession, version)
);

create table data_commons.cvterm (
  dbxref text primary key references data_commons.dbxref(name) deferrable,
  dbxref_unversioned text not null,
  cv text not null references data_commons.cv(name) deferrable,
  name text not null,
  definition text,
  is_obsolete boolean default false not null,
  is_relationshiptype boolean default false not null,
  synonyms text[],
  alternate_dbxrefs text[],
  unique(cv, name, is_obsolete),
  check(dbxref like dbxref_unversioned || ':%')
);

create index on data_commons.cvterm(name);
create index on data_commons.cvterm(dbxref_unversioned);
-- Ugh. These next indexes are used in searches of the form '{term}' <@ synonyms but not 'term' = any(synonyms)
create index on data_commons.cvterm using gin(synonyms);
create index on data_commons.cvterm using gin(alternate_dbxrefs);

create table data_commons.cvtermsynonym (
  cvtermsynonym_id bigserial primary key,
  dbxref text not null references data_commons.cvterm(dbxref) deferrable,
  synonym text not null,
  synonym_type text,
  unique (dbxref, synonym)
);

create table data_commons.cvterm_dbxref (
  cvterm_dbxref_id bigserial primary key,
  cvterm text not null references data_commons.cvterm(dbxref) deferrable,
  alternate_dbxref text not null references data_commons.dbxref(name) deferrable,
  is_for_definition boolean,
  unique(cvterm, alternate_dbxref)
);

create index on data_commons.cvterm_dbxref(cvterm);
create index on data_commons.cvterm_dbxref(alternate_dbxref);

create table data_commons.cvterm_relationship (
  cvterm_relationship_id bigserial primary key,
  type_dbxref text not null references data_commons.cvterm(dbxref) deferrable,
  subject_dbxref text not null references data_commons.cvterm(dbxref) deferrable,
  object_dbxref text not null references data_commons.cvterm(dbxref) deferrable,
  cv text not null references data_commons.cv(name),
  unique (type_dbxref, subject_dbxref, object_dbxref)
);  

create table data_commons.cvtermprop (
  cvtermprop_id bigserial primary key,
  cvterm_dbxref text not null references data_commons.cvterm(dbxref) deferrable,
  type_dbxref text not null references data_commons.cvterm(dbxref) deferrable,
  value text not null,
  rank integer not null,
  unique(cvterm_dbxref, type_dbxref, value, rank)
);
create index on data_commons.cvtermprop(cvterm_dbxref);
create index on data_commons.cvtermprop(type_dbxref);

create table data_commons.cvtermpath (
  cvtermpath_id bigserial primary key,
  type_dbxref text not null references data_commons.cvterm(dbxref) deferrable,
  subject_dbxref text not null references data_commons.cvterm(dbxref) deferrable,
  object_dbxref text not null references data_commons.cvterm(dbxref) deferrable,
  cv text not null references data_commons.cv(name) deferrable,
  pathdistance integer not null,
  unique(type_dbxref, subject_dbxref, object_dbxref)
);
create index on data_commons.cvtermpath(subject_dbxref, type_dbxref);
create index on data_commons.cvtermpath(object_dbxref, type_dbxref);

create table data_commons.relationship_types (
  cvterm_dbxref text primary key references data_commons.cvterm(dbxref) on delete cascade deferrable,
  is_reflexive boolean not null,
  is_transitive boolean not null
);  


commit;
