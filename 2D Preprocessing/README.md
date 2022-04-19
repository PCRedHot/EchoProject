# 2D Preprocessing
![image](https://user-images.githubusercontent.com/43814396/164041914-267a37b3-5794-4461-97cd-7dd2e6280f72.png)
![image](https://user-images.githubusercontent.com/43814396/164042174-83e117fe-4cd6-445b-aeff-755a91b7d1c9.png)

## Remove 3D Files
![image](https://user-images.githubusercontent.com/43814396/164043400-d5bc0ebe-7acc-4e7c-a671-28731d9c6cd8.png)
![image](https://user-images.githubusercontent.com/43814396/164043454-958a68fa-60d3-4c97-a8b3-5dbba256de98.png)

## Output PNG Files
* Split the DICOM files into muliple batches if needed

![image](https://user-images.githubusercontent.com/43814396/164043638-5756634f-b4e9-4ced-95ba-4516dd32831b.png)

* Check the box of create sub-folders for Patient, Study, Series

![image](https://user-images.githubusercontent.com/43814396/164043862-504ee482-bad5-4afa-999c-4f2c1e2d12f1.png)

## Filtering, Greyscale, Remove Overlay
* Done by 2DImageExtractAndPreprocessing.py
* Multi-view Classification Network: https://drive.google.com/drive/folders/1U4SHo3a5arXDhl8FeWQnba1HxEeyes-O?usp=sharing

Inputs:
* MULTI_VIEW_MODEL_PATH: Path to saved network
* RAW_PNG_PATH: Path to pngs 

Outputs:
* RNG_OUTPUT_PATH: Path to output processed pngs
* MASK_OUTPUT_PATH: Path to output overlay masks

## Combine PNG to MP4
* Done by 2dMp4Converter.py
* Requires ffmpeg
* Remember not to delete the DICOM files as it is required here for framerate!

Inputs:
* PNG_PATH: Path to Processed PNG Dir
* DICOM_PATH: Path to DICOM Dir 

Outputs:
* RNG_OUTPUT_PATH: Path to output mp4

