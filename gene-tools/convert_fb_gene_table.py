from deriva.core import DerivaServer, get_credential, BaseCLI
from deriva.core.ermrest_model import Table, Column, Key, ForeignKey, builtin_types
from gene_utils import GeneUtils

curie_prefixes = {
    'dev.facebase.org': 'FACEBASE_DEV',
    'staging.facebase.org': 'FACEBASE_STAGING',
    'www.facebase.org': 'FACEBASE',
    'facebase.org': 'FACEBASE'
}

def main(args):
    gu = GeneUtils(args)

    table = gu.model.table(gu.gene_schema, gu.gene_table)
                   
    # set nullok to false after values are worked out
    table.create_column(    
        Column.define("Gene_Type", builtin_types.text, nullok=True))
    table.create_fkey(
        ForeignKey.define(["Gene_Type"],
                          gu.gene_type_schema, gu.gene_type_table,
                          gu.adjust_fkey_columns_case(gu.gene_type_schema, gu.gene_type_table,["ID"])))
    

    # set nullok to false after values are worked out        
    table.create_column(
        Column.define("Species", builtin_types.text, nullok=True))

    table.create_column(        
        Column.define("Chromosome", builtin_types.text, nullok=True))
        
    table.create_fkey(
        ForeignKey.define(["Chromosome"], gu.chromosome_schema, gu.chromosome_table, ["RID"]))
        
    table.create_column(        
        Column.define("Location", builtin_types.text, nullok=True, comment="Location on chromosome"))

    table.create_column(
        Column.define("Source_Date", builtin_types.date, comment="Last-updated date reported by the gene data source´"))

    table.create_column(
        Column.define("Alternate_IDs", builtin_types['text[]'], comment="IDs for this gene in other ontologies"))    

    table.create_column(
            Column.define("Reference_URL", builtin_types.text, comment="Link to source information for this gene"))
    
    table.create_column(
        Column.define("Has_Data", builtin_types.boolean, nullok=False,
                      default=False, comment="True if any consortium data is associated with this gene"))

if __name__ == '__main__':
    cli = GeneUtils.create_parser('facebase gene table adjustment tool')
    args = cli.parse_cli()
    main(args)
                            
