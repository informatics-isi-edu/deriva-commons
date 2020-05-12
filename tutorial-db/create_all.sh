#!/bin/sh

usage="Usage: $0 [-a] [-e] [-r] [-u] [-w] [-d dir] [-c catalog_number] [-x authn_opts] [-h] [-H] hostname
-e: create empty catalog
-r: load records into catalog
-u: upload files into catalog
-a: all catalog operations (shorthand for -c -r -u). Add -H to also initialize hatrac.
-w: create writable catalog (when specified with -a or -e)
-d dir: specify directory with files to upload (required if -a or -u is specified)
-c catalog_number: catalog number to operate on (required if neither -a nor -e is specified)
-H: initialize hatrac namespaces
-x authn_opts: options to pass to deriva cli progs for authentication
-h: print this message
"

create_catalog=false
load_records=false
upload_files=false
create_hatrac=false
dir=
catalog=
writable=
hostname=
authn_opts=

acl_config=acl_config_readonly.json

while getopts 'aeruhd:c:x:' opt; do
    case $opt in
	(a)
	    create_catalog=true
	    load_records=true
	    upload_files=true
	    ;;
	(e)
	    create_catalog=true
	    ;;
	(r)
	    load_records=true
	    ;;
	(u)
	    upload_files=true
	    ;;
	(w)
	    writable=true
	    acl_config=acl_config_writable.json	    
	    ;;
	(d)
	    upload_dir=$OPTARG
	    ;;
	(c)
	    catalog=$OPTARG
	    ;;
	(H)
	    create_hatrac=true
	    ;;
	(x)
	    authn_opts="$OPTARG"
	    ;;
	(*)
	    echo "$usage"
	    exit 1
	    ;;
    esac
done

shift $((OPTIND-1))

if [ $# -lt 1 -o $# -gt 2 ]; then
    echo "$usage"
    exit 1
fi

hostname=$1; shift
if [ $# -ge 1 ]; then
    dir=$1; shift
fi

if [ -z $create_catalog ]; then
    if [ -z $catalog ]; then
	echo "must specify a catalog number if not creating a new catalog"
	exit 1
    fi
    if [ ! -z $writable ]; then
	echo "-w option can only be used when creating a new catalog"
	exit 1
    fi
else
    if [ ! -z $catalog  ]; then
	echo "ignoring -c option because not creating a catalog"
    fi
fi

if [[ ( -z dir) &&  (-z $upload_files) ]]; then
    echo "must specify a directory when uploading files"
    exit 1
fi

if [[ ! -z $dir && -z $upload_files ]]; then
    echo "ignoring -d option because not uploading files"
fi

if [[ ! -z $extra_upload_options && -z $upload_files ]]; then
    echo "ignoring -x option because not uploading files"
fi

if [ "$create_catalog" == true ]; then
    catalog=`python3 create_demo_catalog.py $authn_opts $hostname`
    if [[ ! $catalog =~ ^[0-9]+$ ]]; then
	echo "create catalog failed"
	exit 1
    fi
    deriva-acl-config --host $hostname --config-file $acl_config $authn_opts $catalog
    deriva-annotation-config --host $hostname --config-file annotation_config.json  $authn_opts $catalog
    echo "created catalog $catalog"
fi

if [ "$create_hatrac" == true ]; then
    sh hatrac-init.sh -x "$authn_opts" $hostname
    echo "created hatrac namespaces on $hostname"
fi
    

if [ $load_records == true ]; then
    python3 load_tables.py $authn_opts --all $hostname $catalog
    echo "populated tables in catalog $catalog on host $hostname"    
fi

if [ $upload_files == true ]; then
    deriva-upload-cli $authn_opts $hostname $dir
    echo "uploaded files to $hostname"
fi
