# A utility for importing CSV/TSV data files into newly defined tables in ERMrest.
import argparse
import csv
import os.path
from requests import HTTPError
from deriva.core import DerivaServer, get_credential
from deriva.core.ermrest_model import Table, Column, Key, builtin_types

# Sub-heading types
subh_display_name = 'displayname'
subh_comments = 'comments'
subh_types = 'types'
subh_annotations = 'annotations'
subh_valuemap = 'valuemap'

known_subheaders = [
subh_display_name,
subh_comments,
subh_types,
subh_annotations,
subh_valuemap,
]

# Program description
description = """
A utility for importing CSV (or CSV-like) files into an ERMrest catalog. For each input 'file' it will create a table in
the specified schema in the catalog and it will load the data file into the newly defined table. The input file format
can be a standard CSV or TSV file format. Optionally, you may specify additional non-standard sub-header rows which may
include: {subheaders}. The 'types' must be defined ERMrest column types (e.g., 'int8'). The 'annotations' must be 
tab-separated list of ERMrest annotations but currently does not support annotation body only annotation tag names 
(e.g., 'tag:isrd.isi.edu,2017:asset'). The 'valuemap' must be a tab-delimited set of '='-delimited value mappings 
(e.g., '1=male\t2=female'). When a valuemap is given the values in that column will be remapped. The extended 
sub-headers will be processed in the order given. A special keyword 'all' may be used in place of specifying the 
sub-headers individually which will specify all sub-headers in the order as introduced above.
""".format(subheaders=', '.join(known_subheaders))


class SubheaderAction(argparse.Action):
    """Custom action for subheader."""
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(SubheaderAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if values == 'all':
            values = known_subheaders
        else:
            values = values.split(':')
            for v in values:
                if v not in known_subheaders:
                    parser.error("unrecognized --subheader '%s'" % v)

        setattr(namespace, self.dest, values)


# Argument parser
parser = argparse.ArgumentParser(description=description)
parser.add_argument('hostname')
parser.add_argument('--catalog', type=int, help='Catalog number, if none given, will attempt to create new catalog on the host')
parser.add_argument('-t', '--tsv', action='store_true', help='Expect tab-delimited values (TSV) format')
parser.add_argument('-s', '--schema', default='public', help='Schema name where tables will be defined')
parser.add_argument('--nosyscols', action='store_true', help='Do not use system columns in table definitions')
parser.add_argument('--droptable', action='store_true', help='If table exists, attempt to drop, otherwise skip it')
parser.add_argument('--subheaders', default=[], action=SubheaderAction,
                    help="A ':'-seperated set of subheaders to read from the data file (e.g., 'displayname:comments:types') or 'all'.")
parser.add_argument('file', nargs='+', help='File names of input data files')
args = parser.parse_args()

# Create/connect catalog and get various interfaces
credential = get_credential(args.hostname)
server = DerivaServer('https', args.hostname, credential)
catalog = server.connect_ermrest(args.catalog) if args.catalog else server.create_ermrest_catalog()
model = catalog.getCatalogModel()
schema = model.schemas[args.schema]
config = catalog.getCatalogConfig()

# ACLs to be defined on catalog and table
acls = {
    "select": ['*'],
    "enumerate": ['*']
}

if not args.catalog:
    # Only when creating a new catalog do we update its ACLs.
    config.acls.update(acls)
    catalog.applyCatalogConfig(config)


def valid_value(val, vtype, vmap=None):
    """ This is a very quick and dirty validator for input values.
    val: the value
    vtype: the value type as an ermrest type
    vmap: the value map dictionary
    """
    if isinstance(val, int):
        # accept all integers
        return val
    elif vtype == builtin_types.timestamp or vtype == builtin_types.timestamptz:
        # make sure timestamps are sent as empty "" strings or invalid values 
        if len(val) and val != "not reported" and val != "unreported":
            return val
        else:
            return None
    elif vmap:
        # if there is a data dictionary value mapping, use it
        return vmap.get(val, None)
    elif len(val):
        # any non-empty string accepted
        return val.strip()
    else:
        return None


for fname in args.file:
    print('Importing {fname}...'.format(fname=fname))
    tname = os.path.splitext(os.path.basename(fname))[0]
    visible_columns = []

    if tname in schema.tables:
        print("Found existing table '{tname}' in catalog".format(tname=tname))
        if args.droptable:
            table = schema.tables[tname]
            table.delete(catalog, schema)
            print("Dropped table from catalog")
        else:
            print("Skipping.")
            continue

    if args.nosyscols:
        pk = 'key'
        col_defs = [Column.define(pk, builtin_types.int8, comment="Row key (generated by client tool on import)")]
        key_defs = [Key.define([pk])]
        types = {pk: builtin_types.int8}
    else:
        col_defs = []
        key_defs = []
        types = {}
        visible_columns.append('RID')

    with open(fname) as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t') if args.tsv else csv.DictReader(csvfile)
        subheaders = {k: {} for k in known_subheaders}
        for subheader in args.subheaders:
            subheaders[subheader] = next(reader)

        for cname in reader.fieldnames:
            visible_columns.append(cname)
            comment = subheaders[subh_comments].get(cname)
            ctype = builtin_types[subheaders[subh_types].get(cname)] if subheaders[subh_types].get(cname) else builtin_types.text
            types[cname] = ctype
            if subheaders[subh_valuemap].get(cname):
                subheaders[subh_valuemap][cname] = {kv.split('=')[0]: kv.split('=')[1] for kv in subheaders[subh_valuemap][cname].split('\n')}
            annotation = {subheaders[subh_annotations][cname]: None} if subheaders[subh_annotations].get(cname) else {}
            if subheaders[subh_display_name].get(cname):
                annotation["tag:misd.isi.edu,2015:display"] = {"markdown_name": subheaders[subh_display_name].get(cname)}
            col_defs.append(Column.define(cname, ctype, comment=comment, annotations=annotation))

        tab_def = Table.define(tname,
                               column_defs=col_defs,
                               key_defs=key_defs,
                               acls=acls,
                               annotations={
                                   "tag:isrd.isi.edu,2016:visible-columns": {"*": visible_columns}
                               },
                               provide_system=(not args.nosyscols))

        print('Creating table {tname}...'.format(tname=tname))
        try:
            schema.create_table(catalog, tab_def)
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
                if args.nosyscols:
                    entity[pk] = reader.line_num
                entity = {k: valid_value(v, types[k], subheaders[subh_valuemap].get(k)) for k,v in entity.items()}
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
