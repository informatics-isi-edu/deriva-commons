# A real quick-and-dirty hack right now for importing the monarch tsv files
import os.path
import traceback
import csv
from requests import HTTPError
from deriva.core import DerivaServer, get_credential
from deriva.core.ermrest_model import Table, Column, Key, builtin_types

# Server properties
scheme = 'https'
hostname = 'dev.isrd.isi.edu'

# Monarch tsv files
# ..."all" that look like good candidates to import
all_monarch_files = [
    'disease_associations/disease_phenotype.all.tsv',
    'gene_associations/gene_phenotype.all.tsv',
    'genotype_associations/genotype_disease.all.tsv',
    'genotype_associations/genotype_phenotype.all.tsv',
    'model_associations/model_disease.all.tsv',
    'variant_associations/variant_phenotype.all.tsv'
]
# ...one small file for testing purposes
one_monarch_files = [
    'genotype_associations/genotype_disease.all.tsv'
]
# ...set this to which collection of files to import
monarch_files = all_monarch_files

# Create catalog and get various interfaces
credential = get_credential(hostname)
server = DerivaServer(scheme, hostname, credential)
catalog = server.create_ermrest_catalog()
model = catalog.getCatalogModel()
public = model.schemas['public']
config = catalog.getCatalogConfig()

# Update catalog config
acls = {
    "select": ['*'],
    "enumerate": ['*']
}
config.acls.update(acls)
catalog.applyCatalogConfig(config)

for fname in monarch_files:
    print('Importing {fname}...'.format(fname=fname))
    tname = os.path.splitext(os.path.basename(fname))[0]

    pk = 'pk'
    col_defs = [Column.define(pk, builtin_types.int8)]
    key_defs = [Key.define([pk])]

    with open(fname) as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter='\t')
        for cname in reader.fieldnames:
            col_defs.append(Column.define(cname, builtin_types.text))
        tab_def = Table.define(tname, column_defs=col_defs, key_defs=key_defs, acls=acls, provide_system=False)

        print('Creating table {tname}...'.format(tname=tname))
        try:
            public.create_table(catalog, tab_def)
        except HTTPError as e:
            print(e)
            print(e.response.text)
            exit(1)

        # Now to import data...
        pb = catalog.getPathBuilder()
        table = pb.public.tables[tname]

        print('Importing data into {tname}'.format(tname=tname))
        print(table.uri)

        done = False
        while not done:
            i, max, done = 0, 1000, True
            entities = []
            # read from file the next batch of entities
            for row in reader:
                entity = dict(row)
                entity[pk] = reader.line_num
                entities.append(entity)
                i += 1
                if i >= max:
                    done = False
                    break
            # insert the entities into the ermrest table
            print('Importing {num} entities into {tname}'.format(num=i, tname=tname))
            try:
                table.insert(entities, add_system_defaults=False)
            except HTTPError as e:
                print(e)
                print(e.response.text)
                exit(1)

        print('Done importing into {tname}'.format(tname=tname))

