#!/bin/bash

echo "Started $(date)"

sh run.sh ${INPUT_DIR} `pwd`

echo "Ended $(date)"
exit 0
