"""
write_launcher_job_file.py
"""
import argparse
import glob
import os


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-j', '--job-fp', help='job file to be written')
    arg_parser.add_argument('-i', '--input-dp', help='directory of input files')
    arg_parser.add_argument('-w', '--work-dp-template', help='template for working directory')
    # remaining arguments ?
    args = arg_parser.parse_args()
    return args


def write_launcher_job_file(job_fp, input_dp, work_dp_template):

    forward_read_file_glob = os.path.join(input_dp, '*_R1_*')
    reverse_read_file_glob = os.path.join(input_dp, '*_R2_*')

    forward_read_file_path_set = glob.glob(forward_read_file_glob)
    reverse_read_file_path_set = glob.glob(reverse_read_file_glob)

    with open(job_fp, 'wt') as job_file:
        for forward_fp, reverse_fp in get_file_path_pairs(forward_read_file_path_set, reverse_read_file_path_set):
            print('python pipeline.py {} {}'.format(forward_fp, work_dp_template))


def get_file_path_pairs(forward_read_file_paths, reverse_read_file_paths):
    unpaired_forward_read_file_paths = set(forward_read_file_paths)
    unpaired_reverse_read_file_paths = set(reverse_read_file_paths)

    while len(unpaired_forward_read_file_paths) > 0:
        forward_read_fp = unpaired_forward_read_file_paths.pop()
        reverse_read_fp = forward_read_fp.replace('_R1_', '_R2_')
        if reverse_read_fp in unpaired_reverse_read_file_paths:
            unpaired_reverse_read_file_paths.remove(reverse_read_fp)
            yield forward_read_fp, reverse_read_fp
        else:
            raise Exception('failed to find reverse read file "{}"'.format(reverse_read_fp))

    if len(unpaired_reverse_read_file_paths) > 0:
        raise Exception('unpaired reverse read files remaining:\n{}'.format('\n'.join(unpaired_reverse_read_file_paths)))


if __name__ == '__main__':
    args = get_args()
    write_launcher_job_file(**args.__dict__)


import pytest


def test_get_file_path_pairs():

    forward_read_files = ('/a/b/c_R1_d.fa', '/e/f/g_R1_h.fa', '/i/j/k_R1_l.fa')
    reverse_read_files = ('/a/b/c_R2_d.fa', '/e/f/g_R2_h.fa', '/i/j/k_R2_l.fa')

    paired_files = set(
        get_file_path_pairs(
            forward_read_file_paths=forward_read_files,
            reverse_read_file_paths=reverse_read_files))

    assert len(paired_files) == 3
    assert ('/a/b/c_R1_d.fa', '/a/b/c_R2_d.fa') in paired_files
    assert ('/e/f/g_R1_h.fa', '/e/f/g_R2_h.fa') in paired_files
    assert ('/i/j/k_R1_l.fa', '/i/j/k_R2_l.fa') in paired_files


def test_get_file_path_pairs_forward_reads_exception():
    forward_read_files = ('/a/b/c_R1_d.fa', '/e/f/g_R1_h.fa')
    reverse_read_files = ('/a/b/c_R2_d.fa', '/e/f/g_R2_h.fa', '/i/j/k_R2_l.fa')

    with pytest.raises(Exception):
        paired_files = set(
            get_file_path_pairs(
                forward_read_file_paths=forward_read_files,
                reverse_read_file_paths=reverse_read_files))


def test_get_file_path_pairs_reverse_reads_exception():
    forward_read_files = ('/a/b/c_R1_d.fa', '/e/f/g_R1_h.fa', '/i/j/k_R1_l.fa')
    reverse_read_files = ('/a/b/c_R2_d.fa', '/e/f/g_R2_h.fa')

    with pytest.raises(Exception):
        paired_files = set(
            get_file_path_pairs(
                forward_read_file_paths=forward_read_files,
                reverse_read_file_paths=reverse_read_files))

