#!/bin/bash

mkdir -p "$1"/owl "$1"/sql

"$1"/parse_owl_ocdm.py -i "$1"

