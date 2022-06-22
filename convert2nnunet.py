import sys
import argparse
import shutil
import pickle
import glob
import copy
import json
import math
import os

import logging

from collections import OrderedDict


def save_json(json_file, save_path):

    with open(save_path, 'w') as handle:
        json.dump(json_file, handle)


def save_pickle(pickle_file, save_path):

    with open(save_path, 'wb') as handle:
        pickle.dump(pickle_file, handle, protocol=pickle.HIGHEST_PROTOCOL)


def is_stitching_correct(subject_dir):
    sub_exists = os.path.isdir(subject_dir)
    wat_exists = os.path.isfile(os.path.join(subject_dir, 'wat.nii.gz'))
    inp_exists = os.path.isfile(os.path.join(subject_dir, 'inp.nii.gz'))
    opp_exists = os.path.isfile(os.path.join(subject_dir, 'opp.nii.gz'))
    fat_exists = os.path.isfile(os.path.join(subject_dir, 'fat.nii.gz'))
    
    return sub_exists and wat_exists and inp_exists and opp_exists and fat_exists


def format_data(nifti_folder, nnunet_folder, json_file, num_subjects, start_idx):

    img_basenames = []
    for i in range(len(json_file['modality'])):
        img_basenames.append(copy.deepcopy(json_file['modality'][copy.deepcopy(str(i))]))

    logging.info('Modalities to be formatted: {0}\n'.format(img_basenames))

    subjects = sorted(glob.glob(os.path.join(nifti_folder, '*', '')))
    if start_idx < 0:
        start_idx = 0
    if num_subjects > 0 and start_idx + num_subjects <= len(subjects):
        subjects = subjects[start_idx:start_idx + num_subjects]
    else:
        subjects = subjects[start_idx:]
        
    
    if os.path.exists(nnunet_folder):
        if input('\"{0}\" exists and will be deleted. Are you sure that this is the intended nnunet_folder [y/n]? '.format(nnunet_folder)).lower() != 'y':
            raise SystemExit(0)
        else:
            shutil.rmtree(nnunet_folder)
    os.makedirs(nnunet_folder, exist_ok=True)

    conversion_map = []
    img_list = []

    skipped_subjects = []
    
    cnt = 0
    num_of_digits = int(math.log10(len(subjects))) + 1
    for sub_path in subjects:
        
        if is_stitching_correct(sub_path):
        
            logging.info('Formatting [cnt: {0}]: {1}'.format(cnt + 1, sub_path))
            id_added = False
            subject_no = cnt + 1
            case_id = json_file['name'] + '_' + str(subject_no).zfill(num_of_digits)
            subject_props = {
                'orig_subject': os.path.basename(os.path.dirname(sub_path)),
                'orig_subject_path': os.path.abspath(sub_path),
                'nnunet_subject_no': subject_no,
                'nnunet_subject': case_id,
                'img_paths': [],
            }

            files = glob.glob(os.path.join(sub_path, '*.nii.gz'))
            for j in range(len(img_basenames)):
            
                f_path = os.path.join(sub_path, img_basenames[j] + '.nii.gz')
                if not id_added:
                    img_list.append(os.path.abspath(os.path.join(nnunet_folder, case_id + '.nii.gz')))
                    id_added = True
    
                new_path = os.path.join(nnunet_folder, case_id + '_' + str(j).zfill(4) + '.nii.gz')
                subject_props['img_paths'].append({'orig': os.path.abspath(f_path), 'nnunet': os.path.abspath(new_path)})
                shutil.copy2(f_path, new_path)

            conversion_map.append(subject_props)
            cnt += 1
        else:
            logging.info('Skipping: {0}'.format(sub_path))
            logging.info('Please check the subject directory and all modalities (wat, opp, fat, inp) exist...\n')
            skipped_subjects.append(os.path.basename(os.path.dirname(sub_path)))

    
    json_file['numTraining'] = 0
    json_file['training'] = []
    json_file['numTest'] = len(img_list)
    json_file['test'] = img_list

    save_json(json_file, os.path.join(nnunet_folder, 'dataset.json'))
    save_pickle(conversion_map, os.path.join(nnunet_folder, 'conversion.pkl'))
    
    logging.info('dataset.json: {0}'.format(os.path.join(nnunet_folder, 'dataset.json')))
    logging.info('conversion.pkl: {0}\n'.format(os.path.join(nnunet_folder, 'conversion.pkl')))
    
    logging.info('All subjects that are skipped during the formatting: {0}\n'.format(skipped_subjects))
    logging.info('Number of formatted subjects: {0}'.format(len(img_list)))
    logging.info('Total number of subjects: {0}'.format(len(subjects)))


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
    parser.add_argument('--nifti_folder', required=True, help='Folder that contains subjects with stitched volumes as nii.gz files')
    parser.add_argument('--nnunet_folder', required=True, help='Folder that contains subjects formatted for nnUNet')
    parser.add_argument('--dataset_name', required=True, choices=['ukbb', 'gnc'], help='Dataset name is either ukbb or gnc')    
    parser.add_argument('--num_channels', type=int, required=True, choices=[1, 4], help='Number of channels to be used. Either 1 or 4.')
    parser.add_argument('--num_subjects', type=int, required=False, default=-1, help='Subjects are firstly ordered. Then, they are selected from index [start_idx] to index [start_idx + num_subjects]. If zero or less, all subjects from index [start_idx] to the end.')
    parser.add_argument('--start_idx', type=int, required=False, default=0, help='Subjects are firstly ordered. Then, they are selected from index [start_idx] to index [start_idx + num_subjects].')
    args = parser.parse_args()
    
    nifti_folder = os.path.abspath(args.nifti_folder)
    nnunet_folder = os.path.abspath(args.nnunet_folder)
    dataset_name = args.dataset_name
    num_channels = args.num_channels
    num_subjects = args.num_subjects
    start_idx = args.start_idx
    
    log_file_path = get_log_file(basename=os.path.basename(nnunet_folder) + '_log.txt')
    logging.basicConfig(
        format='%(asctime)s: %(message)s',  
        level=logging.NOTSET, 
        handlers=[
            logging.FileHandler(filename=log_file_path, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
    ])
    
    logging.info('Started formatting for nnUNet...')
    logging.info('nifti_folder: {0}'.format(nifti_folder))
    logging.info('nnunet_folder: {0}'.format(nnunet_folder))
    logging.info('dataset_name: {0}'.format(dataset_name))
    logging.info('num_channels: {0}'.format(num_channels))
    logging.info('num_subjects: {0}'.format(num_subjects))
    logging.info('start_idx: {0}\n'.format(start_idx))
    
    json_file = OrderedDict()
    json_file['name'] = '{0}_{1}ch'.format(dataset_name, num_channels)

    if dataset_name == 'gnc':
        json_file['description'] = 'Whole-Body Abdominal Segmentation of German National Cohort Dataset'
        json_file['tensorImageSize'] = '4D'
        if num_channels == 1:
            json_file['modality'] = {'0': 'wat'}
        else:
            json_file['modality'] = {'0': 'wat', '1': 'fat', '2': 'inp', '3': 'opp'}
        json_file['labels'] = {'0': 'background', '1': 'liv', '2': 'spl', '3': 'rkd', '4': 'lkd', '5': 'pnc'}
    else:
        json_file['description'] = 'Whole-Body Abdominal Segmentation of UK Biobank Dataset'
        json_file['tensorImageSize'] = '4D'
        if num_channels == 1:
            json_file['modality'] = {'0': 'wat'}
        else:
            json_file['modality'] = {'0': 'wat', '1': 'opp', '2': 'fat', '3': 'inp'}
        json_file['labels'] = {'0': 'background', '1': 'liv', '2': 'spl', '3': 'lkd', '4': 'rkd', '5': 'pnc'}

    format_data(nifti_folder, nnunet_folder, json_file, num_subjects, start_idx)

    logging.info('Finished formatting for nnUNet...')
    
    shutil.copy2(log_file_path, get_log_file(dir_path=nnunet_folder, basename=os.path.basename(nnunet_folder) + '_log.txt'))
    os.remove(log_file_path)

if __name__ == '__main__':
    # For more info: https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/dataset_conversion.md
    main()

