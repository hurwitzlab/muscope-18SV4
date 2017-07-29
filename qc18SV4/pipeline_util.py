import gzip
import logging
import os.path
import shutil


def delete_files(*fp_list):
    log = logging.getLogger(name=__file__)
    for fp in fp_list:
        log.info('deleting file "%s"', fp)
        os.remove(fp)


def gzip_files(*fp_list):
    log = logging.getLogger(name=__file__)
    gzipped_file_list = []
    for fp in fp_list:
        dir_path, file_name = os.path.split(fp)
        if fp.endswith('.gz'):
            log.warning('file "%s" is already gzipped', file_name)
            gzipped_file_list.append(fp)
        else:
            log.info('compressing "%s" with gzip', file_name)
            gzipped_fp = os.path.join(dir_path, file_name + '.gz')
            with open(fp, 'rt') as src, gzip.open(gzipped_fp, 'wt') as dst:
                shutil.copyfileobj(fsrc=src, fdst=dst)
            gzipped_file_list.append(gzipped_fp)
    return gzipped_file_list


def ungzip_files(*fp_list):
    log = logging.getLogger(name=__file__)
    ungzipped_file_list = []
    for fp in fp_list:
        dir_path, gzipped_file_name = os.path.split(fp)
        if not fp.endswith('.gz'):
            log.warning('file "%s" is not gzipped', gzipped_file_name)
            ungzipped_file_list.append(fp)
        else:
            log.info('uncompressing "%s" with gzip', gzipped_file_name)
            ungzipped_fp = os.path.join(dir_path, gzipped_file_name[:-3])
            with gzip.open(fp, 'rt') as src, open(ungzipped_fp, 'wt') as dst:
                shutil.copyfileobj(fsrc=src, fdst=dst)
            ungzipped_file_list.append(ungzipped_fp)
    return ungzipped_file_list

