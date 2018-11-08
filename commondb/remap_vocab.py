# A utility for remapping from 'data_commons' to 'ermrest_model' vocabulary tables.
#
# Example usage:
#
# $ python remap_vocab.py --altids --curie_blacklist '^facebase' dev.facebase.org 5 'vocab' 'phenotype_terms$' '_terms$' '' 'FACEBASE:{RID}' -n -v
#
# The command above would run this script on the facebase catalog 5 over the vocab schema and phenotype_terms table
# replacing the table's name with 'phenotype', as a dry run with verbose output

import argparse
import re
from deriva.core import DerivaServer, get_credential
from deriva.core.ermrest_model import Table, Column, ForeignKey, builtin_types

description = """
A utility for transforming vocabulary tables from the deprecated 'data_commons' format to the revised format, which
has been canonicalized in 'ermrest_model' API.
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
parser.add_argument('table_regex', help='A regular expression to filter the tables in the filtered schemas')
parser.add_argument('name_sub_pattern',
                    help='A regular expression used in substitution pattern matching on the original table name'),
parser.add_argument('name_sub_repl',
                    help='A replacement string used in substitution pattern matching on the original table name'),
parser.add_argument('curie_template', help='The new vocabulary "curie_template", e.g., "MYPROJECT:{RID}"')
parser.add_argument('--altids', action='store_true', help='Extend vocab table definition with "alternate_ids" column')
parser.add_argument('--curie_blacklist', help="""
The old vocabulary term's "dbxref" will be used as the new vocabulary term's "id" unless it matches this blacklist regex
pattern.
""")
parser.add_argument('--fkey_blacklist', default='.*_paths_.*|.*_relationship_types_.*', help="""
A regex blacklist of foreign key constraint names. Default: '.*_paths_.*|.*_relationship_types_.*' will skip all of the
intra-vocabulary schema foreign keys.
""")
parser.add_argument('--droptable', action='store_true', help='If table exists, attempt to drop, otherwise skip it')
parser.add_argument('-n', '--dryrun', action='store_true', help='Dry run. No changes to the catalog.')
parser.add_argument('--max_update', type=int, default=100, help='Maximum update payload sent to server')
parser.add_argument('-v', '--verbose', action="count", default=0, help='Increase verbosity of output.')

args = parser.parse_args()

# Compile regex patterns
schema_pattern = re.compile(args.schema_regex)
table_pattern = re.compile(args.table_regex)
curie_blacklist_pattern = re.compile(args.curie_blacklist) if args.curie_blacklist else re.compile('')
fkey_blacklist_pattern = re.compile(args.fkey_blacklist)

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
                elif old_alt_dbxref.startswith('NULL:C'):
                    old_alt_dbxref = 'NCIT:C'+old_alt_dbxref[len('NULL:C'):old_alt_dbxref.rindex(':')]  # strip 'URL:' prefix and the trailing ':###'
                elif old_alt_dbxref.startswith('NULLXXX:'):
                    old_alt_dbxref = old_alt_dbxref[len('NULL:'):old_alt_dbxref.rindex(':')]  # strip 'URL:' prefix and the trailing ':###'
                else:
                    old_alt_dbxref = old_alt_dbxref[:old_alt_dbxref.rindex(':')]  # strip the trailing ':###'
                term['alternate_ids'].append(old_alt_dbxref)
        del term['alternate_dbxrefs']

        #verbose("ALTERNATE IDs={altid}".format(altid=term['alternate_ids']))


    # Description must be non-null but many existing terms have none
    if not term['description']:
        term['description'] = 'No description'

    return term


def replace_vocab_table(schema_name, old_table_name, new_table_name, replace_if_exists=False):
    """Replaces old vocab table with new and remaps all foreign keys from old to new."""
    schema = model.schemas[schema_name]

    # Drop new_vocab table if exists (optional)
    if not args.dryrun and new_table_name in schema.tables:
        if replace_if_exists:
            verbose("Found {tname}. Dropping...".format(tname=new_table_name))
            schema.tables[new_table_name].delete(catalog, schema)
        else:
            verbose("Found {tname}. Skipping...".format(tname=new_table_name))
            return

    # Define and create new vocab table
    extra_cols = [
        Column.define(
            'dbxref',
            builtin_types['text'],
            comment='Legacy database external reference (dbxref).'
        )
    ]
    if args.altids:
        extra_cols = [
            Column.define(
                'alternate_ids',
                builtin_types['text[]'],
                comment='Alternate identifiers for this term.'
            )
        ] + extra_cols
    vocab_table_def = Table.define_vocabulary(new_table_name, args.curie_template, uri_template='https://www.facebase.org/id/{RID}',column_defs=extra_cols)
    if not args.dryrun:
        new_table = schema.create_table(catalog, vocab_table_def)

    # Populate new vocab table
    datapaths = catalog.getPathBuilder()

    old_table_path = datapaths.schemas[schema_name].tables[old_table_name]
    kwargs = {
        'name': old_table_path.column_definitions['name'],
        'description': old_table_path.column_definitions['definition'],
        'synonyms': old_table_path.column_definitions['synonyms'],
        'dbxref': old_table_path.column_definitions['dbxref']
    }
    if args.altids:
        kwargs['alternate_dbxrefs'] = old_table_path.column_definitions['alternate_dbxrefs']

    cleaned_terms = [clean_term(term) for term in old_table_path.entities(**kwargs)]

    vverbose('Cleaned terms ready for insert into {tname}:'.format(tname=new_table_name))
    vverbose(list(cleaned_terms))

    # Create separate batches for insertion w/ defaults
    terms_w_ids = [term for term in cleaned_terms if term['id'] and len(term['id'])]
    terms_w_no_ids = [term for term in cleaned_terms if not term['id'] or not len(term['id'])]

    if not args.dryrun:
        new_table_path = datapaths.schemas[schema_name].tables[new_table_name]
        new_terms = list(new_table_path.insert(terms_w_ids, defaults=['uri']))
        new_terms += list(new_table_path.insert(terms_w_no_ids, defaults=['id', 'uri']))
        vverbose('New terms returned after insert into {tname}:'.format(tname=new_table_name))
        vverbose(list(new_terms))
    else:
        # This allows for best effort dryrun testing, though the local term CURIEs will be faked
        new_terms = cleaned_terms
        for term in new_terms:
            if not term['id']:
                term['id'] = term['dbxref'][:term['dbxref'].rindex(':')].upper()

    # Create mapping of old dbxref to new id
    dbxref_to_id = {term['dbxref']: term['id'] for term in new_terms}

    # Find all references to old vocab table dbxref
    old_table = schema.tables[old_table_name]
    for fkey in old_table.referenced_by:

        if fkey_blacklist_pattern.match(fkey.names[0][1]):
            verbose('Skipping foreign key "{sname}:{cname}"'.format(sname=fkey.names[0][0], cname=fkey.names[0][1]))
            continue  # skip fkeys from vocab to vocab

        for i in range(len(fkey.referenced_columns)):
            # Get referenced column
            refcol = fkey.referenced_columns[i]

            # See if it references the dbxref of the old vocab table, if not skip
            if (refcol['schema_name'] != schema_name or refcol['table_name'] != old_table_name
                    or refcol['column_name'] != 'dbxref'):
                continue

            # Get the corresponding referring table and its fkey column
            fkeycol = fkey.foreign_key_columns[i]
            reftable = model.schemas[fkeycol['schema_name']].tables[fkeycol['table_name']]
            verbose('Found reference to "dbxref" from "{sname}:{tname}:{cname}"'.format(
                sname=fkeycol['schema_name'], tname=fkeycol['table_name'], cname=fkeycol['column_name']))

            # Delete the fkey
            if not args.dryrun:
                verbose('Deleting foreign key "{sname}:{cname}"'.format(sname=fkey.names[0][0],
                                                                        cname=fkey.names[0][1]))
                fkey.delete(catalog, reftable)

            # Fix fkey column value
            verbose('Getting existing fkey column values')
            reftable_path = datapaths.schemas[fkeycol['schema_name']].tables[fkeycol['table_name']]
            entities = reftable_path.entities(reftable_path.RID, reftable_path.column_definitions[fkeycol['column_name']])

            # Map the old dbxref value to the new curie id value for the reference
            verbose('Remapping {count} fkey column values'.format(count=len(entities)))
            for entity in entities:
                if entity[fkeycol['column_name']]:
                    entity[fkeycol['column_name']] = dbxref_to_id[entity[fkeycol['column_name']]]
            vverbose(list(entities))

            # Update referring table
            if not args.dryrun:
                verbose('Updating fkey column values, {max_up} at a time'.format(max_up=args.max_update))
                slice_ct = 0
                slice_sz = args.max_update
                updated = []
                while (slice_ct * slice_sz) < len(entities):
                    data = entities[(slice_ct * slice_sz):((1 + slice_ct) * slice_sz)]
                    reftable_path.update(data, targets=[fkeycol['column_name']])
                    updated.extend(data)
                    slice_ct += 1
                if len(updated) != len(entities):
                    print('WARNING: only updated {up_count} of {ent_count} entities!'.format(
                        up_count=len(updated), ent_count=len(entities)
                    ))

            # Define new fkey
            verbose('Defining and creating new foreign key reference to new vocab table')
            fkey.referenced_columns[i]['column_name'] = 'id'
            new_fkey = ForeignKey.define(
                [fkey.foreign_key_columns[j]['column_name'] for j in range(len(fkey.foreign_key_columns))],
                schema_name,
                new_table_name,
                [fkey.referenced_columns[k]['column_name'] for k in range(len(fkey.referenced_columns))],
                on_update=fkey.on_update or 'NO ACTION',
                on_delete=fkey.on_delete or 'NO ACTION',
                constraint_names=fkey.names or [],
                comment=fkey.comment or None,
                acls=fkey.acls or {},
                acl_bindings=fkey.acl_bindings or {},
                annotations=fkey.annotations or {}
            )
            vverbose(new_fkey)
            if not args.dryrun:
                reftable.create_fkey(catalog, new_fkey)

    if not args.dryrun:
        verbose('Dropping "dbxref" column from new vocab table')
        dbxref = new_table.column_definitions['dbxref']
        dbxref.delete(catalog, new_table)


def find_and_replace_vocab_tables():
    """Finds vocab tables to be removed and replaces them."""
    for schema_name in list(model.schemas):
        if schema_pattern.match(schema_name):
            verbose('Schema "{sname}" matched "{pattern}"'.format(sname=schema_name, pattern=args.schema_regex))
            for table_name in list(model.schemas[schema_name].tables):
                if table_pattern.match(table_name):
                    new_table_name = re.sub(args.name_sub_pattern, args.name_sub_repl, table_name)
                    verbose('Table "{tname}" matched "{pattern}", replacing with "{new_tname}"'.format(
                        tname=table_name, pattern=args.table_regex, new_tname=new_table_name))
                    replace_vocab_table(schema_name, table_name, new_table_name, replace_if_exists=args.droptable)


find_and_replace_vocab_tables()
