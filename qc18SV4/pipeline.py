"""
Create a virtual environment like this
    $ conda create -n mu18SV4 python=2.7 qiime matplotlib mock nose -c bioconda

It is also necessary to install fastq-join. On systems with apt this will work:
    $ apt install ea-utils

Building fastq-join from source takes less space.

This script requires vsearch, which can be installed on Debian-based systems with apt.
    $ sudo apt update
    $ sudo apt install vsearch

This script handles one pair of paired-end files.

The work-dp is where all output is written.

"""
import argparse
import glob
import logging
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
    Pipeline(**args.__dict__).run()


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-f', '--forward-reads-fp', help='path to a forward-read FASTQ file')
    arg_parser.add_argument('-w', '--work-dp', help='working directory')
    arg_parser.add_argument('-c', '--core-count', help='number of cores to use')
    arg_parser.add_argument('--forward-primer', default='CCAGCASCYGCGGTAATTCC', help='forward primer to be clipped')
    arg_parser.add_argument('--reverse-primer', default='TYRATCAAGAACGAAAGT', help='reverse primer to be clipped')
    arg_parser.add_argument('--min-overlap', type=int, default=20, help='minimum overlap for joining paired ends')
    arg_parser.add_argument('--uchime-ref-db-fp', default='/mu18SV4/pr2/pr2_gb203_version_4.5.fasta', help='database for vsearch --uchime_ref')
    args = arg_parser.parse_args()
    return args


class PipelineException(Exception):
    pass


class Pipeline:
    def __init__(self, forward_reads_fp, forward_primer, reverse_primer, min_overlap, uchime_ref_db_fp, work_dp, core_count):
        self.forward_reads_fp = forward_reads_fp
        self.forward_primer = forward_primer
        self.reverse_primer = reverse_primer
        self.min_overlap = min_overlap
        self.uchime_ref_db_fp = uchime_ref_db_fp
        self.work_dp = work_dp
        self.core_count = core_count

        self.prefix = get_reads_filename_prefix(forward_reads_fp)


    def run(self):
        # if self.work_dp does not exist then create it
        if not os.path.exists(self.work_dp):
            os.makedirs(self.work_dp)

        # write a directory under self.work_dp with name in self.prefix
        # raise an exception if the directory already exists
        # since this suggests the pipeline has already run for the given data and output directory
        output_dp = os.path.join(self.work_dp, self.prefix)
        if os.path.exists(output_dp):
            raise PipelineException('output directory {} already exists'.format(output_dp))
        else:
            os.mkdir(output_dp)

        # the parent output directory is 'prefix'
        step_01_output_dir = self.step_01_join_paired_end_reads(output_dp)
        step_02_output_dir = self.step_02_split_libraries(input_dir=step_01_output_dir)
        step_03_output_dir = self.step_03_cut_primers(input_dir=step_02_output_dir)
        step_04_output_dir = self.step_04_combine_files(input_dir=step_03_output_dir)
        step_05_output_dir = self.step_05_length_filter(input_dir=step_04_output_dir)
        step_06_output_dir = self.step_06_remove_chimeras(input_dir=step_05_output_dir)

        """    
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
        """


    def step_01_join_paired_end_reads(self, output_dp):
        output_dir = create_output_dir(output_dp, sys._getframe().f_code.co_name)

        print('begin join paired ends step')
        reverse_fp = get_reverse_reads_fp(self.forward_reads_fp)
        run_cmd([
            'fastq-join',
            '-m', str(self.min_overlap),
            self.forward_reads_fp,
            reverse_fp,
            '-o', os.path.join(output_dir, 'fastqjoin.%.fastq')]
        )
        print('end join paired ends step')

        joined_reads_fp = os.path.abspath(os.path.join(output_dir, 'fastqjoin.join.fastq'))
        if not os.path.expanduser(joined_reads_fp):
            raise Exception('failed to find joined reads file "{}"'.format(joined_reads_fp))
        else:
            #return joined_reads_fp
            return output_dir


    def create_map_file(self, map_fp):
        with open(map_fp, 'wt') as map_file:
            map_file.write('#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tDescription\n')
            map_file.write('{}\tCCAG\tCASCYGCGGTAATTCC\t{}\n'.format(self.prefix, self.prefix))

        return os.path.abspath(map_fp)


    def step_02_split_libraries(self, input_dir):
        input_parent_dir, _ = os.path.split(input_dir)
        output_dir = create_output_dir(input_parent_dir, sys._getframe().f_code.co_name)

        print('begin split libraries step')

        map_fp = self.create_map_file(map_fp=os.path.join(output_dir, '{}_map.txt'.format(self.prefix)))
        # find the joined reads file in the input directory
        for joined_reads_fp in glob.glob(os.path.join(input_dir, '*.join.fastq')):
            run_cmd([
                'split_libraries_fastq.py',
                '-i', joined_reads_fp,
                '-m', map_fp,
                '--barcode_type', 'not-barcoded',
                '--sample_ids', self.prefix,
                '-q', str(29),
                '-n', str(0),
                '-o', output_dir])
        print('end split libraries step')

        split_fp = os.path.abspath(os.path.join(output_dir, 'seqs.fna'))
        if not os.path.exists(split_fp):
            raise Exception('failed to find split libraries file "{}"'.format(split_fp))
        else:
            return output_dir


    def step_03_cut_primers(self, input_dir):
        input_parent_dir, _ = os.path.split(input_dir)
        cut_dp = create_output_dir(input_parent_dir, sys._getframe().f_code.co_name)

        forward_fasta_fp = os.path.join(cut_dp, self.prefix + '.assembled.clipped.regF.fasta')
        forward_discard_fp = os.path.join(cut_dp, self.prefix + '.discard_regF.fasta')
        reverse_fasta_fp = os.path.join(cut_dp, self.prefix + '.assembled.clipped.regR.fasta')

        input_fp = os.path.join(input_dir, 'seqs.fna')

        run_cmd([
            'cutadapt',
            '-g', self.forward_primer,
            '-O', str(3),
            '--discard-untrimmed',
            '-m', str(10),
            '-o', forward_fasta_fp,
            input_fp
        ])
        run_cmd([
            'cutadapt',
            '-g', self.forward_primer,
            '-O', str(3),
            '--untrimmed-output',
            forward_discard_fp,
            '-m', str(10),
            '-o', os.path.join(cut_dp, 'tmp.fasta'),
            input_fp
        ])
        # TODO: use forward_discard_fp?
        run_cmd([
            'cutadapt',
            '-g', self.reverse_primer,
            '-O', str(3),
            '--discard-untrimmed',
            '-m', str(10),
            '-o', reverse_fasta_fp,
            forward_discard_fp
        ])

        #return forward_fasta_fp, reverse_fasta_fp
        return cut_dp


    def step_04_combine_files(self, input_dir):
        log = logging.getLogger(name=sys._getframe().f_code.co_name)

        input_parent_dir, _ = os.path.split(input_dir)
        output_dp = create_output_dir(input_parent_dir, sys._getframe().f_code.co_name)

        forward_and_reverse_files = glob.glob(os.path.join(input_dir, '*.reg[F|R].*'))
        log.info(forward_and_reverse_files)
        combined_clipped_fp = os.path.join(
            output_dp,
            re.sub('\.regF\.', '.combined.', os.path.basename(forward_and_reverse_files[0])))
        log.info(combined_clipped_fp)

        with open(combined_clipped_fp, 'wt') as destination_file:
            for source_fp in forward_and_reverse_files:
                with open(source_fp, 'rt') as source_file:
                    shutil.copyfileobj(source_file, destination_file)
        return output_dp


    def step_05_length_filter(self, input_dir):
        log = logging.getLogger(name=sys._getframe().f_code.co_name)
        input_parent_dir, _ = os.path.split(input_dir)
        output_dp = create_output_dir(input_parent_dir, sys._getframe().f_code.co_name)

        input_glob = os.path.join(input_dir, '*.combined.fasta')
        log.info('input glob: {}'.format(input_glob))
        for combined_clipped_fp in glob.glob(input_glob):
            length_filtered_fp = os.path.join(
                output_dp,
                re.sub('combined\.fasta$', 'combined.len.fasta', os.path.basename(combined_clipped_fp)))

            log.info('combined_clipped_fp: {}'.format(combined_clipped_fp))
            log.info('length_filtered_fp:  {}'.format(length_filtered_fp))

            with open(combined_clipped_fp, 'rt') as combined_clipped_file, open(length_filtered_fp, 'wt') as length_filtered_file:
                seq_length_cutoff(
                    input_file=combined_clipped_file,
                    min_length=150,
                    max_length=500,
                    output_file=length_filtered_file)

        return output_dp


    def step_06_remove_chimeras(self, input_dir):
        log = logging.getLogger(name=sys._getframe().f_code.co_name)
        input_parent_dir, _ = os.path.split(input_dir)
        output_dp = create_output_dir(input_parent_dir, sys._getframe().f_code.co_name)

        # (8) Chimera check with vsearch (uchime) using a reference database

        input_glob = os.path.join(input_dir, '*.fasta')
        log.info('input glob: %s', input_glob)
        for input_fp in glob.glob(input_glob):
            log.info('run vsearch on file %s', input_fp)
            uchimeout_fp = os.path.join(output_dp, self.prefix + '.uchimeinfo_ref')
            chimeras_fp = os.path.join(output_dp, self.prefix + '.chimeras_ref.fasta')
            final_fp = os.path.join(output_dp, re.sub('\.fasta$', '.nc.fasta', os.path.basename(input_fp)))

            run_cmd(
                ['vsearch',
                 '--uchime_ref', input_fp,
                 '--threads', str(self.core_count),
                 '--db', self.uchime_ref_db_fp,
                 '--uchimeout', uchimeout_fp,
                 '--chimeras', chimeras_fp,
                 '--strand', 'plus',
                 '--nonchimeras', final_fp]
            )
        return output_dp


