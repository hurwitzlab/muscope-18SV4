"""
Create a virtual environment like this
    $ conda create -n mu18SV4 python=2.7 qiime matplotlib mock nose -c bioconda

It is also necessary to install fastq-join. On systems with apt this will work:
    $ apt install ea-utils

Building fastq-join from source takes less space.

This script requires vsearch, which can be installed on Debian-based systems with apt.
    $ sudo apt update
    $ sudo apt install vsearch

This script handles *one* pair of paired-end files.

All output will be written to directory work-dp.

"""
import argparse
import glob
import logging
import os
import re
import sys
import traceback

import subprocess

from Bio import SeqIO


def main():
    logging.basicConfig(level=logging.INFO)
    args = get_args()
    Pipeline(**args.__dict__).run()


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-f', '--forward-reads-fp', required=True, help='path to a forward-read FASTQ file')
    arg_parser.add_argument('-w', '--work-dp', required=True, help='working directory')
    arg_parser.add_argument('-c', '--core-count', required=True, help='number of cores to use')
    arg_parser.add_argument('-p', '--prefix-regex', required=True, help='regular expression matching the input file name with named group <prefix>')
    arg_parser.add_argument('--forward-primer', default='CCAGCASCYGCGGTAATTCC', help='forward primer to be clipped')
    arg_parser.add_argument('--reverse-primer', default='TYRATCAAGAACGAAAGT', help='reverse primer to be clipped')
    arg_parser.add_argument('--min-overlap', type=int, default=20, help='minimum overlap for joining paired ends')
    arg_parser.add_argument('--phred', default='33', help='33 or 64')
    args = arg_parser.parse_args()
    return args


class PipelineException(Exception):
    pass


