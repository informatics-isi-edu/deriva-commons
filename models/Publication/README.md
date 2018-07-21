### Files

* schema.json: model defintion of the `Common` schema
* Publication_Venue.json: model definition of `Publication_Venue` table
* Publication.json: model defintion of the `Publication` table
* foreign_keys.json: foreign key defintion


### ER Model
```
Publication --> Publication_Venue

```


### Schema creation sequence
Follow the following sequences to properly generate the Common schema. 
1. create `Common` schema specified in schema.json
2. create `Publication_Venue` table specified in Publication_Venue.json
2. create `Publication` table specified in Publication.json
4. create foreign keys specified in foreign_key.json 




