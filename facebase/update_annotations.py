#!/usr/bin/python

import sys
import traceback
import json
from deriva.core import ErmrestCatalog, AttrDict
from deriva.core.ermrest_model import builtin_types, Table, Column, Key, ForeignKey
from requests.exceptions import HTTPError
from httplib import CONFLICT

def main(servername, credentialsfilename, catalog, target):

    domain_tables = [
                     'age_stage',
                     'anatomic_source',
                     'anatomy',
                     'chemical_entities',
                     'cvnames',
                     'data_type',
                     'enhancer',
                     'file_format',
                     'gender',
                     'gene',
                     'gene_summary',
                     'genotype',
                     'histone_modification',
                     'human_age',
                     'image_creation_device',
                     'instrument',
                     'mapping_assembly',
                     'molecule_type',
                     'mouse_genetic_background',
                     'mutation',
                     'organism',
                     'origin',
                     'output_type',
                     'paired_end_or_single_read',
                     'phenotype',
                     'rnaseq_selection',
                     'sample_type',
                     'sequencing_data_direction',
                     'species',
                     'specimen',
                     'stage',
                     'strain',
                     'strandedness',
                     'target_of_assay',
                     'theiler_stage'
                     ]
        
    def get_refereced_by(goal, schema_name, table_name, exclude_schema=None):
        """
        Get the "Referenced by:" tables for the given schema:table.
        Exclude from the result the tables from the schema mentioned by the "exclude_schema" parameter
        """
        ret = []
        for schema in goal.schemas.values():
            for table in schema.tables.values():
                for foreign_key in table.foreign_keys:
                    if len(foreign_key.referenced_columns) == 1:
                        referenced_column = foreign_key.referenced_columns[0]
                        if referenced_column['table_name'] == table_name and referenced_column['schema_name'] == schema_name:
                            foreign_key_column = foreign_key.foreign_key_columns[0]
                            if foreign_key_column['schema_name'] != exclude_schema:
                                constraint_name = foreign_key.names[0]
                                ret.append({'foreign_key': foreign_key_column, 'constraint_name': constraint_name})
        return ret
    
    def set_ermrest_system_column_annotations(goal, schema, table):
        """
        Set annotations for the data_commons tables
        """
        counter = 0
        
        system_cols = [
            "RID",
            "RCB",
            "RMB",
            "RCT",
            "RMT"
            ]
        
        system_cols_display = {
            "RCT": "Creation Time",
            "RMT": "Last Modified Time"
            }
        
        for col in system_cols:
            if goal.column(schema, table, col).generated != True:
                goal.column(schema, table, col).generated = True
                
            if goal.column(schema, table, col).immutable != True:
                goal.column(schema, table, col).immutable = True
                
            counter = counter + 2
            
        for col,value in system_cols_display.iteritems():
            goal.column(schema, table, col).display.update({'name': '%s' % value})
            counter = counter + 1
            
        return counter
        
    def set_data_commons_tables_annotations(goal):
        """
        Set the annotations for the data_commons tables
        """

        """
        tag:isrd.isi.edu,2016:visible-columns
        """
        goal.table('data_commons', 'cvtermpath').visible_columns.update({
        "*": [
            ["data_commons", "cvtermpath_subject_dbxref_fkey"],
            ["data_commons", "cvtermpath_type_dbxref_fkey"],
            ["data_commons", "cvtermpath_object_dbxref_fkey"],
            "pathdistance"
            ]
        })                                                                         
    
        goal.table('data_commons', 'cvterm').visible_columns.update({
        "filter": {
                   "and": [
                           {"source": "name"}, 
                           {"source": "dbxref"}, 
                           {"source": "definition"}, 
                           {"source": "cv"}, 
                           {"source": "is_obsolete"}, 
                           {"source": "is_relationshiptype"}
                           ]
                   },
        "*": [
              "name", 
              ["data_commons", "cvterm_dbxref_fkey"], 
              "definition", 
              ["data_commons", "cvterm_cv_fkey"], 
              "is_obsolete", 
              "is_relationshiptype", 
              "synonyms", 
              "alternate_dbxrefs"
              ]
        })       
                                                                          
        """
        tag:isrd.isi.edu,2016:table-display
        """
        goal.table('data_commons', 'cvterm').table_display.update({
            "row_name": {"row_markdown_pattern": "{{name}}"}
        })                                                                         
    
        print 'Setting 3 annotations for the data_commons tables...'
   
    def set_data_commons_columns_annotations(goal):
        """
        Set the annotations for the columns of the data_commons schema
        """
        counter = 0
        
        data_commons_tables = [
            "cv",
            "cvterm",
            "cvterm_dbxref",
            "cvtermpath",
            "cvtermprop",
            "cvterm_relationship",
            "cvtermsynonym",
            "db",
            "dbxref",
            "domain_registry",
            "relationship_types"
            ]
        
        for table in data_commons_tables:
            counter = counter + set_ermrest_system_column_annotations(goal, 'data_commons', table)
        
        goal.column('data_commons', 'cvtermpath', 'type_dbxref').display.update({'name': 'Type'})       
        goal.column('data_commons', 'cvtermpath', 'object_dbxref').display.update({'name': 'Object'})       
        goal.column('data_commons', 'cvterm', 'dbxref').display.update({'name': 'Code'})       
        goal.column('data_commons', 'cvterm', 'cv').display.update({'name': 'Controlled Vocabulary'})       
        goal.column('data_commons', 'cvterm', 'alternate_dbxrefs').display.update({'name': 'Alternate Codes'})       
        
        counter = counter + 5
                                                                 
        print 'Setting %d annotations for the columns of the data_commons schema...' % counter
        
    def set_data_commons_foreign_key_annotations(goal):
        """
        Set the annotations for the Foreign Keys of the data_commons schema
        """
        counter = 0
        
        goal.table(
            'data_commons', 'cvtermpath'
        ).foreign_keys[
            ('data_commons', 'cvtermpath_object_dbxref_fkey')
        ].foreign_key.update({
            "to_name": "Object",
            "from_name": "Relationship paths with this term as object",
        })
        
        goal.table(
            'data_commons', 'cvtermpath'
        ).foreign_keys[
            ('data_commons', 'cvtermpath_subject_dbxref_fkey')
        ].foreign_key.update({
            "to_name": "Subject",
            "from_name": "Relationship paths with this term as subject",
        })
        
        counter = counter + 2
        
        for table in domain_tables:
            goal.table(
                'Vocabulary', '%s_paths' % table
            ).foreign_keys[
                ('Vocabulary', '%s_paths_type_dbxref_fkey1' % table)
            ].foreign_key.update({
                "to_name": "Type",
                "from_name": "Relationship paths with this term as type",
            })
            counter = counter + 1
        
        print 'Setting %d annotations for the Foreign Keys of the data_commons schema...' % counter

    def set_vocabulary_system_columns_annotations(goal):
        """
        Set the annotations for the system columns of the vocabulary tables
        """
        counter = 0
        
        for table in domain_tables:
            counter = counter + set_ermrest_system_column_annotations(goal, 'Vocabulary', '%s_paths' % table)
            counter = counter + set_ermrest_system_column_annotations(goal,'Vocabulary', '%s_relationship_types' % table)
            counter = counter + set_ermrest_system_column_annotations(goal,'Vocabulary', '%s_terms' % table)
            
        print 'Setting %d annotations for the system columns of the vocabulary tables...' % counter
        
    def set_vocabulary_tables_annotations(goal):
        """
        Set the annotations for the vocabulary tables
        """
        counter = 0
        
        for table in domain_tables:
            goal.table(
                'Vocabulary', '%s_terms' % table
            ).table_display.update({
              "row_name": {"row_markdown_pattern": "{{name}}"}                      
            })
            
            goal.table(
                'Vocabulary', '%s_terms' % table
            ).visible_columns.update({
              "filter": {"and": [{"source": "name"}, 
                                 {"source": "dbxref"}, 
                                 {"source": "definition"}, 
                                 {"source": "cv"}, 
                                 {"source": "is_obsolete"}, 
                                 {"source": "is_relationshiptype"}
                                 ]
                         }, 
                "entry": [ 
                      ["Vocabulary", "%s_terms_dbxref_fkey" % table], 
                      ],                      
                "*": ["name", 
                      "dbxref", 
                      "definition", 
                      ["Vocabulary", "%s_terms_cv_fkey" % table], 
                      "is_obsolete", 
                      "is_relationshiptype", 
                      "synonyms", 
                      "alternate_dbxrefs"]                      
            })
            
            goal.table(
                'Vocabulary', '%s_paths' % table
            ).visible_columns.update({
                "*": [["Vocabulary", "%s_paths_subject_dbxref_fkey" % table], 
                      ["Vocabulary", "%s_paths_type_dbxref_fkey" % table], 
                      ["Vocabulary", "%s_paths_object_dbxref_fkey" % table], 
                      "pathdistance"
                      ]               
            })
            
            goal.table(
                'Vocabulary', '%s_relationship_types' % table
            ).visible_columns.update({  
                "*": [["Vocabulary", 
                       "%s_relationship_types_cvterm_dbxref_fkey" % table], 
                       "is_reflexive", 
                       "is_transitive"
                      ]                                    
            })
            
            counter = counter + 4
            
        print 'Setting %d annotations for the vocabulary tables...' % counter
        
            
    def set_vocabulary_columns_annotations(goal, catalog_number):
        """
        Set the annotations for the columns of the vocabulary tables
        """
        counter = 0
        
        for table in domain_tables:
            goal.column(
                'Vocabulary', '%s_terms' % table, 'dbxref'
                ).column_display.update({
                  "*": {"markdown_pattern": "[{{dbxref}}](/data/record/#%d/data_commons:cvterm/dbxref={{#encode}}{{dbxref}}{{/encode}})" % catalog_number}               
            })
                    
            goal.column('Vocabulary', '%s_terms' % table, 'dbxref').display.update({'name': 'Code'})
            goal.column('Vocabulary', '%s_terms' % table, 'cv').display.update({'name': 'Controlled Vocabulary'})
            goal.column('Vocabulary', '%s_terms' % table, 'alternate_dbxrefs').display.update({'name': 'Alternate Codes'})
            goal.column('Vocabulary', '%s_paths' % table, 'type_dbxref').display.update({'name': 'Type'})
            goal.column('Vocabulary', '%s_paths' % table, 'subject_dbxref').display.update({'name': 'Subject'})
            goal.column('Vocabulary', '%s_paths' % table, 'object_dbxref').display.update({'name': 'Object'})
            goal.column('Vocabulary', '%s_relationship_types' % table, 'cvterm_dbxref').display.update({'name': 'Relationship'})
            
            if goal.column('Vocabulary', '%s_relationship_types' % table, 'is_reflexive').generated != True:
                goal.column('Vocabulary', '%s_relationship_types' % table, 'is_reflexive').generated = True
            if goal.column('Vocabulary', '%s_relationship_types' % table, 'is_transitive').generated != True:
                goal.column('Vocabulary', '%s_relationship_types' % table, 'is_transitive').generated = True
        
            if goal.column('Vocabulary', '%s_terms' % table, 'cv').generated != True:
                goal.column('Vocabulary', '%s_terms' % table, 'cv').generated = True
        
            if goal.column('Vocabulary', '%s_terms' % table, 'dbxref_unversioned').generated != True:
                goal.column('Vocabulary', '%s_terms' % table, 'dbxref_unversioned').generated = True
        
            if goal.column('Vocabulary', '%s_terms' % table, 'name').generated != True:
                goal.column('Vocabulary', '%s_terms' % table, 'name').generated = True
        
            if goal.column('Vocabulary', '%s_terms' % table, 'definition').generated != True:
                goal.column('Vocabulary', '%s_terms' % table, 'definition').generated = True
        
            if goal.column('Vocabulary', '%s_terms' % table, 'is_obsolete').generated != True:
                goal.column('Vocabulary', '%s_terms' % table, 'is_obsolete').generated = True
        
            if goal.column('Vocabulary', '%s_terms' % table, 'is_relationshiptype').generated != True:
                goal.column('Vocabulary', '%s_terms' % table, 'is_relationshiptype').generated = True
        
            if goal.column('Vocabulary', '%s_terms' % table, 'synonyms').generated != True:
                goal.column('Vocabulary', '%s_terms' % table, 'synonyms').generated = True
        
            if goal.column('Vocabulary', '%s_terms' % table, 'alternate_dbxrefs').generated != True:
                goal.column('Vocabulary', '%s_terms' % table, 'alternate_dbxrefs').generated = True
        
            counter = counter + 18
            
        print 'Setting %d annotations for the columns of the vocabulary tables...' % counter
        
    def set_vocabulary_foreign_key_annotations(goal):
        """
        Set the annotations for the Foreign Keys of the Vocabulary schema
        """
        counter = 0
        
        for table in domain_tables:
            goal.table(
                'Vocabulary', '%s_paths' % table
            ).foreign_keys[
                ('Vocabulary', '%s_paths_type_dbxref_fkey' % table)
            ].foreign_key.update({
                "from_name": "Relationship paths with this term as type",
            })
        
            goal.table(
                'Vocabulary', '%s_paths' % table
            ).foreign_keys[
                ('Vocabulary', '%s_paths_subject_dbxref_fkey' % table)
            ].foreign_key.update({
                "from_name": "Relationship paths with this term as subject",
                "to_name": "Subject",
            })
        
            goal.table(
                'Vocabulary', '%s_paths' % table
            ).foreign_keys[
                ('Vocabulary', '%s_paths_object_dbxref_fkey' % table)
            ].foreign_key.update({
                "from_name": "Relationship paths with this term as object",
                "to_name": "Object",
            })
        
            counter = counter + 3
            
        print 'Setting %d annotations for the Foreign Keys of the Vocabulary schema...' % counter
        
    def set_vocabulary_references_annotations(goal):
        """
        Set the annotations for the "Referenced by:" tables of the Vocabulary schema
        """
        counter = 0
        
        for table in domain_tables:
            references = get_refereced_by(goal, 'Vocabulary', '%s_terms' % table)
            for reference in references:
                foreign_key = reference['foreign_key']
                goal.table(
                    foreign_key['schema_name'], foreign_key['table_name']
                ).foreign_keys[
                    reference['constraint_name']
                ].foreign_key.update({
                    "to_name": "%s" % foreign_key['column_name'],
                })
                counter = counter + 1
                
        print 'Setting %d annotations for the "Referenced by:" tables of the Vocabulary schema...' % counter
        
                
    def apply(catalog, goal):
        """
        Apply the goal configuration to live catalog
        """
        counter = 0
        ready = False
        while ready == False:
            try:
                catalog.applyCatalogConfig(goal)
                ready = True
            except HTTPError as err:
                if err.errno == CONFLICT:
                    et, ev, tb = sys.exc_info()
                    print 'Conflict Exception "%s"' % str(ev)
                    counter = counter + 1
                    if counter >= 5:
                        print '%s' % str(traceback.format_exception(et, ev, tb))
                        ready = True
                    else:
                        print 'Retrying...'
            except:
                et, ev, tb = sys.exc_info()
                print str(et)
                print 'Exception "%s"' % str(ev)
                print '%s' % str(traceback.format_exception(et, ev, tb))
                ready = True
            
    def set_table_visible_columns():
        """
        Set the visible columns by replacing the columns names with the foreign keys
        """
        
        def getReferencesBy():
            """
            Get the tables ReferencesBy by the Vocabulary.*_terms tables excluding those from the Vocabulary schema
            """
        
            ret = []
            goal = catalog.get_catalog_model()
            for table in domain_tables:
                references = get_refereced_by(goal, 'Vocabulary', '%s_terms' % table, exclude_schema='Vocabulary')
                ret.extend(references)
            return ret
        
        def getVisibleColumns(references):
            """
            Get the visible columns of the tables ReferencesBy by the Vocabulary.*_terms tables excluding those from the Vocabulary schema
            """
            ret = {}
            goal = catalog.get_catalog_model()
            for reference in references:
                schema_name = reference['foreign_key']['schema_name']
                table_name = reference['foreign_key']['table_name']
                visible_columns = goal.table(schema_name, table_name).visible_columns
                if len(visible_columns) > 0:
                    if schema_name not in ret.keys():
                        ret[schema_name] = {}
                    schema = ret[schema_name]
                    if table_name not in schema.keys():
                        schema[table_name] = {}
                    table = schema[table_name]
                    table['old'] = visible_columns
                    if 'references' not in table.keys():
                        table['references'] = []
                    table['references'].append(reference)
            return ret
        
        def update_table_visible_columns(table_visible_columns):
            """
            Set the new value for the visible columns
            """
            
            def getColumnReference(column):
                for reference in table_visible_columns['references']:
                    if reference['foreign_key']['column_name'] == column:
                        return reference
                return None
    
            table_visible_columns['new'] = {}
            for key,columns in table_visible_columns['old'].iteritems():
                table_visible_columns['new'][key] = []
                for column in columns:
                    reference = getColumnReference(column)
                    if reference != None:
                        schema,constraint = reference['constraint_name']
                        table_visible_columns['new'][key].append(['%s' % (schema), '%s' % (constraint)])
                    else:
                        table_visible_columns['new'][key].append('%s' % column)
        
        references = getReferencesBy()
        visibleColumns = getVisibleColumns(references)
        
        goal = catalog.get_catalog_model()
        counter = 0
        for schema,tables in visibleColumns.iteritems():
            for table,visible_columns in tables.iteritems():
                update_table_visible_columns(visible_columns)
                goal.table(schema, table).visible_columns.update(visible_columns['new'])
                counter = counter + 1
                
        print 'Setting %d annotations for the visible columns of the "Referenced by:" tables of the Vocabulary schema...' % counter
        apply(catalog, goal)
        
    def set_pseudo_columns_table_display():
        """
        Set the tag:isrd.isi.edu,2016:table-display annotation for the pseudo_term column
        """
        
        def hasReferences(goal, schema, table):
            """
            Check if the table has ReferencesBy 
            """
        
            ret = False
            if len(get_refereced_by(goal, schema, table)) > 0:
                ret = True
            return ret
        
        def getDoubleReferences():
            """
            Get the tables ReferencesBy by the Vocabulary.*_terms tables excluding those from the Vocabulary schema
            """
        
            ret = {}
            goal = catalog.get_catalog_model()
            for table in domain_tables:
                references = get_refereced_by(goal, 'Vocabulary', '%s_terms' % table, exclude_schema='Vocabulary')
                for reference in references:
                    schema_name = reference['foreign_key']['schema_name']
                    table_name = reference['foreign_key']['table_name']
                    if hasReferences(goal, schema_name, table_name):
                        if schema_name not in ret.keys():
                            ret[schema_name] = []
                        if table_name not in ret[schema_name]:
                            ret[schema_name].append(table_name)
                        
            return ret
        
        tables = getDoubleReferences()
        """
        for schema in tables.keys():
            print len(tables[schema])
            
        print ''
        """
        for schema,table in tables.iteritems():
            print '%s:%s' % (schema, table)
        goal = catalog.get_catalog_model()
        counter = 0
        for schema in tables.keys():
            for table in tables[schema]:
                goal.table(schema, table).table_display.update({
                    "row_name": {"row_markdown_pattern": "{{pseudo_term}}"}
                })  
                goal.column(schema, table, 'pseudo_term').generated = True    
                counter = counter + 2
            
        print 'Setting %d annotations for the pseudo_term columns...' % counter
        apply(catalog, goal)
                                                                           
        
    def get_old_vocabulary_tables_references_by():
        """
        Set the tag:isrd.isi.edu,2016:table-display annotation for the pseudo_term column
        """
        vocabulary = [
            'age',
            'anatomy',
            'chemical_entities',
            'cvnames',
            'equipment_model',
            'experiment_type',
            'file_format',
            'gender',
            'gene',
            'gene_summary',
            'genotype',
            'histone_modification',
            'icd10_code',
            'icd10_diagnosis',
            'image_creation_device',
            'mapping_assembly',
            'molecule_type',
            'mutation',
            'omim_code',
            'omim_diagnosis',
            'origin',
            'output_type',
            'paired_end_or_single_read',
            'phenotype',
            'rnaseq_selection',
            'sample_type',
            'sequencing_data_direction',
            'species',
            'specimen',
            'stage',
            'strain',
            'strandedness',
            'target_of_assay',
            'theiler_stage'
                      ]
        
        isa = [
            'data_type',
            'human_age',
            'human_age_stage',
            'human_anatomic_source',
            'human_enhancer',
            'human_gender',
            'imaging_method',
            'instrument',
            'jax_strain',
            'mouse_age_stage',
            'mouse_anatomic_source',
            'mouse_enhancer',
            'mouse_gene',
            'mouse_genetic_background',
            'mouse_genotype',
            'mouse_mutation',
            'mouse_theiler_stage',
            'organism',
            'specimen',
            'zebrafish_age_stage',
            'zebrafish_anatomic_source',
            'zebrafish_genotype',
            'zebrafish_mutation'
               ]
        
        def hasReferences(goal, schema, table):
            """
            Check if the table has ReferencesBy 
            """
        
            ret = False
            if len(get_refereced_by(goal, schema, table)) > 0:
                ret = True
            return ret
        
        print 'Total old vocabulary tables: %d' % (len(vocabulary) + len(isa))
        goal = catalog.get_catalog_model()
        schema_name = 'vocabulary'
        counter = 0
        for table in vocabulary:
            if hasReferences(goal, schema_name, table) == False:
                print 'DROP TABLE "%s"."%s" CASCADE;' % (schema_name, table)
                counter = counter + 1
        schema_name = 'isa'
        for table in isa:
            if hasReferences(goal, schema_name, table) == False:
                print 'DROP TABLE "%s"."%s" CASCADE;' % (schema_name, table)
                counter = counter + 1
                
        print 'Total excluded tables: %d' % counter
            
        counter = 0
        vocabulary_domain = []
        isa_domain = []
        schema_name = 'vocabulary'
        for table in vocabulary:
            if hasReferences(goal, schema_name, table) == True:
                vocabulary_domain.append(table)
                counter = counter + 1
        schema_name = 'isa'
        for table in isa:
            if hasReferences(goal, schema_name, table) == True:
                isa_domain.append(table)
                counter = counter + 1
                
        print 'Total valid tables: %d' % counter
        schema_name = 'vocabulary'
        for table in vocabulary_domain:
            print '"%s"."%s"' % (schema_name, table)
        schema_name = 'isa'
        for table in isa_domain:
            print '"%s"."%s"' % (schema_name, table)
            
        references = {}
        for table in vocabulary_domain:
            references[table] = get_refereced_by(goal, 'vocabulary', table)
            
        for table in vocabulary_domain:
            print '\n%s:' % table
            for reference in references[table]:
                print reference
        
        for table in vocabulary_domain:
            print ''
            print '-- vocabulary.%s' % table
            for reference in references[table]:
                foreign_key = reference['foreign_key']
                schema_name = foreign_key['schema_name']
                table_name = foreign_key['table_name']
                column_name = foreign_key['column_name']
                if schema_name != 'vocabulary':
                    print 'SELECT data_commons.make_facebase_references(\'%s\', \'%s\', \'%s\', \'vocabulary\', \'%s\', \'id\', \'term\');' % (schema_name, table_name, column_name, table)
                
        for table in vocabulary_domain:
            print 'DROP TABLE "vocabulary"."%s" CASCADE;' % table
               
        """
        for table in vocabulary_domain:
            references = get_refereced_by(goal, 'Vocabulary', table)
            for reference in references:
                schema_name = reference['foreign_key']['schema_name']
                table_name = reference['foreign_key']['table_name']
                if hasReferences(goal, schema_name, table_name):
                    if schema_name not in ret.keys():
                        ret[schema_name] = []
                    if table_name not in ret[schema_name]:
                        ret[schema_name].append(table_name)
        print '"%s"."%s"' % (schema_name, table)
        """    
        
        
    # could wrap in a deriva-qt GUI to use interactive login instead?
    credentials = json.load(open(credentialsfilename))
    catalog_number = int(catalog)
    #print credentials
    catalog = ErmrestCatalog('https', servername, catalog, credentials)
    
    """
    Set the data_commons annotations
    """
    
    if target in ['all', 'data_commons_tables_annotations']:
        # get current model configuration from live DB
        goal = catalog.get_catalog_model()
        set_data_commons_tables_annotations(goal)
        apply(catalog, goal)
            
    if target in ['all', 'data_commons_columns_annotations']:
        # get current model configuration from live DB
        goal = catalog.get_catalog_model()
        set_data_commons_columns_annotations(goal)
        apply(catalog, goal)
        
    if target in ['all', 'data_commons_foreign_key_annotations']:
        # get current model configuration from live DB
        goal = catalog.get_catalog_model()
        set_data_commons_foreign_key_annotations(goal)
        apply(catalog, goal)
        
    
    """
    Set the Vocabulary annotations
    """
    
    if target in ['all', 'vocabulary_system_columns_annotations']:
        # get current model configuration from live DB
        goal = catalog.get_catalog_model()
        set_vocabulary_system_columns_annotations(goal)
        apply(catalog, goal)
        
    if target in ['all', 'vocabulary_tables_annotations']:
        # get current model configuration from live DB
        goal = catalog.get_catalog_model()
        set_vocabulary_tables_annotations(goal)
        apply(catalog, goal)
        
    if target in ['all', 'vocabulary_columns_annotations']:
        # get current model configuration from live DB
        goal = catalog.get_catalog_model()
        set_vocabulary_columns_annotations(goal, catalog_number)
        apply(catalog, goal)
        
    if target in ['all', 'vocabulary_foreign_key_annotations']:
        # get current model configuration from live DB
        goal = catalog.get_catalog_model()
        set_vocabulary_foreign_key_annotations(goal)
        apply(catalog, goal)
        
    if target in ['all', 'vocabulary_references_annotations']:
        # get current model configuration from live DB
        goal = catalog.get_catalog_model()
        set_vocabulary_references_annotations(goal);
        apply(catalog, goal)
        
    if target in ['all', 'vocabulary_schema_annotation']:
        # get current model configuration from live DB
        goal = catalog.get_catalog_model()
        goal.schemas['Vocabulary'].display.update({
           "name_style": {"underline_space": True, "title_case": True}
        })
        print 'Setting 1 annotation for the Vocabulary schema...'
        apply(catalog, goal)
        
    #if target in ['all', 'table_visible_columns']:
        #set_table_visible_columns()
        
    # apply goal configuration to live catalog
    #print 'Total number of updates: %d' % counter
    #print 'Applying the goal configuration to live catalog...'
    
    
if __name__ == '__main__':
    assert len(sys.argv) >= 4, "required arguments: servername credentialsfilename catalog"
    servername = sys.argv[1]
    credentialsfilename = sys.argv[2]
    catalog = sys.argv[3]
    if len(sys.argv) == 5:
        target = sys.argv[4]
    else:
        target = 'all'
    exit(main(servername, credentialsfilename, catalog, target))
