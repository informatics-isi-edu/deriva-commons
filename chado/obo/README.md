In theory, converting OBO files to Chado should be pretty simple: just follow the [instructions from the gmod wiki](http://gmod.org/wiki/Load_a_custom_ontology_in_Chado). In practice, it can be a little more complicated.

Step 1: Convert the OBO text file to oboxml. If you're lucky, you can just do:
```
go2fmt.pl -p obo_text -w xml myfile.obo > myfile.oboxml
```
This fails on the [Uberon OBO file](http://ontologies.berkeleybop.org/uberon/ext.obo) because some of the entries in those files have quoted comma-containing strings in the `notes` field, and the tooling (and, I think the OBO standard, although I haven't read it closely enough to be sure) doesn't honor quotes, and instead expects commas to be escaped by backslashes.

The script `format-hacks/preprocess_obo.py` takes an obo file and escapes the commas in the `notes` field. I'd suggest running go2fmt.pl as above first, but if it fails, you can try this:
```
python preprocess_obo.py < myfile.obo | go2fmt.pl -p obo_text -w xml - > myfile.oboxml

Step 2: Convert the oboxml file to chadoxml.

The gmod instructions say to run the equivalent of:

xsltproc /usr/local/share/perl5/GO/xsl/oboxml_to_chadoxml.xsl - < myfile.oboxml > myfile.chadoxml

This will run without errors, but, depending on the contents of the oboxml file, may create problems when you try to load the chadoxml file into the database. The main issues I've found are:

* There are some circumstances in which the chadoxml file winds up with cvterm definitions that have only a dbxref, not a name.
* There are some circumstances in which the chadoxml file winds up with a cvterm definition with no cv.
* There are some circumstances in which the chadoxml treats term properties as relationships

The script `format-hacks/oboxml_to_chadoxml.xsl` has been tweaked to fix at least some of these problems (enough to load the uberon ontology).

Step 3: load the chadoxml file.

The program to load chadoxml files into chado databases is called `stag-storenode.pl`. It depends on the library `DBStag.pm`, which has a bug that generates errors whenever an ontology is loaded. I couldn't find a source repo for DBStag anywhere, but you can get the distribution through cpan and patch it using `format-hacks/dbstag.patch`.

cd to the chado directory (from https://github.com/GMOD/Chado.git) and do this (note: `make load_schema` **will drop and recreate the database**) (*Todo: test process for to the db instead of recreating it*):

```
make load_schema
make prepdb
```

In theory you can use `make ontologies` to load the relationship ontology, but in practice that doesn't work. Someone has created a version of the relationship ontology that does work, so you'll need to do this instead:

curl -O https://gist.githubusercontent.com/scottcain/10e255c991a41bcf0187/raw/7faba8c6f26766f5a686eb681f5cb2f48e49b78a/ro.obo
go2fmt.pl -p obo_text -w xml ro.obo | xsltproc $DC/chado/obo/format-hacks/ oboxml_to_chadoxml - > ro.xml
stag-storenode.pl -d 'dbi:Pg:dbname=chado' --user=yourname ro.xml

(*Todo: see if the standard ro.obo file works now with the various changes; also check whether the --user argument is necessary*)

Then load your chadoxml file. This takes about an hour for uberon.

```
stag-storenode.pl -d 'dbi:Pg:dbname=chado' --user myname myfile.chadoxml
```

Step 4: generate the cvtermpath table:

```
gmod_make_cvtermpath.pl -D mydb -c uberon >& path.out
```

This generates very verbose output and took about 60 hours to run. Some database tuning would probably help, as would rewriting that script as pure SQL.


*TODO: installation instructions for chado, gmod, dbstag*





