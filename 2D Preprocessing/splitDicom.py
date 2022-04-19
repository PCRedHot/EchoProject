import os


INPUT_PATH = 'D:/EchoPatient2DData/2021-10-11/DICOM'
OUTPUT_PATH = 'D:/EchoPatient2DData/2021-10-11/DICOM2'
MAX_COUNT = 120

dicom_file_list = os.listdir(INPUT_PATH)

if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)

i = 1
file_count = 0
for dicom_file in dicom_file_list:
    if file_count >= MAX_COUNT:
        file_count = 0
        i += 1
    dest_folder_path = os.path.join(OUTPUT_PATH, str(i))
    if not os.path.exists(dest_folder_path):
        os.makedirs(dest_folder_path)
    os.rename(os.path.join(INPUT_PATH, dicom_file), os.path.join(dest_folder_path, dicom_file))
    file_count += 1

