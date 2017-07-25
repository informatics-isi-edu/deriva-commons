\set dc data_commons

begin;
create schema :dc;

create table :dc.db (
  name text primary key,
  description text,
  urlprefix text,
  url text
  );

create table :dc.cv (
  name text primary key,
  definition text
);

create table :dc.dbxref (
  name text primary key,
  db text not null references :dc.db(name) deferrable,
  accession text not null,
  version text not null default '',
  description text,
  unique(db, accession, version)
);

create table :dc.cvterm (
  dbxref text primary key references :dc.dbxref(name) deferrable,
  dbxref_unversioned text not null,
  cv text not null references :dc.cv(name) deferrable,
  name text not null,
  definition text,
  is_obsolete boolean not null,
  is_relationshiptype boolean not null,
  synonyms text[],
  alternate_dbxrefs text[],
  unique(cv, name, is_obsolete),
  check(dbxref like dbxref_unversioned || ':%')
);

create index on :dc.cvterm(dbxref_unversioned);
-- Ugh. These next indexes are used in searches of the form '{term}' <@ synonyms but not 'term' = any(synonyms)
create index on :dc.cvterm using gin(synonyms);
create index on :dc.cvterm using gin(alternate_dbxrefs);

create table :dc.cvtermsynonym (
  cvtermsynonym_id bigserial primary key,
  dbxref text not null references :dc.cvterm(dbxref) deferrable,
  synonym text not null,
  synonym_type text,
  unique (dbxref, synonym)
);

create table :dc.cvterm_dbxref (
  cvterm_dbxref_id bigserial primary key,
  cvterm text not null references :dc.cvterm(dbxref) deferrable,
  alternate_dbxref text not null references :dc.dbxref(name) deferrable,
  is_for_definition boolean,
  unique(primary_dbxref, alternate_dbxref)
);

create table :dc.cvtermpath (
  cvtermpath_id bigserial primary key,
  type_dbxref text not null references :dc.cvterm(dbxref) deferrable,
  subject_dbxref text not null references :dc.cvterm(dbxref) deferrable,
  object_dbxref text not null references :dc.cvterm(dbxref) deferrable,
  pathdistance integer not null,
  unique(type_dbxref, subject_dbxref, object_dbxref)
);  

commit;
