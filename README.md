# Abdominal Organ Segmentations of UK Biobank (UKBB) and German National Cohort (GNC) Studies

## Getting Started

Abdominal organ segmentations for UKBB and GNC studies can be obtained with 4 straightforward steps below.

## Obtaining Predictions

### Arguments
Folder names can be set as preferred. Details of arguments that will be used in the script are as follows:
```
zip_folder        = Folder that contains downloaded zip files for each subject. 
nifti_folder      = Folder that contains subjects with stitched volumes as .nii.gz files
nnunet_folder     = Folder that contains subjects formatted for nnUNet
prediction_folder = Folder that contains final predictions
output_folder     = Folder that contains predictions with the original naming
dataset_name      = Either ukbb or gnc
num_channels      = Either 1 or 4
```

### Step 0: Download data 
Download and put whole-body MRI data into a single directory


### Step 1: Run extract_ukbb.py or extract_gnc.py 
This is the initial pre-processing step (only run either UKBB or GNC script depending on your source of data).

```
python extract_ukbb.py 
    --zip_folder my_original_data/ 
    --nifti_folder my_nifti_data/
```


### Step 2: Run convert2nnunet.py 
The script converts files to the nnUNet naming.

```
python convert2nnunet.py 
    --nifti_folder my_nifti_data/ 
    --nnunet_folder my_nnunet_data/ 
    --dataset_name ukbb 
    --num_channels 4
```


### Step 3: Run predict.py 
The script generates the predictions for abdominal organs (example below is for UKBB with 4-channel model).

```
CUDA_VISIBLE_DEVICES=0 
RESULTS_FOLDER=models/ 
python predict.py 
    --nnunet_folder my_nnunet_data/ 
    --prediction_folder my_predictions/ 
    --dataset_name ukbb 
    --num_channels 4
```


### Step 4: Run convert2original.py 
The script converts predictions back to the original naming.

```
python convert2original.py 
    --prediction_folder my_predictions/ 
    --output_folder my_outputs/
```


All organ segmentations are saved into the output folder with their original naming convention.

