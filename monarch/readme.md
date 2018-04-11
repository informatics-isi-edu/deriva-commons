# Importing Monarch

The script here can be used to import the monarch data dump into an ERMrest
catalog.

## Get the Monarch database dump files

```
$ wget --recursive --no-parent https://data.monarchinitiative.org/tsv/
...
```

## Requirements

1. The script uses the `deriva-py` library.
2. A valid credential established by `DERIVA-Auth`.

## Run the import script

```
$ cd data.monarchinitiative.org/tsv
$ python import_monarch.py
...
```

