begin;

create index if not exists cvterm_relationship_relid_idx on data_commons.cvterm_relationship(cvterm_relationship_id);
create index if not exists cvterm_relationship_type_dbxref_idx on data_commons.cvterm_relationship(type_dbxref);
create index if not exists cvterm_relationship_subject_dbxref_idx on data_commons.cvterm_relationship(subject_dbxref);
create index if not exists cvterm_relationship_object_dbxref_idx on data_commons.cvterm_relationship(object_dbxref);
create index if not exists cvtermpath_type_dbxref_idx on data_commons.cvtermpath(type_dbxref);

analyze data_commons.cvterm_relationship;
analyze data_commons.cvtermpath;

create or replace function data_commons.add_transitive_paths(base_relid bigint, new_relationship_type text, max_distance bigint) returns boolean as $$
declare
    is_a text = 'OBO_REL:is_a:';
begin
     with recursive
        path(subject_dbxref, object_dbxref, cv, pathdistance) as (
          select p.subject_dbxref, p.object_dbxref, p.cv, p.pathdistance
            from data_commons.cvtermpath p
  	  join data_commons.cvterm_relationship r on r.subject_dbxref = p.object_dbxref
	     and p.type_dbxref in (new_relationship_type, is_a)
  	  where r.cvterm_relationship_id = base_relid
          and r.subject_dbxref != r.object_dbxref
	  and p.subject_dbxref != p.object_dbxref
          union 
           select p.subject_dbxref, r.object_dbxref, p.cv, p.pathdistance + 1
             from path p
             join data_commons.cvterm_relationship r on r.subject_dbxref = p.object_dbxref
	        and r.subject_dbxref != r.object_dbxref
                and r.type_dbxref in (new_relationship_type, is_a)
             where p.pathdistance < max_distance)
        insert into data_commons.cvtermpath (type_dbxref, subject_dbxref, object_dbxref, cv, pathdistance) 
               select new_relationship_type, subject_dbxref, object_dbxref, min(cv), min(pathdistance) from path
               group by subject_dbxref, object_dbxref
               on conflict (type_dbxref, subject_dbxref, object_dbxref) do update set pathdistance = least(cvtermpath.pathdistance, EXCLUDED.pathdistance);
  
     with recursive
        path(subject_dbxref, object_dbxref, cv, pathdistance) as (
          select p.subject_dbxref, p.object_dbxref, p.cv, p.pathdistance
            from data_commons.cvtermpath p
  	  join data_commons.cvterm_relationship r on r.object_dbxref = p.subject_dbxref
	    and p.type_dbxref in (new_relationship_type, is_a)
  	  where r.cvterm_relationship_id = base_relid
          and r.subject_dbxref != r.object_dbxref
	  and p.subject_dbxref != p.object_dbxref	  
          union
           select r.subject_dbxref, p.object_dbxref, p.cv, p.pathdistance+1
             from path p
             join data_commons.cvterm_relationship r on r.object_dbxref = p.subject_dbxref
	        and r.subject_dbxref != r.object_dbxref	     
	        and r.type_dbxref in (new_relationship_type, is_a)
             where p.pathdistance < max_distance)
        insert into data_commons.cvtermpath (type_dbxref, subject_dbxref, object_dbxref, cv, pathdistance) 
               select new_relationship_type, subject_dbxref, object_dbxref, min(cv), min(pathdistance) from path
               group by subject_dbxref, object_dbxref
               on conflict (type_dbxref, subject_dbxref, object_dbxref) do update set pathdistance = least(cvtermpath.pathdistance, EXCLUDED.pathdistance);
   return true;
   end;
$$ language plpgsql;

