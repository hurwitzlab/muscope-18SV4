import io
import logging
import os
import shutil

import pytest

from Bio import SeqIO

import qc18SV4.pipeline as pipeline_18SV4


logging.basicConfig(level=logging.DEBUG)


def test_get_reverse_fp():
    reverse_fp = pipeline_18SV4.get_reverse_reads_fp(forward_reads_fp='/a/b/c_d_L001_R1_001.fastq')
    assert reverse_fp == '/a/b/c_d_L001_R2_001.fastq'


def test_get_reads_filename_prefix():
    prefix = pipeline_18SV4.get_reads_filename_prefix(forward_reads_fp='/a/b/c_d_L001_R1_001.fastq')
    assert prefix == 'c_d'


def test__seq_length_cutoff_arguments_1():
    with pytest.raises(ValueError):
        pipeline_18SV4.seq_length_cutoff(input_file=None, min_length=-1, max_length=1, output_file=None)


def test__seq_length_cutoff_arguments_2():
    with pytest.raises(ValueError):
        pipeline_18SV4.seq_length_cutoff(input_file=None, min_length=2, max_length=1, output_file=None)


def test_fastq_join_binary_fp():
    fastq_join_binary_fp = 'fastq-join-from-env-var'
    os.environ['FASTQ_JOIN'] = fastq_join_binary_fp
    pipeline = get_pipeline()
    assert pipeline.fastq_join_binary_fp == fastq_join_binary_fp
    del os.environ['FASTQ_JOIN']


four_short_sequences_fasta = """\
>\nC\n\n
>\nCG\n\n
>\nCGC\n\n
>\nCGCG
"""

def test__seq_length_cutoff_1():
    input_buffer = io.BytesIO(four_short_sequences_fasta)
    output_buffer = io.BytesIO()
    pipeline_18SV4.seq_length_cutoff(input_file=input_buffer, min_length=2, max_length=3, output_file=output_buffer)
    output_buffer.seek(0)
    filtered_sequences = tuple(SeqIO.parse(handle=output_buffer, format='fasta'))
    assert len(filtered_sequences) == 2
    assert filtered_sequences[0].seq == 'CG'
    assert filtered_sequences[1].seq == 'CGC'


def test__seq_length_cutoff_2():
    input_buffer = io.BytesIO(four_short_sequences_fasta)
    output_buffer = io.BytesIO()
    pipeline_18SV4.seq_length_cutoff(input_file=input_buffer, min_length=2, max_length=2, output_file=output_buffer)
    output_buffer.seek(0)
    filtered_sequences = tuple(SeqIO.parse(handle=output_buffer, format='fasta'))
    assert len(filtered_sequences) == 1
    assert filtered_sequences[0].seq == 'CG'


@pytest.mark.xfail(reason='not able to find fastq-join with Travis CI')
def test_pipeline(uchime_ref_db_fp):
    here = os.path.dirname(__file__)
    test_data_dir = os.path.join(here, 'data')
    test_data_fp = os.path.join(test_data_dir, 'Test01_L001_R1_001.fastq')
    functional_test_dir = os.path.join(here, '_functional_test_pipeline')
    shutil.rmtree(functional_test_dir, ignore_errors=True)



    assert not os.path.exists(functional_test_dir)

    pipeline_18SV4.Pipeline(
        forward_reads_fp=test_data_fp,
        forward_primer='CCAGCASCYGCGGTAATTCC',
        reverse_primer='TYRATCAAGAACGAAAGT',
        min_overlap=20,
        uchime_ref_db_fp=uchime_ref_db_fp,
        work_dp=functional_test_dir,  # removed {prefix}
        core_count=4).run()

    assert os.path.exists(functional_test_dir)
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_01_join_paired_end_reads'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_01_join_paired_end_reads', 'fastqjoin.join.fastq'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_02_split_libraries'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_02_split_libraries', 'Test01_map.txt'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_02_split_libraries', 'seqs.fna'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_03_cut_primers'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_03_cut_primers', 'Test01.assembled.clipped.regF.fasta'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_03_cut_primers', 'Test01.assembled.clipped.regR.fasta'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_03_cut_primers', 'Test01.discard_regF.fasta'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_03_cut_primers', 'tmp.fasta'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_04_combine_files', 'Test01.assembled.clipped.combined.fasta'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_05_length_filter', 'Test01.assembled.clipped.combined.len.fasta'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_06_remove_chimeras'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01', 'step_06_remove_chimeras', 'Test01.assembled.clipped.combined.len.nc.fasta'))


def get_pipeline(forward_reads_fp='',):
    return pipeline_18SV4.Pipeline(
        forward_reads_fp=forward_reads_fp,
        forward_primer='',
        reverse_primer='',
        min_overlap=0,
        uchime_ref_db_fp='',
        work_dp='',
        core_count=1
    )