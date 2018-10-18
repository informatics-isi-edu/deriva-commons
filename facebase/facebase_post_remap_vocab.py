# A utility script to clean up the tables and set annotations after running remap_vocab.py to remapping from 'data_commons' to 'ermrest_model' vocabulary tables.
#
# Example usage:
#
#
# $ python facebase_post_remap_vocab.py   dev.facebase.org 11 'vocab' '.*$'   -v --annotations --cleanup
# The command above would run this script on the facebase catalog 11 over the vocab schema and all tables  table


import argparse
import re

from deriva.core import DerivaServer, get_credential
from deriva.core.ermrest_model import builtin_types, Table, Column, ForeignKey


import sys
import traceback
import json
from deriva.core import ErmrestCatalog, AttrDict
from deriva.core.ermrest_model import builtin_types, Table, Column, Key, ForeignKey


description = """
A utility script to clean up the tables and set annotations after running remap_vocab.py to remapping from 'data_commons' to 'ermrest_model' vocabulary tables.
"""


class ReplacementPatternAction(argparse.Action):
    """Custom action for subheader."""
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(ReplacementPatternAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        replacement = values.split('=')
        if len(replacement) != 2:
            parser.error("Invalid replacement pattern '{values}' for '{arg}'. The pattern must be 'old=new'.".format(
                values=values,
                arg=self.dest
            ))
        setattr(namespace, self.dest, {'old': replacement[0], 'new': replacement[1]})


# Argument parser
parser = argparse.ArgumentParser(description=description)
parser.add_argument('hostname')
parser.add_argument('catalog', type=int, help='Catalog number')
parser.add_argument('schema_regex', help='A regular expression to filter the schemas')
parser.add_argument('exclude_table_regex', help='A regular expression to exclude the tables matching that pattern')
parser.add_argument('-n', '--dryrun', action='store_true', help='Dry run. No changes to the catalog.')
parser.add_argument('-v', '--verbose', action="count", default=0, help='Increase verbosity of output.')
parser.add_argument('--cleanup', action='store_true', help='Cleanup. Drop old tables w/ names ending in _terms, _relationship_types and _paths.')
parser.add_argument('--annotations', action='store_true', help='Annotations. Add basic level annotations to tables in selected schema')

args = parser.parse_args()

# Compile regex patterns
schema_pattern = re.compile(args.schema_regex)
table_pattern = re.compile(args.exclude_table_regex)


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


def clean_term(term):
    """Cleans up the term by monkey patching and returning it."""

    # Use dbxref in curie if it does not match the blacklist
    if not curie_blacklist_pattern.match(term['dbxref']):
        term['id'] = term['dbxref'][:term['dbxref'].rindex(':')]  # strip the trailing ':###'
    else:
        term['id'] = None

    # Similarly, clean up the alternative_dbxrefs
    if args.altids:
        term['alternate_ids'] = []
        if term['alternate_dbxrefs']:
            for old_alt_dbxref in term['alternate_dbxrefs']:
                if old_alt_dbxref.startswith('URL:'):
                    old_alt_dbxref = old_alt_dbxref[len('URL:'):old_alt_dbxref.rindex(':')]  # strip 'URL:' prefix and the trailing ':###'
                else:
                    old_alt_dbxref = old_alt_dbxref[:old_alt_dbxref.rindex(':')]  # strip the trailing ':###'
                term['alternate_ids'].append(old_alt_dbxref)
        del term['alternate_dbxrefs']

    # Description must be non-null but many existing terms have none
    if not term['description']:
        term['description'] = 'No description'

    return term


def cleanup_old_vocab_tables():
    """Drop all _terms, _paths, _relationship_types tables in the vocabulary schema"""

    verbose('Cleaning old tables ending on _terms, _relationship_types, _paths ....')

    p1 = re.compile('.+_terms$')
    p2 = re.compile('.+_relationship_types$')
    p3 = re.compile('.+_paths$')

    for schema_name in list(model.schemas):
        if schema_pattern.match(schema_name):
            schema = model.schemas[schema_name]
            verbose('Schema "{sname}" matched "{pattern}"'.format(sname=schema_name, pattern=args.schema_regex))
            for table_name in list(model.schemas[schema_name].tables):
                #verbose('Processing table "{tname}" for deletion.....'.format(tname=table_name))
                if p3.match(table_name):
                    #verbose('    --->Table "{tname}" matches delete pattern....'.format(tname=table_name))
                    if not args.dryrun:
                        verbose('Table "{tname}" matched deteting pattern....Deleting it....'.format(tname=table_name))
                        schema.tables[table_name].delete(catalog, schema)
                    else:
                        verbose("Found {tname} but skipping delete in dry-run mode...".format(tname=table_name))


            for table_name in list(model.schemas[schema_name].tables):
                #verbose('Processing table "{tname}" for deletion.....'.format(tname=table_name))
                if p2.match(table_name):
                    #verbose('    --->Table "{tname}" matches delete pattern....'.format(tname=table_name))
                    if not args.dryrun:
                        verbose('Table "{tname}" matched deteting pattern....Deleting it....'.format(tname=table_name))
                        schema.tables[table_name].delete(catalog, schema)
                    else:
                        verbose("Found {tname} but skipping delete in dry-run mode...".format(tname=table_name))

            for table_name in list(model.schemas[schema_name].tables):
                #verbose('Processing table "{tname}" for deletion.....'.format(tname=table_name))
                if p1.match(table_name):
                    #verbose('    --->Table "{tname}" matches delete pattern....'.format(tname=table_name))
                    if not args.dryrun:
                        verbose('Table "{tname}" matched deteting pattern....Deleting it....'.format(tname=table_name))
                        schema.tables[table_name].delete(catalog, schema)
                    else:
                        verbose("Found {tname} but skipping delete in dry-run mode...".format(tname=table_name))


def update_annotations_vocab_tables(goal):

    for schema_name in list(model.schemas):
        if schema_pattern.match(schema_name):
            schema = model.schemas[schema_name]

            for table_name in list(model.schemas[schema_name].tables):
                if not table_pattern.match(table_name):
                    verbose('Setting up annotations for table "{tname}" ...'.format(tname=table_name))
                    if not args.dryrun:
                        update_annotations_vocab_table(schema_name,table_name,goal)
                        verbose('    Done setting up annotations for table "{tname}" ...'.format(tname=table_name))
                    else:
                        verbose("    Found {tname} but skipping setting up annotations in dry-run mode...".format(tname=table_name))


def update_annotations_vocab_table(schema_name,table_name,goal):

    verbose('Setting up annotations for table "{tname}" ...'.format(tname=table_name))

    row_order = [{"column": "name"}]

    if table_name == 'stage':
        row_order = [{"column": "sort_key"}, {"column": "name"}]


    if table_name != 'file_extension' and table_name != 'gene_summary':
        goal.table(
            '%s' % schema_name, '%s' % table_name
        ).table_display.update({
            "row_name": {"row_markdown_pattern": "{{name}}"},
            "*": {"row_order": row_order}
        })

        goal.column(
            '%s' % schema_name, '%s' % table_name, 'uri'
        ).column_display.update({
            "detailed": {
                "markdown_pattern": "[{{uri}}]({{uri}})"
            }
        })

        goal.column(
            '%s' % schema_name, '%s' % table_name, 'id'
        ).column_display.update({
            "detailed": {
                "markdown_pattern": "[{{id}}]({{uri}})"
            }
        })

        goal.table(
            '%s' % schema_name, '%s' % table_name
        ).visible_columns.update({
            "filter": {"and": [{"source": "name"},
                               {"source": "id"},
                               {"source": "description"},
                               {"source": "synonyms"},
                               {"source": "alternate_ids"}
                               ]
                       },
            "entry": [
                "id","name","uri","description","synonyms","alternate_ids"
            ],
            "detailed": [["vocab","%s_RIDkey1" % table_name],
                  "name",
                  "uri",
                  "description",
                  "synonyms",
                  "alternate_ids"
            ],
            "compact": [["vocab","%s_RIDkey1" % table_name],
                         "name",
                         "description",
                         "synonyms",
                         "alternate_ids"
            ]
        })

    if table_name == 'gene_summary':
        goal.table(
            '%s' % schema_name, '%s' % table_name
        ).visible_columns.update({
            "filter": {"and": [
                {"source":[{"outbound": ["vocab", "gene_summary_gene_fkey"]},"id"],"entity": True},
                {"source":[{"outbound": ["vocab", "gene_summary_species_fkey"]}, "id"],"entity": True}
                              ]
                       },
            "entry": [
                ["vocab", "gene_summary_gene_fkey"],["vocab", "gene_summary_species_fkey"],["vocab","gene_summary_contributed_by_fkey"],"summary"
            ],
            "detailed": [["vocab", "gene_summary_gene_fkey"],
                         ["vocab", "gene_summary_species_fkey"],
                         ["vocab","gene_summary_contributed_by_fkey"],
                         "summary"
                         ],
            "compact": [["vocab", "gene_summary_gene_fkey"],
                         ["vocab", "gene_summary_species_fkey"],
                         ["vocab","gene_summary_contributed_by_fkey"],
                         "summary"
                        ]
        })


    if table_name == 'file_extension':
        goal.table(
            '%s' % schema_name, '%s' % table_name
        ).visible_columns.update({
            "filter": {"and": [
                {"source": "extension"},
                {"source":[{"outbound": ["vocab", "file_extension_file_format_fkey"]},"id"],"entity": True}
                              ]
                       },
            "entry": [
                "extension",["vocab", "file_extension_file_format_fkey"]
            ],
            "detailed": [
                ["vocab","file_extension_rid_key"],
                "extension",
                ["vocab", "file_extension_file_format_fkey"]
                        ],
            "compact": [
                ["vocab", "file_extension_rid_key"],
                "extension",
                ["vocab", "file_extension_file_format_fkey"]
                        ]
        })

    if table_name == 'phenotype':
        goal.table(
            '%s' % schema_name, '%s' % table_name
        ).visible_foreign_keys.update({
            "*": [{"source": [{"inbound": ["isa", "dataset_%s_%s_fkey" % (table_name, table_name)]},
                              {"outbound": ["isa", "dataset_%s_dataset_fkey" % table_name]}, "id"]}]
        })
    elif table_name == 'species':
        goal.table(
            '%s' % schema_name, '%s' % table_name
        ).visible_foreign_keys.update({
            "*": [{"source": [{"inbound": ["isa", "dataset_organism_organism_fkey"]},
                              {"outbound": ["isa", "dataset_organism_dataset_id_fkey"]}, "id"]}]
        })

    else:
        goal.table(
            '%s' % schema_name, '%s' % table_name
        ).visible_foreign_keys.update({
            "*": [{"source": [{"inbound": ["isa", "dataset_%s_%s_fkey" % (table_name, table_name)]},
                              {"outbound": ["isa", "dataset_%s_dataset_id_fkey" % table_name]}, "id"]}]
        })


def update_annotations():
    try:
        goal = catalog.get_catalog_model()
    except AttributeError:
        goal = catalog.getCatalogModel()

    update_annotations_vocab_tables(goal)

    try:
        catalog.applyCatalogConfig(goal)
    except HTTPError as err:
        if err.errno == CONFLICT:
            et, ev, tb = sys.exc_info()
            verbose('Conflict Exception "{evv}"'.format(evv=str(ev)))
    except:
        et, ev, tb = sys.exc_info()
        verbose('Exception "{yoon}"'.format(yoon=str(ev)))

if args.cleanup:
    cleanup_old_vocab_tables()

if args.annotations:
    update_annotations()




