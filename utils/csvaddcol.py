"""Adds column(s) to CSV data based on results of DERIVA (ERMrest) queries."""

import argparse
import csv
import string
import sys
from deriva.core import DerivaServer, get_credential, urlquote


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog="""
    All QUERY expressions will be evaluated for each row in the order specified on the command line. For a given COLUMN,
    the first non-null value will be taken from the results of the QUERY set. There is no implicit pairing of COLUMN and
    QUERY parameters.
    """)
    parser.add_argument("hostname", help="Server hostname.")
    parser.add_argument("catalog_id", help="Catalog ID.")
    parser.add_argument("file", nargs='?', help="File name (STDIN if not given).")
    parser.add_argument("-c", "--column", action="append", help="Column name to be added to the right. Value of same name taken from query results for each row. For example, '-c new_col'.")
    parser.add_argument("-q", "--query", action="append", help="Query path template evaluated for each row. Uses formatted string '{...}' replacement style. For example, '-q /attribute/tA/tB/c={input_col}/new_col:=d'.")
    parser.add_argument("-s", "--separator", help="Use separator to split input values before using them in query templates, discarding all but first value in the set. For example, '-s \";\"'.")
    args = parser.parse_args()

    # connect to catalog
    server = DerivaServer('https', args.hostname, credentials=get_credential(args.hostname))
    catalog = server.connect_ermrest(args.catalog_id)

    # coerce args
    new_columns = args.column or []
    queries = args.query or []

    # parse query template keys
    query_template_keys = []
    for query in queries:
        query_template_keys.extend(
            [fname for _, fname, _, _ in string.Formatter().parse(query) if fname]
        )

    # query request cache
    request_cache = {}

    # process the file
    with open(args.file) if args.file else sys.stdin as file:
        reader = csv.DictReader(file, dialect='excel')
        writer = csv.DictWriter(sys.stdout, list(reader.fieldnames) + new_columns, dialect='excel')

        try:
            writer.writeheader()
            for row in reader:
                # urlquote row values
                row_urlquoted = {k: urlquote(v.split(args.separator)[0] if v else v) for k, v in row.items() if k in query_template_keys}

                # query catalog (or get cached results) to accumulate all row results
                row_results = []
                for query in queries:
                    path = query.format(**row_urlquoted)
                    if path in request_cache:
                        results = request_cache[path]
                    else:
                        results = catalog.get(path).json()
                        if len(results) > 1:
                            print(f'Warning: "{path}" has more than one result', file=sys.stderr)
                        results = results[0] if results else {}
                        request_cache[path] = results
                    row_results.append(results)

                # set col value to first matching value from all row results
                for col in new_columns:
                    row[col] = None
                    for results in row_results:
                        if results.get(col) is not None:
                            row[col] = results[col]
                            break

                # write row values
                writer.writerow(row)
        except csv.Error as e:
            print('File {}, line {}: {}'.format(args.data_file, reader.line_num, e), file=sys.stderr)
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
