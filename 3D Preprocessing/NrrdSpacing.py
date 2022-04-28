from cmath import nan
from hashlib import new
from math import floor
import os, nrrd, json, numpy as np
import cupy as cp
import cupyx.scipy.ndimage
import scipy.ndimage
import time


def exportNormalisedNrrdAndAnnotation(nrrdFilePath=None, annotationFilePath=None, exportNrrdPath=None, exportAnnotationPath=None, debug=False):
	if nrrdFilePath is None or annotationFilePath is None or (exportAnnotationPath is None and exportNrrdPath is None and not debug):
		return
	
	if exportNrrdPath is not None:
		if not os.path.exists(exportNrrdPath):
			os.makedirs(exportNrrdPath)
	if exportAnnotationPath is not None:
		if not os.path.exists(exportAnnotationPath):
			os.makedirs(exportAnnotationPath)

	nrrdFileName = os.path.basename(nrrdFilePath)
	annotationFileName = os.path.basename(annotationFilePath)

	nrrdFileData, nrrdFileHeader = nrrd.read(nrrdFilePath, index_order='C')
	#print(nrrdFileData.dtype)scipy.ndimage.zoom

	space_directions = nrrdFileHeader['space directions']
	origin = nrrdFileHeader['space origin']

	m_RAS_To_IJK = np.array([
			[1 / space_directions[1, 0], 0, 0, -origin[0]/space_directions[1, 0]],
			[0, 1 / space_directions[2, 1], 0, -origin[1]/space_directions[2, 1]],
			[0, 0, 1 / space_directions[3, 2], -origin[2]/space_directions[3, 2]],
			[0, 0, 0, 1],
		])

	m_old_to_new = np.array([
			[space_directions[1, 0], 0, 0, 0],
			[0, space_directions[2, 1], 0, 0],
			[0, 0, space_directions[3, 2], 0],
			[0, 0, 0, 1],
		])
	
	
	if exportNrrdPath is not None or debug:
		print("Exporting Adjusted NRRD For", os.path.basename(nrrdFilePath), '...')
		if os.path.isfile(os.path.join(exportNrrdPath, nrrdFileName)) and os.path.exists(os.path.join(exportNrrdPath, nrrdFileName)) and not debug:
			print('File Exists')
		else:
			time_start = time.process_time()
			data_shape = np.array(nrrdFileData.shape)
			new_data_array = np.empty(np.rint(data_shape*np.array([space_directions[3, 2], space_directions[2, 1], space_directions[1, 0], 1])).astype(int), dtype=np.float64)

			for t in range(new_data_array.shape[3]):
				new_data_array[:,:,:,t] = cupyx.scipy.ndimage.zoom(cp.array(nrrdFileData[:,:,:,t], dtype=cp.float64), [space_directions[3, 2], space_directions[2, 1], space_directions[1, 0]], output=cp.float64).get()

			new_data_array[new_data_array>254.5] = 255
			new_data_array[new_data_array<0.5] = 0

			new_data_array = new_data_array.astype(np.uint8)

			elapsed_time = time.process_time() - time_start
			print('Zoom DONE. Zoom Time used:', elapsed_time)
			time_start = time.process_time()

			newNrrdHeader = {}
			for key, val in nrrdFileHeader.items():
				if key == 'type' or key == 'endian' or key == 'dimension' or key == 'sizes':
					continue
				newNrrdHeader[key] = val
				#print(key, val)
			
			newNrrdHeader['space directions'] = [[nan, nan, nan], [1, 0, 0], [0, 1, 0], [0, 0, 1]]
			newNrrdHeader['space origin'] = [0, 0, 0]

			if exportNrrdPath is not None:
				nrrd.write(os.path.join(exportNrrdPath, nrrdFileName), new_data_array, header=newNrrdHeader, index_order='C')
			elapsed_time2 = time.process_time() - time_start
			print('Export DONE. Export Time used:', elapsed_time2)
			print('Total Time used:', elapsed_time + elapsed_time2)
			print('--------------------------------------------------')



	if exportAnnotationPath is not None:
		with open(annotationFilePath, 'r') as f:
			jsonData = json.load(f)
		
		jsonData['adjusted'] = {
			'oldSpacing': [space_directions[1, 0], space_directions[2, 1], space_directions[3, 2]],
			'points': [],
			'planes': [],
		}

		for point_data in jsonData['fidData']:
			jsonData['adjusted']['points'].append({
				'Structure Name': point_data['Structure Name'],
				'Position-IJK': (np.array(point_data['Position-IJK']) * np.array([space_directions[1, 0], space_directions[2, 1], space_directions[3, 2]])).tolist(),
				'View Name': point_data['View Name'],
				'Time': point_data['Time'],
				'Time Index': point_data['Time Index'],
			})
		
		for plane_data in jsonData['planeData']:
			colour = plane_data['colour']
			if 'SliceToIJK' in plane_data:
				m_slice_to_IJK = np.array(plane_data['SliceToIJK']).reshape(4, 4)
			else:
				m_slice_to_RAS = np.array(plane_data[colour]['SliceToRAS']).reshape(4, 4)
				m_slice_to_IJK = np.matmul(m_RAS_To_IJK, m_slice_to_RAS)
			m_slice_to_new_IJK = np.matmul(m_old_to_new, m_slice_to_IJK)

			jsonData['adjusted']['planes'].append({
				'FieldOfView': plane_data[colour]['FieldOfView'],
				'Dimensions': plane_data[colour]['Dimensions'],
				'Origin': plane_data[colour]['Origin'],
				'SliceToIJK': m_slice_to_new_IJK.flatten().tolist(),
				'view': plane_data['view'],
				'timeIndex': plane_data['timeIndex'],
			})
		
		with open(os.path.join(exportAnnotationPath, annotationFileName), 'w+') as f:
			json.dump(jsonData, f)
		





