#!/bin/bash
for f in *.txt; do
	mv  "$f" "$(echo "$f" | sed s/rnaseq-nfs/rnaseq-orig-nfs/)";
done

for f in *.csv; do
	mv  "$f" "$(echo "$f" | sed s/rnaseq-nfs/rnaseq-orig-nfs/)";
done
