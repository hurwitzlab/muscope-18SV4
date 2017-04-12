#!/bin/bash

#SBATCH -A iPlant-Collabs
#SBATCH -N 1
#SBATCH -n 16
#SBATCH -t 00:30:00
#SBATCH -p development
#SBATCH -J test-mu18SV4
#SBATCH --mail-type BEGIN,END,FAIL
#SBATCH --mail-user jklynch@email.arizona.edu

OUT_DIR="$SCRATCH/muscope-18SV4/test"

if [[ -d $OUT_DIR ]]; then
  rm -rf $OUT_DIR
fi

mkdir -p $OUT_DIR

./run.sh "$SCRATCH/muscope-18SV4/test-data/" $OUT_DIR
