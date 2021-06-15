from deriva.core import BaseCLI
import sys
from gene_utils import GeneUtils

if __name__ == '__main__':
    cli = GeneUtils.create_parser("gene table creation tool")
    cli.parser.add_argument('--skip-species', help='skip species table creation', action='store_true')
    cli.parser.add_argument('--skip-chromosome', help='skip chromosome table creation', action='store_true')
    cli.parser.add_argument('--skip-gene-type', help='skip gene type table creation', action='store_true')
    cli.parser.add_argument('--skip-gene', help='skip gene table creation', action='store_true')
    cli.parser.add_argument('--skip-dbxref', help='skip gene table creation', action='store_true')    
    cli.parser.add_argument('--skip-source-file', help='skip source file table creation', action='store_true')    
    cli.parser.add_argument('--extra-boolean-cols', default=[], nargs='+',
                        help='extra boolean columns to create in the gene table\
  (e.g., to indicate existence of data for a particular gene)')
    cli.parser.add_argument('curie_prefix', help='prefix for CURIEs to assign to project-generated terms')
    
    args = cli.parse_cli()
    gene_utils = GeneUtils(args)

    if not args.skip_source_file:
        gene_utils.create_source_file_table()
    if not args.skip_species:
        gene_utils.create_species_table()
    if not args.skip_chromosome:
        gene_utils.create_chromosome_table()
    if not args.skip_gene_type:
        gene_utils.create_gene_type_table()
    if not args.skip_gene:
        gene_utils.create_gene_table()
    if not args.skip_dbxref:
        gene_utils.create_dbxref_table()
