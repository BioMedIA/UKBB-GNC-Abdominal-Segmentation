import sys
import os
import shutil
import logging
import zipfile
import argparse
import urllib.request

import nnunet.inference.predict_simple as ps


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
    parser.add_argument('--nnunet_folder', required=True, help='Folder that contains results of convert2nnunet.py. Files must be named \
                                                               as CASENAME_XXXX_nii.gz where XXXX is just (0000) for 1-channel model \
                                                               and (0000, 0001, 0002, 0003) for 4-channel model. Please see the nnUNet \
                                                               documentation for more info at https://github.com/MIC-DKFZ/nnUNet')
    parser.add_argument('--prediction_folder', required=True, help='Folder that contains final predictions')
    parser.add_argument('--dataset_name', required=True, choices=['ukbb', 'gnc'], help='Dataset name is either ukbb or gnc')    
    parser.add_argument('--num_channels', type=int, required=True, choices=[1, 4], help='Number of channels to be used. Either 1 or 4.')
    args = parser.parse_args()
    
    nnunet_folder = os.path.abspath(args.nnunet_folder)
    prediction_folder = os.path.abspath(args.prediction_folder)
    dataset_name = args.dataset_name
    num_channels = args.num_channels
    
    log_file_path = get_log_file(basename=os.path.basename(prediction_folder) + '_log.txt')
    logging.basicConfig(
        format='%(asctime)s: %(message)s',  
        level=logging.NOTSET, 
        handlers=[
            logging.FileHandler(filename=log_file_path, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
    ])
    
    logging.info('Started predict...')
    logging.info('CUDA_VISIBLE_DEVICES: {0}'.format(os.environ['CUDA_VISIBLE_DEVICES']))
    logging.info('RESULTS_FOLDER: {0}'.format(os.environ['RESULTS_FOLDER']))
    logging.info('nnunet_folder: {0}'.format(nnunet_folder))
    logging.info('prediction_folder: {0}'.format(prediction_folder))
    logging.info('dataset_name: {0}'.format(dataset_name))
    logging.info('num_channels: {0}\n'.format(num_channels))
    
    
    if 'CUDA_VISIBLE_DEVICES' not in os.environ:
        raise('The environment variable CUDA_VISIBLE_DEVICES must be set. This is the GPU number which nnUNet will use for predictions.')
    
    if 'RESULTS_FOLDER' not in os.environ:
        raise('The environment variable RESULTS_FOLDER must be set. This is the place where nnUNet will look for the models.')
    
    os.makedirs(os.environ['RESULTS_FOLDER'], exist_ok=True)
    
    model = '3d_fullres'
    folds = 'all'
    
    if dataset_name == 'ukbb' and num_channels == 4:
        task_name = '501'
        retrieval_url = 'https://gitlab.com/turkaykart/ukbb-gnc-abdominal-segmentation/-/raw/main/ukbb_4ch_model.zip?inline=false'
        retrival_name = 'ukbb_4ch_model.zip'
    elif dataset_name == 'ukbb' and num_channels == 1:
        task_name = '502'
        retrieval_url = 'https://gitlab.com/turkaykart/ukbb-gnc-abdominal-segmentation/-/raw/main/ukbb_1ch_model.zip?inline=false'
        retrival_name = 'ukbb_1ch_model.zip'
    elif dataset_name == 'gnc' and num_channels == 4:
        task_name = '503'
        retrieval_url = 'https://gitlab.com/turkaykart/ukbb-gnc-abdominal-segmentation/-/raw/main/gnc_4ch_model.zip?inline=false'
        retrival_name = 'gnc_4ch_model.zip'
    elif dataset_name == 'gnc' and num_channels == 1:
        task_name = '504'
        retrieval_url = 'https://gitlab.com/turkaykart/ukbb-gnc-abdominal-segmentation/-/raw/main/gnc_1ch_model.zip?inline=false'
        retrival_name = 'gnc_1ch_model.zip'
    
    model_location = os.path.join(os.environ['RESULTS_FOLDER'], 'nnUNet', model, 'Task{0}_{1}_{2}ch'.format(task_name, dataset_name, num_channels), 'nnUNetTrainerV2__nnUNetPlansv2.1', folds, 'model_final_checkpoint.model')
    logging.info('model_location: {0}\n'.format(model_location))
    if os.path.isfile(model_location):
        logging.info('model exists at the location...')
    else:
        logging.info('Downloading: [Dataset: {0}, Number_of_Channels:{1}]...'.format(dataset_name, num_channels))
        urllib.request.urlretrieve(retrieval_url, retrival_name)
        os.chmod(retrival_name, 0o755)
        zip_ref = zipfile.ZipFile(retrival_name, 'r')
        zip_ref.extractall(os.environ['RESULTS_FOLDER'])
        zip_ref.close()
        os.system('chmod -R 755 {0}'.format(os.environ['RESULTS_FOLDER']))
        logging.info('model is downloaded.')
    
    os.makedirs(prediction_folder, exist_ok=True)
    shutil.copy2(os.path.join(nnunet_folder, 'conversion.pkl'), os.path.join(prediction_folder, 'conversion.pkl'))
    shutil.copy2(os.path.join(nnunet_folder, 'dataset.json'), os.path.join(prediction_folder, 'dataset.json'))
    
    logging.info('dataset.json: {0}'.format(os.path.join(prediction_folder, 'dataset.json')))
    logging.info('conversion.pkl: {0}\n'.format(os.path.join(prediction_folder, 'conversion.pkl')))
    
    sys.argv = [sys.argv[0],
                '--input_folder', nnunet_folder, 
                '--output_folder', prediction_folder, 
                '--task_name', task_name, 
                '--model', model, 
                '--folds', folds]
     
    logging.info('sys.argv: {0}\n'.format(sys.argv))
    
    ps.main()

    logging.info('Finished predict...')
    shutil.copy2(log_file_path, get_log_file(dir_path=prediction_folder, basename=os.path.basename(prediction_folder) + '_log.txt'))
    os.remove(log_file_path)


if __name__ == '__main__':
    main()

