from deriva.core import BaseCLI
import sys
from gene_utils import GeneUtils

if __name__ == '__main__':
    cli = GeneUtils.create_parser("gene table creation tool")
    cli.parser.add_argument('--skip-species', help='skip species table creation', default=False)
    cli.parser.add_argument('--skip-chromosome', help='skip chromosome table creation', default=False)
    cli.parser.add_argument('--skip-gene-type', help='skip gene type table creation', default=False)
    cli.parser.add_argument('--skip-gene', help='skip gene table creation', default=False)
    cli.parser.add_argument('--gene-table-style', help='gene table style (vocabulary table or not)',
                            choices=['vocab', 'classic'], default='vocab')
    cli.parser.add_argument('--curie-prefix', help='prefix for CURIEs to assign to project-generated terms', default=None)
    cli.parser.add_argument('--extra-boolean-cols', default=[], nargs='+',
                        help='extra boolean columns to create in the gene table\
  (e.g., to indicate existence of data for a particular gene)')
    
    args = cli.parse_cli()
    gene_utils = new GeneUtils(args)

    if ! args.skip_species:
        gene_utils.create_species_table()
    if ! args.skip_chromosome:
        gene_utils.create_chromosome_table()
    if ! args.skip_gene_type:
        gene_utils.create_gene_type_table()
    if ! args.skip_gene:
        gene_utils.create_gene_table(args.gene_table_style == 'vocab')
