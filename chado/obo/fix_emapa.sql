begin;
create temporary table duplicates as
   select cv_id, name, is_obsolete, count(*) occurrences from cvterm group by cv_id, name, is_obsolete having count(*) > 1;

create temporary table cvterm2 as select * from cvterm c
where not exists (select 1 from duplicates d where d.name = c.name and d.cv_id = c.cv_id and d.is_obsolete = c.is_obsolete);

insert into cvterm2 (cvterm_id, cv_id, name, definition, dbxref_id, is_obsolete, is_relationshiptype)
  select
    c.cvterm_id,
    c.cv_id,
    c.name || coalesce(' (' || s.name || ' - ' || e.name || ')', ''),
    c.definition,
    c.dbxref_id,
    c.is_obsolete,
    c.is_relationshiptype
  from duplicates dup
    join cvterm c on c.cv_id = dup.cv_id and c.name = dup.name and c.is_obsolete = dup.is_obsolete
    join cvterm ts on ts.name = 'starts_at'
    join cvterm_relationship rs on rs.subject_id = c.cvterm_id and rs.type_id = ts.cvterm_id
    join cvterm s on s.cvterm_id = rs.object_id
    join cvterm te on te.name = 'ends_at'
    join cvterm_relationship re on re.subject_id = c.cvterm_id and re.type_id = te.cvterm_id
    join cvterm e on e.cvterm_id = re.object_id
;

alter table cvterm2 add primary key(cvterm_id);
    
create temporary table dup2 as
   select cv_id, name, is_obsolete, count(*) occurrences from cvterm2 group by cv_id, name, is_obsolete having count(*) > 1;

update cvterm2 c2 set name = d.name || ':' || dbx.accession || ' - ' ||  c2.name
  from dbxref dbx 
  join db d on d.db_id = dbx.db_id
  where dbx.dbxref_id = c2.dbxref_id
  and exists
     (select 1 from dup2 d2 where d2.cv_id = c2.cv_id and d2.name = c2.name and d2.is_obsolete = c2.is_obsolete);
  
update cvterm c set name = c2.name from cvterm2 c2 where c2.cvterm_id = c.cvterm_id;

alter table cvterm add constraint cvterm_c1 unique (name, cv_id, is_obsolete);

commit;

