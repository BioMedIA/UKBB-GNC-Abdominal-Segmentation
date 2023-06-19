import sys
import argparse
import dicom2nifti
import subprocess
import zipfile
import logging
import shutil
import glob
import re
import os
import urllib.request


def tryint(s):
    try:
        return int(s)
    except:
        return s


def alphanum_key(s):
    return [tryint(c) for c in re.split('([0-9]+)', s) ]


def sort_nicely(l):
    l.sort(key=alphanum_key)


def is_stitching_correct(subject_dir):
    sub_exists = os.path.isdir(subject_dir)
    wat_exists = os.path.isfile(os.path.join(subject_dir, 'wat.nii.gz'))
    inp_exists = os.path.isfile(os.path.join(subject_dir, 'inp.nii.gz'))
    opp_exists = os.path.isfile(os.path.join(subject_dir, 'opp.nii.gz'))
    fat_exists = os.path.isfile(os.path.join(subject_dir, 'fat.nii.gz'))
    
    return sub_exists and wat_exists and inp_exists and opp_exists and fat_exists


def rename_and_filter_files(subject_dir):
    files = glob.glob(os.path.join(subject_dir, '*.nii.gz'))
    for f in files:
        f_base = os.path.basename(f)
        if f_base == 'T1_water.nii.gz':
            os.rename(f, os.path.join(subject_dir, 'wat.nii.gz'))
        elif f_base == 'T1_opp.nii.gz':
            os.rename(f, os.path.join(subject_dir, 'opp.nii.gz'))
        elif f_base == 'T1_in.nii.gz':
            os.rename(f, os.path.join(subject_dir, 'inp.nii.gz'))
        elif f_base == 'T1_fat.nii.gz':
            os.rename(f, os.path.join(subject_dir, 'fat.nii.gz'))
    
    if not is_stitching_correct(subject_dir):
        shutil.rmtree(subject_dir)


def stitch(zip_file, subject_dir, subject_id, tool):
    out_fnames = ['T1_in.nii.gz', 'T1_opp.nii.gz', 'T1_fat.nii.gz', 'T1_water.nii.gz',]
    margin = 3
    
    if not is_stitching_correct(subject_dir):
        
        logging.warning('Currently converting subject id [{0}]: {1}'.format(subject_id, subject_dir))
        
        if os.path.exists(subject_dir):
            shutil.rmtree(subject_dir)
        os.makedirs(subject_dir, exist_ok=True)
       
        dicom_dir = os.path.join(subject_dir, 'dcm')
        os.makedirs(dicom_dir, exist_ok=True)

        zip_ref = zipfile.ZipFile(zip_file, 'r')
        zip_ref.extractall(dicom_dir)
        zip_ref.close()

        dicom2nifti.convert_directory(dicom_dir, subject_dir)
        shutil.rmtree(dicom_dir)

        nii_files = [name for name in os.listdir(subject_dir) 
                if os.path.isfile(os.path.join(subject_dir, name))]
        sort_nicely(nii_files)

        if len(nii_files) >= 24:
            for k in range(4):
                output_image = os.path.join(subject_dir, out_fnames[k])
                input_images = os.path.join(subject_dir, nii_files[k])
                for f in range(1, 6):
                    input_images += ' ' + os.path.join(subject_dir, nii_files[k+f*4])

                command = ' '.join((tool, '-a -m', str(margin), '-i', input_images, '-o', output_image))
                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                output, error = process.communicate()
                logging.warning('Output [{0}]: {1}'.format(out_fnames[k], str(output)))
                logging.error('Error [{0}]: {1}'.format(out_fnames[k], str(error)))     
        else:
            logging.warning('Insufficient stations for subject id [{0}]...\n'.format(subject_id))

        for f in nii_files:
            os.remove(os.path.join(subject_dir, f))
            
        rename_and_filter_files(subject_dir)
        
    else:
        logging.warning('Already converted subject id [{0}]...\n'.format(subject_id))


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
    
    logging.warning('Started extract_ukbb...')
    logging.warning('zip_folder: {0}'.format(zip_folder))
    logging.warning('nifti_folder: {0}'.format(nifti_folder))
    logging.warning('num_subjects: {0}'.format(num_subjects))
    logging.warning('start_idx: {0}\n'.format(start_idx))
    
    zip_files = glob.glob(os.path.join(zip_folder, '*_20201_*.zip'))
    zip_files.sort()
    if start_idx < 0:
        start_idx = 0
    if num_subjects > 0 and start_idx + num_subjects <= len(zip_files):
        zip_files = zip_files[start_idx:start_idx + num_subjects]
    else:
        zip_files = zip_files[start_idx:]

    logging.warning('Number of subjects will be converted: {0}\n'.format(len(zip_files)))

    tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stitching')
    if not os.path.isfile(tool):
        logging.warning('Downloading stitching tool...\n')
        urllib.request.urlretrieve('https://gitlab.com/turkaykart/ukbb-gnc-abdominal-segmentation/-/raw/main/stitching?inline=false', 'stitching')
        os.chmod('stitching', 0o755)
        
    logging.warning('Stitching tool: {0}\n'.format(tool))


    os.makedirs(nifti_folder, exist_ok=True)

    for f in zip_files:
        # assumed the first part of the file name describes the subject ID
        subject_id = os.path.basename(f).split('_')[0] + '_' + os.path.basename(f).split('_')[2]
        subject_dir = os.path.join(nifti_folder, subject_id, '')
        stitch(f, subject_dir, subject_id, tool)

    logging.warning('Finished extract_ukbb...')
    shutil.copy2(log_file_path, get_log_file(dir_path=nifti_folder, basename=os.path.basename(nifti_folder) + '_log.txt'))
    os.remove(log_file_path)

if __name__ == '__main__':
    main()

