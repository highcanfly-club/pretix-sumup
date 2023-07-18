#!/bin/bash
NS=pretix
DBFILE="db.sqlite3"
DB="/data/$DBFILE"
POD=$(kubectl -n $NS get pods | grep "pretix-" | cut -d' ' -f1)
kubectl cp $NS/$POD:$DB $DBFILE