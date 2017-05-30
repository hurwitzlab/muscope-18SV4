# muscope-18SV4
A CyVerse app implementing "Microbial eukaryotic 18S tag-sequence processing/QC - V4 region" from protocols.io.

[![Build Status](https://travis-ci.org/hurwitzlab/muscope-18SV4.svg?branch=master)](https://travis-ci.org/hurwitzlab/muscope-18SV4)

## Requirements
This application uses QIIME, which is assumed to be installed in a Python 2 virtual environment called 'mu18SV4'. Here is one way to create the necessary virtual environment using the Anaconda Python distribution:

```
conda create -n mu18SV4 python=2.7 qiime matplotlib mock nose -c bioconda
```

In addition fastq-join and vsearch are required. An easy way to install fastq-join is this:

```
conda install -c bioconda fastq-join=1.3.1
```

It is not necessary to build vsearch from source. An executable is available from https://github.com/torognes/vsearch.
