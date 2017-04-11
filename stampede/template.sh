#!/bin/bash

echo "Started $(date)"

inputDir=${INPUT_DIR}
echo "input directory: ${inputDir}"

sh run.sh ${inputDir} `pwd`

echo "Ended $(date)"
exit 0
