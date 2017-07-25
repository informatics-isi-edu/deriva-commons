\set dc data_commons
\set chado public

begin;

create or replace function :dc.chado_dbxref_id_to_dbxref(dbxref_id bigint) returns text as $$
  select d.name || ':' || x.accession || ':' || x.version
    from public.dbxref x join public.db d on d.db_id = x.db_id
    where x.dbxref_id = $1;
$$ language sql;

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


insert into :dc.cvterm_dbxref (cvterm, alternate_dbxref, is_for_definition)
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

