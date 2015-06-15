#!/bin/bash

RSC=""
if [ $# -eq 3 ]
then
  RSC="select {\$key \"$2:.*$3\"}"
elif [ ! $# -eq 1 ]
then
  echo "Usage: clean_bib.sh file.bib [conf short_year]"
  exit 1
fi

bibtool -r format $1 -- "$RSC" | \
  sed '/  author = /s/ and / andddd /g' | \
  sed 's/ andddd / and \n                  /g'
