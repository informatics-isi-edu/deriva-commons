"""Script to load MGI mouse strain data into a DERIVA catalog with a 'Strain' vocabulary table."""

import argparse
import csv
import json
from pprint import pprint
import sys
from deriva.core import DerivaServer, get_credential, urlquote


def main():
    parser = argparse.ArgumentParser(description="Loads MGI strain data report into a 'Strain' table in a DERIVA catalog")
    parser.add_argument("-v", "--verbose", default=False, action='store_true', help="Verbose output")
    parser.add_argument("-n", "--dry-run", default=False, action='store_true', help="Dry run will not change schema.")
    parser.add_argument("hostname", help="Server hostname")
    parser.add_argument("catalog_id", help="Catalog ID")
    parser.add_argument("config_file", help="Configuration file")
    parser.add_argument("data_file", help="MGI strain report")
    args = parser.parse_args()

    # connect to catalog
    server = DerivaServer('https', args.hostname, credentials=get_credential(args.hostname))
    catalog = server.connect_ermrest(args.catalog_id)
    pbuilder = catalog.getPathBuilder()

    # load configuration file
    with open(args.config_file) as fp:
        config = json.load(fp)

    if args.verbose:
        print(f'Configuration read from file {args.config_file}:')
        pprint(config)

    # lookup table
    schema_name, table_name = config.get('schema'), config.get('table')
    schema, table = pbuilder.schemas.get(schema_name), None
    if schema:
        table = schema.tables[table_name]
    if not table:
        print(f'Table "{schema_name}"."{table_name}" not found. Quitting.', file=sys.stderr)
        return 1

    # helper functions
    cname_fn = lambda key: config.get('column_map', {}).get(key, key)
    mgi_uri_fn = lambda mgi_id: config.get('mgi_uri_template', "http://www.informatics.jax.org/strain/{MGI_ID}").replace('{MGI_ID}', mgi_id)

    # read MGI strain report and generate data records
    with open(args.data_file) as fp:
        reader = csv.DictReader(fp, fieldnames=['MGI Strain ID', 'Strain Name', 'Strain Type'], delimiter='\t')
        data = []
        try:
            for row in reader:
                if args.verbose:
                    print(row)

                uri = mgi_uri_fn(urlquote(row['MGI Strain ID']))
                display_name = row['Strain Name'].replace('<', '^').replace('>', '^')

                record = {
                    cname_fn('ID'): row['MGI Strain ID'],
                    cname_fn('URI'): uri,
                    cname_fn('Name'): row['Strain Name'],
                    cname_fn('Description'): f'For more information on strain "{display_name}" go to [{row["MGI Strain ID"]}]({uri}).',
                    cname_fn('Type'): row['Strain Type'],
                    cname_fn('Display_Name'): display_name
                }
                data.append(record)

        except csv.Error as e:
            print('File {}, line {}: {}'.format(args.data_file, reader.line_num, e), file=sys.stderr)
            return 1

    if args.verbose:
        print(f'Attempting to insert {len(data)} rows of data:')
        pprint(data)

    if not args.dry_run:
        results = table.insert(data)
        print(f'Inserted {len(results)} rows into the "{schema_name}"."{table_name}".')

    return 0


if __name__ == '__main__':
    sys.exit(main())
