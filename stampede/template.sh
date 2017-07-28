#!/bin/bash

echo "Started $(date)"

sh run.sh ${INPUT_DIR} ${forward_primer} ${reverse_primer} ${prefix_regular_expression} ${phred} ${core_count}

echo "Ended $(date)"
exit 0
