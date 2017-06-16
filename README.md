# muscope-18SV4

[![Build Status](https://travis-ci.org/hurwitzlab/muscope-18SV4.svg?branch=develop)](https://travis-ci.org/hurwitzlab/muscope-18SV4)

A CyVerse application implementing "Microbial eukaryotic 18S tag-sequence processing/QC - V4 region" as described by https://www.protocols.io/view/microbial-eukaryotic-18s-tag-sequence-processing-q-g33byqn.

## Requirements
This application uses Python 2.7, QIIME, fastq-join, and vsearch.
QIIME and additional Python dependencies should be installed in a Python 2 virtual environment.
Within the CyVerse application the virtual environment is called 'mu18SV4'.
Here is one way to create the necessary virtual environment using the Anaconda Python distribution:

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
