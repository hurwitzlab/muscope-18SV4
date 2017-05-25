import io
import os.path
import shutil

import pytest

from Bio import SeqIO

import qc18SV4.pipeline as pipeline


def test_get_reverse_fp():
    reverse_fp = pipeline.get_reverse_reads_fp(forward_reads_fp='/a/b/c_d_L001_R1_001.fastq')
    assert reverse_fp == '/a/b/c_d_L001_R2_001.fastq'


def test_get_reads_filename_prefix():
    prefix = pipeline.get_reads_filename_prefix(forward_reads_fp='/a/b/c_d_L001_R1_001.fastq')
    assert prefix == 'c_d'


def test__seq_length_cutoff_arguments_1():
    with pytest.raises(ValueError):
        pipeline.seq_length_cutoff(input_file=None, min_length=-1, max_length=1, output_file=None)


def test__seq_length_cutoff_arguments_2():
    with pytest.raises(ValueError):
        pipeline.seq_length_cutoff(input_file=None, min_length=2, max_length=1, output_file=None)


four_short_sequences_fasta = """\
>\nC\n\n
>\nCG\n\n
>\nCGC\n\n
>\nCGCG
"""

def test__seq_length_cutoff_1():
    input_buffer = io.BytesIO(four_short_sequences_fasta)
    output_buffer = io.BytesIO()
    pipeline.seq_length_cutoff(input_file=input_buffer, min_length=2, max_length=3, output_file=output_buffer)
    output_buffer.seek(0)
    filtered_sequences = tuple(SeqIO.parse(handle=output_buffer, format='fasta'))
    assert len(filtered_sequences) == 2
    assert filtered_sequences[0].seq == 'CG'
    assert filtered_sequences[1].seq == 'CGC'


def test__seq_length_cutoff_2():
    input_buffer = io.BytesIO(four_short_sequences_fasta)
    output_buffer = io.BytesIO()
    pipeline.seq_length_cutoff(input_file=input_buffer, min_length=2, max_length=2, output_file=output_buffer)
    output_buffer.seek(0)
    filtered_sequences = tuple(SeqIO.parse(handle=output_buffer, format='fasta'))
    assert len(filtered_sequences) == 1
    assert filtered_sequences[0].seq == 'CG'


def test_pipeline():
    here = os.path.dirname(__file__)
    test_data_dir = os.path.join(here, 'data')
    test_data_fp = os.path.join(test_data_dir, 'Test01_L001_R1_001.fastq')
    functional_test_dir = os.path.join(here, '_functional_test_pipeline')
    shutil.rmtree(functional_test_dir, ignore_errors=True)

    pipeline.pipeline(
        forward_reads_fp=test_data_fp,
        forward_primer='CCAGCASCYGCGGTAATTCC',
        reverse_primer='TYRATCAAGAACGAAAGT',
        uchime_ref_db_fp=os.path.join(test_data_dir, 'tiny_pr2_gb203_version_4.5.fasta'),
        work_dp_template=functional_test_dir,  # removed {prefix}
        core_count=4)

    assert os.path.exists(functional_test_dir)
    assert os.path.exists(os.path.join(functional_test_dir, 'join'))
    assert os.path.exists(os.path.join(functional_test_dir, 'join', 'fastqjoin.join.fastq'))
    assert os.path.exists(os.path.join(functional_test_dir, 'Test01_map.txt'))
    assert os.path.exists(os.path.join(functional_test_dir, 'split'))
    assert os.path.exists(os.path.join(functional_test_dir, 'split', 'seqs.fna'))
    assert os.path.exists(os.path.join(functional_test_dir, 'cut'))
    assert os.path.exists(os.path.join(functional_test_dir, 'cut', 'Test01.assembled.clipped.regF.fasta'))
    assert os.path.exists(os.path.join(functional_test_dir, 'cut', 'Test01.assembled.clipped.regR.fasta'))
    assert os.path.exists(os.path.join(functional_test_dir, 'cut', 'Test01.discard_regF.fasta'))
    assert os.path.exists(os.path.join(functional_test_dir, 'cut', 'tmp.fasta'))
    assert os.path.exists(os.path.join(functional_test_dir, 'cut', 'Test01.assembled.clipped.combined.fasta'))
    assert os.path.exists(os.path.join(functional_test_dir, 'cut', 'Test01.assembled.clipped.combined.len.fasta'))
