# Abdominal Organ Segmentations of UK Biobank (UKBB) and German National Cohort (GNC) Studies

If you utilize this repository in your projects, please consider citing our work:

```
[1] Kart, T., Fischer, M., et. al. Deep Learning‐Based Automated Abdominal Organ Segmentation
in the UK Biobank and German National Cohort Magnetic Resonance Imaging Studies. Investigative Radiology
56(6):p 401-408, June 2021. doi: 10.1097/RLI.0000000000000755

[2] Kart, T., et al. Automated imaging-based abdominal organ segmentation and quality control
in 20,000 participants of the UK Biobank and German National Cohort Studies. Sci Rep 12, 18733 (2022).
doi: 10.1038/s41598-022-23632-9

[3] Gatidis S, Kart T, et.al. Better Together: Data Harmonization and Cross-Study Analysis of
Abdominal MRI Data From UK Biobank and the German National Cohort. Invest Radiol. 2023 May 1;58(5):346-354.
doi: 10.1097/RLI.0000000000000941.
```

## Getting Started

First, check dependencies in requirements.txt and make sure they are installed in your environment. Then, abdominal organ segmentations for the UKBB and GNC studies can be obtained with 4 straightforward steps detailed below. 

### Requirements
If you want to install them, simply run the following:

```
pip install -r requirements.txt
```

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
Download and put whole-body MRI data into a single directory. (Note: you can put 1st and 2nd visits of a subject in the same directory.)


### Step 1: Run extract_ukbb.py or extract_gnc.py 
This is the initial pre-processing step (only run either UKBB or GNC script depending on your source of data).

```
python extract_ukbb.py 
    --zip_folder my_original_data/ 
    --nifti_folder my_nifti_data/
```
The script takes into account of multiple visits in the UK Biobank. Therefore, the ```my_nifti_data``` directory may include different visits of the same subject as separate subdirectories. We follow the UK Biobank's naming convention so these subdirectories will be named as "SubjectID_VisitID".

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

### Maintainer: Turkay Kart

If you have any questions, please reach me by email or Twitter:

Email: t.kart@imperial.ac.uk\
Twitter: [@turkaykart](https://twitter.com/turkaykart)


