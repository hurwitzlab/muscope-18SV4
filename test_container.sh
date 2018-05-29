#!/bin/bash

rm -rf test/output_container
mkdir test/output_container

time singularity run stampede2/muscope-18SV4.img \
  --forward-reads-fp ./test/data/Test01_L001_R1_001.fastq \
  --work-dp ./test/output_container/work \
  --core-count 2 \
  --phred 33 \
  --prefix-regex "^(?P<prefix>[a-zA-Z0-9_]+)_L001_R[12]"
