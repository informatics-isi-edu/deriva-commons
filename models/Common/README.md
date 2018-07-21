### Files

* schema.json: model defintion of the `Common` schema
* Curation_Status.json: model definition of `Curation_Status` table
* Collection.json: model defintion of the `Collection` table
* foreign_keys.json: foreign key defintion


### ER Model
```
Collection --> Curation_Status

```


### Schema creation sequence
Follow the following sequences to properly generate the Common schema. 
1. create `Common` schema specified in schema.json
2. create `Curation_Status` table specified in Curation_Status.json
3. create `Collection` table specified in Collection.json
4. create foreign keys specified in foreign_key.json 




