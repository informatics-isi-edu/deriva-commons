from pprint import pprint
from deriva.core import DerivaServer, BaseCLI, get_credential
from deriva.core.ermrest_model import Schema, Table, Column, Key, ForeignKey, builtin_types

class DemoCatalog:
    VOCABULARY = "Vocabulary"
    DATA = "Data"
    def __init__(self, host, credentials, catalog_number=None):
        self.server = DerivaServer("https", host, credentials=credentials)        

        if catalog_number is None:            
            self.catalog = self.server.create_ermrest_catalog()
        else:
            self.catalog = self.server.connect_ermrest(catalog_number)
        self.model = self.catalog.getCatalogModel()

    def create_tables(self):
        self.create_schemas()
        self.create_vocabulary_tables()
        self.create_specimen_table()
        self.create_study_table()
        self.create_experiment_table()
        self.create_replicate_table()
        self.create_file_table()
        self.create_collection_table()
        self.create_study_collection_table()
        

    def create_schemas(self):
        try:
            self.model.create_schema(Schema.define(self.VOCABULARY, comment=None))
            self.model.create_schema(Schema.define(self.DATA, comment=None))
        except ValueError:
            pass

    def try_create_table(self, schema, table_def):
        try:
            schema.create_table(table_def)
        except ValueError:
            pass

    def create_vocabulary_tables(self):
        schema = self.model.schemas[self.VOCABULARY]        
        table_def = Table.define_vocabulary("Species", "deriva-demo:{RID}", 
                                            provide_system=True, key_defs=[Key.define(['Name'])],
                                            comment="Species")
        self.try_create_table(schema, table_def)

        table_def = Table.define_vocabulary("Stage", "deriva-demo:{RID}", 
                                            provide_system=True, key_defs=[Key.define(['Name'])],
                                            comment="Developmental Stage (e.g., Theiler stage, Carnegie stage)")
        self.try_create_table(schema, table_def)                              

        table_def = Table.define_vocabulary("Sex", "deriva-demo:{RID}", 
                                            provide_system=True, key_defs=[Key.define(['Name'])],
                                            comment="Sex")
        self.try_create_table(schema, table_def)

        table_def = Table.define_vocabulary("Assay_Type", "deriva-demo:{RID}", 
                                            provide_system=True, key_defs=[Key.define(['Name'])],
                                            comment="Assay type (e.g., mRNA-Seq, scRNA-Seq, ISH")
        self.try_create_table(schema, table_def)

        table_def = Table.define_vocabulary("Anatomy", "deriva-demo:{RID}", 
                                            provide_system=True,
                                            comment="Anatomical Region")
        self.try_create_table(schema, table_def)

        table_def = Table.define_vocabulary("Sequencing_Type", "deriva-demo:{RID}", 
                                            provide_system=True, key_defs=[Key.define(['Name'])],
                                            comment="Type of sequencing performed")
        self.try_create_table(schema, table_def)

        table_def = Table.define_vocabulary("Molecule_Type", "deriva-demo:{RID}", 
                                            provide_system=True, key_defs=[Key.define(['Name'])],
                                            comment="Type of molecule (e.g., DNA, RNA)")
        self.try_create_table(schema, table_def)        

        table_def = Table.define_vocabulary("File_Type", "deriva-demo:{RID}", 
                                            provide_system=True, key_defs=[Key.define(['Name'])],
                                            comment="File type")
        self.try_create_table(schema, table_def)        
        
    def create_specimen_table(self):
        schema = self.model.schemas[self.DATA]
        table_def = Table.define(
            "Specimen",
            column_defs = [
                Column.define("Species", builtin_types.text, nullok=False),
                Column.define("Sex", builtin_types.text, nullok=True),
                Column.define("Stage", builtin_types.text, nullok=True, comment="developmental stage of this specimen"),
                Column.define("Anatomy", builtin_types.text, nullok=True),                
                Column.define("Assay_Type", builtin_types.text, nullok=False, comment="type of assay performed on this specimen"),
                Column.define("Internal_ID", builtin_types.text, nullok=True, comment="data-provider-defined unique identifier")
                ],
            key_defs = [
                Key.define(["Internal_ID"])
                ],
            fkey_defs = [
                ForeignKey.define(["Species"], self.VOCABULARY, "Species", ["Name"],
                                  constraint_names=[[self.DATA, "Specimen_Species_fkey"]]),
                ForeignKey.define(["Sex"], self.VOCABULARY, "Sex", ["Name"],
                                  constraint_names=[[self.DATA, "Specimen_Sex_fkey"]]),
                ForeignKey.define(["Stage"], self.VOCABULARY, "Stage", ["Name"],
                                  constraint_names=[[self.DATA, "Specimen_Stage_fkey"]]),
                ForeignKey.define(["Assay_Type"], self.VOCABULARY, "Assay_Type", ["Name"],
                                  constraint_names=[[self.DATA, "Specimen_Assay_Type_fkey"]]),
                ForeignKey.define(["Anatomy"], self.VOCABULARY, "Anatomy", ["ID"],
                                  constraint_names=[[self.DATA, "Specimen_Anatomy_fkey"]])
            ],
            comment="A biospeciment"
        )
        self.try_create_table(schema, table_def)

    def create_study_table(self):
        schema = self.model.schemas[self.DATA]
        table_def = Table.define(
            "Study"            ,
            column_defs = [
                Column.define("Internal_ID", builtin_types.text, nullok=False, comment="data-provider-defined unique identifier"),
                Column.define("Title", builtin_types.text, nullok=False),
                Column.define("Summary", builtin_types.text, nullok=False),                
                Column.define("Pubmed_ID", builtin_types.text, nullok=True),
                ],
            key_defs = [
                Key.define(["Internal_ID"]),
                Key.define(["Title"])
                ],
            comment="A sequencing or metabolomics study"
        )
        self.try_create_table(schema, table_def)        
        

    def create_experiment_table(self):
        schema = self.model.schemas[self.DATA]
        table_def = Table.define(
            "Experiment",
            column_defs = [
                # rbk Notes becomes experiment Internal_ID
                Column.define("Internal_ID", builtin_types.text, nullok=False, comment="data-provider-defined unique identifier"),
                Column.define("Study", builtin_types.text, nullok=False, comment="study that this experiment is part of"),
                Column.define("Molecule_Type", builtin_types.text, nullok=False),                
                Column.define("Sequencing_Type", builtin_types.text, nullok=True),
                Column.define("Cell_Count", builtin_types.int4, nullok=True),
                Column.define("Notes", builtin_types.markdown, nullok=True),
                ],
            key_defs = [
                Key.define(["Internal_ID"]),
                ],
            fkey_defs = [
                ForeignKey.define(["Study"], self.DATA, "Study", ["RID"],
                                  constraint_names=[[self.DATA, "Experiment_Study_fkey"]]),
                ForeignKey.define(["Molecule_Type"], self.VOCABULARY, "Molecule_Type", ["Name"],
                                  constraint_names=[[self.DATA, "Experiment_Molecule_Type_fkey"]]),
                ForeignKey.define(["Sequencing_Type"], self.VOCABULARY, "Sequencing_Type", ["Name"],
                                  constraint_names=[[self.DATA, "Experiment_Sequencing_Type_fkey"]])
                ],
            comment="A sequencing or metabolomics experiment"
        )
        self.try_create_table(schema, table_def)
        
    def create_replicate_table(self):
        schema = self.model.schemas[self.DATA]
        table_def = Table.define(
            "Replicate",
            column_defs = [
                Column.define("Experiment", builtin_types.text, nullok = False, comment="Experiment that produced this replicate"),
                Column.define("Biological_Replicate_Number", builtin_types.int4, nullok = False),
                Column.define("Technical_Replicate_Number", builtin_types.int4, nullok = False),
                Column.define("Mapped_Reads", builtin_types.float8, nullok = True),                
                Column.define("RNA_Reads", builtin_types.float8, nullok = True),
                Column.define("Specimen", builtin_types.text, nullok=True),
                Column.define("Description", builtin_types.text, nullok = True)
                ],
            key_defs = [
                Key.define(["Experiment", "Biological_Replicate_Number", "Technical_Replicate_Number"])
                ],
            fkey_defs = [
                ForeignKey.define(["Experiment"], self.DATA, "Experiment", ["RID"],
                                  constraint_names=[[self.DATA, "Replicate_Experiment_fkey"]]),
                ForeignKey.define(["Specimen"], self.DATA, "Specimen", ["RID"],
                                  constraint_names=[[self.DATA, "Replicate_Specimen_fkey"]])
                ],
            comment="A biological or technical replicate in a sequencing experiment")
        self.try_create_table(schema, table_def)

    def create_file_table(self):
        schema = self.model.schemas[self.DATA]
        table_def = Table.define(
            "File",
            column_defs = [
                Column.define("Replicate", builtin_types.text, nullok = False, comment="Replicate that generated this file"),
                Column.define("File_URI", builtin_types.text, nullok=False, comment="URI for this file"),
                Column.define("File_Name", builtin_types.text, nullok=False, comment="Name of file when uploaded"),
                Column.define("File_Size", builtin_types.int8, nullok=False, comment="Size of file in bytes"),
                Column.define("File_MD5", builtin_types.text, nullok=False, comment="MD5 checksum of this file"),
                Column.define("File_SHA256", builtin_types.text, nullok=False, comment="SHA256 checksum of this file"),
                Column.define("File_Type", builtin_types.text, nullok=False),
                Column.define("Caption", builtin_types.text, nullok=True)
                ],
            key_defs = [
                Key.define(["File_MD5"]),
                Key.define(["File_URI"])
                ],
            fkey_defs = [
                ForeignKey.define(["Replicate"], self.DATA, "Replicate", ["RID"],
                                  constraint_names=[[self.DATA, "File_Replicate_fkey"]]),
                ForeignKey.define(["File_Type"], self.VOCABULARY, "File_Type", ["Name"],
                                  constraint_names=[[self.DATA, "File_File_Type_fkey"]])
            ],
            comment="Data files")
        self.try_create_table(schema, table_def)

    def create_collection_table(self):
        schema = self.model.schemas[self.DATA]
        table_def = Table.define(
            "Collection",
            column_defs = [
                Column.define("Title", builtin_types.text, nullok = False),
                Column.define("Description", builtin_types.text, nullok = False),
                Column.define("Persistent_ID", builtin_types.text, nullok = True),
                Column.define("Details", builtin_types.markdown, nullok = True)
                ],
            key_defs = [
                Key.define(["Title"])
                ],
            comment="A collection of data")
        self.try_create_table(schema, table_def)

    def create_study_collection_table(self):
        schema = self.model.schemas[self.DATA]
        table_def = Table.define(
            "Study_Collection",
            column_defs = [
                Column.define("Study", builtin_types.text, nullok = False),
                Column.define("Collection", builtin_types.text, nullok = False)
                ],
            key_defs = [
                Key.define(["Study", "Collection"])
                ],
            fkey_defs = [
                ForeignKey.define(["Study"], self.DATA, "Study", ["RID"],
                                  constraint_names=[[self.DATA, "Study_Collection_Study_fkey"]]),
                ForeignKey.define(["Collection"], self.DATA, "Collection", ["RID"],
                                  constraint_names=[[self.DATA, "Study_Collection_Collection_fkey"]])
                ],
            comment="Many-to-many associations between studies and collection")
        self.try_create_table(schema, table_def)                                  
            
            
        
if __name__ == '__main__':
    cli = BaseCLI("demo database creation tool", None, hostname_required=True)
    cli.parser.add_argument("--use-catalog", type=int, default=None)
    args = cli.parse_cli()
    credentials = get_credential(args.host)
    dc = DemoCatalog(args.host, credentials, catalog_number=args.use_catalog)
    dc.create_tables()
    print(dc.catalog.catalog_id)
