"""Script to update a DERIVA catalog with a 'Strain' vocabulary table."""

import argparse
import json
from pprint import pprint
import sys
from deriva.core import DerivaServer, get_credential
from deriva.core.ermrest_model import Table, Column, builtin_types


def _strain_type_cdef(cname='Type'):
    """Returns the strain 'Type' column definition."""
    return Column.define(cname, builtin_types['text'], comment='Type of strain')


def _strain_display_name_cdef(cname='Display_Name'):
    """Returns the 'Display_Name' column definition."""
    return Column.define(cname, builtin_types['markdown'], comment='Formatted display name for the term')


def main():
    parser = argparse.ArgumentParser(description="Creates or updates a 'strain' table in a DERIVA catalog")
    parser.add_argument("-v", "--verbose", default=False, action='store_true', help="Verbose output")
    parser.add_argument("-n", "--dry-run", default=False, action='store_true', help="Dry run will not change schema.")
    parser.add_argument("hostname", help="Server hostname")
    parser.add_argument("catalog_id", help="Catalog ID")
    parser.add_argument("config_file", help="Configuration file")
    args = parser.parse_args()

    # connect to catalog
    server = DerivaServer('https', args.hostname, credentials=get_credential(args.hostname))
    catalog = server.connect_ermrest(args.catalog_id)
    model = catalog.getCatalogModel()

    # load configuration file
    with open(args.config_file) as fp:
        config = json.load(fp)

    if args.verbose:
        print(f'Configuration read from file {args.config_file}:')
        pprint(config)

    # lookup schema
    schema_name = config.get('schema')
    schema = model.schemas.get(schema_name)
    if not schema:
        print(f'Schema "{schema_name}" not found. Quitting.', file=sys.stderr)
        return 1

    # lookup table, create or modify
    table_name = config.get('table')
    table = schema.tables.get(table_name)
    if not table:
        print(f'Table "{schema_name}"."{table_name}" not found. Creating...')

        if 'column_map' in config:
            print('The "column_map" property is not supported when creating a new Strain table. Please remove '
                  '"column_map" to use the default naming convention. Quitting.', file=sys.stderr)
            return 1

        if 'curie_template' not in config:
            print('The "curie_template" property is not in the configuration file. Quitting.', file=sys.stderr)
            return 1

        tdef = Table.define_vocabulary(table_name,
                                       config['curie_template'],
                                       uri_template=config.get('uri_template', '/id/{RID}'),
                                       column_defs=[_strain_type_cdef(), _strain_display_name_cdef()])
        if args.verbose:
            print('Table Definition:')
            pprint(tdef)

        if not args.dry_run:
            schema.create_table(tdef)
            print(f'Table "{schema_name}"."{table_name}" created.')

    else:
        print(f'Table "{schema_name}"."{table_name}" found. Inspecting...')

        # validate that all required standard vocabulary columns exist in table (does not check type, etc.)
        existing_cnames = {c.name for c in table.column_definitions}
        for cname in {'ID', 'URI', 'Name', 'Description'}:
            cname = config.get('column_map', {}).get(cname, cname)
            if cname not in existing_cnames:
                print(f'Column "{cname}" not found in table. Quitting.', file=sys.stderr)
                return 1
            elif args.verbose:
                print(f'Column "{cname}" found in table.')

        # alter table add non-standard columns, if not exists
        for cname, cdef_fn in [
            ('Type', _strain_type_cdef),
            ('Display_Name', _strain_display_name_cdef)
        ]:
            cname = config.get('column_map', {}).get(cname, cname)
            if cname not in existing_cnames:
                print(f'Column "{cname}" not found in table. Creating...')
                cdef = cdef_fn(cname=cname)

                if args.verbose:
                    print('Column definition:')
                    pprint(cdef)

                if not args.dry_run:
                    table.create_column(cdef)
                    print(f'Column "{cname}" created.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
