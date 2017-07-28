#!/bin/bash

module load singularity

echo "starting directory : `pwd`"
echo "`ls -l`"
echo "arguments: $@"

export LAUNCHER_DIR="$HOME/src/launcher"
export LAUNCHER_PLUGIN_DIR=$LAUNCHER_DIR/plugins
#export LAUNCHER_WORKDIR=${OUTPUT_DIR}
export LAUNCHER_WORKDIR=`pwd`
export LAUNCHER_RMI=SLURM

export LAUNCHER_JOB_FILE=`pwd`/${SLURM_JOB_ID}_launcher_jobfile
echo ${LAUNCHER_JOB_FILE}

xz --decompress --force muscope-18SV4.img.xz
singularity exec muscope-18SV4.img write_launcher_job_file -j ${LAUNCHER_JOB_FILE} -w `pwd` $@
sleep 10
export LAUNCHER_PPN=2

$LAUNCHER_DIR/paramrun
echo "Ended launcher"
