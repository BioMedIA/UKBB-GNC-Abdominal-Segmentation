import sys
import argparse
import logging
import shutil 
import pickle
import glob 
import os


def load_pickle(pickle_path):
    with open(pickle_path, 'rb') as f:
        pkl_file = pickle.load(f)
    return pkl_file


def format_back(conversion_map, prediction_folder, output_folder):

    pred_paths = glob.glob(os.path.join(prediction_folder, '*.nii.gz'))
    pred_paths.sort()

    conversion_cnt = 0
    subjects_with_no_predictions = []
    for entry in conversion_map:
        
        orig_subject = entry['orig_subject']
        new_subject_path = os.path.join(output_folder, orig_subject, '')
        
        nnunet_subject = entry['nnunet_subject']
        nnunet_pred_path = os.path.join(prediction_folder, nnunet_subject + '.nii.gz')
        
        new_pred_path = os.path.join(new_subject_path, 'prd.nii.gz')

        if nnunet_pred_path in pred_paths:
            logging.info('Found prediction [cnt: {0}] for subject id [{1}] and nnunet id [{2}]: {3}'.format(conversion_cnt + 1, orig_subject, nnunet_subject, new_pred_path))
            os.makedirs(new_subject_path, exist_ok=True)
            shutil.copy2(nnunet_pred_path, new_pred_path)
            conversion_cnt += 1
        else:
            logging.info('NOT Found prediction for subject id [{0}] and nnunet id [{1}]...\n'.format(orig_subject, nnunet_subject))
            subjects_with_no_predictions.append(orig_subject)
    
    logging.info('Number of converted predictions: {0}\n'.format(conversion_cnt))
    logging.info('Subjects with no prediction: {0}\n'.format(subjects_with_no_predictions))


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
    parser.add_argument('--prediction_folder', required=True, help='Folder that contains nnunet predictions')
    parser.add_argument('--output_folder', required=True, help='Folder that contains predictions with the original naming')
    args = parser.parse_args()
    
    prediction_folder = os.path.abspath(args.prediction_folder)
    output_folder = os.path.abspath(args.output_folder)
    
    log_file_path = get_log_file(basename=os.path.basename(output_folder) + '_log.txt')
    logging.basicConfig(
        format='%(asctime)s: %(message)s',  
        level=logging.NOTSET, 
        handlers=[
            logging.FileHandler(filename=log_file_path, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
    ])
    
    logging.info('Started convert2original...')
    logging.info('prediction_folder: {0}'.format(prediction_folder))
    logging.info('output_folder: {0}\n'.format(output_folder))
    
    os.makedirs(output_folder, exist_ok=True)
    conversion_map = load_pickle(os.path.join(prediction_folder, 'conversion.pkl'))
    
    logging.info('conversion.pkl: {0}\n'.format(os.path.join(prediction_folder, 'conversion.pkl')))

    format_back(conversion_map, prediction_folder, output_folder)

    logging.info('Finished convert2original...')
    shutil.copy2(log_file_path, get_log_file(dir_path=output_folder, basename=os.path.basename(output_folder) + '_log.txt'))
    os.remove(log_file_path)


if __name__ == '__main__':
    main()
    

