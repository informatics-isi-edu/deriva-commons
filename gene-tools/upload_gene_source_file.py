from deriva.core import DerivaServer, get_credential, HatracStore
from deriva.core.utils import hash_utils
from deriva.core.datapath import DataPathException
from gene_utils import GeneUtils
import re
from urllib import request, parse
from pathlib import Path

def main(gu, species, source_url, hatrac_parent, skip_hatrac):
    hatrac_server = HatracStore('https', gu.host, gu.credential)

    # fetch source file and write it to scratch
    src = request.urlopen(source_url)
    filename = re.sub('.*/', '', source_url)
    parent = Path(gu.scratch_directory) / 'raw'
    parent.mkdir(parents=True, exist_ok=True)
    scratchpath = parent / filename
    scratchfile = scratchpath.open(mode='wb')

    while True:
        buf = src.read(102400)
        if len(buf) < 1:
            break
        scratchfile.write(buf)

    # get species id from name
    raw_species_table = gu.model.table(gu.species_schema, gu.species_table)
    name_col = gu.find_column_case_match(raw_species_table, 'Name')
    id_col = gu.find_column_case_match(raw_species_table, 'ID')
    species_table = gu.pb.schemas[gu.species_schema].tables[gu.species_table]
    rows=species_table.filter(species_table.column_definitions[name_col]==species).entities()
    species_id = rows[0][id_col]
    
    # upload and add record to catalog
    if not skip_hatrac:
        desturl = hatrac_parent + '/' + parse.quote(species_id) + '/' + parse.quote(filename)
        print(desturl)
        url = hatrac_server.put_obj(desturl, scratchpath, parents=True)
        table = gu.pb.schemas.get(gu.source_file_schema).tables[gu.source_file_table]
        record = {
            'Species' : species_id,
            'Downloaded_From' : source_url,
            'File_Name': filename,
            'File_URL' : url,
            'File_Bytes' : scratchpath.stat().st_size,
            'File_MD5' : hash_utils.compute_file_hashes(str(scratchpath), hashes=['md5'])['md5'][0]
        }
        
        try:
            table.insert([record])
        except DataPathException:
            table.update([record], ['Species'])

    # output the name of the scratch file that was created
    print(str(scratchpath))

if __name__ == '__main__':
    cli = GeneUtils.create_parser("gene table creation tool")
    cli.parser.add_argument('--skip-hatrac', help="don't upload source file to hatrac", action='store_true')    
    cli.parser.add_argument('species', help='species name, e.g. "Homo sapiens"')
    cli.parser.add_argument('source_url', help='url of file to fetch and upload')
    cli.parser.add_argument('hatrac_parent', help='hatrac namespace in which to create object (typically /hatrac/some/path)')
    args = cli.parse_cli()
    gu = GeneUtils(args)
    main(gu, args.species, args.source_url, args.hatrac_parent, args.skip_hatrac)
        
