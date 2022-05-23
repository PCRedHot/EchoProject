
import os, pandas as pd
import csv, json, nrrd, numpy as np


ROOT_PATH = 'E:/Datasets/Annotation Analysis'
ANNOTATIONS_PATH = 'E:/Datasets/All Annotations'
DATA_FILE_PATH = 'E:/Datasets/Annotation Analysis/Data.csv'
NRRD_PATH = 'E:/Datasets/Echocardio/CU/'

NRRD_FILES_PATHS = {}
for root, dirs, files in os.walk(NRRD_PATH):
    for file in files:
        NRRD_FILES_PATHS[file[0:-9]] = os.path.join(root, file)

JSON_FILES_PATHS = {}
for root, dirs, files in os.walk(ANNOTATIONS_PATH):
    for file in files:
        JSON_FILES_PATHS[file[0:-5]] = os.path.join(root, file)

point_total_count = 0
point_count = {}

with open(DATA_FILE_PATH, 'r') as data_file:
    reader = csv.reader(data_file)
    for i, line in enumerate(reader):
        if i == 0:
            continue
        view = line[0].strip('., ')

        structures_in_csv = line[1].split(',')
        structure_list = []
        for structure in structures_in_csv:
            structure_list.append(structure.strip('., '))
        
        point_count[view] = {x: 0 for x in structure_list}

for file_name, json_file_path in JSON_FILES_PATHS.items():
    point_total_count += 1
    with open(json_file_path, 'r') as json_file:
        json_data = json.load(json_file)
        fid_data = json_data['fidData']
        for fid in fid_data:
            view = fid['View Name'].strip('., ')
            structure = fid['Structure Name'].strip('., ')
            point_count[view][structure] += 1

#print(point_count)
#print(point_total_count)


pointsCenters = {}
nrrdFileHeaders = {}
nrrdFileDataShapes = {}
nrrdTimeLengths = {}

centers = []
for file_name, json_file_path in JSON_FILES_PATHS.items():
    nrrd_file_path = NRRD_FILES_PATHS[file_name]
    f = nrrd.read(nrrd_file_path, index_order='C')
    nrrdFileHeader = f[1]
    nrrdFileDataShape = np.array([f[0].shape[2], f[0].shape[1], f[0].shape[0]])
    nrrdTimeLength = f[0].shape[3]

    points = []
    with open(json_file_path, 'r') as json_file:
        json_data = json.load(json_file)
        fid_data = json_data['fidData']
        for fid in fid_data:
            view = fid['View Name'].strip('., ')
            structure = fid['Structure Name'].strip('., ')
            if point_count[view][structure] == point_total_count:
                points.append(fid['Position-IJK'])
    
    points = np.array(points)
    points_mean = np.mean(points, axis=0) / nrrdFileDataShape

    pointsCenters[file_name] = points_mean
    nrrdFileHeaders[file_name] = nrrdFileHeader
    nrrdFileDataShapes[file_name] = nrrdFileDataShape
    nrrdTimeLengths[file_name] = nrrdTimeLength
    centers.append(points_mean)
    
    print(np.mean(points, axis=0) / nrrdFileDataShape)
    
centers = np.array(centers)

center = np.mean(centers, axis=0)


for file_name, json_file_path in JSON_FILES_PATHS.items():
    
    with open(json_file_path, 'r') as json_file:
        json_data = json.load(json_file)
        fid_data = json_data['fidData']
        for fid in fid_data:
            view = fid['View Name'].strip('., ')
            structure = fid['Structure Name'].strip('., ')
            
    



exit(0)

data = {}
data_count = 0
with open(DATA_FILE_PATH, 'r') as data_file:
    reader = csv.reader(data_file)
    for i, line in enumerate(reader):
        if i == 0:
            continue
        view = line[0].strip('., ')

        structures_in_csv = line[1].split(',')
        structure_list = []
        for structure in structures_in_csv:
            structure_list.append(structure.strip('., '))
        
        data[view] = {x: 0 for x in structure_list}



annotation_folders = os.listdir(ANNOTATIONS_PATH)
for annotation_folder in annotation_folders:
    annotation_folder_path = os.path.join(ANNOTATIONS_PATH, annotation_folder)
    annotation_files = os.listdir(annotation_folder_path)
    for annotation_file in annotation_files:
        annotation_file_path = os.path.join(annotation_folder_path, annotation_file)
        data_count += 1
        with open(annotation_file_path, 'r') as json_file:
            json_data = json.load(json_file)
            fid_data = json_data['fidData']
            for fid in fid_data:
                view = fid['View Name'].strip('., ')
                structure = fid['Structure Name'].strip('., ')
                data[view][structure] += 1


for _, view_data in data.items():
    for structure_key, structure_val in view_data.items():
        view_data[structure_key] = structure_val/data_count

print(data)
print(data_count)