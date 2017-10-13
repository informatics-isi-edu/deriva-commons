begin;
create or replace function data_commons.chado_dbxref_id_to_dbxref(dbxref_id bigint) returns text as $$
  select d.name || ':' || x.accession || ':' || x.version
    from public.dbxref x join public.db d on d.db_id = x.db_id
    where x.dbxref_id = $1;
$$ language sql;

create or replace function data_commons.create_relationship_paths(cvterm_relid bigint, max_distance bigint) returns boolean as $$
declare is_a text = 'OBO_REL:is_a:';
declare is_transitive boolean;
begin
   select t.is_transitive into is_transitive
     from data_commons.cvterm_relationship r
     join data_commons.relationship_types t on t.cvterm_dbxref = r.type_dbxref
     where r.cvterm_relationship_id = cvterm_relid;

   insert into data_commons.cvtermpath (type_dbxref, subject_dbxref, object_dbxref, cv, pathdistance)
      select type_dbxref, subject_dbxref, object_dbxref, cv, 1
      from data_commons.cvterm_relationship where cvterm_relationship_id = cvterm_relid
      on conflict (type_dbxref, subject_dbxref, object_dbxref) do update set pathdistance = least(cvtermpath.pathdistance, EXCLUDED.pathdistance);
   if is_transitive then
     with recursive
        path(type_dbxref, subject_dbxref, object_dbxref, cv, pathdistance) as (
          select p.type_dbxref, p.subject_dbxref, p.object_dbxref, p.cv, p.pathdistance
            from data_commons.cvtermpath p
  	  join data_commons.cvterm_relationship r on r.type_dbxref = p.type_dbxref and r.subject_dbxref = p.object_dbxref
  	  where r.cvterm_relationship_id = cvterm_relid
          union 
           select p.type_dbxref, p.subject_dbxref, r.object_dbxref, p.cv, p.pathdistance+1
             from path p
             join data_commons.cvterm_relationship r on r.subject_dbxref = p.object_dbxref and r.type_dbxref = p.type_dbxref
             where p.pathdistance < max_distance)
        insert into data_commons.cvtermpath (type_dbxref, subject_dbxref, object_dbxref, cv, pathdistance) 
               select type_dbxref, subject_dbxref, object_dbxref, cv, min(pathdistance) from path
               group by type_dbxref, subject_dbxref, object_dbxref, cv
               on conflict (type_dbxref, subject_dbxref, object_dbxref) do update set pathdistance = least(cvtermpath.pathdistance, EXCLUDED.pathdistance);
  
     with recursive
        path(type_dbxref, subject_dbxref, object_dbxref, cv, pathdistance) as (
          select p.type_dbxref, p.subject_dbxref, p.object_dbxref, p.cv, p.pathdistance
            from data_commons.cvtermpath p
  	  join data_commons.cvterm_relationship r on r.type_dbxref = p.type_dbxref and r.object_dbxref = p.subject_dbxref
  	  where r.cvterm_relationship_id = cvterm_relid
          union
           select p.type_dbxref, r.subject_dbxref, p.object_dbxref, p.cv, p.pathdistance+1
             from path p
             join data_commons.cvterm_relationship r on r.object_dbxref = p.subject_dbxref and r.type_dbxref = p.type_dbxref	
             where p.pathdistance < max_distance)
        insert into data_commons.cvtermpath (type_dbxref, subject_dbxref, object_dbxref, cv, pathdistance) 
               select type_dbxref, subject_dbxref, object_dbxref, cv, min(pathdistance) from path
               group by type_dbxref, subject_dbxref, object_dbxref, cv
               on conflict (type_dbxref, subject_dbxref, object_dbxref) do update set pathdistance = least(cvtermpath.pathdistance, EXCLUDED.pathdistance);
  end if;
  return true;
end
$$ language plpgsql;

create or replace function data_commons.cvtermpath_add() returns trigger as $$
begin
   perform data_commons.create_relationship_paths(NEW.cvterm_relationship_id, 100);
   return NEW;
end
$$ language plpgsql;

drop trigger if exists relationship_insert_trigger on data_commons.cvterm_relationship;
create trigger relationship_insert_trigger
after insert on data_commons.cvterm_relationship
for each row execute procedure data_commons.cvtermpath_add();

create sequence if not exists data_commons.local_dbxref_seq;

create or replace function data_commons.generate_dbxref(db text) returns text as $$
declare
  accession_id text;
