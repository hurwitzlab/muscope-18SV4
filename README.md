# muscope-18SV4
A CyVerse app implementing "Microbial eukaryotic 18S tag-sequence processing/QC - V4 region" from protocols.io.


## Requirements
This application uses some QIIME installed in a Python 2 virtual environment called 'mu18SV4'. If the virtual environment
does not exist it can be created using conda:

```
conda create -n mu18SV4 python=2.7 qiime matplotlib mock nose -c bioconda
```

In addition fastq-join and vsearch are required. An easy way to install fastq-join is this:

```
conda install -c bioconda fastq-join=1.3.1
```

It is not necessary to build vsearch from source. An executable is available to download.