if __name__ == '__main__':

	ANNOTATION_PATH = 'E:/Datasets/Annotations/All Annotations/Normal Annotations/11-10-2021-annotations/PWHOR190733599Q_11Oct2021_CWJKF3OP_3DQ.json'
	NRRD_PATH = 'E:/Datasets/Echocardio/CU/11-10-2021-3d-nrrd/PWHOR190733599Q_11Oct2021_CWJKF3OP_3DQ.seq.nrrd'
	EXPORT_PATH = 'E:/FYP/Nrrd Spacing/Normal-Export-gpu2'

	exportCorrectNrrdAndAnnotation(nrrdFilePath=NRRD_PATH, annotationFilePath=ANNOTATION_PATH, exportNrrdPath=EXPORT_PATH, exportAnnotationPath=None, debug=True)
	

	exit(0)
	
	NRRD_NORMAL = 'E:/FYP/Nrrd Spacing/Normal-Export-cpu/PWHOR190733599Q_11Oct2021_CWJKF3OP_3DQ.seq.nrrd'		
	NRRD_GPU = 'E:/FYP/Nrrd Spacing/Normal-Export-gpu2/PWHOR190733599Q_11Oct2021_CWJKF3OP_3DQ.seq.nrrd'		

	nrrdFileDataCpu, nrrdFileHeaderCpu = nrrd.read(NRRD_NORMAL, index_order='C')
	nrrdFileDataGpu, nrrdFileHeaderGpu = nrrd.read(NRRD_GPU, index_order='C')

	same_array = nrrdFileDataCpu == nrrdFileDataGpu
	diff_array2 = nrrdFileDataCpu != nrrdFileDataGpu
	diff_array = np.absolute(nrrdFileDataCpu[np.logical_not(same_array)] - nrrdFileDataGpu[np.logical_not(same_array)])
	print(np.prod(nrrdFileDataCpu.shape) - np.sum(same_array))
	print(np.sum(diff_array2))
	print(diff_array.shape[0]/np.prod(nrrdFileDataCpu.shape)*100, '%')
	print(diff_array.shape[0], np.prod(nrrdFileDataCpu.shape))
	print(np.mean(diff_array))
	print(np.max(diff_array))
	print(np.min(diff_array))

	print('==================================')

	print(np.sum(nrrdFileDataCpu[nrrdFileDataCpu==255]))

	exit(0)
	
	

	