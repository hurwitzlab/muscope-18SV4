# muscope-18SV4

[![Build Status](https://travis-ci.org/hurwitzlab/muscope-18SV4.svg?branch=develop)](https://travis-ci.org/hurwitzlab/muscope-18SV4)

A CyVerse application implementing "Microbial eukaryotic 18S tag-sequence processing/QC - V4 region" as described by https://www.protocols.io/view/microbial-eukaryotic-18s-tag-sequence-processing-q-g33byqn.

## Usage

This pipeline can be used in three ways:
  + as a [Python](https://www.python.org/) application (local or remote)
  + as a [Singularity](http://singularity.lbl.gov/) container (local or remote)
  + as a [CyVerse](http://www.cyverse.org/) application (remote)

## Requirements

Installing and running this pipeline as a simple application requires Python 3.5+,
[Trimmomatic](http://www.usadellab.org/cms/index.php?page=trimmomatic),
[fastq-join](https://expressionanalysis.github.io/ea-utils/), and
[FASTX-Toolkit](http://hannonlab.cshl.edu/fastx_toolkit/).

Installing and running this pipeline as a Singularity container requires only the
Singularity software and sudo permission on a Linux system.

Using the CyVerse app requires a CyVerse account and membership in the muSCOPE
group. Contact someone.

## Installation

```
$ cd muscope-18SV4
$ conda create -n mu18SV4 python=2.7 --channel=bioconda --file=requirements.txt
```

Install fastq-join this way:

```
$ conda install -c bioconda fastq-join=1.3.1
```

A vsearch executable is available from https://github.com/torognes/vsearch.
It will be necessary to add vsearch to the PATH environment variable.
A convenient location for the executable is /usr/bin on Linux operating systems.

Deploying the code as a CyVerse application requires the CyVerse SDK to be installed.


## Installation

Once the requirements are satisfied there is no further work needed to install the software.
