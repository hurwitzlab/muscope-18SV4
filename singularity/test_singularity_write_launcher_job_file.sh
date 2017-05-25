#!/bin/bash

INPUT_DIR=../test/data
OUTPUT_DIR=_dummy

LAUNCHER_JOB_FILE=_singularity_test_job_file
SLURM_JOB_ID=000

# write_launcher_job_file.py needs these
export SLURM_JOB_NUM_NODES=1
export SLURM_NTASKS=1
export SLURM_JOB_CPUS_PER_NODE=16
export SLURM_TASKS_PER_NODE=1

mkdir -p $OUTPUT_DIR

singularity exec muscope-18SV4.img write_launcher_job_file -i ${INPUT_DIR} -j ${LAUNCHER_JOB_FILE} -w ${OUTPUT_DIR}/work-${SLURM_JOB_ID}-{prefix}
wc -l $LAUNCHER_JOB_FILE
chmod u+x $LAUNCHER_JOB_FILE
./$LAUNCHER_JOB_FILE
