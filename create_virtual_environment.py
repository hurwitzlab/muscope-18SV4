#!/bin/env/python3
import argparse
import os
import subprocess


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('--name', default='qc18SV4',
    help='name for the new virtual environment')
arg_parser.add_argument('--conda', default=False, action='store_true',
    help='create a virtual environment using Miniconda3')
args = arg_parser.parse_args()

print(args)

if args.conda:
    conda_create = subprocess.run(
        'conda create -y -n {} python=3.6'.format(args.name),
        stdout=subprocess.PIPE
    )
    print(conda_create.stdout)
    conda_info_envs = subprocess.run('conda info --envs', stdout=subprocess.PIPE)
    env_path = [
        line.strip().split()[-1]
        for line
        in conda_info_envs.stdout.splitlines()
        if line.startswith(args.name)
    ][0]
else:
    os.makedirs(os.path.expanduser('~/venv'))
    subprocess.run('python3 -m venv ~/venv/{}'.format(args.name))
