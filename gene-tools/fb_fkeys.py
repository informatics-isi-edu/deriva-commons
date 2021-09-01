from deriva.core.ermrest_model import ForeignKey
from gene_utils import GeneUtils

fkey_specs = {
    'isa' : [
        ['biosample', 'biosample_species_fkey'],
        ['chromosome', 'chromosome_species_fkey'],
        ['clinical_assay', 'clinical_assay_species_fkey'],
        ['dataset_organism', 'dataset_organism_organism_fkey'],
        ['sample', 'sample_species_fkey']
    ],
    'vocab': [
        ['gene_summary', 'gene_summary_species_fkey']
    ]
}

def main(gu):
    model = gu.model
    fkey_specs['isa'].append(
        [gu.source_file_table, gu.source_file_table + '_Species_fkey']
    )

    for sname in fkey_specs.keys():
        for spec in fkey_specs[sname]:
            process_fkey(model, sname, spec[0], spec[1])

def process_fkey(model, sname, tname, fkname):
    table = model.table(sname, tname)
    for fkey in table.foreign_keys:
        if fkey.name[0].name == sname and fkey.name[1] == fkname:
            fkey.alter(on_update='CASCADE')
            return

if __name__ == '__main__':
    cli = GeneUtils.create_parser("gene table creation tool")
    args = cli.parse_cli()
    gu = GeneUtils(args)
    main(gu)
