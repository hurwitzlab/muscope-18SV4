#!/bin/bash

source activate mu18SV4

echo "starting directory: `pwd`"

BIN=$( cd "$( dirname "$0" )" && pwd )

echo "BIN=${BIN}"

#echo "Starting launcher"
#echo "  SLURM_JOB_NUM_NODES=$SLURM_JOB_NUM_NODES"
#echo "  SLURM_NTASKS=$SLURM_NTASKS"
#echo "  SLURM_JOB_CPUS_PER_NODE=$SLURM_JOB_CPUS_PER_NODE"
#echo "  SLURM_TASKS_PER_NODE=$SLURM_TASKS_PER_NODE"

export LAUNCHER_DIR="$HOME/src/launcher"
export LAUNCHER_PLUGIN_DIR=$LAUNCHER_DIR/plugins
export LAUNCHER_WORKDIR=$SCRATCH/muscope-18SV4
export LAUNCHER_RMI=SLURM

LAUNCHER_JOBFILE=${SLURM_JOB_ID}_launcher_jobfile
echo ${LAUNCHER_JOBFILE}
python write_launcher_job_file.py -i $1 -j ${LAUNCHER_JOBFILE} -w ${SCRATCH}/work-${SLURM_JOB_ID}-{prefix}

#$LAUNCHER_DIR/paramrun
echo "Ended launcher"

