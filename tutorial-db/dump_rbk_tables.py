from pprint import pprint
from deriva.core import DerivaServer, BaseCLI, get_credential
from deriva.core.ermrest_model import Schema, Table, Column, Key, ForeignKey, builtin_types
from pathlib import Path
import json

class RBKDump:
    VOCABULARY="Vocabulary"
    DATA="Data"
    def __init__(self, host, catalog):
        # Don't authenticate - get only publicly-readable data
        server = DerivaServer("https", host)
        catalog = server.connect_ermrest(catalog)
        catalog.dcctx['cid'] = "oneoff/load_tables.py";        
        self.pb = catalog.getPathBuilder()
        self.schema_map = { "Vocab" : "Vocabulary"}

    def dump_all(self):
        for d in [self.VOCABULARY, self.DATA]:
            Path("./data/{d}".format(d=d)).mkdir(parents=True, exist_ok=True)
        
        for table in [self.pb.Vocabulary.Species, self.pb.Vocabulary.Developmental_Stage, self.pb.Vocabulary.Sex,
                      self.pb.Vocabulary.Assay_Type, self.pb.Vocab.Sequencing_Type,
                      self.pb.Vocab.File_Type, self.pb.Vocab.Molecule_Type]:
            self.dump_table(table)

        self.dump_experiment()
        self.dump_study()
        self.dump_specimen()
        self.dump_replicate()
        self.dump_anatomy()
        self.dump_study_collection()
        self.dump_collection()

    def dump_table(self, table):
        self.finalize_and_write(table.name, table.sname, list(table.entities()))

    def finalize_and_write(self, basename, schema, records):
        if schema == "Vocab":
            schema = self.VOCABULARY
        dellist = self.get_manual_changes("./data_adjustments/{s}/{b}.deletions.json".format(s=schema, b=basename))
        outfile = open("./data/{s}/{b}.json".format(s=schema, b=basename), "w")

        if dellist:
            for i in range(0, len(records)):
                if records[i].get("RID") in dellist:
                    records.pop(i)
                    break

        json.dump(records, outfile, indent=4)
            
    def get_manual_changes(self, filename):
        changelist = None
        p = Path(filename)
        if p.exists():
           f = p.open()
           changelist = json.load(f)
           f.close()
        return changelist
        


    def transform_schema(self, schema):
        if self.schema_map.get(schema) is None:
            return schema
        else:
            return self.schema_map[schema]

    def dump_experiment(self):
        table=self.pb.RNASeq.Experiment
        data = table.filter(table.Species=='Mus musculus').filter(table.Sequencing_Type=="mRNA-Seq").entities()
        self.finalize_and_write("Experiment", self.DATA, list(data))

    def dump_study(self):
        table=self.pb.RNASeq.Experiment
        data = table.filter(table.Species=='Mus musculus').filter(table.Sequencing_Type=="mRNA-Seq")\
                                                          .link(self.pb.RNASeq.Study).entities()
        self.finalize_and_write("Study", self.DATA, list(data))        

    def dump_replicate(self):
        file = Path("./data/Data/Replicate.json").open("w")
        table=self.pb.RNASeq.Experiment
        data = table.filter(table.Species=='Mus musculus').filter(table.Sequencing_Type=="mRNA-Seq")\
                                                          .link(self.pb.RNASeq.Replicate).entities()
        self.finalize_and_write("Replicate", self.DATA, list(data))        

    def dump_specimen(self):
        experiment=self.pb.RNASeq.Experiment
        replicate=self.pb.RNASeq.Replicate
        specimen=self.pb.Gene_Expression.Specimen
        stage=self.pb.Vocabulary.Developmental_Stage
        anatomy=self.pb.Vocabulary.Anatomy
        tissue=self.pb.Gene_Expression.Specimen_Tissue
        stage=self.pb.Vocabulary.Developmental_Stage

        path = experiment.filter(experiment.Species=='Mus musculus')\
           .filter(experiment.Sequencing_Type=="mRNA-Seq")\
           .link(replicate)\
           .link(specimen.alias("S"))

        data = path.attributes(
            path.S.RID,
            path.S.Species,path.S.Sex, path.S.Stage_ID, path.S.Assay_Type, path.S.Internal_ID
        )
        stage_map = dict()
        for row in stage.entities():
            stage_map[row['ID']] = row['Name']
        for row in data:
            row["Stage"] = stage_map.get(row.get("Stage_ID"))

        anatomy_map = dict()
        for row in tissue.entities():
            anatomy_map[row['Specimen_RID']] = row['Tissue']
        for row in data:
            row["Anatomy"] = anatomy_map.get(row.get("RID"))
        self.finalize_and_write("Specimen", self.DATA, list(data))
        
    def dump_anatomy(self):
        file = Path("./data/Vocabulary/Anatomy.json").open("w")
        data = self.pb.Gene_Expression.Specimen_Tissue.link(self.pb.Vocabulary.Anatomy).entities()
        self.finalize_and_write("Anatomy", self.VOCABULARY, list(data))

    def dump_study_collection(self):
        table=self.pb.RNASeq.Experiment
        data = table.filter(table.Species=='Mus musculus')\
                    .filter(table.Sequencing_Type=="mRNA-Seq")\
                    .link(self.pb.RNASeq.Study)\
                    .link(self.pb.RNASeq.Sequencing_Study_Collection)\
                    .entities()
        self.finalize_and_write("Sequencing_Study_Collection", self.DATA, list(data))        

    def dump_collection(self):
        table=self.pb.RNASeq.Experiment
        data = table.filter(table.Species=='Mus musculus')\
                    .filter(table.Sequencing_Type=="mRNA-Seq")\
                    .link(self.pb.RNASeq.Study)\
                    .link(self.pb.RNASeq.Sequencing_Study_Collection)\
                    .link(self.pb.Common.Collection)\
                    .entities()
        self.finalize_and_write("Collection", self.DATA, list(data))        
        

if __name__ == '__main__':
    cli = BaseCLI("dump tables to import into demo", None, hostname_required=True)
    cli.parser.add_argument("catalog", type=int, default=None)
    args=cli.parse_cli()
    dmp = RBKDump(args.host, args.catalog)
    dmp.dump_all()

