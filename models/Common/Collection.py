from deriva.core import HatracStore, ErmrestCatalog, get_credential, DerivaPathError
import deriva.core.ermrest_model as em

table_name = "Collection"
table_comment = 'a collection of data'

acls = {}
acl_bindings = {}
annotations = {
    "tag:isrd.isi.edu,2016:visible-columns": {
      "*": [
        "RID",
        "Name",
	"Description",
	"URI",
        "RCT",
        "RMT"
      ]
    }
  }

key_defs = [
  em.Key.define(["Title"],
                constraint_names=["Common", "Collection_Title_key"]
                ),
  em.Key.define(["RID"],
                'constraint_names'["Common", "Collection_RID_key"]
                )
]

fkey_defs = []

column_defs = [
  em.Column.define("Title",
                   em.builtin_types.text,
                   nullok=False
                   ),
  em.Column.define("Description",
                   em.builtin_types.markdown,
                   nullok=False,
                   comment="A short description of the collection. This value will be used for DOI metadata.",
                   ),
  em.Column.define('Details',
                   em.builtin_types.markdown,
                   comment="Additional details. This value will NOT be used for DOI metadata.",
                   ),
  em.Column.define('Require_DOI?',
                   em.builtin_types.boolean,
                   comment="True/Yes if a DOI is required (recommended if the collection will be cited in a publication). A DOI will be generated after the Collection is Released. Default is False/No.",
                   default='false',
                   annotations={
                     "tag:isrd.isi.edu,2016:column-display": {
                       "*": {
                         "pre_format": {
                           "bool_true_value": "Yes",
                           "bool_false_value": "No",
                           "format": "%t"
                         }
                       }
                     }
                   }
                   ),
  em.Columns.define("Persistend_ID",
                    em.builtin_types.text,
                    annotations={
                      "tag:isrd.isi.edu,2016:column-display": {
                        "*": {
                          "markdown_pattern": "[{{{Persistent_ID}}}]({{{Persistent_ID}}})"
                        }
                      },
                      "tag:isrd.isi.edu,2016:generated": 'null'
                    }
                    )
]

table_def = em.Table.define(
    table_name,
    column_defs,
    key_defs=key_defs,
    fkey_defs=fkey_defs,
    comment= table_comment,
    acls=acls,
    acl_bindings=acl_bindings,
    annotations=annotations,
    provide_system=True
)

def create_table(server):
    credential = get_credential(server)
    catalog = ErmrestCatalog('https', server, 1, credentials=credential)
    model_root = catalog.getCatalogModel()
    schema = model_root.schemas['Common']
    table = schema.create_table(catalog, table_def)