create or replace function data_commons.create_relationship_paths(cvterm_relid bigint, max_distance bigint) returns boolean as $$
declare is_a text = 'OBO_REL:is_a:';
declare is_transitive boolean;
declare is_reflexive boolean;
declare new_relationship_type text;
begin
  select r.type_dbxref, t.is_transitive into new_relationship_type, is_transitive, is_reflexive
     from data_commons.cvterm_relationship r
     join data_commons.relationship_types t on t.cvterm_dbxref = r.type_dbxref
     where r.cvterm_relationship_id = cvterm_relid;

  insert into data_commons.cvtermpath(type_dbxref, subject_dbxref, object_dbxref, cv, pathdistance)
     select r.type_dbxref, r.subject_dbxref, r.object_dbxref, r.cv, 1
     from data_commons.cvterm_relationship r where r.cvterm_relationship_id = cvterm_relid
     on conflict (type_dbxref, subject_dbxref, object_dbxref) do update set pathdistance = least(cvtermpath.pathdistance, EXCLUDED.pathdistance);	  

  if new_relationship_type = is_a then
     for new_relationship_type in
         select cvterm_dbxref from data_commons.relationship_types t where t.is_transitive
     loop
         begin
            perform data_commons.add_transitive_paths(cvterm_relid, new_relationship_type, max_distance);
	 end;
      end loop;
  elsif is_transitive then
       perform data_commons.add_transitive_paths(cvterm_relid, new_relationship_type, max_distance);
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

insert into data_commons.db(name, description) values (:my_db, 'locally-generated terms')
on conflict do nothing;

create or replace function create_dbxref_index(db text) returns boolean as $$
begin
   execute format('create index if not exists %I on data_commons.dbxref(accession) where db = %L', 'dbxref_accession_' || db || '_idx', db);
   return true;
end
$$ language plpgsql;

select create_dbxref_index(:my_db);
analyze data_commons.dbxref;

drop trigger if exists cvterm_insert_trigger on data_commons.cvterm;
create trigger cvterm_insert_trigger
after insert on data_commons.cvterm
for each row execute procedure data_commons.cvterm_add(:my_db);

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
   perform public.try_ermrest_data_change_event('data_commons', 'cvtermpath');
   perform public.try_ermrest_data_change_event('data_commons', 'relationship_types');   
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
for each row execute procedure data_commons.cvterm_generate_dbxref(:my_db);

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

create or replace function data_commons.update_synonym_array() returns trigger as $$
begin
   update data_commons.cvterm c set synonyms =
      (select array_agg(synonym) from data_commons.cvtermsynonym s where s.dbxref = NEW.dbxref)
      where c.dbxref = NEW.dbxref;
   perform public.try_ermrest_data_change_event('data_commons', 'cvterm');      
   return NEW;
end
$$ language plpgsql;;

drop trigger if exists synonym_push_trigger on data_commons.cvtermsynonym;
create trigger synonym_push_trigger after insert on data_commons.cvtermsynonym for each row execute procedure data_commons.update_synonym_array();

create or replace function data_commons.update_dbxref_array() returns trigger as $$
begin
   update data_commons.cvterm c set alternate_dbxrefs =
      (select array_agg(alternate_dbxref) from data_commons.cvterm_dbxref d where d.cvterm = NEW.cvterm)
      where c.dbxref = NEW.cvterm;
   perform public.try_ermrest_data_change_event('data_commons', 'cvterm');
   return NEW;
end
$$ language plpgsql;;

drop trigger if exists cvterm_dbxref_push_trigger on data_commons.cvterm_dbxref;
create trigger cvterm_dbxref_push_trigger after insert on data_commons.cvterm_dbxref for each row execute procedure data_commons.update_dbxref_array();

create or replace function data_commons.push_cvterm_updates() returns trigger as $$
declare
   term_schema text;
   term_table text;
begin
   for term_schema, term_table in
       select d.term_schema, d.term_table from data_commons.domain_registry d
   loop
       begin
           execute format('update %I.%I set cv = $1, name = $2, definition = $3, is_obsolete = $4, is_relationshiptype = $5, synonyms = $6, alternate_dbxrefs = $7 where dbxref = $8',
	   term_schema, term_table)
	   using NEW.cv, NEW.name, NEW.definition, NEW.is_obsolete, NEW.is_relationshiptype, NEW.synonyns, NEW.alternate_dbxrefs, NEW.dbxref;
       exception when others then
           continue;
       perform public.try_ermrest_data_change_event(term_schema, term_table);	   
       end;
   end loop;
   return NEW;
