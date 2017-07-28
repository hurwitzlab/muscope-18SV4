#!/bin/bash

rm -rf test/container_output
mkdir test/container_output

time singularity run singularity/muscope-18SV4.img \
  --forward-reads-fp ./test/data/Test01_L001_R1_001.fastq \
  --work-dp ./test/container_output/work \
  --core-count 2 \
  --phred 33 \
  --prefix-regex "^(?P<prefix>[a-zA-Z0-9_]+)_L001_R[12]"
