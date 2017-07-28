"""
write_launcher_job_file.py
"""
import argparse
import glob
import math
import os


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-j', '--job-fp', required=True, help='job file to be written')
    arg_parser.add_argument('-i', '--input-dp', required=True, help='directory of input files')
    arg_parser.add_argument('-w', '--work-dp-template', required=True, help='template for working directory')
    #arg_parser.add_argument('-f', '--forward-reads-fp', required=True, help='path to a forward-read FASTQ file')
    #arg_parser.add_argument('-w', '--work-dp', required=True, help='working directory')
    arg_parser.add_argument('-c', '--core-count', required=True, help='number of cores to use')
    arg_parser.add_argument('-p', '--prefix-regex', required=True, help='regular expression matching the input file name with named group <prefix>')
    arg_parser.add_argument('--forward-primer', default='CCAGCASCYGCGGTAATTCC', help='forward primer to be clipped')
    arg_parser.add_argument('--reverse-primer', default='TYRATCAAGAACGAAAGT', help='reverse primer to be clipped')
    arg_parser.add_argument('--min-overlap', type=int, default=20, help='minimum overlap for joining paired ends')
    arg_parser.add_argument('--phred', default='33', help='33 or 64')
    args = arg_parser.parse_args()
    return args


def write_launcher_job_file(
        job_fp,
        input_dp,
        work_dp_template,
        #forward_reads_fp,
        forward_primer, reverse_primer,
        prefix_regex,
        phred,
        #work_dp,
        core_count=1,
        trimmomatic_minlen=50,
        min_overlap=20):

    forward_read_file_path_set = glob.glob(os.path.join(input_dp, '*_R1*'))
    reverse_read_file_path_set = glob.glob(os.path.join(input_dp, '*_R2*'))

    if len(forward_read_file_path_set) == 0:
        raise Exception('found no forward read files in directory "{}"'.format(input_dp))
    # this script will run in muscope-18SV4/stampede but Launcher
    # jobs will run in the Launcher's work directory
    # so specify absolute paths
    singularity_container_fp = os.path.abspath('muscope-18SV4.img')
    print('path to Singularity container: {}'.format(singularity_container_fp))

    forward_reverse_read_pairs = [
        (forward_fp, reverse_fp)
        for forward_fp, reverse_fp
        in get_file_path_pairs(forward_read_file_path_set, reverse_read_file_path_set)]

    slurm_job_num_nodes = int(os.environ['SLURM_JOB_NUM_NODES'])
    slurm_ntasks = int(os.environ['SLURM_NTASKS'])
    slurm_job_cpus_per_node = int(os.environ['SLURM_JOB_CPUS_PER_NODE'])
    slurm_tasks_per_node= int(os.environ['SLURM_TASKS_PER_NODE'])

    print('SLURM_JOB_NUM_NODES     : {}'.format(slurm_job_num_nodes))
    print('SLURM_NTASKS            : {}'.format(slurm_ntasks))
    print('SLURM_JOB_CPUS_PER_NODE : {}'.format(slurm_job_cpus_per_node))
    print('SLURM_TASKS_PER_NODE    : {}'.format(slurm_tasks_per_node))

    #cores_per_job = get_cores_per_job(
    #    job_count=len(forward_reverse_read_pairs),
    #    slurm_job_num_nodes=slurm_job_num_nodes,
    #    slurm_ntasks=slurm_ntasks,
    #    slurm_job_cpus_per_node=slurm_job_cpus_per_node,
    #    slurm_tasks_per_node=slurm_tasks_per_node)

    with open(job_fp, 'wt') as job_file:
        for forward_fp, _ in forward_reverse_read_pairs:
            job_file.write(
                'singularity exec singularity/muscope-18SV4.img pipeline '
                + '-f {} '.format(forward_fp)
                + '-w {} '.format(work_dp_template)
                + '-c {} '.format(core_count)
                + '-p "{}" '.format(prefix_regex)
                + '--forward-primer {} '.format(forward_primer)
                + '--reverse-primer {} '.format(reverse_primer)
                + '--min-overlap {} '.format(min_overlap)
                + '--phred {} '.format(phred)
                + '\n'
            )

    return len(forward_read_file_path_set)


def get_file_path_pairs(forward_read_file_paths, reverse_read_file_paths):
    # use a list for the forward reads files so they can be in sorted order
    unpaired_forward_read_file_paths = sorted(list(forward_read_file_paths))
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


