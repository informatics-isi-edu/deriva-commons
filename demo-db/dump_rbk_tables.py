from pprint import pprint
from deriva.core import DerivaServer, BaseCLI, get_credential
from deriva.core.ermrest_model import Schema, Table, Column, Key, ForeignKey, builtin_types
from pathlib import Path
import json

class RBKDump:
    def __init__(self, host, catalog):
        # Don't authenticate - get only publicly-readable data
        server = DerivaServer("https", host)
        catalog = server.connect_ermrest(catalog)
        pb = catalog.getPathBuilder()
        for d in ["Vocabulary", "Data"]:
            Path("./data/{d}".format(d=d)).mkdir(parents=True, exist_ok=True)
        
        for table in [pb.Vocabulary.Species, pb.Vocabulary.Developmental_Stage, pb.Vocabulary.Sex,
                      pb.Vocabulary.Assay_Type, pb.Vocab.Sequencing_Type,
                      pb.Vocab.Molecule_Type]:
            file=Path("./data/Vocabulary/{t}.json".format(t=table.name)).open('w')
            json.dump(list(table.entities()), file)
            table.entities()
            file.close()

if __name__ == '__main__':
    cli = BaseCLI("dump tables to import into demo", None, hostname_required=True)
    cli.parser.add_argument("catalog", type=int, default=None)
    args=cli.parse_cli()
    dmp = RBKDump(args.host, args.catalog)

