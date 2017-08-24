# muscope-18SV4

[![Build Status](https://travis-ci.org/hurwitzlab/muscope-18SV4.svg?branch=develop)](https://travis-ci.org/hurwitzlab/muscope-18SV4)

A CyVerse application implementing "Microbial eukaryotic 18S tag-sequence processing/QC - V4 region" as described by https://www.protocols.io/view/microbial-eukaryotic-18s-tag-sequence-processing-q-g33byqn.

## Usage

This pipeline can be used in three ways:

  + as a [Python](https://www.python.org/) application (local or remote)
  + as a [Singularity](http://singularity.lbl.gov/) container (local or remote)
  + as a [CyVerse](http://www.cyverse.org/) application (remote)

In all cases the following command line arguments must be specified:

  #### -f FORWARD_READS_FP
  File path to a FASTQ file of forward reads. The corresponding file of reverse reads should also be in the same directory.

  #### -w WORK_DP
  Directory path for all output. The work directory will be created if it does not exist.

  #### -c CORE_COUNT
  Number of cores to use. Specify at least 1.

  #### -p PREFIX_REGEX
  Regular expression that will match the forward and reverse read file prefix. For example `^(?P<prefix>[a-zA-Z0-9_]+)_L001_R[12]` will identify 'Test001' as the prefix in the file name 'Test001_L001_R1_001.fastq'. Use a regular expression tool such as [Pythex](https://pythex.org/) to verify your regular expression will work with your files.

  #### --forward-primer
  Forward primer to be removed.
  
  #### --reverse-primer
  Reverse primer to be removed.
  
  #### --min-overlap
  Minimum overlap for joining paired end reads.
    
  #### --phred
  PHRED format of the input files. Specify 33 or 64.

## Python Application

### Requirements

Installing and running this pipeline as a simple application requires

  + Python 3.6 or later
  + [Trimmomatic](http://www.usadellab.org/cms/index.php?page=trimmomatic)
  + [fastq-join](https://expressionanalysis.github.io/ea-utils/)
  + [FASTX-Toolkit](http://hannonlab.cshl.edu/fastx_toolkit/)

### Installation

It is recommended that a the Python application be installed in a Python virtual environment. If Python 3.6 or later is available then a virtual environment can be created like this:

```
$ python3 -m venv mu
$ source mu/bin/activate
(mu) $ pip install git+https://github.com/hurwitzlab/muscope-18SV4.git
```
The last line installs the application in the virtual environment.


If Python 3.6 or later is not available then the Anaconda Python distribution can be installed to provide Python 3.6 and a virtual environment can be created like this:

```
$ conda create -n mu numpy
$ source activate mu
(mu) $ pip install git+https://github.com/hurwitzlab/muscope-18SV4.git
```
The last line installs the application in the virtual environment.

### Usage

Once the Python application has been installed it can be run from the command line like this:

```
(mu) $ pipeline
usage: pipeline [-h] -f FORWARD_READS_FP -w WORK_DP -c CORE_COUNT -p
                PREFIX_REGEX [--forward-primer FORWARD_PRIMER]
                [--reverse-primer REVERSE_PRIMER] [--min-overlap MIN_OVERLAP]
                [--phred PHRED]
```

## Singularity Container

### Requirements

Building the Singularity container requires sudo permissions on a Linux system, Singularity 2.3 or later, and make.

Simply using the Singularity container requires no special permissions but does require Singularity 2.3 or later.

### Building the Singularity Container

```
$ git clone https://github.com/hurwitzlab/muscope-18SV4.git
$ cd muscope-18SV4
$ make container
```

The container will be built in the `muscope18SV4/singularity` directory.

### Usage

The pipeline program can be executed from the Singularity container like this:

```
$ singularity exec singularity/muscope-18SV4.img pipeline
```

The command line arguments are the same as for the stand-alone Python program.


## CyVerse Application

### Requirements

Using the CyVerse app requires a CyVerse account and membership in the muSCOPE
group.

