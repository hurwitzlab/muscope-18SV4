#!/bin/bash

source activate mu18SV4

echo "starting directory: `pwd`"

BIN=$( cd "$( dirname "$0" )" && pwd )

echo "BIN=${BIN}"

LAUNCHER_JOBFILE=${SLURM_JOB_ID}_launcher_jobfile
echo ${LAUNCHER_JOBFILE}
python write_launcher_job_file.py -i $1 -j ${LAUNCHER_JOBFILE} -w ${SCRATCH}/work-${SLURM_JOB_ID}-{prefix}

echo "Starting launcher"
echo "  SLURM_JOB_NUM_NODES=$SLURM_JOB_NUM_NODES"
echo "  SLURM_NTASKS=$SLURM_NTASKS"
echo "  SLURM_JOB_CPUS_PER_NODE=$SLURM_JOB_CPUS_PER_NODE"
echo "  SLURM_TASKS_PER_NODE=$SLURM_TASKS_PER_NODE"

export LAUNCHER_DIR="$HOME/src/launcher"
export LAUNCHER_PLUGIN_DIR=$LAUNCHER_DIR/plugins
export LAUNCHER_WORKDIR=$SCRATCH/muscope-18SV4
export LAUNCHER_RMI=SLURM
export LAUNCHER_JOB_FILE=$BIN/${LAUNCHER_JOBFILE}
export LAUNCHER_NJOBS=$(cat ${LAUNCHER_JOBFILE} | wc -l)
export LAUNCHER_NHOSTS=$SLURM_JOB_NUM_NODES
export LAUNCHER_NPROCS=$SLURM_JOB_NUM_NODES
export LAUNCHER_PPN=1
export LAUNCHER_SCHED=dynamic

echo "  LAUNCHER_NJOBS=$LAUNCHER_NJOBS"
echo "  LAUNCHER_NHOSTS=$LAUNCHER_NHOSTS"
echo "  LAUNCHER_NPROCS=$LAUNCHER_NPROCS"
echo "  LAUNCHER_PPN=$LAUNCHER_PPN"

$LAUNCHER_DIR/paramrun
echo "Ended launcher"

