Use chado_data_commons_schema.sql to create a chado-style schema (called `data_commons` by default).

Use chado_to_data_commons.sql to transform a standard chado schema into our data-commons-chado style (by default, this expects the source chado tables to be in the `public` schema and the destination tables to be in the `data_commons` schema).

Use the tools and processes in the [obo](obo) subdirectory to create chado tables in the `public` schema from obo files.
