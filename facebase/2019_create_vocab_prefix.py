# A utility for remapping from 'data_commons' to 'ermrest_model' vocabulary tables.
#
# Example usage:
#
# $ python 2019_create_vocab_prefix.py dev.facebase.org 1 
# The command above would run this script on the dev.facebase.org catalog 1

import argparse
import re

from deriva.core import DerivaServer, get_credential
from deriva.core.ermrest_model import Table, Column, ForeignKey, builtin_types as typ


import deriva.core.ermrest_model as em

description = """
Creates the new vocab.prefix table  
"""


# Argument parser
parser = argparse.ArgumentParser(description=description)
parser.add_argument('hostname')
parser.add_argument('catalog', type=int, help='Catalog number')

args = parser.parse_args()

# Create/connect catalog and get various interfaces
credential = get_credential(args.hostname)
server = DerivaServer('https', args.hostname, credential)
catalog = server.connect_ermrest(args.catalog)
model = catalog.getCatalogModel()
config = catalog.getCatalogConfig()


def verbose(message):
    """Print message for verbose output"""
    if args.verbose:
        print(message)


def vverbose(message):
    """Print message for very verbose output"""
    if args.verbose > 1:
        print(message)





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
                print('Conflict Exception "%s"' % str(ev))
                counter = counter + 1
                if counter >= 5:
                    print('%s' % str(traceback.format_exception(et, ev, tb)))
                    ready = True
                else:
                    print('Retrying...')
        except:
            et, ev, tb = sys.exc_info()
            print(str(et))
            print('Exception "%s"' % str(ev))
            print('%s' % str(traceback.format_exception(et, ev, tb)))
            ready = True



def create_new_table(schema_name):
    column_defs = [
        em.Column.define("prefix", typ.text),
        em.Column.define("uri", typ.text),
    ]
    table_def = em.Table.define(
        "prefix",
        column_defs,
        comment="Table to map ontology prefix to an uri",
        acls={},
        acl_bindings={},
        annotations={},
        provide_system=True,
    )
    schema = model.schemas[schema_name]
    new_table = schema.create_table(catalog, table_def)


def set_table_annotations(goal):
    """
    Set the annotations for the new table
    """

    goal.table(
        'vocab', 'prefix'
    ).visible_columns.update({
        "filter": {"and": [{"source": "prefix"},
                           {"source": "uri"}
                           ]
                   },
        "*": ["prefix",
              "uri"
        ]
    })

    print('Setting annotations for the prefix vocabulary table...')


#create_new_table('vocab')

try:
    goal = catalog.get_catalog_model()
except AttributeError:
    goal = catalog.getCatalogModel()


set_table_annotations(goal)
apply(catalog, goal)
