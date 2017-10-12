\set dc data_commons
\set chado public

begin;

insert into :dc.db(name, description, urlprefix, url)
  select name, description, urlprefix, url from :chado.db
  on conflict(name) do update set description=EXCLUDED.description, urlprefix=EXCLUDED.urlprefix, url=EXCLUDED.url;

insert into :dc.cv(name, definition)
  select name, definition from :chado.cv
  on conflict(name) do update set definition=EXCLUDED.definition;;

insert into :dc.dbxref (db, accession, version, description)
  select
    d.name,
    x.accession,
    x.version,
    x.description
from :chado.db d join :chado.dbxref x on x.db_id = d.db_id
on conflict(name) do update set accession=EXCLUDED.accession, version=EXCLUDED.version, description=EXCLUDED.description;;
analyze :dc.dbxref;

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
join :chado.cv c on c.cv_id = t.cv_id
on conflict(dbxref) do update
   set cv=EXCLUDED.cv, name=EXCLUDED.name, definition=EXCLUDED.definition, is_obsolete=EXCLUDED.is_obsolete, is_relationshiptype=EXCLUDED.is_relationshiptype,
       synonyms=EXCLUDED.synonyms, alternate_dbxrefs=EXCLUDED.alternate_dbxrefs;
analyze :dc.cvterm;

insert into :dc.cvtermsynonym (dbxref, synonym, synonym_type)
select
  :dc.chado_dbxref_id_to_dbxref(c.dbxref_id),
  s.synonym,
  cst.name
from :chado.cvtermsynonym s
join :chado.cvterm c on c.cvterm_id = s.cvterm_id
join :chado.cvterm cst on cst.cvterm_id = s.type_id
on conflict (dbxref, synonym) do update set synonym_type = EXCLUDED.synonym_type;


insert into :dc.cvterm_dbxref (cvterm, alternate_dbxref, is_for_definition)
select
  :dc.chado_dbxref_id_to_dbxref(c.dbxref_id),
  :dc.chado_dbxref_id_to_dbxref(d.dbxref_id),
  cd.is_for_definition::boolean
from :chado.cvterm_dbxref cd
join :chado.cvterm c on c.cvterm_id = cd.cvterm_id
join :chado.dbxref d on d.dbxref_id = cd.dbxref_id
on conflict(cvterm, alternate_dbxref) do update set is_for_definition = EXCLUDED.is_for_definition
;

insert into :dc.cvtermprop(cvterm_dbxref, type_dbxref, value, rank)
  select
  :dc.chado_dbxref_id_to_dbxref(c.dbxref_id),
  :dc.chado_dbxref_id_to_dbxref(t.dbxref_id),
  value,
  rank
from :chado.cvtermprop p
join :chado.cvterm c on c.cvterm_id = p.cvterm_id
join :chado.cvterm t on t.cvterm_id = p.type_id;
analyze :dc.cvtermprop;

insert into :dc.cvterm_relationship (type_dbxref, subject_dbxref, object_dbxref)
  select
  :dc.chado_dbxref_id_to_dbxref(t.dbxref_id),
  :dc.chado_dbxref_id_to_dbxref(s.dbxref_id),
  :dc.chado_dbxref_id_to_dbxref(o.dbxref_id)
from :chado.cvterm_relationship r
join :chado.cvterm t on t.cvterm_id = r.type_id
join :chado.cvterm s on s.cvterm_id = r.subject_id
join :chado.cvterm o on o.cvterm_id = r.object_id
on conflict(type_dbxref, subject_dbxref, object_dbxref) do update set cv = EXCLUDED.cv;

commit;

vacuum analyze;