def get_cores_per_job(job_count, slurm_job_num_nodes, slurm_ntasks, slurm_job_cpus_per_node, slurm_tasks_per_node):
    # at least 4 cores per job
    #   1 node * 16 cores per node / 1 job  = 16    cores per job
    #   1 node * 16 cores per node / 2 jobs = 8     cores per job
    #   1 node * 16 cores per node / 3 jobs = 5.333 cores per job
    #   1 node * 16 cores per node / 4 jobs = 4     cores per job
    #   1 node * 16 cores per node / 5 jobs = 3.2   cores per job
    core_count = slurm_job_num_nodes * slurm_job_cpus_per_node / job_count
    cores_per_job = max(int(math.floor(core_count)), 4)
    #   16 cores per node / 16 cores per job = 1 job per node
    #   16 cores per node /  8 cores per job = 2 jobs per node
    #   16 cores per node /  5 cores per job = 3.2 jobs per node
    #   16 cores per node /  4 cores per job = 4 jobs per node
    processes_per_node = int(math.floor(16 / cores_per_job))

    print('core count         : {}'.format(core_count))
    print('cores per job      : {}'.format(cores_per_job))
    print('processes per node : {}'.format(processes_per_node))

    return cores_per_job


def set_launcher_env_vars(job_fp, job_count):
    """Define the TACC Launcher environment variables to spread the work across all available cores.

    Give each job at least 4 cores and try to use all cores at all times. Not always possible.

    :param job_count: (int) number of jobs in the Launcher job file
    :return:
    """

    #"Starting launcher"
    #"  SLURM_JOB_NUM_NODES=$SLURM_JOB_NUM_NODES"
    #"  SLURM_NTASKS=$SLURM_NTASKS"
    #"  SLURM_JOB_CPUS_PER_NODE=$SLURM_JOB_CPUS_PER_NODE"
    #"  SLURM_TASKS_PER_NODE=$SLURM_TASKS_PER_NODE"

    slurm_job_num_nodes = int(os.environ['SLURM_JOB_NUM_NODES'])
    slurm_ntasks = int(os.environ['SLURM_NTASKS'])
    slurm_job_cpus_per_node = int(os.environ['SLURM_JOB_CPUS_PER_NODE'])
    slurm_tasks_per_node= int(os.environ['SLURM_TASKS_PER_NODE'])

    print('SLURM_JOB_NUM_NODES     : {}'.format(slurm_job_num_nodes))
    print('SLURM_NTASKS            : {}'.format(slurm_ntasks))
    print('SLURM_JOB_CPUS_PER_NODE : {}'.format(slurm_job_cpus_per_node))
    print('SLURM_TASKS_PER_NODE    : {}'.format(slurm_tasks_per_node))

    # at least 4 cores per job
    #   1 node * 16 cores per node / 1 job  = 16    cores per job
    #   1 node * 16 cores per node / 2 jobs = 8     cores per job
    #   1 node * 16 cores per node / 3 jobs = 5.333 cores per job
    #   1 node * 16 cores per node / 4 jobs = 4     cores per job
    #   1 node * 16 cores per node / 5 jobs = 3.2   cores per job
    core_count = slurm_job_num_nodes * slurm_job_cpus_per_node / job_count
    cores_per_job = max(int(math.floor(core_count)), 4)
    #   16 cores per node / 16 cores per job = 1 job per node
    #   16 cores per node /  8 cores per job = 2 jobs per node
    #   16 cores per node /  5 cores per job = 3.2 jobs per node
    #   16 cores per node /  4 cores per job = 4 jobs per node
    processes_per_node = int(math.floor(16 / cores_per_job))

    print('core count         : {}'.format(core_count))
    print('cores per job      : {}'.format(cores_per_job))
    print('processes per node : {}'.format(processes_per_node))

    #os.environ['LAUNCHER_DIR'] = '$HOME/src/launcher'
    #os.environ['LAUNCHER_PLUGIN_DIR']= '$LAUNCHER_DIR/plugins
    #os.environ['LAUNCHER_WORKDIR'] = '$SCRATCH/muscope-18SV4'
    #os.environ['LAUNCHER_RMI'] = 'SLURM'
    os.environ['LAUNCHER_JOB_FILE'] = job_fp
    #os.environ['LAUNCHER_NJOBS'] = str(job_count)
    #os.environ['LAUNCHER_NHOSTS'] =
    #os.environ['LAUNCHER_NPROCS'] =
    os.environ['LAUNCHER_PPN'] = str(processes_per_node)
    os.environ['LAUNCHER_SCHED'] = 'dynamic'


def main():
    args = get_args()
    write_launcher_job_file(**args.__dict__)


if __name__ == '__main__':
    main()
