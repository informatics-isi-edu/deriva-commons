if [ $# != 1 ]; then
    echo "Usage: $0 db"
    exit 1
fi

db=$1

psql -f chado_data_commons_schema.sql $db
psql -f functions_and_triggers.sql $db
psql -f domain_table_functions.sql $db
psql -f chado_to_data_commons.sql $db
max=`psql -t -c "select max(cvterm_relationship_id) from cvterm_relationship" $db`
low=-1
increment=1000
high=$((low + increment))

while [ $high -lt $max ]; do
    cat <<EOF
insert into data_commons.cvterm_relationship (type_dbxref, subject_dbxref, object_dbxref)
  select
  data_commons.chado_dbxref_id_to_dbxref(t.dbxref_id),
  data_commons.chado_dbxref_id_to_dbxref(s.dbxref_id),
  data_commons.chado_dbxref_id_to_dbxref(o.dbxref_id)
from public.cvterm_relationship r
join public.cvterm t on t.cvterm_id = r.type_id
join public.cvterm s on s.cvterm_id = r.subject_id
join public.cvterm o on o.cvterm_id = r.object_id
where r.cvterm_relationship_id > $low and r.cvterm_relationship_id <= $high
on conflict(type_dbxref, subject_dbxref, object_dbxref) do update set cv = EXCLUDED.cv;
analyze data_commons.cvterm_relationship;
EOF
    ((low=high))
    ((high=high+increment))
done | psql $db

psql $db <<EOF
  select _ermrest.model_change_event();
  vacuum analyze;
EOF
