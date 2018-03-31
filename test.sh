#!/bin/bash
set -e

cd test

for FILE in $(ls *.yml); do
	echo "running $FILE"
	pgspawn "$FILE"
done
