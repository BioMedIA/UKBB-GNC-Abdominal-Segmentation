import sys
import argparse
import logging
import shutil
import glob
import os

def is_stitching_correct(subject_dir):
    sub_exists = os.path.isdir(subject_dir)
    wat_exists = os.path.isfile(os.path.join(subject_dir, 'wat.nii.gz'))
    inp_exists = os.path.isfile(os.path.join(subject_dir, 'inp.nii.gz'))
    opp_exists = os.path.isfile(os.path.join(subject_dir, 'opp.nii.gz'))
    fat_exists = os.path.isfile(os.path.join(subject_dir, 'fat.nii.gz'))
    
    return sub_exists and wat_exists and inp_exists and opp_exists and fat_exists


def rename_files(subject_dir, new_subject_dir):
    def find_instances(files, key):
        key_instances = []
        for f in files:
            f_base = os.path.basename(f)
            if key in f_base:
                key_instances.append(f)
        return key_instances
    
    files = glob.glob(os.path.join(subject_dir, '*.nii.gz'))
    for key in ['wat', 'opp', 'in', 'fat']:
        key_instances = find_instances(files, key)
        key = key + 'p' if key == 'in' else key
        if len(key_instances) == 1:
            shutil.copy2(key_instances[0], os.path.join(new_subject_dir, key + '.nii.gz'))
        elif len(key_instances) == 0:
            logging.error('Error: No files for {0} at the directory {1}'.format(key, subject_dir))
            return False
        else:
            logging.error('Error: Too files for {0} at the directory {1}'.format(key, subject_dir))  
            return False  
    
    return True


def get_log_file(dir_path=None, basename=None):
    file_name, file_extension  = os.path.splitext(__file__)
    if dir_path is None and basename is None:
        log_file_path = file_name + '_log.txt'
    elif dir_path is not None and basename is None:
        log_file_path = os.path.join(dir_path, os.path.basename(file_name) + '_log.txt')
    elif dir_path is None and basename is not None:
        log_file_path = os.path.join(os.path.dirname(file_name), basename)
    else:
        log_file_path = os.path.join(dir_path, basename)
    return log_file_path


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--zip_folder', required=True, help='Folder that contains downloaded zip files for each subject')
    parser.add_argument('--nifti_folder', required=True, help='Folder that contains subjects with stitched volumes as .nii.gz files')
    parser.add_argument('--num_subjects', type=int, required=False, default=-1, help='Subjects are firstly ordered. Then, they are selected from index [start_idx] to index [start_idx + num_subjects]. If zero or less, all subjects from index [start_idx] to the end.')
    parser.add_argument('--start_idx', type=int, required=False, default=0, help='Subjects are firstly ordered. Then, they are selected from index [start_idx] to index [start_idx + num_subjects].')
    
    args = parser.parse_args()

    zip_folder = os.path.abspath(args.zip_folder)
    nifti_folder = os.path.abspath(args.nifti_folder)
    num_subjects = args.num_subjects
    start_idx = args.start_idx
    
    log_file_path = get_log_file(basename=os.path.basename(nifti_folder) + '_log.txt')
    logging.basicConfig(
        format='%(asctime)s: %(message)s',  
        level=logging.WARNING, 
        handlers=[
            logging.FileHandler(filename=log_file_path, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
    ])
    
    logging.warning('Started extract_gnc...')
    logging.warning('zip_folder: {0}'.format(zip_folder))
    logging.warning('nifti_folder: {0}'.format(nifti_folder))
    logging.warning('num_subjects: {0}'.format(num_subjects))
    logging.warning('start_idx: {0}\n'.format(start_idx))
    
    subject_dirs = sorted(glob.glob(os.path.join(zip_folder, '*/')))
    if start_idx < 0:
        start_idx = 0
    if num_subjects > 0 and start_idx + num_subjects <= len(subject_dirs):
        subject_dirs = subject_dirs[start_idx:start_idx + num_subjects]
    else:
        subject_dirs = subject_dirs[start_idx:]

    logging.warning('Number of subjects will be converted: {0}\n'.format(len(subject_dirs)))

    os.makedirs(nifti_folder, exist_ok=True)

    for sub_dir in subject_dirs:
        # assumed the directory name describes the subject ID
        sub_id = os.path.basename(os.path.dirname(sub_dir))
        logging.warning('Currently formatting subject id [{0}]: {1}'.format(sub_id, sub_dir))
        new_sub_dir = os.path.join(nifti_folder, sub_id, '')
        os.makedirs(new_sub_dir, exist_ok=True)
        is_rename_success = rename_files(sub_dir, new_sub_dir)
        is_stitch_success = is_stitching_correct(new_sub_dir)
        if not (is_rename_success and is_stitch_success):
            shutil.rmtree(new_sub_dir)
        
    logging.warning('Finished extract_gnc...')
    shutil.copy2(log_file_path, get_log_file(dir_path=nifti_folder, basename=os.path.basename(nifti_folder) + '_log.txt'))
    os.remove(log_file_path)

if __name__ == '__main__':
    main()