begin
  insert into data_commons.db(name, description) values (db, 'local terms') on conflict do nothing;
  select nextval('data_commons.local_dbxref_seq')::text into accession_id;
  insert into data_commons.dbxref(db, accession) values (db, accession_id);
  return db || ':' || accession_id || ':';
end
$$language plpgsql;

create or replace function data_commons.cvterm_generate_dbxref() returns trigger as $$
declare
  db text = TG_ARGV[0];
begin
  if NEW.dbxref is null then
     NEW.dbxref = data_commons.generate_dbxref(db);
  end if;
  NEW.dbxref_unversioned = (select d.db || ':' || d.accession from data_commons.dbxref d where d.name = NEW.dbxref);
  return NEW;
end
$$language plpgsql;

create or replace function data_commons.cvterm_add() returns trigger as $$
begin
   insert into data_commons.cvtermpath(type_dbxref, subject_dbxref, object_dbxref, cv, pathdistance)
      select t.cvterm_dbxref, NEW.dbxref, NEW.dbxref, NEW.cv, 0
      from data_commons.relationship_types t where t.is_reflexive
      on conflict(type_dbxref, subject_dbxref, object_dbxref) do update set pathdistance = 0;
   
   if NEW.is_relationshiptype then
      insert into data_commons.relationship_types(cvterm_dbxref, is_reflexive, is_transitive)
         select
	   NEW.dbxref,
	   exists (select 1 from data_commons.cvtermprop where cvterm_dbxref = NEW.dbxref and type_dbxref = 'internal:is_reflexive:' and value = '1'),
	   exists (select 1 from data_commons.cvtermprop where cvterm_dbxref = NEW.dbxref and type_dbxref = 'internal:is_transitive:' and value = '1');
   end if;	   
   return NEW;
end
$$ language plpgsql;

drop trigger if exists cvterm_insert_trigger on data_commons.cvterm;
create trigger cvterm_insert_trigger
after insert on data_commons.cvterm
for each row execute procedure data_commons.cvterm_add('laura');

create or replace function data_commons.dbxref_set_name() returns trigger as $$
begin
  NEW.name = NEW.db || ':' || NEW.accession || ':' || NEW.version;
  return NEW;
end
$$ language plpgsql;

drop trigger if exists dbxref_insert_trigger on data_commons.dbxref;
create trigger dbxref_insert_trigger
before insert on data_commons.dbxref
for each row execute procedure data_commons.dbxref_set_name();

create or replace function data_commons.cvtermprop_add() returns trigger as $$
begin
   insert into data_commons.cvtermpath(type_dbxref, subject_dbxref, object_dbxref, cv, pathdistance)
      select NEW.cvterm_dbxref, c.dbxref, c.dbxref, c.cv, 0
      from data_commons.cvterm c where NEW.type_dbxref = 'internal:is_reflexive:' and NEW.value = '1'
      on conflict(type_dbxref, subject_dbxref, object_dbxref) do update set pathdistance = 0;
   if NEW.type_dbxref = 'internal:is_reflexive:' then
      update data_commons.relationship_types set is_reflexive = (NEW.value = '1') where cvterm_dbxref = NEW.cvterm_dbxref;
   end if;
   if NEW.type_dbxref = 'internal:is_transitive:' then
      update data_commons.relationship_types set is_transitive = (NEW.value = '1') where cvterm_dbxref = NEW.cvterm_dbxref;
   end if;
   return NEW;
end
$$ language plpgsql;

drop trigger if exists cvtermprop_insert_trigger on data_commons.cvtermprop;
create trigger cvtermprop_insert_trigger
before insert on data_commons.cvtermprop
for each row execute procedure data_commons.cvtermprop_add();


drop trigger if exists cvterm_generate_dbxref on data_commons.cvterm;
create trigger cvterm_generate_dbxref
before insert on data_commons.cvterm
for each row execute procedure data_commons.cvterm_generate_dbxref('laura');

create or replace function data_commons.relationship_set_cv() returns trigger as $$
begin
  NEW.cv = coalesce(NEW.cv, (select cv from data_commons.cvterm where dbxref = NEW.subject_dbxref));
  return NEW;
end
$$ language plpgsql;

drop trigger if exists relationship_cv_trigger on data_commons.cvterm_relationship;
create trigger relationship_cv_trigger
before insert on data_commons.cvterm_relationship
for each row execute procedure data_commons.relationship_set_cv();
commit;
