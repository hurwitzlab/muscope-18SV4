#!/bin/bash

source activate mu18SV4

echo "starting directory: `pwd`"

INPUT_DIR=$1
OUTPUT_DIR=$2

echo "input directory: ${INPUT_DIR}"
echo "output directory: ${OUTPUT_DIR}"
#BIN=$( cd "$( dirname "$0" )" && pwd )
#echo "BIN=${BIN}"

#echo "Starting launcher"
#echo "  SLURM_JOB_NUM_NODES=$SLURM_JOB_NUM_NODES"
#echo "  SLURM_NTASKS=$SLURM_NTASKS"
#echo "  SLURM_JOB_CPUS_PER_NODE=$SLURM_JOB_CPUS_PER_NODE"
#echo "  SLURM_TASKS_PER_NODE=$SLURM_TASKS_PER_NODE"

export LAUNCHER_DIR="$HOME/src/launcher"
export LAUNCHER_PLUGIN_DIR=$LAUNCHER_DIR/plugins
export LAUNCHER_WORKDIR=${OUTPUT_DIR}
export LAUNCHER_RMI=SLURM

export LAUNCHER_JOB_FILE=`pwd`/${SLURM_JOB_ID}_launcher_jobfile
echo ${LAUNCHER_JOB_FILE}
python write_launcher_job_file.py -i ${INPUT_DIR} -j ${LAUNCHER_JOB_FILE} -w ${OUTPUT_DIR}/work-${SLURM_JOB_ID}-{prefix}
sleep 10
export LAUNCHER_PPN=2

$LAUNCHER_DIR/paramrun
echo "Ended launcher"

