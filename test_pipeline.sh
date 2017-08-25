#!/bin/bash

rm -rf test/output_pipeline
mkdir test/output_pipeline

time pipeline \
  --forward-reads-fp ./test/data/Test01_L001_R1_001.fastq \
  --work-dp ./test/output_pipeline/work \
  --core-count 2 \
  --phred 33 \
  --prefix-regex "^(?P<prefix>[a-zA-Z0-9_]+)_L001_R[12]"
