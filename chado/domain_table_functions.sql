create or replace function data_commons.register_domain_table(term_schema name, term_table name, rel_type_schema name, rel_type_table name, path_schema name, path_table name) returns boolean  as $$
  insert into data_commons.domain_registry(term_schema, term_table, rel_type_schema, rel_type_table, path_schema, path_table)
     values (term_schema, term_table, rel_type_schema, rel_type_table, path_schema, path_table);
  select true;
$$ language sql;

create or replace function data_commons.populate_domain_cvterm() returns trigger as $$
declare
   dbxref_unversioned text;
   cv text;
   name text;
   definition text;
   is_obsolete boolean;
   is_relationshiptype boolean;
   synonyms text[];
   alternate_dbxrefs text[];
begin
   select c.dbxref_unversioned, c.cv, c.name, c.definition, c.is_obsolete, c.is_relationshiptype, c.synonyms, c.alternate_dbxrefs
     into dbxref_unversioned, cv, name, definition, is_obsolete, is_relationshiptype, synonyms, alternate_dbxrefs
     from data_commons.cvterm c where c.dbxref = NEW.dbxref;
   NEW.dbxref_unversioned = dbxref_unversioned;
   NEW.cv = cv;
   NEW.name = name;
   NEW.definition = definition;
   NEW.is_obsolete = is_obsolete;
   NEW.is_relationshiptype = is_relationshiptype;
   NEW.synonyms = synonyms;
   NEW.alternate_dbxrefs = alternate_dbxrefs;
   return NEW;
end
$$ language plpgsql;

create or replace function data_commons.push_path_table_entries(type_schema name, type_table name, term_schema name, term_table name, path_schema name, path_table name, dbxref text) returns boolean as $$
begin
   execute format ('insert into %I.%I(cvtermpath_id, type_dbxref, subject_dbxref, object_dbxref, cv, pathdistance)
       select p.cvtermpath_id, p.type_dbxref, p.subject_dbxref, p.object_dbxref, p.cv, p.pathdistance from data_commons.cvtermpath p
       where %L in (type_dbxref, subject_dbxref, object_dbxref)
       and exists (select 1 from %I.%I t where t.cvterm_dbxref = p.type_dbxref)
       and exists (select 1 from %I.%I s where s.dbxref = p.subject_dbxref)
       and exists (select 1 from %I.%I o where o.dbxref = p.object_dbxref)
       on conflict (type_dbxref, subject_dbxref, object_dbxref) do update set cv=EXCLUDED.cv, pathdistance=EXCLUDED.pathdistance',
       path_schema, path_table,
       dbxref,
       type_schema, type_table,
       term_schema, term_table,
       term_schema, term_table);
   return true;
end
$$ language plpgsql;


create or replace function data_commons.populate_domain_tables_from_cvterm() returns trigger as $$
declare
   rel_type_schema name;
   rel_type_table name;
   path_schema name;
   path_table name;   
begin
   rel_type_schema = TG_ARGV[0];
   rel_type_table = TG_ARGV[1];
   path_schema = TG_TABLE_SCHEMA;
   select regexp_replace(TG_TABLE_NAME, '_terms$', '_paths') into path_table;

   if NEW.is_relationshiptype then
      execute format('insert into %I.%I(cvterm_dbxref, is_reflexive, is_transitive)
         select cvterm_dbxref, is_reflexive, is_transitive from data_commons.relationship_types where cvterm_dbxref = %L
         on conflict(cvterm_dbxref) do update set is_reflexive = EXCLUDED.is_reflexive, is_transitive = EXCLUDED.is_transitive',
	 rel_type_schema, rel_type_table, NEW.dbxref);
   end if;

   perform data_commons.push_path_table_entries(rel_type_schema, rel_type_table, TG_TABLE_SCHEMA, TG_TABLE_NAME, path_schema, path_table, NEW.dbxref);
   return NEW;
end
$$ language plpgsql;

create or replace function data_commons.update_domain_paths_from_relationship_type() returns trigger as $$
declare
   term_schema text;
   term_table text;
   path_schema text;
   path_table text;
