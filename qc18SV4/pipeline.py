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
import os
import re
import shutil
import sys
import traceback

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess

from Bio import SeqIO


def main():
    args = get_args()
    pipeline(**args.__dict__)


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-f', '--forward-reads-fp', help='path to a forward-read FASTQ file')
    arg_parser.add_argument('-w', '--work-dp-template', help='template for working directory')
    arg_parser.add_argument('-c', '--core-count', help='number of cores to use')
    arg_parser.add_argument('--forward-primer', default='CCAGCASCYGCGGTAATTCC', help='forward primer to be clipped')
    arg_parser.add_argument('--reverse-primer', default='TYRATCAAGAACGAAAGT', help='reverse primer to be clipped')
    arg_parser.add_argument('--uchime-ref-db-fp', default='/mu18SV4/pr2/pr2_gb203_version_4.5.fasta', help='database for vsearch --uchime_ref')
    args = arg_parser.parse_args()
    return args


def pipeline(forward_reads_fp, forward_primer, reverse_primer, uchime_ref_db_fp, work_dp_template, core_count):

    reverse_reads_fp = get_reverse_reads_fp(forward_reads_fp)
    prefix = get_reads_filename_prefix(forward_reads_fp)
    work_dp = work_dp_template.format(prefix=prefix)

    if not os.path.exists(work_dp):
        os.mkdir(work_dp)

    joined_reads_fp = join_paired_ends(
        forward_fp=forward_reads_fp,
        reverse_fp=reverse_reads_fp,
        j=20,
        work_dp=work_dp)

    map_fp = create_map_file(prefix=prefix, work_dp=work_dp)

    split_fp = split_libraries_fastq(
        map_fp=map_fp,
        joined_reads_fp=joined_reads_fp,
        sample_ids=prefix,
        work_dp=work_dp)

    forward_clipped_fp, reverse_clipped_fp = cut_primers(
        prefix=prefix,
        forward_primer=forward_primer,
        reverse_primer=reverse_primer,
        work_dp=work_dp,
        input_fp=split_fp)

    combined_clipped_fp = combine_files(
        forward_clipped_fp.replace('.regF.', '.combined.'),
        forward_clipped_fp, reverse_clipped_fp)

    length_filtered_fp = re.sub('combined\.fasta$', 'combined.len.fasta', combined_clipped_fp)
    with open(combined_clipped_fp, 'rt') as combined_clipped_file, open(length_filtered_fp, 'wt') as length_filtered_file:
        seq_length_cutoff(
            input_file=combined_clipped_file,
            min_length=150,
            max_length=500,
            output_file=length_filtered_file)

    vsearch(
        prefix=prefix,
        work_dp=work_dp,
        length_filtered_fp=length_filtered_fp,
        core_count=core_count,
        uchime_ref_db_fp=uchime_ref_db_fp)


def run_cmd(cmd_line_list):
    try:
        print(' '.join(cmd_line_list))
        output = subprocess.check_output(
            cmd_line_list,
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        print(output)
    except subprocess.CalledProcessError as c:
        print(c.message)
        print(c.cmd)
        print(c.output)
        raise c
    except Exception as e:
        print('blarg!')
        print(e)
        traceback.print_exc()
        raise e


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
    if not os.path.exists(join_work_dp):
        os.makedirs(join_work_dp)
    print('begin joined paired ends step')
    #run_cmd([
    #    'join_paired_ends.py',
    #    '-j', str(j),
    #    '-f', forward_fp,
    #    '-r', reverse_fp,
    #    '-o', join_work_dp]
    #)
    run_cmd([
        'fastq-join',
        '-m', str(j),
        forward_fp,
        reverse_fp,
        '-o', os.path.join(join_work_dp, 'fastqjoin.%.fastq')]
    )
    print('end joined paired ends step')

    joined_reads_fp = os.path.abspath(os.path.join(join_work_dp, 'fastqjoin.join.fastq'))
    if not os.path.expanduser(joined_reads_fp):
        raise Exception('failed to find joined reads file "{}"'.format(joined_reads_fp))
    else:
        return joined_reads_fp


def split_libraries_fastq(map_fp, joined_reads_fp, sample_ids, work_dp):
    split_work_dp = os.path.join(work_dp, 'split')
    print('begin split libraries step')
    run_cmd([
        'split_libraries_fastq.py',
        '-i', joined_reads_fp,
        '-m', map_fp,
        '--barcode_type', 'not-barcoded',
        '--sample_ids', sample_ids,
        '-q', str(29),
        '-n', str(0),
        '-o', split_work_dp])
    print('end split libraries step')

    split_fp = os.path.abspath(os.path.join(split_work_dp, 'seqs.fna'))
    if not os.path.exists(split_fp):
        raise Exception('failed to find split libraries file "{}"'.format(split_fp))
    else:
        return split_fp


def cut_primers(prefix, forward_primer, reverse_primer, input_fp, work_dp):
    cut_dp = os.path.join(work_dp, 'cut')
    if not os.path.exists(cut_dp):
        os.makedirs(cut_dp)

    forward_fasta_fp = os.path.join(work_dp, 'cut', prefix + '.assembled.clipped.regF.fasta')
    forward_discard_fp = os.path.join(work_dp, 'cut', prefix + '.discard_regF.fasta')
    reverse_fasta_fp = os.path.join(work_dp, 'cut', prefix + '.assembled.clipped.regR.fasta')

    run_cmd([
        'cutadapt',
        '-g', forward_primer,
        '-O', str(3),
        '--discard-untrimmed',
        '-m', str(10),
        '-o', forward_fasta_fp,
        input_fp
    ])
    run_cmd([
        'cutadapt',
        '-g', forward_primer,
        '-O', str(3),
        '--untrimmed-output',
        forward_discard_fp,
        '-m', str(10),
        '-o', os.path.join(work_dp, 'cut', 'tmp.fasta'),
        input_fp
    ])
    run_cmd([
        'cutadapt',
        '-g', reverse_primer,
        '-O', str(3),
        '--discard-untrimmed',
        '-m', str(10),
        '-o', reverse_fasta_fp,
        forward_discard_fp
    ])

    return forward_fasta_fp, reverse_fasta_fp


def combine_files(destination_file_fp, *source_fp_list):
    with open(destination_file_fp, 'wt') as destination_file:
        for source_fp in source_fp_list:
            with open(source_fp, 'rt') as source_file:
                shutil.copyfileobj(source_file, destination_file)
    return destination_file_fp


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


def vsearch(prefix, work_dp, length_filtered_fp, core_count, uchime_ref_db_fp):
    #(8) Chimera check with vsearch (uchime) using a reference database
    vsearch_dp = os.path.join(work_dp, 'vsearch')
    if not os.path.exists(vsearch_dp):
        os.mkdir(vsearch_dp)

    vsearch_filename = os.path.basename(length_filtered_fp)
    uchimeout_fp = os.path.join(vsearch_dp, prefix + '.uchimeinfo_ref')
    chimeras_fp = os.path.join(vsearch_dp, prefix + '.chimeras_ref.fasta')
    final_fp = os.path.join(vsearch_dp, re.sub('len\.fasta$', 'len.nc.fasta', vsearch_filename))

    run_cmd(
        ['vsearch',
         '--uchime_ref', length_filtered_fp,
         '--threads', str(core_count),
         '--db', uchime_ref_db_fp,
         '--uchimeout', uchimeout_fp,
         '--chimeras', chimeras_fp,
         '--strand', 'plus',
         '--nonchimeras', final_fp]
    )


if __name__ == '__main__':
    main()