class Pipeline:
    def __init__(
            self,
            forward_reads_fp,
            forward_primer, reverse_primer,
            prefix_regex,
            phred,
            work_dp,
            core_count=1,
            trimmomatic_minlen=50,
            min_overlap=20):

        log = logging.getLogger(name=self.__class__.__name__)

        self.forward_reads_fp = forward_reads_fp
        self.forward_primer = forward_primer
        self.reverse_primer = reverse_primer
        self.prefix_pattern = re.compile(prefix_regex)
        self.phred = phred
        self.min_overlap = min_overlap
        self.work_dp = work_dp
        self.core_count = core_count

        self.trimmomatic_minlen = trimmomatic_minlen

        self.prefix = self.get_reads_filename_prefix(forward_reads_fp)

        # if self.work_dp does not exist then create it
        if not os.path.exists(self.work_dp):
            os.makedirs(self.work_dp)

        #self.fastq_join_binary_fp = os.environ.get('FASTQ_JOIN', 'fastq-join')
        #log.info('fastq_join binary: "%s"', self.fastq_join_binary_fp)


    def run(self):
        output_dirs = []
        output_dirs.append(self.step_01_trim_primers())
        output_dirs.append(self.step_02_join_paired_end_reads(input_dir=output_dirs[-1]))
        output_dirs.append(self.step_03_quality_filter(input_dir=output_dirs[-1]))
        output_dirs.append(self.step_04_fasta_format(input_dir=output_dirs[-1]))
        output_dirs.append(self.step_05_length_filter(input_dir=output_dirs[-1]))
        output_dirs.append(self.step_06_rewrite_sequence_ids(input_dir=output_dirs[-1]))

        return output_dirs

    def initialize_step(self):
        function_name = sys._getframe(1).f_code.co_name
        log = logging.getLogger(name=function_name)
        output_dir = create_output_dir(output_parent_dir=self.work_dp, output_dir_name=function_name)
        return log, output_dir


    def complete_step(self, log, output_dir):
        output_dir_list = sorted(os.listdir(output_dir))
        if len(output_dir_list) == 0:
            raise PipelineException('ERROR: no output files in directory "{}"'.format(output_dir))
        else:
            log.info('output files:\n\t%s', '\n\t'.join(os.listdir(output_dir)))


    def step_01_trim_primers(self):
        log, trim_dp = self.initialize_step()

        forward_fastq_basename = os.path.basename(self.forward_reads_fp)
        reverse_reads_fp = get_reverse_reads_fp(self.forward_reads_fp)
        log.info('reverse reads: "%s"', reverse_reads_fp)
        reverse_fastq_basename = os.path.basename(reverse_reads_fp)

        output1P_fp = os.path.join(
            trim_dp, re.sub(string=forward_fastq_basename, pattern=r'\.fastq', repl='.trim1p.fastq'))
        output1U_fp = os.path.join(
            trim_dp, re.sub(string=forward_fastq_basename, pattern=r'\.fastq', repl='.trim1u.fastq'))
        output2P_fp = os.path.join(
            trim_dp, re.sub(string=reverse_fastq_basename, pattern=r'\.fastq', repl='.trim2p.fastq'))
        output2U_fp = os.path.join(
            trim_dp, re.sub(string=reverse_fastq_basename, pattern=r'\.fastq', repl='.trim2u.fastq'))

        primer_fp = os.path.join(trim_dp, 'trimPE.fasta')

        with open(primer_fp, 'wt') as primer_file:
            primer_file.write('>Prefix/1\n{}\n>Prefix/2\n{}\n'.format(self.forward_primer, self.reverse_primer))

        run_cmd([
            'TrimmomaticPE',
            self.forward_reads_fp, reverse_reads_fp,
            output1P_fp,
            output1U_fp,
            output2P_fp,
            output2U_fp,
            'LEADING:10',
            'TRAILING:10',
            'SLIDINGWINDOW:10:30',
            'MINLEN:{}'.format(self.trimmomatic_minlen),
            'ILLUMINACLIP:{}:2:30:10'.format(primer_fp)  # was 2:30:10
        ])

        self.complete_step(log, trim_dp)
        return trim_dp


    def step_02_join_paired_end_reads(self, input_dir):
        log, output_dp = self.initialize_step()

        print('begin joined paired ends step')

        trimmed_reads_file_glob = os.path.join(input_dir, '{}*.trim[12]p.fastq'.format(self.prefix))
        log.info('trimmed reads file glob: %s', trimmed_reads_file_glob)
        trimmed_reads_files = glob.glob(trimmed_reads_file_glob)
        log.info('trimmed reads files:\n\t%s', '\n\t'.join(trimmed_reads_files))
        trimmed_forward_reads_fp, trimmed_reverse_reads_fp = sorted(trimmed_reads_files)

        joined_reads_fp = os.path.join(
            output_dp,
            re.sub(
                string=os.path.basename(trimmed_forward_reads_fp),
                pattern=r'\.trim1p.fastq$',
                repl='.trim.%.fastq'))

        run_cmd([
            'fastq-join',
            trimmed_forward_reads_fp,
            trimmed_reverse_reads_fp,
            '-m', '20',
            '-o', joined_reads_fp
        ])

        self.complete_step(log, output_dp)
        return output_dp


    def step_03_quality_filter(self, input_dir):
        log, output_dp = self.initialize_step()

        print('begin quality filtering step')

        joined_reads_file_glob = os.path.join(input_dir, '{}*.join.fastq'.format(self.prefix))
        log.info('trimmed reads file glob: %s', joined_reads_file_glob)
        joined_reads_fp = glob.glob(joined_reads_file_glob)[0]
        log.info('joined reads file: %s', joined_reads_fp)

        quality_filtered_reads_fp = os.path.join(
            output_dp,
            re.sub(
                string=os.path.basename(joined_reads_fp),
                pattern=r'\.fastq$',
                repl='.quality.fastq'))

        quality_cutoff = 30
        min_percentage = 90

        run_cmd([
            'fastq_quality_filter',
            '-i', joined_reads_fp,
            '-o', quality_filtered_reads_fp,
            '-v',
            '-q', str(quality_cutoff),
            '-p', str(min_percentage),
            '-Q{}'.format(self.phred)
        ])

        self.complete_step(log, output_dp)
        return output_dp


    def step_04_fasta_format(self, input_dir):
        log, output_dp = self.initialize_step()

        print('begin FASTA format step')

        fastq_file_glob = os.path.join(input_dir, '{}*.fastq'.format(self.prefix))
        log.info('FASTQ file glob: %s', fastq_file_glob)
        fastq_file_list = glob.glob(fastq_file_glob)
        log.info('FASTQ file list:\n\t%s', '\n\t'.join(fastq_file_list))

        for fastq_fp in fastq_file_list:
            fasta_fp = os.path.join(
                output_dp,
                re.sub(
                    string=os.path.basename(fastq_fp),
                    pattern='\.fastq$',
                    repl='.fasta'
                )
            )

            run_cmd([
                'fastq_to_fasta',
                '-i', fastq_fp,
                '-o', fasta_fp,
                '-n',
                '-v',
                '-r'
            ])

        self.complete_step(log=log, output_dir=output_dp)
        return output_dp


    def step_05_length_filter(self, input_dir):
        log, output_dp = self.initialize_step()

        print('begin FASTA format step')

        fasta_file_glob = os.path.join(input_dir, '{}*.fasta'.format(self.prefix))
        log.info('FASTA file glob: %s', fasta_file_glob)
        fasta_file_list = glob.glob(fasta_file_glob)
        log.info('FASTA file list:\n\t%s', '\n\t'.join(fasta_file_list))

        for fasta_fp in fasta_file_list:
            length_filtered_fp = os.path.join(
                output_dp,
                re.sub(
                    string=os.path.basename(fasta_fp),
                    pattern='\.fasta$',
                    repl='.length.fasta'
                )
            )

            run_cmd([
                'fastx_clipper',
                '-i', fasta_fp,
                '-o', length_filtered_fp,
                '-l', str(50),
                '-n',
                '-v',
            ])

        self.complete_step(log=log, output_dir=output_dp)
        return output_dp


    def step_06_rewrite_sequence_ids(self, input_dir):
        log, output_dp = self.initialize_step()

        print('begin sequence id rewrite step')

        fasta_file_glob = os.path.join(input_dir, '{}*.fasta'.format(self.prefix))
        log.info('FASTA file glob: %s', fasta_file_glob)
        fasta_file_list = glob.glob(fasta_file_glob)
        log.info('FASTA file list:\n\t%s', '\n\t'.join(fasta_file_list))

        for fasta_fp in fasta_file_list:
            rewritten_sequence_id_fp = os.path.join(
                output_dp,
                re.sub(
                    string=os.path.basename(fasta_fp),
                    pattern='\.fasta$',
                    repl='.id.fasta'
                )
            )

            with open(fasta_fp, 'rt') as input_file, open(rewritten_sequence_id_fp, 'wt') as output_file:
                for seq_record in SeqIO.parse(input_file, format='fasta'):
                    seq_record.id = '{}_{}'.format(self.prefix, seq_record.id)
                    # if description does not match id it will be printed
                    # resulting in, for example,  >prefix_1 1 rather than >prefix_1
                    seq_record.description = seq_record.id
                    SeqIO.write(seq_record, output_file, format='fasta')

        self.complete_step(log=log, output_dir=output_dp)
        return output_dp


    def get_reads_filename_prefix(self, forward_reads_fp):
        forward_filename = os.path.basename(forward_reads_fp)
        # m = re.search('^(?P<prefix>[a-zA-Z0-9_]+)_L001_R[12]', forward_filename)
        m = self.prefix_pattern.search(forward_filename)
        if m is None:
            raise PipelineException(
                'failed to parse filename "{}" with regular expression "{}"'.format(
                    forward_filename, self.prefix_pattern.pattern))
        else:
            return m.group('prefix')


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
        #print(c.message)
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
    reverse_filename = forward_filename.replace('R1', 'R2')
    reverse_fp = os.path.join(forward_dp, reverse_filename)
    return reverse_fp


def create_output_dir(output_parent_dir, output_dir_name):
    output_dir = os.path.join(output_parent_dir, output_dir_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


if __name__ == '__main__':
    main()