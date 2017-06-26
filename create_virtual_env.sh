#!/bin/bash -i

VENV_NAME=18SV4

#if [ -d "~/miniconda3/envs/${VENV_NAME}" ]; then
  conda remove -y -n ${VENV_NAME} --all
#fi

# there is a problem with VirtualBox shared filesystems
# that prevents a Python virtual environment from being created
# in a host directory

conda create -y -n ${VENV_NAME} python=2.7
source activate ${VENV_NAME}
conda update conda
conda update pip

# install numpy explicitly or biom-format will not install
conda install -y numpy=1.11

pip install -e .[test]
