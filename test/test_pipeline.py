import logging
import os
import tempfile

import qc18SV4.pipeline as pipeline_18SV4


logging.basicConfig(level=logging.DEBUG)


def test_get_reverse_fp():
    reverse_fp = pipeline_18SV4.get_reverse_reads_fp(forward_reads_fp='/a/b/c_d_L001_R1_001.fastq')
    assert reverse_fp == '/a/b/c_d_L001_R2_001.fastq'


def test_get_reads_filename_prefix():
    with tempfile.TemporaryDirectory() as work_dir:
        prefix = get_pipeline(work_dir=work_dir).get_reads_filename_prefix(forward_reads_fp='/a/b/c_d_L001_R1_001.fastq')
        assert prefix == 'c_d'


def get_pipeline(
        work_dir,
        forward_reads_fp='unittest_L001_R1.fastq',
        forward_primer=None,
        reverse_primer=None,
        prefix_regex=r'^(?P<prefix>[a-zA-Z0-9_]+)_L001_R[12]',
        phred='33',
        **kwargs):
    return pipeline_18SV4.Pipeline(
        forward_reads_fp=forward_reads_fp,
        forward_primer=forward_primer, reverse_primer=reverse_primer,
        prefix_regex=prefix_regex,
        phred=phred,
        work_dp=work_dir,
        **kwargs)


def write_test_input(input_dir, file_name, content):
    fp = os.path.join(input_dir, file_name)
    with open(fp, 'wt') as input_file:
        input_file.write(content)
    return fp


def test_step_01_trim_primers():
    with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as work_dir:

        # a is phred64 score of 33 (high quality)
        forward_read = 'G'*100
        forward_qual = 'a'*100
        forward_reads_fp = write_test_input(
            input_dir=input_dir, file_name='unittest_L001_R1.fastq', content='@read_1 forward\n{}\n+\n{}\n'.format(forward_read, forward_qual))
        reverse_read = 'C'*100
        reverse_qual = 'a'*100
        write_test_input(
            input_dir=input_dir, file_name='unittest_L001_R2.fastq', content='@read_1 reverse\n{}\n+\n{}\n'.format(reverse_read, reverse_qual))

        output_dir = get_pipeline(
            work_dir=work_dir,
            forward_reads_fp=forward_reads_fp,
            forward_primer='A'*30,
            reverse_primer='T'*30,
            trimmomatic_minlen=4
        ).step_01_trim_primers()

        assert os.path.exists(output_dir)
        assert os.path.isdir(output_dir)

        output_file_list = sorted(os.listdir(output_dir))
        print(output_file_list)
        assert len(output_file_list) == 5

        forward_output_fp = os.path.join(output_dir, output_file_list[1])
        with open(forward_output_fp, 'rt') as forward_output:
            assert forward_output.read() == '@read_1 forward\n{}\n+\n{}\n'.format(forward_read, forward_qual)

        reverse_output_fp = os.path.join(output_dir, output_file_list[3])
        with open(reverse_output_fp, 'rt') as reverse_output:
            assert reverse_output.read() == '@read_1 reverse\n{}\n+\n{}\n'.format(reverse_read, reverse_qual)


def test_step_02_join_paired_end_reads():
    """
    Output from fastq-join will be three files:
        'unittest.trim.join.fastq', 'unittest.trim.un1.fastq', 'unittest.trim.un2.fastq'

    """
    with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as work_dir:

        write_test_input(input_dir=input_dir, file_name='unittest.trim1p.fastq', content='@read_1 forward\n{}\n+\n{}\n'.format('A'*100, 'a'*100))
        write_test_input(input_dir=input_dir, file_name='unittest.trim2p.fastq', content='@read_1 reverse\n{}\n+\n{}\n'.format('T'*100, 'a'*100))

        output_dir = get_pipeline(
            work_dir=work_dir
        ).step_02_join_paired_end_reads(input_dir=input_dir)

        assert os.path.exists(output_dir)
        assert os.path.isdir(output_dir)

        output_file_list = sorted(os.listdir(output_dir))
        assert len(output_file_list) == 3
        assert output_file_list[0] == 'unittest.trim.join.fastq'
        assert output_file_list[1] == 'unittest.trim.un1.fastq'
        assert output_file_list[2] == 'unittest.trim.un2.fastq'


def test_step_03_quality_filter():
    with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as work_dir:
        write_test_input(input_dir=input_dir, file_name='unittest.trim.join.fastq', content='@read_1 joined\n{}\n+\n{}\n'.format('A'*100, 'a'*100))

        output_dir = get_pipeline(
            work_dir=work_dir, phred='64'
        ).step_03_quality_filter(input_dir=input_dir)

        assert os.path.exists(output_dir)
        assert os.path.isdir(output_dir)

        output_file_list = sorted(os.listdir(output_dir))
        assert len(output_file_list) == 1

        assert output_file_list[0] == 'unittest.trim.join.quality.fastq'


def test_step_04_fasta_format():
    with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as work_dir:
        write_test_input(input_dir=input_dir, file_name='unittest.trim.join.quality.fastq', content='@read_1\n{}\n+\n{}\n'.format('A'*100, 'a'*100))

        output_dir = get_pipeline(
            work_dir=work_dir
        ).step_04_fasta_format(input_dir=input_dir)

        assert os.path.exists(output_dir)
        assert os.path.isdir(output_dir)

        output_file_list = sorted(os.listdir(output_dir))
        assert len(output_file_list) == 1
        assert output_file_list[0] == 'unittest.trim.join.quality.fasta'


def test_step_05_length_filter():
    with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as work_dir:
        write_test_input(input_dir=input_dir, file_name='unittest.trim.join.quality.fasta', content='>read_1\n{}\n'.format('A'*100))

        output_dir = get_pipeline(
            work_dir=work_dir
        ).step_05_length_filter(input_dir=input_dir)

        assert os.path.exists(output_dir)
        assert os.path.isdir(output_dir)

        output_file_list = sorted(os.listdir(output_dir))
        assert len(output_file_list) == 1
        assert output_file_list[0] == 'unittest.trim.join.quality.length.fasta'


def test_step_06_rewrite_sequence_ids():
    with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as work_dir:
        write_test_input(input_dir=input_dir, file_name='unittest.quality.fasta', content='>1\n{}\n'.format('A'*100))

        output_dir = get_pipeline(
            work_dir=work_dir
        ).step_06_rewrite_sequence_ids(input_dir=input_dir)

        assert os.path.exists(output_dir)
        assert os.path.isdir(output_dir)

        output_file_list = sorted(os.listdir(output_dir))
        assert len(output_file_list) == 1
        assert output_file_list[0] == 'unittest.quality.id.fasta'

        with open(os.path.join(output_dir, output_file_list[0]), 'rt') as output_file:
            assert output_file.readlines()[0] == '>unittest_1\n'
