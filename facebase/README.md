# OCDM Vocabulary

## Download the OCDM ontology files.

The website for the `Ontology of Craniofacial Development and Malformation` can be found at [OCDM](http://www.si.washington.edu/projects/ocdm).
Download the [ocdm.zip](http://sig.biostr.washington.edu/share/downloads/ocdm/release/latest/ocdm.zip) file.

On the `ontology` server, create a top directory:

```
mkdir -p <top_directory>

```

We will refer it as `$top_directory`. 
Create the directory `$top_directory/owl` and extract the `*.owl` files into it.

## Extract the terms from the `OCDM` ontology (on the `ontology` server)

From the github `data-commons/facebase` directory, copy into the `$top_directory` directory, the following files:

```
parse_owl_file.py
parse_owl_ocdm.py
ocdm.sh

```

Run:

```
"$top_directory"/ocdm.sh "$top_directory"

```

The script will generate `sql` files into the `"$top_directory"/sql` directory.
The `sql` files will load the tables that contain the terms and predicates of the `OCDM` ontology.

Copy the `sql` files from the `"$top_directory"/sql` directory into the top directory of the `facebase` server (`$facebase_directory`).

## Export the `data-commons` schema from the `ontology` server

As `root` run:

```
su -c "pg_dump -f data_commons.sql -n 'data_commons' data_commons" - postgres

```

Copy the `data_commons.sql` file into the top directory of the `facebase` server (`$facebase_directory`).

## Load the vocabulary (on the facebase server)

The vocabulary will be loaded in the database that we will refer it as `$database`.

On the `facebase` server, create a top directory:

```
mkdir -p <facebase_directory>

```

We will refer it as `$facebase_directory`. 

From the github `data-commons/facebase` directory, copy into the `$facebase_directory` directory, the following files:

```
00_common_functions.sql
clean_up.sql
data_commons_ermrest.sql
data_commons_ocdm.sql
domain.sql
local_ocdm.sql
uberon.sql
vocabulary_references.sql
vocabulary.sh

```

In addition, the `$facebase_directory` directory will also have the sql files copied from the `ontology` server.


Run:

```
$facebase_directory/vocabulary.sh $database $facebase_directory
```

The script will:

- drop the `vocabulary` tables that don't have `Referenced by` tables.
- create the `data_commons` schema imported from the `ontology` server.
- create the database functions used for making the domain tables.
- add the `ermrest` system columns to the `data_commons.*` tables.
- create `temp.*` tables that contain the `facebase` and `uberon` terms.
- expand the `data_commons.*` tables with the terms from the `OCDM` ontology.
- load the `data_commons.cv` and `data_commons.db` tables with the new values of `OCDM` and `FaceBase` (the `cv = facebase` will contain the terms not found in the `uberon` or `OCDM` ontologies).
- expand the `data_commons.*` tables with the `facebase` terms not found in the `uberon` or `OCDM` ontologies.
- create and load the `"Vocabulary".*` domain tables.
- update the tables references to the `old` vocabulary tables to the `domain` vocabulary tables.
- drop the `old` vocabulary tables.

## Set the annotations of the vocabulary tables

We will use the following references:

- `$server`: the server on which the `FaceBase` database resides on (for example `dev.facebase.org`). 
- `$credentials`: the location of the credentials file.
- `$catalog`: the catalog number for the `FaceBase` database.

Run:

```
$facebase_directory/update_annotations.py $server $credentials $catalog
```

The script will:

- set the annotations for the `data_commons.*` tables.
- set the annotations for the columns of the `data_commons.*` tables.
- set the annotations for the Foreign Keys of the `data_commons.*` tables.
- set the annotations for the `ermrest` system columns of the domain vocabulary tables.
- set the annotations for the domain vocabulary tables.
- set the annotations for the columns of the domain vocabulary tables.
- set the annotations for the Foreign Keys of the domain vocabulary tables.
- set the annotations for the `Referenced by:` tables of the domain vocabulary tables.
- set the annotations for the schema of the domain vocabulary tables.




