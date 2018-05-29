#!/bin/bash -i

VENV_NAME=18SV4

#if [ -d "~/venv/${VENV_NAME}" ]; then
  rm -rf ~/venv/${VENV_NAME}
#fi

# there is a problem with VirtualBox shared filesystems
# that prevents a Python virtual environment from being created
# in a host directory
# so use ~/venv/${VENV_NAME}

python3 -m venv ~/venv/${VENV_NAME}
source ~/venv/${VENV_NAME}/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools wheel

pip install -e .[test]
