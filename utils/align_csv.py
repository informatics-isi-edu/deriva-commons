"""Script to align a spreadsheet to table in a DERIVA catalog."""

import argparse
import csv
import json
from operator import itemgetter
from pprint import pprint
import string
import sys
from deriva.core import DerivaServer, get_credential, urlquote


def main():
    parser = argparse.ArgumentParser(description="Aligns a spreadsheet to a table in a DERIVA catalog.")
    parser.add_argument("-m", "--create-mapping-template", default=False, action='store_true', help="Creates a 'mapping' template in <config_file>")
    parser.add_argument("-n", "--dry-run", default=False, action='store_true', help="Dry run will not change schema")
    parser.add_argument("-s", "--subset", action="append", help="Only use a subset of the <config_file> mappings")
    parser.add_argument("-u", "--unique", default=False, action='store_true', help="Only output unique rows")
    parser.add_argument("-v", "--verbose", default=0, action='count', help="Verbose output")
    parser.add_argument("hostname", help="Server hostname")
    parser.add_argument("catalog_id", help="Catalog ID")
    parser.add_argument("config_file", help="Configuration file")
    parser.add_argument("data_file", nargs='?', help="Input spreadsheet file")
    args = parser.parse_args()

    # connect to catalog
    server = DerivaServer('https', args.hostname, credentials=get_credential(args.hostname))
    catalog = server.connect_ermrest(args.catalog_id)

    # load configuration file
    with open(args.config_file) as fp:
        config = json.load(fp)

    if args.verbose >= 1:
        print(f'Configuration read from file {args.config_file}', file=sys.stderr)
        pprint(config, stream=sys.stderr)

    # create template?
    if args.create_mapping_template:
        if 'mappings' in config:
            print('Configuration already includes a "mappings" property.', file=sys.stderr)
            return 1

        # create mappings template from table description
        model = catalog.getCatalogModel()
        table = model.schemas[config['schema']].tables[config['table']]
        config['mappings'] = {
            c.name: None for c in table.columns
        }

        # write out to config file
        with open(args.config_file, 'w') as fp:
            json.dump(config, fp, indent=2)

        return 0
    elif 'mappings' not in config:
        print(f'The "mappings" property was not found in "{args.config_file}"', file=sys.stderr)

    # check for data_file
    if not args.data_file:
        print('<data_file> argument missing', file=sys.stderr)
        return 1

    # subset the mappings, optionally
    if args.subset:
        config['mappings'] = {k: v for k, v in config['mappings'].items() if k in args.subset}

    # check for non-empty mappings
    if not config['mappings']:
        print(f'The "mappings" property is empty in "{args.config_file}"', file=sys.stderr)
        return 1

    # for query-based mappings, populate field names for each mapping, and create isolated set of query mappings
    formatter = string.Formatter()
    for key, mapping in config['mappings'].items():
        if isinstance(mapping, dict):
            mapping['fieldnames'] = tuple([fname for _, fname, _, _ in formatter.parse(mapping.get('query', '')) if fname])
            if 'query' in mapping:
                mapping['itemgetter'] = itemgetter(*mapping['fieldnames'])
        elif mapping and not isinstance(mapping, str):
            print(f'Mapping for "{key}" invalid. Expected null, string, or dictionary.', file=sys.stderr)
            return 1

    # nullable indicator from the config
    null = config.get('null', None)

    # helper for converting to None, if values is nullable
    def nullable(value):
        return None if value == null else value

    # request cache, for queries based on path template and input parameters
    request_cache = {}

    # helper for converting a row from input file into a record for the database table
    def row_to_record(row):
        record = {}
        for cname, mapping in config['mappings'].items():
            if isinstance(mapping, str):
                record[cname] = nullable(mapping.format(**row))
            elif isinstance(mapping, dict):
                # set value to null and continue, if any relevant row values are in the skip list
                if any([(row[fname] in mapping.get('skip', [])) for fname in mapping['fieldnames']]):
                    record[cname] = None
                    continue

                # do simple value replacements
                if 'replace' in mapping:
                    record[cname] = mapping['replace'].get(mapping['value'].format(**row))
                    continue

                # check query cache, for past results
                cache_key = (mapping['query'], mapping['itemgetter'](row))
                if cache_key in request_cache:
                    # get results from the cache
                    results = request_cache[cache_key]
                else:
                    # query the catalog
                    sep = mapping.get('separator')
                    path = mapping['query'].format(**{
                        k: urlquote(v.split(sep)[0] if v and sep else v)
                        for k, v in row.items() if k in mapping['fieldnames']
                    })
                    request_cache[cache_key] = results = catalog.get(path).json()
                    if len(results) > 1:
                        print(f'Warning: "{path}" has more than one result', file=sys.stderr)

                # populate column value from query results results
                if not results:
                    record[cname] = None
                else:
                    record[cname] = mapping['value'].format(**results[0])
            else:
                record[cname] = None  # in practice, this should not be reached

        return record

    # process the data file
    with open(args.data_file) as file:
        reader = csv.DictReader(file, dialect='excel')
        writer = csv.DictWriter(sys.stdout, config['mappings'].keys(), dialect='excel')

        # if only unique values are wanted, wrap the 'writer'
        if args.unique:
            uniques = set()

            def writerow(r):
                values = tuple(r.values())
                if values not in uniques:
                    writer.writerow(r)
                    uniques.add(values)

        else:
            writerow = writer.writerow

        try:
            writer.writeheader()
            for row in reader:
                if args.verbose >= 3:
                    print(row, file=sys.stderr)
                record = row_to_record(row)
                writerow(record)
        except csv.Error as e:
            print('File {}, line {}: {}'.format(args.data_file, reader.line_num, e), file=sys.stderr)
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
