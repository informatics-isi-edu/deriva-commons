To create and populate a new catalog instance:

1. Install the deriva stack.

2. Create the catalog:
```
python3 create_demo_catalog.py <hostname>
 ```
 This will create a new catalog with the tutorial data model (but no data). The program will return the catalog number of the newly-created catalog.
 
3. Tweak the provided acl_config.json to reflect your own policies and run
```
deriva-acl-config --host <hostname> --config-file acl_config.json <catalog_number>
```
Where _catalog_number_ is the catalog number of the newly-created catalog (the same one that was returned in step 2).

4. Configure the catalog with the provided annotation_config.json file
```
deriva-annotation-config --host <hostname> --config-file annotation_config.json <catalog_number>
```
Note: we're using a very minimal chaise-config.js; menus, footers, etc. should be managed with the chaise-config attribute in each individual catalog.

5. Populate the catalog:
```
cd <source_directory>
python3 load_tables.py --all <hostname> <catalog_number>
```
where <source_directory> is the directory where this README is located.

6. The data was extracted from rbk with the _dump_rbk_tables.py_ script.

