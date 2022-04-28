import os, json, sys
from NrrdSpacing import exportNormalisedNrrdAndAnnotation


NRRD_PATH = 'E:/Datasets/Echocardio/CU/'
ANNOTATION_PATH = 'E:/Datasets/Annotations/Unadjusted Annotations/'
# REFERENCE_FILE_PATH = 'E:/FYP/View Reconstruction/reference_points.json'
ADJUSTED_NRRD_EXPORT_PATH = 'E:/Datasets/Echocardio/CU Adjusted/'
ADJUSTED_ANNOTATION_EXPORT_PATH = 'E:/Datasets/Annotations/Adjusted Annotations'


NRRD_FILES_PATHS = {}
for root, dirs, files in os.walk(NRRD_PATH):
    for file in files:
        NRRD_FILES_PATHS[file[0:-9]] = os.path.join(root, file)

JSON_FILES_PATHS = {}
for root, dirs, files in os.walk(ANNOTATION_PATH):
    for file in files:
        JSON_FILES_PATHS[file[0:-5]] = os.path.join(root, file)



for file_name, json_file_path in JSON_FILES_PATHS.items():
    nrrd_file_path = NRRD_FILES_PATHS[file_name]
    nrrd_export_path = os.path.join(ADJUSTED_NRRD_EXPORT_PATH, os.path.relpath(nrrd_file_path, NRRD_PATH)[:-len(os.path.basename(nrrd_file_path))])
    json_export_path = os.path.join(ADJUSTED_ANNOTATION_EXPORT_PATH, os.path.relpath(json_file_path, ANNOTATION_PATH)[:-len(os.path.basename(json_file_path))])
    
    exportNormalisedNrrdAndAnnotation(nrrdFilePath=nrrd_file_path, annotationFilePath=json_file_path, exportNrrdPath=nrrd_export_path, exportAnnotationPath=None, debug=False)