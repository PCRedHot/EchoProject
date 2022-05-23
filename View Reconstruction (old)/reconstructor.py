from ViewReconstruction import ViewReconstructor
import os, json


NRRD_FILES_PATHS = {}
for root, dirs, files in os.walk('E:/Datasets/Echocardio/CU/'):
    for file in files:
        NRRD_FILES_PATHS[file[0:-9]] = os.path.join(root, file)

JSON_FILES_PATHS = {}
for root, dirs, files in os.walk('E:/Datasets/Annotations/Unexported Annotations'):
    for file in files:
        JSON_FILES_PATHS[file[0:-5]] = os.path.join(root, file)

REFERENCE_FILE_PATH = 'E:/FYP/View Reconstruction/reference_points.json'
EXPORT_PATH = 'E:/FYP/View Reconstruction/Exports'

for file_name, json_file_path in JSON_FILES_PATHS.items():
    nrrd_file_path = NRRD_FILES_PATHS[file_name]
    export_path = os.path.join(EXPORT_PATH, file_name)
        
    pointData = {}
    with open(json_file_path, 'r') as f:
        labelled_data = json.load(f)
        fidData = labelled_data['fidData']
        planeData = labelled_data['planeData']
        for viewData in fidData:
            view = viewData['View Name']
            if view not in pointData:
                pointData[view] = []
            pointData[view].append({
                'structure': viewData['Structure Name'].replace('.', ''),
                'ijk': viewData['Position-IJK']+[1],
            })

    viewReconstructor = ViewReconstructor()
    viewReconstructor.setup(nrrd_file_path, REFERENCE_FILE_PATH)
    viewReconstructor.exportAll(pointData=pointData, exportFilePath=export_path, uniqueName=file_name, showPoint=False, debug=False, planeIfError=True, planeInfoMaps=planeData)




