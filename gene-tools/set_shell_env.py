from gene_utils import GeneUtils
import json
from pathlib import Path
from string import Template
import shutil


def main(args):
    gu = GeneUtils(args)
    print(gu.shell_attr_string)

if __name__ == "__main__":
    cli = GeneUtils.create_parser("Usage: eval `python3 set_shell_env.py`")
    args = cli.parse_cli()
    main(args)
                            