begin
   for term_schema, term_table, path_schema, path_table in
       select d.term_schema, d.term_table, d.path_schema, d.path_table from data_commons.domain_registry d
         where d.rel_type_schema = TG_TABLE_SCHEMA and d.rel_type_table = TG_TABLE_NAME
   loop
       begin
           perform data_commons.push_path_table_entries(TG_TABLE_SCHEMA, TG_TABLE_NAME, term_schema, term_table, path_schema, path_table, NEW.dbxref);
       exception when others then
           continue;
       end;
   end loop;
   return NEW;
end
$$ language plpgsql;

create or replace function data_commons.make_domain_tables(schema_name name, base_name name, rel_type_schema name, rel_type_table name) returns boolean as $$
declare
   cvterm_name text = base_name || '_terms';
   path_name text = base_name || '_paths';
begin
   if rel_type_schema is null then
      rel_type_schema = schema_name;
   end if;
   if rel_type_table is null then
      rel_type_table = 'relationship_types';
   end if;   
   execute format('create table %I.%I (
                    dbxref text primary key references data_commons.cvterm(dbxref),
                    dbxref_unversioned text not null,
                    cv text not null references data_commons.cv(name),
                    name text not null,
                    definition text,
                    is_obsolete boolean not null,
                    is_relationshiptype boolean not null,
                    synonyms text[],
                    alternate_dbxrefs text[],
                    unique(cv, name, is_obsolete))',
		    schema_name, cvterm_name);

   execute format('create index on %I.%I(name)', schema_name, cvterm_name);
   execute format('create index on %I.%I(dbxref_unversioned)', schema_name, cvterm_name);
   execute format ('create index on %I.%I using gin(synonyms)', schema_name, cvterm_name);
   execute format ('create index on %I.%I using gin(alternate_dbxrefs)', schema_name, cvterm_name);
   execute format ('create trigger %I before insert on %I.%I for each row execute procedure data_commons.populate_domain_cvterm()',
                   cvterm_name || '_populate_trigger', schema_name, cvterm_name);
   execute format ('create trigger %I after insert on %I.%I for each row execute procedure data_commons.populate_domain_tables_from_cvterm(%I, %I)',
                   cvterm_name || '_populate_other_tables_trigger', schema_name, cvterm_name, rel_type_schema, rel_type_table);		   

   execute format('create table if not exists %I.%I (
     cvterm_dbxref text primary key references data_commons.relationship_types(cvterm_dbxref) on delete cascade deferrable,
     is_reflexive boolean not null,
     is_transitive boolean not null)',
     rel_type_schema, rel_type_table);

   execute format('drop trigger if exists %I on %I.%I', rel_type_table || '_push_trigger', rel_type_schema, rel_type_table);
   execute format('create trigger %I after insert on %I.%I for each row execute procedure data_commons.update_domain_paths_from_relationship_type()',
     rel_type_table || '_push_trigger', rel_type_schema, rel_type_table);

   execute format ('create table %I.%I (
                    cvtermpath_id bigint primary key,
                    type_dbxref text not null references %I.%I(cvterm_dbxref),
                    subject_dbxref text not null references %I.%I(dbxref),
                    object_dbxref text not null references %I.%I(dbxref),
                    cv text not null,
                    pathdistance integer not null,
                    unique(type_dbxref, subject_dbxref, object_dbxref),
                    foreign key (type_dbxref, subject_dbxref, object_dbxref) references data_commons.cvtermpath(type_dbxref, subject_dbxref, object_dbxref))',
		    schema_name, path_name,
		    rel_type_schema, rel_type_table,
		    schema_name, cvterm_name,
		    schema_name, cvterm_name);
   execute format ('create index on %I.%I(subject_dbxref, type_dbxref)', schema_name, path_name);
   execute format ('create index on %I.%I(object_dbxref, type_dbxref)', schema_name, path_name);
   perform data_commons.register_domain_table(schema_name, cvterm_name, rel_type_schema, rel_type_table, schema_name, path_name);
   return true;
end



$$ language plpgsql;

create or replace function data_commons.make_domain_tables(schema_name name, base_name name) returns boolean as $$
begin
   return data_commons.make_domain_tables(schema_name, base_name, null, null);
end
$$ language plpgsql;
