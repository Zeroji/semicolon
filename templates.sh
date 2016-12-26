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

# generate translation file, update only if different
gen () { # gen(input, output)
  tmp="/tmp/`basename $2`.temp"
  # generate temporary translation
  xgettext $FLAGS -o "$tmp" "$1"
  # check file existence and non-emptiness, compare with original, ignore POT-Creation-Date tag
  if [[ -s "$tmp" ]] && ! diff -I "POT-Creation-Date" "$tmp" "$2" > /dev/null ; then
    cp "$tmp" "$2"
    echo "Generated translation file $2"
  fi
  # remove temporary file
  rm -f "$tmp"
}

for cog in `find cogs -name "*.py"`; do
  cutpath=`echo $cog | cut -d/ -f2- | rev | cut -d. -f2- | rev`
  mkdir -p $dest`dirname $cutpath`
  gen $cog $dest$cutpath".pot"
done

gen gearbox.py $dest"gearbox.pot"
