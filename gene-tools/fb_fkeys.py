from deriva.core import DerivaServer, get_credential, BaseCLI
from deriva.core.ermrest_model import ForeignKey

fkey_specs = {
    'isa' : [
        ['Gene_Source_File', 'Gene_Source_File_Species_fkey'],
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

def main(host, catalog_id=1):
    credential = get_credential(host)
    server = DerivaServer('https', host, credential)
    catalog = server.connect_ermrest(catalog_id)
    model = catalog.getCatalogModel()

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
    cli = BaseCLI("make facebase species foreign keys 'on update cascade'", None, 1, hostname_required=True)
    args = cli.parse_cli()
    main(args.host)
