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

6. Upload the files:
```
mydir=`pwd`
cd <some scratch directory>
mkdir -p assets/replicate
bdbag --materialize $mydir/asset_bag.zip
mv Experiment_16-DW7T/data/assets/Study/16-DW7R/Experiment/16-DW7T/Replicate/* assets/replicate/.
deriva-upload-cli <any necessary credential options> tutorial.derivacloud.org <catalog_number>
```

Please run the bdbag command as an *unauthenticated* user (those files are public as of this writing, but in theory that could change). The expanded asset directory will take up about 28G of space.

Additional scripts: `hatrac-init.sh` creates the hatrac `resources` namespace.

I've also included the `dump_rbk_tables.py` script, which was used to extract data from RBK.



