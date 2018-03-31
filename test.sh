#!/bin/bash
set -e

SC=sc
CS=cs

function cleanup {
	rm -r -f "$SC" "$CS"
}

function assert {
	diff /proc/self/fd/0 <(echo -en "$1")
}

mkfifo "$SC" "$CS"
trap cleanup EXIT


pblock-srv -r "$CS" -w "$SC" ./test/test_file.txt &
pblock-cat -r "$SC" -w "$CS" | assert '0123456789\n'
wait

pblock-srv -r "$CS" -w "$SC" ./test/test_file.txt &
pblock-cat -r "$SC" -w "$CS" -b3 -s2 -c5 | assert '23456'
wait
