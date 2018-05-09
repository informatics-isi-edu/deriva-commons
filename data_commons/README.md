# Loading the data_commons schema

## Export the data-commons schema from the ontology server

On the `ontology` server, as `root` run:

```
su -c "pg_dump -f data_commons.sql -n 'data_commons' data_commons" - postgres

```

On the server you want to load the `data_commons` schema:

1. Create a top directory:

```
mkdir -p <top_directory>

```

We will refer it as `$top_directory`. 

2. Copy the dumped `data-commons` schema from the `ontology` server into the `$top_directory`:

```
scp ontology.isrd.isi.edu:data_commons.sql $top_directory

```

3. Copy the `common_functions.sql` and `data_commons_ermrest.sql` files from the github `data-commons/data_commons` directory into the `$top_directory`.


4. From the `$top_directory`, as `root`, execute the following commands:

```
su -c "psql <db_name>" - postgres < data_commons.sql > out.log 2>err.log
su -c "psql <db_name>" - postgres < common_functions.sql > out.log 2>err.log
su -c "psql <db_name>" - postgres < data_commons_ermrest.sql > out.log 2>err.log

```

where `<db_name>` is the database name where you load the `data_commons` schema.

After each command, check that the `err.log` file does not contain errors.