end
$$ language plpgsql;

drop trigger if exists cvterm_push_updates_trigger on data_commons.cvterm;
create trigger cvterm_push_updates_trigger  after update on data_commons.cvterm for each row execute procedure data_commons.push_cvterm_updates();

create or replace function data_commons.push_cvtermpath_adds() returns trigger as $$
declare
   term_schema text;
   term_table text;
   path_schema text;
   path_table text;
   rel_schema text;
   rel_table text;
begin
   for term_schema, term_table, path_schema, path_table, rel_schema, rel_table in
       select d.term_schema, d.term_table, d.path_schema, d.path_table, d.rel_type_schema, d.rel_type_table from data_commons.domain_registry d
   loop
       begin
           if TG_OP = 'DELETE' or TG_OP = 'UPDATE' then
	      execute format ('delete from %I.%I where subject_dbxref = %L and object_dbxref = %L and type_dbxref = %L',
                 path_schema, path_table, OLD.subject_dbxref, OLD.object_dbxref, OLD.type_dbxref);
	   end if;
           if TG_OP = 'UPDATE' or TG_OP = 'INSERT' then
	      execute format ('insert into %I.%I (subject_dbxref, object_dbxref, type_dbxref, cv, pathdistance, cvtermpath_id) 
                  select %L, %L, %L, %L, %s, %s
                  where exists (select 1 from %I.%I where dbxref = %L)
                  and exists (select 1 from %I.%I where dbxref = %L)
                  and exists (select 1 from %I.%I where cvterm_dbxref = %L)',
                 path_schema, path_table, NEW.subject_dbxref, NEW.object_dbxref, NEW.type_dbxref, NEW.cv, NEW.pathdistance, NEW.cvtermpath_id,
		 term_schema, term_table, NEW.subject_dbxref,
		 term_schema, term_table, NEW.object_dbxref,
		 rel_schema, rel_table, NEW.type_dbxref
		 );
           end if;
--       exception when others then
--           continue;
       perform public.try_ermrest_data_change_event(term_schema, term_table);	   
       end;
   end loop;
   return NEW;
end
$$ language plpgsql;

drop trigger if exists cvtermpath_push_updates_trigger on data_commons.cvtermpath;
create trigger cvtermpath_push_updates_trigger  after insert or update or delete on data_commons.cvtermpath for each row execute procedure data_commons.push_cvtermpath_adds();

-- terrible hack
insert into data_commons.db(name) values ('internal'), ('OBO_REL')
on conflict do nothing;

insert into data_commons.cv(name) values ('cvterm_property_type'), ('relationship')
on conflict do nothing;

insert into data_commons.dbxref(db, accession) values ('internal', 'is_reflexive'), ('OBO_REL', 'is_a'), ('internal', 'is_transitive')
on conflict do nothing;

insert into data_commons.cvterm(dbxref, name, cv)
  select d.name, d.accession, 'cvterm_property_type' from data_commons.dbxref d where d.db = 'internal' and d.accession in ('is_reflexive', 'is_transitive')
on conflict do nothing;

insert into data_commons.cvterm(dbxref, name, cv, is_relationshiptype)
  select d.name, 'is_a', 'relationship', true from data_commons.dbxref d where d.db = 'OBO_REL' and d.accession = 'is_a'
on conflict do nothing;

insert into data_commons.cvtermprop(cvterm_dbxref, type_dbxref, value, rank)
  select c.dbxref,
  d.name,
  1, 0
  from data_commons.cvterm c
  join data_commons.dbxref d on d.db = 'internal' and d.accession in ('is_reflexive', 'is_transitive')
  where c.name = 'is_a' and c.is_relationshiptype and c.cv = 'relationship'
on conflict do nothing;

commit;
