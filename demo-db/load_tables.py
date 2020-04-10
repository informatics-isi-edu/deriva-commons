from pprint import pprint
from deriva.core import DerivaServer, BaseCLI, get_credential
from deriva.core.ermrest_model import Schema, Table, Column, Key, ForeignKey, builtin_types
from pathlib import Path
from collections import OrderedDict
import json
import sys

class DemoLoad:
    def __init__(self, host, catalog, credentials, data_directory):
        self.server = DerivaServer("https", host, credentials)
        self.catalog = self.server.connect_ermrest(catalog)
        self.pb = self.catalog.getPathBuilder()
        self.parent = Path(data_directory)
        self.known_tables = OrderedDict({
            "Species" : {
                "src" : "Vocabulary/Species.json",
                "dest": self.pb.Vocabulary.Species,
            },
            "Stage" : {
                "src" : "Vocabulary/Developmental_Stage.json",
                "dest" :  self.pb.Vocabulary.Stage,
            },
            "Sex" : {
                "src" : "Vocabulary/Sex.json",
                "dest" : self.pb.Vocabulary.Sex
            },
            "Assay_Type": {
                "src" : "Vocabulary/Assay_Type.json",
                "dest": self.pb.Vocabulary.Assay_Type,
            },
            "Sequencing_Type": {
                "src": "Vocabulary/Sequencing_Type.json",
                "dest": self.pb.Vocabulary.Sequencing_Type,
                "extra_defaults" : ["ID", "URI"],
                "transform_func": self.vocab_to_vocabulary
            },
            "Molecule_Type": {
                "src": "Vocabulary/Molecule_Type.json",
                "dest": self.pb.Vocabulary.Molecule_Type,
                "extra_defaults" : ["ID", "URI"],
                "transform_func": self.vocab_to_vocabulary
            }
        })


    def load(self, table_names):
        todo = []
        keys = self.known_tables.keys()
        if table_names is None:
            todo = self.known_tables.values()
        else:
            for n in table_names:
                if n not in keys:
                    raise ValueError("unknown table name: {n}".format(n=n))
            for key in keys:
                if key in table_names:
                    todo.append(self.known_tables[key])
        for entry in todo:
            self.load_file(entry)

    def load_file(self, entry):
        src = self.parent.joinpath(entry['src']).open("r")
        data = json.load(src)
        src.close()
        transform = entry.get("transform_func")
        if transform:
            transform(entry["dest"], data)
        if entry.get("extra_defaults") is None:
            entry['dest'].insert(data)
        else:
            entry['dest'].insert(data, defaults=entry.get("extra_defaults"))

    def vocab_to_vocabulary(self, table, data):
        for row in data:
            if row.get("Description") is None:
                row["Description"] = row["Name"]


if __name__ == '__main__':
    cli = BaseCLI("load tables into demo server", None, hostname_required=True)
    cli.parser.add_argument("--directory", "-d", type=str, help="Parent directory of data files", default="./data")
    cli.parser.add_argument("--all", "-a", action = "store_const", const=True, help="load all tables")
    cli.parser.add_argument("catalog", type=int, default=None)
    cli.parser.add_argument("--table", type=str, action = "append", help="table(s) to load")
    args=cli.parse_cli()
    credentials = get_credential(args.host)
    dl = DemoLoad(args.host, args.catalog, credentials, args.directory)
    if not (args.table or args.all):
        print("Specify --all or at least one table")
        sys.exit(1)
    dl.load(args.table if args.table else None)
    
        
