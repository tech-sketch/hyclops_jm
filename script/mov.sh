#!/bin/bash

USER=$1
DIR=$2
LIST=`find . -type f`

for d in `find . -type d`
do
	mkdir -p $DIR/$d
done

for f in `find . -type f`
do
	if [ "$f" != "./mov.sh" ]
	then
		echo $f
		sed 's/OSSLUSER/'$USER'/g' $f > $DIR/$f
	fi
done


