\set dc data_commons
\set chado public

begin;
create schema :dc;
create or replace function :dc.chado_dbxref_id_to_dbxref(dbxref_id bigint) returns text as $$
  select d.name || ':' || x.accession || ':' || x.version
    from public.dbxref x join public.db d on d.db_id = x.db_id
    where x.dbxref_id = $1;
$$ language sql;

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
  cv text not null,
  name text not null,
  definition text,
  is_obsolete boolean not null,
  is_relationshiptype boolean not null,
  synonyms text[],
  alternate_dbxrefs text[],
  unique(cv, name, is_obsolete),
  check(dbxref like dbxref_unversioned || ':%')
);

create table :dc.cvtermsynonym (
  cvtermsynonym_id bigserial primary key,
  dbxref text not null references :dc.cvterm(dbxref) deferrable,
  synonym text not null,
  synonym_type text,
  unique (dbxref, synonym)
);

create table :dc.cvterm_dbxref (
  cvterm_dbxref_id bigserial primary key,
  primary_dbxref text not null references :dc.cvterm(dbxref) deferrable,
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

insert into :dc.db(name, description, urlprefix, url)
  select name, description, urlprefix, url from :chado.db;

insert into :dc.cv(name, definition)
  select name, definition from :chado.cv;

insert into :dc.dbxref (name, db, accession, version, description)
  select
    :dc.chado_dbxref_id_to_dbxref(x.dbxref_id),
    d.name,
    x.accession,
    x.version,
    x.description
from :chado.db d join :chado.dbxref x on x.db_id = d.db_id;

insert into :dc.cvterm (
  dbxref,
  dbxref_unversioned,
  cv,
  name,
  definition,
  is_obsolete,
  is_relationshiptype,
  synonyms,
  alternate_dbxrefs
)
select
  :dc.chado_dbxref_id_to_dbxref(t.dbxref_id),
  d.name || ':' || x.accession,
  c.name,
  t.name,
  t.definition,
  t.is_obsolete::boolean,
  t.is_relationshiptype::boolean,
  (select array_agg(synonym) from :chado.cvtermsynonym s where s.cvterm_id = t.cvterm_id),
  (select array_agg(:dc.chado_dbxref_id_to_dbxref(cx.dbxref_id)) from :chado.cvterm_dbxref cx where cx.cvterm_id = t.cvterm_id)
from :chado.cvterm t
join :chado.dbxref x on x.dbxref_id = t.dbxref_id
join :chado.db d on d.db_id = x.db_id
join :chado.cv c on c.cv_id = t.cv_id;

insert into :dc.cvtermsynonym (dbxref, synonym, synonym_type)
select
  :dc.chado_dbxref_id_to_dbxref(c.dbxref_id),
  s.synonym,
  cst.name
from :chado.cvtermsynonym s
join :chado.cvterm c on c.cvterm_id = s.cvterm_id
join :chado.cvterm cst on cst.cvterm_id = s.type_id;


insert into :dc.cvterm_dbxref (primary_dbxref, alternate_dbxref, is_for_definition)
select
  :dc.chado_dbxref_id_to_dbxref(c.dbxref_id),
  :dc.chado_dbxref_id_to_dbxref(d.dbxref_id),
  cd.is_for_definition::boolean
from :chado.cvterm_dbxref cd
join :chado.cvterm c on c.cvterm_id = cd.cvterm_id
join :chado.dbxref d on d.dbxref_id = cd.dbxref_id;

insert into :dc.cvtermpath (
  type_dbxref,
  subject_dbxref,
  object_dbxref,
  pathdistance
)
select
  :dc.chado_dbxref_id_to_dbxref(ct.dbxref_id),
  :dc.chado_dbxref_id_to_dbxref(cs.dbxref_id),
  :dc.chado_dbxref_id_to_dbxref(co.dbxref_id),  
  min(p.pathdistance)
from :chado.cvtermpath p
join :chado.cvterm ct on ct.cvterm_id = p.type_id
join :chado.cvterm cs on cs.cvterm_id = p.subject_id
join :chado.cvterm co on co.cvterm_id = p.object_id
where pathdistance > 0
group by
  ct.dbxref_id,
  cs.dbxref_id,
  co.dbxref_id
;

commit;

