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
        catalog.dcctx['cid'] = "oneoff/load_tables.py";        
        self.pb = catalog.getPathBuilder()
        self.schema_map = { "Vocab" : "Vocabulary"}

    def dump_all(self):
        for d in ["Vocabulary", "Data"]:
            Path("./data/{d}".format(d=d)).mkdir(parents=True, exist_ok=True)
        
        for table in [self.pb.Vocabulary.Species, self.pb.Vocabulary.Developmental_Stage, self.pb.Vocabulary.Sex,
                      self.pb.Vocabulary.Assay_Type, self.pb.Vocab.Sequencing_Type,
                      self.pb.Vocab.Molecule_Type]:
            self.dump_file(table)

        self.dump_experiment()
        self.dump_study()
        self.dump_specimen()
        self.dump_replicate()
        self.dump_anatomy()
        self.dump_study_collection()
        self.dump_collection()


    def dump_file(self, table):
        file=Path("./data/{s}/{t}.json".format(s=self.transform_schema(table.sname), t=table.name)).open('w')
        json.dump(list(table.entities()), file)
        file.close()

    def transform_schema(self, schema):
        if self.schema_map.get(schema) is None:
            return schema
        else:
            return self.schema_map[schema]

    def dump_experiment(self):
        file = Path("./data/Data/Experiment.json").open("w")
        table=self.pb.RNASeq.Experiment
        data = table.filter(table.Species=='Mus musculus').filter(table.Sequencing_Type=="mRNA-Seq").entities()
        json.dump(list(data), file)

    def dump_study(self):
        file = Path("./data/Data/Study.json").open("w")
        table=self.pb.RNASeq.Experiment
        data = table.filter(table.Species=='Mus musculus').filter(table.Sequencing_Type=="mRNA-Seq")\
                                                          .link(self.pb.RNASeq.Study).entities()
        json.dump(list(data), file)
        file.close()        

    def dump_replicate(self):
        file = Path("./data/Data/Replicate.json").open("w")
        table=self.pb.RNASeq.Experiment
        data = table.filter(table.Species=='Mus musculus').filter(table.Sequencing_Type=="mRNA-Seq")\
                                                          .link(self.pb.RNASeq.Replicate).entities()
        json.dump(list(data), file)
        file.close()

    def dump_specimen(self):
        file = Path("./data/Data/Specimen.json").open("w")
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
           .link(specimen.alias("S"))\
           .link(tissue.alias("T"), on=specimen.RID==tissue.Specimen_RID, join_type="left")

        data = path.attributes(
            path.S.RID,
            path.S.Species,path.S.Sex, path.S.Stage_ID, path.S.Assay_Type, path.S.Internal_ID,
            path.T.Tissue
        )
        stage_map = dict()
        for row in stage.entities():
            stage_map[row['ID']] = row['Name']
        for row in data:
            row["Stage"] = stage_map.get(row.get("Stage_ID"))
        print(len(data))
        json.dump(list(data), file)
        file.close()
        
    def dump_anatomy(self):
        file = Path("./data/Vocabulary/Anatomy.json").open("w")
        data = self.pb.Gene_Expression.Specimen_Tissue.link(self.pb.Vocabulary.Anatomy).entities()
        json.dump(list(data), file)
        file.close()

    def dump_study_collection(self):
        file = Path("./data/Data/Sequencing_Study_Collection.json").open("w")
        table=self.pb.RNASeq.Experiment
        data = table.filter(table.Species=='Mus musculus')\
                    .filter(table.Sequencing_Type=="mRNA-Seq")\
                    .link(self.pb.RNASeq.Study)\
                    .link(self.pb.RNASeq.Sequencing_Study_Collection)\
                    .entities()
        json.dump(list(data), file)
        file.close()        

    def dump_collection(self):
        file = Path("./data/Data/Collection.json").open("w")
        table=self.pb.RNASeq.Experiment
        data = table.filter(table.Species=='Mus musculus')\
                    .filter(table.Sequencing_Type=="mRNA-Seq")\
                    .link(self.pb.RNASeq.Study)\
                    .link(self.pb.RNASeq.Sequencing_Study_Collection)\
                    .link(self.pb.Common.Collection)\
                    .entities()
        json.dump(list(data), file)
        file.close()        
                          
        

if __name__ == '__main__':
    cli = BaseCLI("dump tables to import into demo", None, hostname_required=True)
    cli.parser.add_argument("catalog", type=int, default=None)
    args=cli.parse_cli()
    dmp = RBKDump(args.host, args.catalog)
    dmp.dump_all()