def run_cmd(cmd_line_list, **kwargs):
    try:
        print(' '.join(cmd_line_list))
        output = subprocess.check_output(
            cmd_line_list,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            **kwargs)
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


def create_output_dir(output_parent_dir, output_dir_name):
    output_dir = os.path.join(output_parent_dir, output_dir_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


# def join_paired_ends(forward_fp, reverse_fp, work_dp, j):
#     join_work_dp = os.path.join(work_dp, 'join')
#     if not os.path.exists(join_work_dp):
#         os.makedirs(join_work_dp)
#     print('begin joined paired ends step')
#     #run_cmd([
#     #    'join_paired_ends.py',
#     #    '-j', str(j),
#     #    '-f', forward_fp,
#     #    '-r', reverse_fp,
#     #    '-o', join_work_dp]
#     #)
#     run_cmd([
#         'fastq-join',
#         '-m', str(j),
#         forward_fp,
#         reverse_fp,
#         '-o', os.path.join(join_work_dp, 'fastqjoin.%.fastq')]
#     )
#     print('end joined paired ends step')
#
#     joined_reads_fp = os.path.abspath(os.path.join(join_work_dp, 'fastqjoin.join.fastq'))
#     if not os.path.expanduser(joined_reads_fp):
#         raise Exception('failed to find joined reads file "{}"'.format(joined_reads_fp))
#     else:
#         return joined_reads_fp


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
         '--nonchimeras', final_fp],
        shell=True
    )


if __name__ == '__main__':
    main()