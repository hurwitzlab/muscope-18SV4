"""
Create a virtual environment like this
    $ conda create -n mu18SV4 python=2.7 qiime matplotlib mock nose -c bioconda

It is also necessary to install fastq-join. On systems with apt this will work:
    $ apt install ea-utils

This script requires vsearch, which can be installed on Debian-based systems with apt.
    $ sudo apt update
    $ sudo apt install vsearch

This script handles one pair of paired-end files.



"""
import argparse
import io
import os
import re
import sys

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess

from Bio import SeqIO


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-f', '--forward-reads-fp', help='path to a forward-read FASTQ file')
    arg_parser.add_argument('-w', '--work-dp-template', help='template for working directory')
    args = arg_parser.parse_args()
    return args


def pipeline(forward_reads_fp, work_dp_template):

    reverse_reads_fp = get_reverse_reads_fp(forward_reads_fp)
    prefix = get_reads_filename_prefix(forward_reads_fp)
    work_dp = work_dp_template.format(prefix=prefix)

    joined_reads_fp = join_paired_ends(
        forward_fp=forward_reads_fp,
        reverse_fp=reverse_reads_fp,
        j=20,
        work_dp=work_dp)

    map_fp = create_map_file(
        prefix=prefix,
        work_dp=work_dp)

    split_fp = split_libraries_fastq(
        map_fp=map_fp,
        joined_reads_fp=joined_reads_fp,
        sample_ids=prefix,
        work_dp=work_dp)

    forward_clipped_fp, reverse_clipped_fp = cut_primers(
        prefix=prefix,
        forward_primer='CCAGCASCYGCGGTAATTCC',
        reverse_primer='TYRATCAAGAACGAAAGT',
        work_dp=work_dp,
        input_fp=split_fp)

    combined_clipped_fp = combine_files(forward_clipped_fp, reverse_clipped_fp)

    length_filtered_fp = combined_clipped_fp.replace('combined.fasta', 'combined.len.fasta')
    with open(combined_clipped_fp, 'rt') as combined_clipped_file, open(length_filtered_fp, 'wt') as length_filtered_file:
        seq_length_cutoff(
            input_file=combined_clipped_file,
            min_length=150,
            max_length=500,
            output_file=length_filtered_file)

    #(8) Chimera check with vsearch (uchime) using a reference database
    vsearch_dp = os.path.join(work_dp, 'vsearch')
    os.mkdir(vsearch_dp)
    vsearch_filename = os.path.basename(length_filtered_fp)
    uchimeout_fp = os.path.join(vsearch_dp, prefix + '.uchimeinfo_ref')
    chimeras_fp = os.path.join(vsearch_dp, prefix + '.chimeras_ref.fasta')
    final_fp = os.path.join(vsearch_dp, vsearch_filename)
    output = subprocess.check_call(
        ['vsearch',
         '--uchime_ref', length_filtered_fp,
         '--db', '/work/04658/jklynch/external_dbs/pr2_gb203_version_4.5.fasta',
         '--uchimeout', uchimeout_fp,
         '--chimeras', chimeras_fp,
         '--strand', 'plus',
         '--nonchimeras', final_fp],
        shell=True,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    print(output)


def get_reverse_reads_fp(forward_reads_fp):
    forward_dp, forward_filename = os.path.split(forward_reads_fp)
    reverse_filename = forward_filename.replace('_R1_', '_R2_')
    reverse_fp = os.path.join(forward_dp, reverse_filename)
    return reverse_fp


def get_reads_filename_prefix(forward_reads_fp):
    _, forward_filename = os.path.split(forward_reads_fp)
    m = re.search('(?P<prefix>[a-zA-Z0-9_]+)_L001_R[12]_001\.', forward_filename)
    if m is None:
        raise Exception('failed to parse filename "{}"'.format(forward_reads_fp))
    else:
        return m.group('prefix')


def create_map_file(prefix, work_dp):
    map_work_dp = os.path.join(work_dp, )
    map_filename = '{}_map.txt'.format(prefix)
    map_fp = os.path.join(map_work_dp, map_filename)
    with open(map_fp, 'wt') as map_file:
        map_file.write('#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tDescription\n')
        map_file.write('{}\tCCAG\tCASCYGCGGTAATTCC\t{}\n'.format(prefix, prefix))

    return os.path.abspath(map_fp)


def join_paired_ends(forward_fp, reverse_fp, work_dp, j):
    join_work_dp = os.path.join(work_dp, 'join')
    print('begin joined paired ends step')
    output = subprocess.check_output([
        'join_paired_ends.py',
        '-f', forward_fp,
        '-r', reverse_fp,
        '-o', join_work_dp,
        '-j', str(j)],
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    print(output)
    print('end joined paired ends step')

    joined_reads_fp = os.path.abspath(os.path.join(join_work_dp, 'fastqjoin.join.fastq'))
    if not os.path.expanduser(joined_reads_fp):
        raise Exception('failed to find joined reads file "{}"'.format(joined_reads_fp))
    else:
        return joined_reads_fp


def split_libraries_fastq(map_fp, joined_reads_fp, sample_ids, work_dp):
    split_work_dp = os.path.join(work_dp, 'split')
    print('begin split libraries step')
    output = subprocess.check_output([
        'split_libraries_fastq.py',
        '-i', joined_reads_fp,
        '-m', map_fp,
        '--barcode_type', 'not-barcoded',
        '--sample_ids', sample_ids,
        '-q', str(29),
        '-n', str(0),
        '-o', split_work_dp],
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    print('end split libraries step')
    print(output)

    split_fp = os.path.abspath(os.path.join(split_work_dp, 'seqs.fna'))
    if not os.path.exists(split_fp):
        raise Exception('failed to find split libraries file "{}"'.format(split_fp))
    else:
        return split_fp


def cut_primers(prefix, forward_primer, reverse_primer, input_fp, work_dp):
    os.makedirs(os.path.join(work_dp, 'cut'))

    forward_fasta_fp = os.path.join(work_dp, 'cut', prefix + '.assembled.clipped.regF.fasta')
    forward_discard_fp = os.path.join(work_dp, 'cut', prefix + '.discard_regF.fasta')
    reverse_fasta_fp = os.path.join(work_dp, 'cut', prefix + '.assembled.clipped.regR.fasta')

    output1 = subprocess.check_output([
        'cutadapt',
        '-g', forward_primer,
        '-O', str(3),
        '--discard-untrimmed',
        '-m', str(10),
        '-o', forward_fasta_fp,
        input_fp
    ])
    output2 = subprocess.check_output([
        'cutadapt',
        '-g', forward_primer,
        '-O', str(3),
        '--untrimmed-output',
        forward_discard_fp,
        '-m', str(10),
        '-o', os.path.join(work_dp, 'cut', 'tmp.fasta'),
        input_fp
    ])
    output3 = subprocess.check_output([
        'cutadapt',
        '-g', reverse_primer,
        '-O', str(3),
        '--discard-untrimmed',
        '-m', str(10),
        '-o', reverse_fasta_fp,
        forward_discard_fp
    ])

    return forward_fasta_fp, reverse_fasta_fp


def combine_files(forward_clipped_fp, reverse_clipped_fp):
    forward_and_reverse_clipped_fp = forward_clipped_fp.replace('.regF.', '.combined.')
    with open(forward_and_reverse_clipped_fp, 'wt') as output_file:
        for fp in (forward_clipped_fp, reverse_clipped_fp):
            with open(fp, 'rt') as input_file:
                for line in input_file:
                    output_file.write(line)
    return forward_and_reverse_clipped_fp


def seq_length_cutoff(input_file, min_length, max_length, output_file):
    if not 0 < min_length <= max_length:
        raise ValueError('invalid: min_length={}, max_length={}'.format(min_length, max_length))
    else:
        SeqIO.write(
            sequences=(
                seq for seq in SeqIO.parse(handle=input_file, format='fasta')
                if min_length <= len(seq) <= max_length),
            handle=output_file,
            format='fasta')


if __name__ == '__main__':
    args = get_args()
    pipeline(**args.__dict__)


import pytest


def test_get_reverse_fp():
    reverse_fp = get_reverse_reads_fp(forward_reads_fp='/a/b/c_d_L001_R1_001.fastq')
    assert reverse_fp == '/a/b/c_d_L001_R2_001.fastq'


def test_get_reads_filename_prefix():
    prefix = get_reads_filename_prefix(forward_reads_fp='/a/b/c_d_L001_R1_001.fastq')
    assert prefix == 'c_d'


def test__seq_length_cutoff_arguments_1():
    with pytest.raises(ValueError):
        seq_length_cutoff(input_file=None, min_length=-1, max_length=1, output_file=None)


def test__seq_length_cutoff_arguments_2():
    with pytest.raises(ValueError):
        seq_length_cutoff(input_file=None, min_length=2, max_length=1, output_file=None)


four_short_sequences_fasta = """\
>\nC\n\n
>\nCG\n\n
>\nCGC\n\n
>\nCGCG
"""

def test__seq_length_cutoff_1():
    input_buffer = io.BytesIO(four_short_sequences_fasta)
    output_buffer = io.BytesIO()
    seq_length_cutoff(input_file=input_buffer, min_length=2, max_length=3, output_file=output_buffer)
    output_buffer.seek(0)
    filtered_sequences = tuple(SeqIO.parse(handle=output_buffer, format='fasta'))
    assert len(filtered_sequences) == 2
    assert filtered_sequences[0].seq == 'CG'
    assert filtered_sequences[1].seq == 'CGC'


def test__seq_length_cutoff_2():
    input_buffer = io.BytesIO(four_short_sequences_fasta)
    output_buffer = io.BytesIO()
    seq_length_cutoff(input_file=input_buffer, min_length=2, max_length=2, output_file=output_buffer)
    output_buffer.seek(0)
    filtered_sequences = tuple(SeqIO.parse(handle=output_buffer, format='fasta'))
    assert len(filtered_sequences) == 1
    assert filtered_sequences[0].seq == 'CG'


import shutil


def test_pipeline():
    shutil.rmtree('work-Test_0_1', ignore_errors=True)
    pipeline(forward_reads_fp='test-data/Test_0_1_L001_R1_001.fastq', work_dp_template='work-{prefix}')

    assert os.path.exists('work-Test01')
    assert os.path.exists('work-Test01/join')
    assert os.path.exists('work-Test01/join/fastqjoin.join.fastq')
    assert os.path.exists('work-Test01/Test01_map.txt')
    assert os.path.exists('work-Test01/split')
    assert os.path.exists('work-Test01/split/seqs.fna')
    assert os.path.exists('work-Test01/cut')
    assert os.path.exists('work-Test01/cut/Test01.assembled.clipped.regF.fasta')
    assert os.path.exists('work-Test01/cut/Test01.assembled.clipped.regR.fasta')
    assert os.path.exists('work-Test01/cut/Test01.discard_regF.fasta')
    assert os.path.exists('work-Test01/cut/tmp.fasta')
    assert os.path.exists('work-Test01/cut/Test01.assembled.clipped.combined.fasta')
    assert os.path.exists('work-Test01/cut/Test01.assembled.clipped.combined.len.fasta')
