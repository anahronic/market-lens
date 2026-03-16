#!/usr/bin/env bash
set -e

BASE=~/projects/market-lens/var/queue

mkdir -p $BASE/pending
mkdir -p $BASE/processing
mkdir -p $BASE/completed
mkdir -p $BASE/failed

echo "Queue directories initialized:"
find $BASE -maxdepth 2 -type d | sort
