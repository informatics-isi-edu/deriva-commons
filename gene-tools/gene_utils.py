from deriva.core import DerivaServer, get_credential, BaseCLI
from deriva.core.ermrest_model import Table, Column, Key, ForeignKey, builtin_types

class GeneUtils:
    def __init__(values):
        self.values = values
        credential = get_credential(self.values.host)
        server = DerivaServer('https', self.values.host, credential)
        catalog = server.connect_ermrest(self.values.catalog_id)
        model = catalog.getCatalogModel()
        self.pb = catalog.getPathBuilder()

    @staticmethod
    def create_parser(description):
        cli = BaseCLI(description, None, 1, hostname_required=True)
        cli.parser.add_argument('--species-schema', help='schema for species table', default='Vocabulary')
        cli.parser.add_argument('--species-table', help='species table name', default='Species')
        
        cli.parser.add_argument('--chromosome-schema', help='schema for chromosome table', default='Common')
        cli.parser.add_argument('--chromosome-table', help='chromosome table name', default='Chromosome')

        cli.parser.add_argument('--gene-type-schema', help='schema for gene types table', default='Vocabulary')
        cli.parser.add_argument('--gene-type-table', help='gene types table name', default='Gene_Type')
            
        cli.parser.add_argument('--gene-schema', help='schema for gene table', default='Vocabulary')
        cli.parser.add_argument('--gene-table', help='gene table name', default='Gene')

        cli.parser.add_argument('--catalog-id', type=int, default=1)
        return(cli)


    def create_species_table(self):
        schema = self.model.schemas[self.values.species_schema]
        schema.create_table(
            Table.define_vocabulary(self.values.species_table,
                                    '{prefix}:{RID}'.format(prefix=self.values.curie_prefix),
                                    keys=[Key.define(['Name'])],
                                    comment="Species"))

    def create_chromosome_table(self):
        schema = self.model.schemas[self.values.chromosome_schema]
        schema.create_table(
            Table.define(self.values.chromosome_table,
                         [
                             Column.define("Name", builtin_types.text, nullok=False),
                             Column.define("Species", builtin_types.text, nullok=False)
                         ],
                         keys= [
                             Key.define(["Name", "Species"])
                         ],
                         fkeys = [
                             ForeignKey.define(["Species"], self.values.species_schema,
                                               self.values.species_table, ["Name"])
                         ]))

    def create_gene_type_table(self):
        schema = self.model.schemas[self.values.gene_type_schema]
        schema.create_table(
            Table.define_vocabulary(self.values.gene_type_table,
                                    '{prefix}:{RID}'.format(prefix=self.values.curie_prefix),
                                    keys=[Key.define(['Name'])],
                                    comment="Gene types"))

    def create_gene_table(self, extra_boolean_cols=[]):
        schema = self.model.schemas[self.values.gene_schema]
        common_cols = [
            Column.define("NCBI_GeneID", builtin_types.int4, nullok=False, comment="NCBI (Entrez) numeric gene ID"),
            Column.define("Gene_Type", builtin_types.text),
            Column.define("Species", builtin_types.text, nullok=False),
            Column.define("Chromosome", builtin_types.text),
            Column.define("Location", builtin_types.text, comment="Location on chromosome"),
            Column.define("NCBI_Date", builtin_types.timestamptz, comment="Date of NCBI file this record was derived from")
        ]
        for colname in extra_boolean_cols:
            common_cols.append(Column.define(colname, builtin_types.boolean))

        fkeys = [
            ForeignKey.define(["Species"], self.values.species_schema, self.values.species_table, ["Name"]),
            ForeignKey.define(["Chromosome"], self.values.chromosome_schema, self.values.chromosome_table, ["RID"])
        ]

        keys = [
            ["NCBI_GeneID"]
        ]

        if use_vocab_style:
            schema.create_table(
            table_def = Table.define_vocabulary(self.values.gene_table,
                                                '{prefix}:{RID}'.format(prefix=self.values.curie_prefix),
                                                comment="Genes"))

            
            

                                          
