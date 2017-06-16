import os
import shutil

import pytest

from qc18SV4.write_launcher_job_file import get_file_path_pairs, get_cores_per_job, write_launcher_job_file


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


def test_get_cores_per_job():
    one_node = {
        'slurm_job_num_nodes': 1,
        'slurm_ntasks': 1,
        'slurm_job_cpus_per_node': 16,
        'slurm_tasks_per_node': 16
    }
    assert get_cores_per_job(job_count=1, **one_node) == 16
    assert get_cores_per_job(job_count=2, **one_node) == 8
    assert get_cores_per_job(job_count=3, **one_node) == 5
    assert get_cores_per_job(job_count=4, **one_node) == 4
    assert get_cores_per_job(job_count=5, **one_node) == 4
    assert get_cores_per_job(job_count=6, **one_node) == 4

    # TODO: more than one node results in unreasonable choices
    # for example 10 cores for each of 3 jobs is not feasible I think
    two_nodes = {
        'slurm_job_num_nodes': 2,
        'slurm_ntasks': 1,
        'slurm_job_cpus_per_node': 16,
        'slurm_tasks_per_node': 16
    }
    assert get_cores_per_job(job_count=1, **two_nodes) == 32
    assert get_cores_per_job(job_count=2, **two_nodes) == 16
    assert get_cores_per_job(job_count=3, **two_nodes) == 10
    assert get_cores_per_job(job_count=4, **two_nodes) == 8
    assert get_cores_per_job(job_count=5, **two_nodes) == 6


def test_write_launcher_job_file():
    os.environ['SLURM_JOB_NUM_NODES'] = str(1)
    os.environ['SLURM_NTASKS'] = str(8)
    os.environ['SLURM_JOB_CPUS_PER_NODE'] = str(16)
    os.environ['SLURM_TASKS_PER_NODE'] = str(16)

    here = os.path.dirname(__file__)
    test_data_dir = os.path.join(here, 'data')
    functional_test_dir = os.path.join(here, '_functional_test_job_file')
    shutil.rmtree(functional_test_dir, ignore_errors=True)
    os.mkdir(functional_test_dir)

    write_launcher_job_file(
        os.path.join(functional_test_dir, '_functional_test_job_file'),
        test_data_dir,
        'unit-test-work-{prefix}')
