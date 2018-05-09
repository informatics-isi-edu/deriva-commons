# Loading an Ontology from the OWL Files

## Prerequisites

The `data_commons` schema needs to be loaded in the database.
For instructions, see [Loading the data_commons schema](/data_commons/README.md).

## Extract the terms and the synonyms from the ontology (on the ontology server)

The ontology terms and synonyms are identified by using the predicates `preferred_name`, respectively `synonym`.

We will refer the name of the ontology as `$ontology`.

On the `ontology` server, create a top directory:

```
mkdir -p <top_directory>

```

We will refer it as `$top_directory`. 

Create the `$top_directory/owl` and `$top_directory/sql` directories:

```
mkdir -p "$top_directory"/sql "$top_directory"/sql

```

Place the `*.owl` files into the `$top_directory/owl` directory.

From the github `data-commons/owl` directory, copy into the `$top_directory` directory, the following files:

```
parse_owl_file.py
parse_owl_directory.py

```

Run:

```
"$top_directory"/parse_owl_directory.py -i "$top_directory" -n "$ontology"

```

The script will generate `sql` files into the `$top_directory/sql` directory as well as the `$ontology.sh` file in the `$top_directory`.


## Load the ontology (on the database server)

On the `database` server, create a directory:

```
mkdir -p <database_directory>

```

We will refer it as `$database_directory`. 

The ontology will be loaded in the database that we will refer it as `$database`.

Copy the `sql` files from the `$top_directory/sql` directory of the ontology server into the `$database_directory`. 

```
scp ontology.isrd.isi.edu:"$top_directory"/sql/*.sql "$database_directory"/

```

Copy also the `$ontology.sh` file from the `$top_directory` directory of the ontology server into the `$database_directory` directory.

```
scp ontology.isrd.isi.edu:"$top_directory"/"$ontology.sh" "$database_directory"/

```


Run (as root):

```
"$database_directory"/"$ontology".sh "$database" "$database_directory"

```

The script will load the terms and synonyms of the ontology into the `data_commons` schema having:

 - The `db` values as the `owl` files names.
 - The `cv` values as `$ontology_$db`
 
