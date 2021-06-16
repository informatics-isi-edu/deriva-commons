## Initial Setup

To create a new set of gene-related tables:

0. Create a config file with the names of schemas and tables, etc. (see facebase_gene_defaults.csv for an example).

1. Create new tables with create_tables.py:

python3 create_tables.py <host> <config_file> <curie_prefix>

this should be pretty obvious -- <host> is the host you want to act on,
<config_file> is the file you created in step 0, and
<curie_prefix> is the prefix for curies for vocabulary terms you create

If some of these tables exist, there are options to skip creating them (python3 create_tables.py --help
to list them all)

2. Make sure your species table has entries for all species you'll need to reference. The ID column for each species should have an NCBI Taxon identifier (e.g., `NCBITaxon:10090`)

3. update some values at the top of load-gene-table.sh:
- hatrac_parent: a directory in which to put the raw gene files fetched from ncbi
- config_file: the file you created in step 0.
- database - your ermrest database
- scratch_db - an empty database to be used temporarily for etl

## Data import / update

To add gene (and associated table) entries for a new species or update your gene records with
a fresh copy from ncbi, do this:

```
sh load-gene-table.sh 
```
sh load-gene-table.sh <host> <species> <source_url>
```
for example:

```
sh load-gene-table.sh dev.facebase.org "Homo sapiens" \
   ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
```
