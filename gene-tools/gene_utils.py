from deriva.core import DerivaServer, get_credential, BaseCLI
from deriva.core.ermrest_model import Table, Column, Key, ForeignKey, builtin_types
import argparse
import json
from pprint import pprint
import sys

class GeneUtils:
    def __init__(self, values, connect_to_ermrest=True):
        self.attrs = [
            "species_schema",
            "species_table",
            "chromosome_schema",
            "chromosome_table",
            "gene_type_schema",
            "gene_type_table",
            "gene_schema",
            "gene_table",
            "dbxref_schema",
            "dbxref_table",
            "catalog_id",
            "host",
            "curie_prefix",
            "source_file_schema",
            "source_file_table",
            "scratch_directory"
        ]

        config_file=None
        if isinstance(values, argparse.Namespace):
            if hasattr(values, 'config_file'):
                config_file=values.config_file
            for attr in self.attrs:
                if hasattr(values, attr):
                    setattr(self, attr, getattr(values, attr))
                else:
                    setattr(self, attr, None)
        else:
            config_file=values.get('config_file')            
            for attr in self.attrs:
                setattr(self, attr, values.get(attr))

        if (config_file):
            file = open(config_file, "r")
            defaults=json.load(file)
            file.close()

            for attr in self.attrs:
                if defaults.get(attr) and not getattr(self, attr):
                    setattr(self, attr, defaults[attr])

        shell_attrs = []
        for attr in self.attrs:
            val = getattr(self, attr)
            if val:
                shell_attrs.append('export {attr}="{val}"'.format(attr=attr, val=val))
        self.shell_attr_string = ';'.join(shell_attrs)
        self.pb = None
        if connect_to_ermrest:
            self.credential = get_credential(self.host)
            server = DerivaServer('https', self.host, self.credential)
            catalog = server.connect_ermrest(self.catalog_id)
            self.model = catalog.getCatalogModel()
            self.pb = catalog.getPathBuilder()


    @staticmethod
    def create_parser(description):
        cli = BaseCLI(description, None, 1, hostname_required=True)
        cli.remove_options(['--config-file'])
        cli.parser.add_argument('config_file', help='project-specific config file')
        cli.parser.add_argument('--catalog-id', type=int, default=1)
        cli.parser.add_argument('--scratch-directory',
                                help='directory for temporary storage of downloaded files')            
        return(cli)

    def create_species_table(self):
        schema = self.model.schemas[self.species_schema]
        schema.create_table(
            Table.define_vocabulary(self.species_table,
                                    '{prefix}:{{RID}}'.format(prefix=self.curie_prefix),
                                    key_defs=[Key.define(['Name'])],
                                    comment="Species"))

    def create_chromosome_table(self):
        schema = self.model.schemas[self.chromosome_schema]
        schema.create_table(
            Table.define(self.chromosome_table,
                         [
                             Column.define("Name", builtin_types.text, nullok=False),
                             Column.define("Species", builtin_types.text, nullok=False)
                         ],
                         key_defs = [
                             Key.define(["Name", "Species"])
                         ],
                         fkey_defs = [
                             ForeignKey.define(
                                 ["Species"], self.species_schema,
                                 self.species_table,
                                 self.adjust_fkey_columns_case(
                                     self.species_schema,
                                     self.species_table,
                                     ["ID"]))
                         ]))

    def create_gene_type_table(self):
        schema = self.model.schemas[self.gene_type_schema]
        schema.create_table(
            Table.define_vocabulary(self.gene_type_table,
                                    '{prefix}:{{RID}}'.format(prefix=self.curie_prefix),
                                    key_defs=[Key.define(['Name'])],
                                    uri_template='https://{host}/id/{{RID}}'.format(host=self.host),
                                    comment="Gene types"))

    def create_gene_table(self, extra_boolean_cols=[]):
        schema = self.model.schemas[self.gene_schema]
        common_cols = [
            Column.define("Gene_Type", builtin_types.text, nullok=False),
            Column.define("Species", builtin_types.text, nullok=False),
            Column.define("Chromosome", builtin_types.text),
            Column.define("Location", builtin_types.text, comment="Location on chromosome"),
            Column.define("Source_Date", builtin_types.date, comment="Last-updated date reported by the gene data source´"),
            Column.define("Reference_URL", builtin_types.text, comment="Link to source information for this gene")
        ]
        for colname in extra_boolean_cols:
            common_cols.append(Column.define(colname, builtin_types.boolean))

        fkey_defs = [
            ForeignKey.define(["Gene_Type"],
                              self.gene_type_schema, self.gene_type_table,
                              self.adjust_fkey_columns_case(["ID"])),
                              
            ForeignKey.define(["Species"], self.species_schema, self.species_table,
                              self.adjust_fkey_columns_case(
                                  self.species_schema,
                                  self.species_table,
                                  ["ID"])),
            ForeignKey.define(["Chromosome"], self.chromosome_schema, self.chromosome_table, ["RID"])
        ]

        key_defs = [
            ["NCBI_GeneID"]
        ]

        schema.create_table(
            table_def = Table.define_vocabulary(self.gene_table,
                                                '{prefix}:{{RID}}'.format(prefix=self.curie_prefix),
                                                comment="Genes"))

            
            
    def create_dbxref_table(self):
        schema = self.model.schemas[self.dbxref_schema]
        schema.create_table (
            Table.define (
                self.dbxref_table,
                [
                    Column.define("Gene", builtin_types.text, nullok=False, comment='Gene that this identifier refers to'),
                    Column.define("Alternate_ID", builtin_types.text, nullok=False),
                    Column.define("Alternate_Ontology", builtin_types.text, nullok=False, comment='Ontology this identifier is from'),
                    Column.define("Reference_URL", builtin_types.text, nullok=True, comment='URL to a description, in this alternate ontology, of this gene')
                ],
                key_defs = [
                    Key.define(["Gene", "Alternate_ID"])
                ],
                fkey_defs = [
                    ForeignKey.define(["Gene"], self.gene_schema, self.gene_table,
                                      self.adjust_fkey_columns_case(
                                          self.gene_schema,
                                          self.gene_table,
                                          ["ID"]))
                ],
                comment= 'Alternate gene identifiers from different ontologies')
        )

    def adjust_fkey_columns_case(self, schema_name, table_name, column_names):
        table = self.model.table(schema_name, table_name)
        new_cols = []
        for colname in column_names:
            new_cols.append(self.find_column_case_match(table, colname))
            return(new_cols)
        
    @staticmethod
    # Look for alternate column-name capitalizations for foreign key target columns.
    # If an exact match is found, use that.
    # Otherwise, if a unique case-insensitive match is found (e.g., "id" instead of "ID"), return that
    # If not, return None
    def find_column_case_match(table, column_name):
        found_col = None
        for col in table.column_definitions:
            if col.name == column_name:
                return(col.name)

            column_name = column_name.lower()
            if col.name.lower() == column_name:
                if found_col:
                    # more than one match; give up
                    return(None)
                found_col = col.name
        return(found_col)

    def create_source_file_table(self):
        schema = self.model.schemas[self.source_file_schema]
        schema.create_table(
            Table.define(
                self.source_file_table,
                [
                    Column.define("Species", builtin_types.text, nullok=False, comment="Species this file represents"),
                    Column.define("Downloaded_From", builtin_types.text, comment="URL of remote file (e.g., from NCBI) that this was downladoed from"),
                    Column.define("File_URL", builtin_types.text, nullok=False),
                    Column.define("File_Bytes", builtin_types.int4, nullok=False),
                    Column.define("File_MD5", builtin_types.text, nullok=False)
                ],
                key_defs = [
                    Key.define(["Species"])
                ],
                fkey_defs = [
                    ForeignKey.define(
                        ["Species"], self.species_schema,
                        self.species_table,
                        self.adjust_fkey_columns_case(
                            self.species_schema,
                            self.species_table,
                            ["ID"]))
                ]))
