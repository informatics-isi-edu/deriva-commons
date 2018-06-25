
# Data Modeling


## Model Element Naming

In ERMrest, model elements are named by the user. This includes
schema, table, column, and constraint names.

- Names are Unicode strings
   - The `0x0000` or NULL character is not allowed
   - The UTF-8 encoding of the string MUST NOT exceed 63 bytes
   - In ERMrest URLs, the UTF-8 names are URL "percent" encoded for safety
- Uniqueness requirements vary by model category
   - Schema names are unique within a catalog
   - Table names are unique within a schema
   - Column names are unique within a table
   - Constraint names are unique within the schema of the table they govern

### Display Names and Formatting

There are three options for naming model elements and configuring
their display names:

1. Use the exact display value you want to show to users.
   - Mixed capitalization
   - Whitespace and other punctation
   - Chaise can present the value unchanged
2. Use typical SQL style of underscore-separated, lower-case words
   - Chaise can be configured to replace underscore with space
   - Chaise can be configured to apply "title-casing" to each word
3. Configure two names
   - Use a lower-level SQL style or abbreviation in model
   - Use a display annotation to configure a separate display name

The first two options are the most common.  The first and last are
most flexible in allowing arbitrary display values, while the second
style is more limited in what can be displayed. For its proponents,
the second style has a benefit that the names can work as valid
identifiers in many programming languages, as well as providing
unsurprising column names in JSON and CSV data formats.

### Naming Conventions

Aside from the display-name and formatting choices above, we recommend
the following conventions for naming.

#### Table Naming Conventions

1. Entity tables
   - Name in singular
   - Presented to users in many display contexts
   - Usable as a "type" or "class" presentation qualifier
2. Association tables
   - Not usually presented directly to user
   - Use the pattern _left table_ `_` _right table_ e.g. `Experiment_Dataset`
   - The _left table_ is usually considered the more central table in the model

When embedding table names in an association table name, they should
be embedded verbatim, e.g. with identical casing, whitespace, and
punctation as in their constituent table names.

Exceptions for some esoteric cases with association tables:

- Very long table names may be abbreviated
- If table names are ambiguous, a schema name or other qualifier may be added

#### Constraint Naming Conventions

1. Key or uniqueness constraints
   - Not usually presented directly to user
   - Use the pattern _table_ `_` _columns_ `_key`
2. Foreign key reference constraints
   - Not usually presented directly to user
   - Use the pattern _table_ `_` _columns_ `_fkey`

In both cases, _columns_ is an underscore-separated list of column
names present in the table named by _table_ which is also the table
being constrained.

When embedding table and column names in an constraint name, they
should be embedded verbatim, e.g. with identical casing, whitespace,
and punctation as in their constituent source names.

Exceptions for some esoteric cases with constraints:

- Very long table names may be abbreviated
- If table names are ambiguous, a schema name or other qualifier may be added
- If several reference constraints govern the same columns, other
  qualifiers may be added

In some models, where the system is allowed to choose a default name,
other naming schemes may be witnessed:

- A primary key may have suffix `_pkey` instead of `_key`.
- When auto-generated names in ERMrest would collide, a suffix such as
  `_2` may be added to disambiguate.
- Very long auto-generated names in ERMrest may replace components
  with hash values to disambiguate.
