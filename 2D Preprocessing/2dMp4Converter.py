import os, pydicom

PNG_PATH = 'D:/EchoPatient2DData/2021-10-08/PNG Output'
DICOM_PATH = 'D:/EchoPatient2DData/2021-10-08/DICOM'

TO_PATH = 'D:/EchoPatient2DData/2021-10-08/MP4'

if not os.path.exists(TO_PATH):
    os.makedirs(TO_PATH)


dicom_file_path_list = {}
for root, dirs, files in os.walk(DICOM_PATH):
    for name in files:
        dicom_file_path_list[name] = os.path.join(root, name)

png_file_folder_path_list = {}
for root, dirs, files in os.walk(PNG_PATH):
    for name in files:
        if not name.endswith('.png'):
            continue
        sequence_id = name.split('_')[0]
        if sequence_id not in png_file_folder_path_list:
            png_file_folder_path_list[sequence_id] = root

for sequence_id, png_folder_path in png_file_folder_path_list.items():
    dicom_file_path = dicom_file_path_list[sequence_id]
    ds = pydicom.dcmread(dicom_file_path)
    framerate = str(round(1000 / ds.FrameTime, 2))

    img_path = os.path.join(png_folder_path, sequence_id+'_Frame%03d_out.png')

    output_file_path = os.path.join(TO_PATH, sequence_id+'.mp4')

    os.system('ffmpeg -framerate ' + framerate + ' -i \"' + img_path + '\" \"' + output_file_path + '\"')

