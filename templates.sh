#!/bin/bash
# Usage: ./templates.sh [locale folder]
# Finds all .py files in cogs/ and generates strings
# Dependencies: xgettext, find, echo, cut, rev, mkdir, bash

FLAGS="-L Python --from-code UTF-8"

dest='locale'
if [[ $# -eq 1 ]]; then
  dest=$1
fi

dest=$dest"/templates/"

for cog in `find cogs -name "*.py"`; do
  cutpath=`echo $cog | cut -d/ -f2- | rev | cut -d. -f2- | rev`
  mkdir -p $dest`dirname $cutpath`
  xgettext $FLAGS -o $dest$cutpath".pot" $cog
done

xgettext $FLAGS -o $dest"gearbox.pot" gearbox.py
