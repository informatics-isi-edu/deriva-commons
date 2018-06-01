## Creating a template database from a FaceBase database

The following script must be run on a host with ERMrest installed and a copy
of the FaceBase database.

The options for running the script are described in comments at the top of the
script.

```
$ sudo ./make_templatedb.sh
```

This script produces a plain text postgres database dump file, by default named
`commondb.sql`.

## Setting up policies

The `acl_config.json` can be used as a template for defining policies for 
a set of roles defined within it. Just add/remove globus group IDs from the
roles for `admin`, `curators`, `writers`, etc.

Then run the `deriva-acl-config` utility. See its `--help` for its list of
options.

