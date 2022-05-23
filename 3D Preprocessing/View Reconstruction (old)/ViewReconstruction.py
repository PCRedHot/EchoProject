import nrrd, os
import numpy as np
from PIL import Image
import scipy.ndimage
import cv2
import json


def getSliceToRASMatrixFromThreePoints(pts, orientation=0):	# CORRECT
	"""
	pts: a numpy array (3, 3) or (4, 3) containing the 3 RAS points on a plane
	orientation: 0: para-Axial, 1: para-Sagittal, 2: para-Coronal, default = 0
	return: Slice_to_RAS_Matrix - a 4x4 numpy array matrix
			return False if error
	"""
	if not 0 <= orientation <= 2:
		return False

	pts_RAS = np.array(pts)[0:3, ]

	n = np.cross(pts_RAS[:, 1] - pts_RAS[:, 0], pts_RAS[:, 2] - pts_RAS[:, 0])
	t = pts_RAS[:, 1] - pts_RAS[:, 0]
	p = pts_RAS.mean(axis=1)
	# C = N x T
	# T = C x N
	c = np.cross(n, t)
	t = np.cross(c, n)

	# Normalize the vectors
	n = n / np.linalg.norm(n)
	t = t / np.linalg.norm(t)
	c = c / np.linalg.norm(c)

	# get negative vectors
	negN = -n
	# negT = -t
	negC = -c

	# Set the return matrix as identity matrix
	m_Slice_to_RAS = np.array([
		[1, 0, 0, 0],
		[0, 1, 0, 0],
		[0, 0, 1, 0],
		[0, 0, 0, 1],
	], dtype=float)

	m_Slice_to_RAS[0, 3] = p[0]
	m_Slice_to_RAS[1, 3] = p[1]
	m_Slice_to_RAS[2, 3] = p[2]

	if orientation == 0:
		m_Slice_to_RAS[0, 2] = n[0]
		m_Slice_to_RAS[1, 2] = n[1]
		m_Slice_to_RAS[2, 2] = n[2]

		m_Slice_to_RAS[0, 1] = c[0]
		m_Slice_to_RAS[1, 1] = c[1]
		m_Slice_to_RAS[2, 1] = c[2]

		m_Slice_to_RAS[0, 0] = t[0]
		m_Slice_to_RAS[1, 0] = t[1]
		m_Slice_to_RAS[2, 0] = t[2]

	elif orientation == 1:
		m_Slice_to_RAS[0, 2] = t[0]
		m_Slice_to_RAS[1, 2] = t[1]
		m_Slice_to_RAS[2, 2] = t[2]

		m_Slice_to_RAS[0, 1] = negN[0]
		m_Slice_to_RAS[1, 1] = negN[1]
		m_Slice_to_RAS[2, 1] = negN[2]

		m_Slice_to_RAS[0, 0] = negC[0]
		m_Slice_to_RAS[1, 0] = negC[1]
		m_Slice_to_RAS[2, 0] = negC[2]

	else:
		m_Slice_to_RAS[0, 2] = c[0]
		m_Slice_to_RAS[1, 2] = c[1]
		m_Slice_to_RAS[2, 2] = c[2]

		m_Slice_to_RAS[0, 1] = negN[0]
		m_Slice_to_RAS[1, 1] = negN[1]
		m_Slice_to_RAS[2, 1] = negN[2]

		m_Slice_to_RAS[0, 0] = t[0]
		m_Slice_to_RAS[1, 0] = t[1]
		m_Slice_to_RAS[2, 0] = t[2]

	return m_Slice_to_RAS

def getXYToSliceMatrix(dimensions=None, fieldOfView=None, sliceOrigin=None):
	"""
	fieldOfView: an array with len 3 that specify the zooming, larger => zoom out
				default: None ([250, 250, 1])
	sliceOrigin: The origin of the XY plane, default: None ([0,0,0])
	return: XY_to_Slice_Matrix - a 4x4 numpy array matrix
	"""
	if fieldOfView is None:
		fieldOfView = [250, 250, 1]
	if sliceOrigin is None:
		sliceOrigin = [0, 0, 0]
	if dimensions is None:
		dimensions = [512, 512, 1]
		#dimensions = (256, 256, 1)

	m_XY_To_Slice = np.array([
		[1, 0, 0, 0],
		[0, 1, 0, 0],
		[0, 0, 1, 0],
		[0, 0, 0, 1],
	], dtype=float)

	for i in range(3):
		spacing = fieldOfView[i] / dimensions[i]
		m_XY_To_Slice[i, i] = spacing
		m_XY_To_Slice[i, 3] = - fieldOfView[i] / 2 + sliceOrigin[i]

	m_XY_To_Slice[2, 3] = 0

	return m_XY_To_Slice

def getXYToRASMatrixFromThreePoints(pts, orientation=0, fieldOfView=None, sliceOrigin=None):
	"""
	pts, orientation: see getSliceToRASMatrixFromThreePoints()
	fieldOfView, origin: see getXYToSliceMatrix()
	return: XY_to_RAS_Matix - a 4x4 nump array matrix
			return False if error
	"""
	m_Slice_to_RAS = getSliceToRASMatrixFromThreePoints(pts, orientation)
	m_XY_to_Slice = getXYToSliceMatrix(fieldOfView=fieldOfView, sliceOrigin=sliceOrigin)
	return np.matmul(m_Slice_to_RAS, m_XY_to_Slice)

POINT_DATA = {}

class ViewReconstructor:
	def __init__(self) -> None:
		# 1. Data File Related
		self.nrrdFileData = None
		self.volume_spacing = None

		# matrix
		self.m_IJK_To_RAS = None
		self.m_RAS_To_IJK = None

		self.PADDING = 500
		self.REFERENCE_POINT = {}
	
	def setup(self, nrrdFilePath=None, referencePointFilePath=None):
		if nrrdFilePath is None:
			return
		f = nrrd.read(nrrdFilePath, index_order='C')
		self.nrrdFileData = f[0]
		nrrdFileHeader = f[1]
		self.num_time = f[0].shape[3]
		
		space_directions = nrrdFileHeader['space directions']
		origin = nrrdFileHeader['space origin']
		self.volume_spacing = np.array([space_directions[1, 0], space_directions[2, 1], space_directions[3, 2]])
		self.m_IJK_To_RAS = np.array([
			[space_directions[1, 0], 0, 0, origin[0]],
			[0, space_directions[2, 1], 0, origin[1]],
			[0, 0, space_directions[3, 2], origin[2]],
			[0, 0, 0, 1],
		])
		self.m_RAS_To_IJK = np.array([
			[1 / space_directions[1, 0], 0, 0, -origin[0]/space_directions[1, 0]],
			[0, 1 / space_directions[2, 1], 0, -origin[1]/space_directions[2, 1]],
			[0, 0, 1 / space_directions[3, 2], -origin[2]/space_directions[3, 2]],
			[0, 0, 0, 1],
		])

		if referencePointFilePath is not None:
			with open(referencePointFilePath, 'r') as f:
				self.REFERENCE_POINT = json.load(f)

	def drawPointsOnImageArray(self, arr=None, coordinates=None):
		if arr is None or coordinates is None:
			return arr

		# To RGB
		arr = np.repeat(arr[:, :, np.newaxis], 3, axis=2)

		for pt in coordinates:
			draw_x_min = int(self.PADDING + pt[0] - 2)
			draw_x_max = int(self.PADDING + pt[0] + 2)
			draw_y_min = arr.shape[0]-int(self.PADDING + pt[1]) - 2
			draw_y_max = arr.shape[0]-int(self.PADDING + pt[1]) + 2

			#print(draw_x_min, draw_x_max, draw_y_min, draw_y_max)

			arr[draw_y_min:draw_y_max+1, draw_x_min:draw_x_max+1, :] = np.array([255,0,0])
		return arr

	""" 	
	def exportReconstructionWithMatrix(self, m_XY_to_IJK=None, viewName=None, exportFilePath=None):
		if m_XY_to_IJK is None or viewName is None or exportFilePath is None:
			return
		
		if not os.path.exists(exportFilePath):
			os.makedirs(exportFilePath)
		
		#dimensions = (256, 256, 1)  # Default dimension
		dimensions = (512, 512, 1)  # Default dimension

		num_image_pix = (dimensions[0]+self.PADDING*2)*(dimensions[1]+self.PADDING*2)
		x2D, y2D = np.meshgrid(range(-self.PADDING, dimensions[0]+self.PADDING), range(dimensions[1]-1+self.PADDING, -1-self.PADDING, -1))
		pts_pix = np.column_stack((x2D.ravel(), y2D.ravel(), np.zeros(num_image_pix), np.ones(num_image_pix)))

		pts_ijk = np.matmul(m_XY_to_IJK, pts_pix.T)[0:3,:]	
		pts_ijk[[0, 2], :] = pts_ijk[[2, 0], :]  # Swap rows as Volume Array is accessed [k, j, i] !!!!!
		
		
		
		x0 = None
		x1 = None
		y0 = None
		y1 = None

		viewName = viewName.replace(' ', '_').replace('-', '_').replace('(', '_').replace(')', '_')
		for t in range(self.num_time):
			voxelArray = self.nrrdFileData[:,:,:,t]
			values = scipy.ndimage.map_coordinates(voxelArray, pts_ijk).reshape((dimensions[0]+self.PADDING*2, dimensions[1]+self.PADDING*2)).astype(dtype=np.uint8)

			if x0 is None:
				try:
					mask = values > 0
					coords = np.argwhere(mask)
					x0, y0 = coords.min(axis=0)
					x1, y1 = coords.max(axis=0) + 1
					x0 = max(0, x0-5)
					y0 = max(0, y0-5)
					x1 = min(values.shape[0], x1+5)
					y1 = min(values.shape[1], y1+5)
				except:
					x0 = 0
					x1 = values.shape[0]
					y0 = 0
					y1 = values.shape[1]
			
			img = Image.fromarray(values[x0:x1, y0:y1], 'L')
			img.save(os.path.join(exportFilePath, viewName + '_Frame' + str(t).rjust(4, '0') + '.png'))



	def exportReconstructionWithPointsWithMatrix(self, m_XY_to_IJK=None, points_ijk=None, viewName=None, exportFilePath=None):
		if m_XY_to_IJK is None or viewName is None or exportFilePath is None:
			return
		
		if points_ijk is None:
			return self.exportReconstructionWithMatrix(m_XY_to_IJK=m_XY_to_IJK, viewName=viewName, exportFilePath=exportFilePath)
		
		if not os.path.exists(exportFilePath):
			os.makedirs(exportFilePath)
		
		#dimensions = (256, 256, 1)  # Default dimension
		dimensions = (512, 512, 1)  # Default dimension

		num_image_pix = (dimensions[0]+self.PADDING*2)*(dimensions[1]+self.PADDING*2)
		x2D, y2D = np.meshgrid(range(-self.PADDING, dimensions[0]+self.PADDING), range(dimensions[1]-1+self.PADDING, -1-self.PADDING, -1))
		pts_pix = np.column_stack((x2D.ravel(), y2D.ravel(), np.zeros(num_image_pix), np.ones(num_image_pix)))

		pts_ijk = np.matmul(m_XY_to_IJK, pts_pix.T)[0:3,:]	
		pts_ijk[[0, 2], :] = pts_ijk[[2, 0], :]  # Swap rows as Volume Array is accessed [k, j, i] !!!!!

		points_xy = np.matmul(np.linalg.inv(m_XY_to_IJK), points_ijk.T)[0:2,:].T
		
		x0 = None
		x1 = None
		y0 = None
		y1 = None

		viewName = viewName.replace(' ', '_').replace('-', '_').replace('(', '_').replace(')', '_')
		for t in range(self.num_time):
			voxelArray = self.nrrdFileData[:,:,:,t]
			values = scipy.ndimage.map_coordinates(voxelArray, pts_ijk).reshape((dimensions[0]+self.PADDING*2, dimensions[1]+self.PADDING*2)).astype(dtype=np.uint8)
			values = self.drawPointsOnImageArray(arr=values, coordinates=points_xy)			
			
			if x0 is None:
				try:
					mask = values[:,:,0] > 0
					coords = np.argwhere(mask)
					x0, y0 = coords.min(axis=0)
					x1, y1 = coords.max(axis=0) + 1
					x0 = max(0, x0-5)
					y0 = max(0, y0-5)
					x1 = min(values.shape[0], x1+5)
					y1 = min(values.shape[1], y1+5)
				except:
					x0 = 0
					x1 = values.shape[0]
					y0 = 0
					y1 = values.shape[1]
			
			img = Image.fromarray(values[x0:x1, y0:y1])
			img.save(os.path.join(exportFilePath, viewName + '_Frame' + str(t).rjust(4, '0') + '.png'))	
	
	
	def exportReconstructions(self, points=None, viewName=None, exportFilePath=None, fieldOfView=None):
		# points: 3 * 4 numpy array

		if points is None or exportFilePath is None or viewName is None:
			return
		pts_IJK = points[0:3].T
		pts_RAS = np.matmul(self.m_IJK_To_RAS, pts_IJK)

		m_XY_to_RAS = getXYToRASMatrixFromThreePoints(pts_RAS, fieldOfView=fieldOfView)
		m_XY_to_IJK = np.matmul(self.m_RAS_To_IJK, m_XY_to_RAS)

		self.exportReconstructionWithMatrix(m_XY_to_IJK=m_XY_to_IJK, viewName=viewName, exportFilePath=exportFilePath)


	def exportAllReconstructions(self, n_points=None, n_viewName=None, exportFilePath=None, fieldOfView=None):
		# n_points: n * (3 * 4 numpy array)

		if n_points is None or exportFilePath is None or n_viewName is None:
			return
		n = len(n_viewName)
		for i in range(n):
			viewName = n_viewName[i].replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
			points = n_points[i]
			outputPath = os.path.join(exportFilePath, viewName)
			if not os.path.exists(outputPath):
				os.makedirs(outputPath)
			self.exportReconstructions(points=points, viewName=viewName, exportFilePath=outputPath, fieldOfView=fieldOfView)

	
	def exportAllReconstructionsWithPoints(self, n_points=None, n_viewName=None, exportFilePath=None, fieldOfView=None):
		# n_points: n * (3 * 4 numpy array)
		
		if n_points is None or exportFilePath is None or n_viewName is None:
			return
		n = len(n_viewName)
		for i in range(n):
			viewName = n_viewName[i].replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
			points = n_points[i]
			outputPath = os.path.join(exportFilePath, viewName)
			if not os.path.exists(outputPath):
				os.makedirs(outputPath)
			self.exportReconstructionsWithPoints(points=points, viewName=viewName, exportFilePath=outputPath, fieldOfView=fieldOfView)
	
	
	def exportReconstructionsWithPoints(self, points=None, viewName=None, exportFilePath=None, fieldOfView=None):
		#points: 3 * 4 numpy array

		if points is None or exportFilePath is None or viewName is None:
			return
		pts_IJK = points[0:3].T
		pts_RAS = np.matmul(self.m_IJK_To_RAS, pts_IJK)

		m_XY_to_RAS = getXYToRASMatrixFromThreePoints(pts_RAS, fieldOfView=fieldOfView)
		m_XY_to_IJK = np.matmul(self.m_RAS_To_IJK, m_XY_to_RAS)

		self.exportReconstructionWithPointsWithMatrix(m_XY_to_IJK=m_XY_to_IJK, points_ijk=points, viewName=viewName, exportFilePath=exportFilePath)

		
	
	"""

	def pointRASToIJK(self, pts):
		return np.matmul(self.m_RAS_To_IJK, pts.T).T
	
	def pointIJKToRAS(self, pts):
		return np.matmul(self.m_IJK_To_RAS, pts.T).T
	
	def exportReconstructionFromPlaneInfoMap(self, map=None, exportFilePath=None, createSubfolder=False):
		if map is None or exportFilePath is None:
			return
		viewName = map['view']

		colourToExport = map['colour']
		colourMap = map[colourToExport]

		m_Slice_to_RAS = np.array(colourMap['SliceToRAS']).reshape(4, 4)
		#m_XY_to_Slice = getXYToSliceMatrix(dimensions=colourMap['Dimensions'], fieldOfView=colourMap['FieldOfView'], origin=colourMap['Origin'])
		m_XY_to_Slice = getXYToSliceMatrix()

		print(m_Slice_to_RAS)

		m_XY_to_IJK = np.matmul(self.m_RAS_To_IJK, np.matmul(m_Slice_to_RAS, m_XY_to_Slice))

		if createSubfolder:
			exportFilePath = os.path.join(exportFilePath, viewName)

		self.exportReconstructionWithMatrix(m_XY_to_IJK=m_XY_to_IJK, viewName=viewName, exportFilePath=exportFilePath)
	
	def exportReconstructionWithPointsFromPlaneInfoMap(self, map=None, exportFilePath=None, createSubfolder=False, points_map=None):
		if map is None or exportFilePath is None:
			return
		viewName = map['view']
		points_ijk = np.array(points_map[viewName])
		#points_ijk = points_map[viewName]

		colourToExport = map['colour']
		colourMap = map[colourToExport]

		m_Slice_to_RAS = np.array(colourMap['SliceToRAS']).reshape(4, 4)
		#m_XY_to_Slice = getXYToSliceMatrix(dimensions=colourMap['Dimensions'], fieldOfView=colourMap['FieldOfView'], origin=colourMap['Origin'])
		m_XY_to_Slice = getXYToSliceMatrix()

		print(m_Slice_to_RAS)

		m_XY_to_IJK = np.matmul(self.m_RAS_To_IJK, np.matmul(m_Slice_to_RAS, m_XY_to_Slice))

		if createSubfolder:
			exportFilePath = os.path.join(exportFilePath, viewName)

		self.exportReconstructionWithPointsWithMatrix(m_XY_to_IJK=m_XY_to_IJK, viewName=viewName, exportFilePath=exportFilePath, points_ijk=points_ijk)
		#self.exportReconstructionWithPointsWithMatrixTEMP(m_XY_to_IJK=m_XY_to_IJK, viewName=viewName, exportFilePath=exportFilePath, points_data=points_ijk)


	def addToPointData(self, m_XY_to_IJK=None, points_data=None, viewName=None):
		if m_XY_to_IJK is None or viewName is None or points_data is None:
			return
		
		m_IJK_to_XY = np.linalg.inv(m_XY_to_IJK)
		
		viewPoints = points_data
		for point in viewPoints:
			point_xy = np.matmul(m_IJK_to_XY, np.array(point['ijk']).T)[0:2].T
			if viewName not in POINT_DATA:
				POINT_DATA[viewName] = []
			POINT_DATA[viewName].append({
				'structure': point['structure'],
				'xy': point_xy.tolist(),
			})
			
	def exportReferencePoints(self, listOfMaps=None, exportFilePath=None, points_map=None):
		for map in listOfMaps:
			if map is None:
				continue
			viewName = map['view']
			points_ijk = np.array(points_map[viewName])
			#points_ijk = points_map[viewName]

			colourToExport = map['colour']
			colourMap = map[colourToExport]

			m_Slice_to_RAS = np.array(colourMap['SliceToRAS']).reshape(4, 4)
			m_XY_to_Slice = getXYToSliceMatrix()
			m_XY_to_IJK = np.matmul(self.m_RAS_To_IJK, np.matmul(m_Slice_to_RAS, m_XY_to_Slice))

			self.addToPointData(m_XY_to_IJK=m_XY_to_IJK, viewName=viewName, points_data=points_ijk)
		print(POINT_DATA)
		with open(exportFilePath, 'w+') as f:
			json.dump(POINT_DATA, f)


	def showMatrixWithPoints(self, points=None):
		if points is None:
			return
		pts_IJK = points.T
		pts_RAS = np.matmul(self.m_IJK_To_RAS, pts_IJK)
		print()

		#dimensions = (256, 256, 1)  # Default dimension
		dimensions = (512, 512, 1) 

		m_Slice_to_RAS = getSliceToRASMatrixFromThreePoints(pts_RAS)
		m_XY_to_Slice = getXYToSliceMatrix()

		m_XY_to_RAS = np.matmul(m_Slice_to_RAS, m_XY_to_Slice)


		print("XY -> Slice:", m_XY_to_Slice)
		print("Slice -> RAS:", m_Slice_to_RAS)
		print("RAS -> IJK:", self.m_RAS_To_IJK)
	
	def showMatrix(self):
		print(self.m_RAS_To_IJK)	
		print(self.m_IJK_To_RAS)





	def exportFromPlaneInfo(self, planeData=None, points=None, viewName=None, exportFilePath=None, uniqueName=False, showPoint=False, debug=False):
		if planeData is None or (points is None and showPoint) or viewName is None or exportFilePath is None:
			return
		
		planeColour = planeData['colour']
		plane_info = planeData[planeColour]

		m_Slice_to_RAS = np.array(plane_info['SliceToRAS']).reshape(4, 4)
		m_XY_to_Slice = getXYToSliceMatrix()

		m_XY_to_IJK = np.matmul(self.m_RAS_To_IJK, np.matmul(m_Slice_to_RAS, m_XY_to_Slice))

		

		# RECONSTRUCT IMAGE
		dimensions = (512, 512, 1)  # Default dimension
		outputViewName = viewName.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')

		num_image_pix = (dimensions[0]+self.PADDING*2)*(dimensions[1]+self.PADDING*2)
		x2D, y2D = np.meshgrid(range(-self.PADDING, dimensions[0]+self.PADDING), range(dimensions[1]-1+self.PADDING, -1-self.PADDING, -1))
		pts_pix = np.column_stack((x2D.ravel(), y2D.ravel(), np.zeros(num_image_pix), np.ones(num_image_pix)))

		pts_ijk = np.matmul(m_XY_to_IJK, pts_pix.T)[0:3,:]	
		pts_ijk[[0, 2], :] = pts_ijk[[2, 0], :]  # Swap rows as Volume Array is accessed [k, j, i] !!!!!


		if showPoint:
			points_ijk = []
			for pointData in points:
				points_ijk.append(pointData['ijk'])
			points_xy = np.matmul(np.linalg.inv(m_XY_to_IJK), np.array(points_ijk).T)[0:2,:].T
		
		x0 = None
		x1 = None
		y0 = None
		y1 = None

		
		for t in range(self.num_time):
			if debug and t > 0:
				break
			voxelArray = self.nrrdFileData[:,:,:,t]
			values = scipy.ndimage.map_coordinates(voxelArray, pts_ijk).reshape((dimensions[0]+self.PADDING*2, dimensions[1]+self.PADDING*2)).astype(dtype=np.uint8)

			if showPoint:
				values = self.drawPointsOnImageArray(values, points_xy)

			if x0 is None:
				try:
					if showPoint:
						mask = values[:,:,0] > 0
					else:
						mask = values > 0
					coords = np.argwhere(mask)
					x0, y0 = coords.min(axis=0)
					x1, y1 = coords.max(axis=0) + 1
					x0 = max(0, x0-5)
					y0 = max(0, y0-5)
					x1 = min(values.shape[0], x1+5)
					y1 = min(values.shape[1], y1+5)
				except:
					x0 = 0
					x1 = values.shape[0]
					y0 = 0
					y1 = values.shape[1]

			if showPoint:
				img = Image.fromarray(values[x0:x1, y0:y1])
			else:
				img = Image.fromarray(values[x0:x1, y0:y1], 'L')
			
			imgOutputName = outputViewName + '_Frame' + str(t).rjust(4, '0') + '.png'
			if uniqueName:
				imgOutputName = uniqueName + '_' + imgOutputName
			if isinstance(exportFilePath, list):
				for path in exportFilePath:
					img.save(os.path.join(path, imgOutputName))
			else:
				img.save(os.path.join(exportFilePath, imgOutputName))		

	def exportAllFromPlaneInfo(self, planeInfoMaps=None, exportFilePath=None, uniqueName=False, showPoint=False, pointData=None, debug=False):
		if planeInfoMaps is None or exportFilePath is None or (showPoint and pointData is None):
			return
		for planeData in planeInfoMaps:
			viewName = planeData['view']
			outputViewName = viewName.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')


			if isinstance(exportFilePath, list):
				for path in exportFilePath:
					outputPath = os.path.join(path, outputViewName)
					if not os.path.exists(outputPath):
						os.makedirs(outputPath)
			else:
				outputPath = os.path.join(exportFilePath, outputViewName)
				if not os.path.exists(outputPath):
					os.makedirs(outputPath)

			planeData = None
			for plane_info in planeInfoMaps:
				if plane_info['view'] == viewName:
					planeData = plane_info
					break
			
			if planeData is None:
				print('No Plane Data Match')
			else:
				self.exportFromPlaneInfo(planeData=planeData, points=None, viewName=viewName, exportFilePath=outputPath, uniqueName=uniqueName, showPoint=showPoint, debug=debug)
			
	def exportAllFromAdjustedPlaneInfo(self, planeInfoMaps=None, exportFilePath=None, uniqueName=False, debug=False):
		if planeInfoMaps is None or exportFilePath is None:
			return
		
		for planeData in planeInfoMaps:
			viewName = planeData['view']
			outputViewName = viewName.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')

			if isinstance(exportFilePath, list):
				for path in exportFilePath:
					outputPath = os.path.join(path, outputViewName)
					if not os.path.exists(outputPath):
						os.makedirs(outputPath)
			else:
				outputPath = os.path.join(exportFilePath, outputViewName)
				if not os.path.exists(outputPath):
					os.makedirs(outputPath)
			

			m_Slice_to_IJK = np.array(planeData['SliceToIJK']).reshape(4, 4)
			m_XY_to_Slice = getXYToSliceMatrix()

			m_XY_to_IJK = np.matmul(m_Slice_to_IJK, m_XY_to_Slice)

			# RECONSTRUCT IMAGE
			dimensions = (512, 512, 1)  # Default dimension

			num_image_pix = (dimensions[0]+self.PADDING*2)*(dimensions[1]+self.PADDING*2)
			x2D, y2D = np.meshgrid(range(-self.PADDING, dimensions[0]+self.PADDING), range(dimensions[1]-1+self.PADDING, -1-self.PADDING, -1))
			pts_pix = np.column_stack((x2D.ravel(), y2D.ravel(), np.zeros(num_image_pix), np.ones(num_image_pix)))

			pts_ijk = np.matmul(m_XY_to_IJK, pts_pix.T)[0:3,:]	
			pts_ijk[[0, 2], :] = pts_ijk[[2, 0], :]  # Swap rows as Volume Array is accessed [k, j, i] !!!!!
			
			x0 = None
			x1 = None
			y0 = None
			y1 = None

			for t in range(self.num_time):
				if debug and t > 0:
					break
				voxelArray = self.nrrdFileData[:,:,:,t]
				values = scipy.ndimage.map_coordinates(voxelArray, pts_ijk).reshape((dimensions[0]+self.PADDING*2, dimensions[1]+self.PADDING*2)).astype(dtype=np.uint8)

				if x0 is None:
					try:
						mask = values > 0
						coords = np.argwhere(mask)
						x0, y0 = coords.min(axis=0)
						x1, y1 = coords.max(axis=0) + 1
						x0 = max(0, x0-5)
						y0 = max(0, y0-5)
						x1 = min(values.shape[0], x1+5)
						y1 = min(values.shape[1], y1+5)
					except:
						x0 = 0
						x1 = values.shape[0]
						y0 = 0
						y1 = values.shape[1]

				img = Image.fromarray(values[x0:x1, y0:y1], 'L')
				
				imgOutputName = outputViewName + '_Frame' + str(t).rjust(4, '0') + '.png'
				if uniqueName:
					imgOutputName = uniqueName + '_' + imgOutputName
				if isinstance(outputPath, list):
					for path in outputPath:
						img.save(os.path.join(path, imgOutputName))
				else:
					img.save(os.path.join(outputPath, imgOutputName))		



	def exportFromPoints(self, points=None, viewName=None, exportFilePath=None, uniqueName=False, showPoint=False, debug=False):
		if points is None or viewName is None or exportFilePath is None:
			return
				
		# MATRIX FORMATION
		pts_IJK = []
		for pointData in points:
			if len(pts_IJK) >= 3:
				break
			pts_IJK.append(np.array(pointData['ijk']))
		pts_IJK = np.array(pts_IJK).T
		pts_RAS = np.matmul(self.m_IJK_To_RAS, pts_IJK)

		m_XY_to_RAS = getXYToRASMatrixFromThreePoints(pts_RAS)
		m_XY_to_IJK = np.matmul(self.m_RAS_To_IJK, m_XY_to_RAS)
		m_IJK_to_XY = np.linalg.inv(m_XY_to_IJK)

		m_flipX = np.array([
			[-1, 0, 0, 0],
			[0, 1, 0, 0],
			[0, 0, 1, 0],
			[0, 0, 0, 1],
		])

		VIEW_REF_POINTS = self.REFERENCE_POINT[viewName]
		ref_points = []
		dst_points = []

		#if viewName == '4 chamber view (A4C)':		# Point Filtering for A4C
		#	print(viewName)

		points_ijk = []
		for pointData in points:
			structure = pointData['structure']
			points_ijk.append(pointData['ijk'])
			for ref_pointData in VIEW_REF_POINTS:
				if structure == ref_pointData['structure']:
					dst_points.append(np.matmul(m_IJK_to_XY, np.array(pointData['ijk']).T).T[0:2])
					ref_points.append(np.array(ref_pointData['xy']))
					if structure == 'A4C-LV apex':
						dst_points.append(np.matmul(m_IJK_to_XY, np.array(pointData['ijk']).T).T[0:2])
						ref_points.append(np.array(ref_pointData['xy']))
						dst_points.append(np.matmul(m_IJK_to_XY, np.array(pointData['ijk']).T).T[0:2])
						ref_points.append(np.array(ref_pointData['xy']))
					break
		
		ref_points = np.array(ref_points)
		dst_points = np.array(dst_points)
		
		# Check for plane normal
		ref_a = ref_points[1] - ref_points[0]
		ref_b = ref_points[2] - ref_points[0]
		ref_normal_z = ref_a[0] * ref_b[1] - ref_a[1] * ref_b[0]
		dst_a = dst_points[1] - dst_points[0]
		dst_b = dst_points[2] - dst_points[0]
		dst_normal_z = dst_a[0] * dst_b[1] - dst_a[1] * dst_b[0]
		if ref_normal_z * dst_normal_z < 0:		# DIFFERENT NORMAL!! FLIPPINGGG
			for i in range(len(dst_points)):
				dst_points[i] = np.matmul(np.array([[-1, 0],[0, 1]]), dst_points[i].T).T
				
	
		m_similarity, _ = cv2.estimateAffinePartial2D(ref_points, dst_points)
		#m_similarity, _ = cv2.estimateAffinePartial2D(np.array(dst_points), np.array(ref_points))
		m_similarity = np.array([
			[m_similarity[0,0], m_similarity[0,1], 0, m_similarity[0,2]],
			[m_similarity[1,0], m_similarity[1,1], 0, m_similarity[1,2]],
			#[m_similarity[0,0], m_similarity[0,1], 0, m_similarity[0,2]],
			[0, 0, 1, 0],
			[0, 0, 0, 1],
		])
		if ref_normal_z * dst_normal_z < 0:		# DIFFERENT NORMAL!! FLIPPINGGG
			m_XY_to_IJK = np.matmul(m_XY_to_IJK, m_flipX)
		m_XY_to_IJK = np.matmul(m_XY_to_IJK, m_similarity)

		# RECONSTRUCT IMAGE
		dimensions = (512, 512, 1)  # Default dimension
		outputViewName = viewName.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')

		num_image_pix = (dimensions[0]+self.PADDING*2)*(dimensions[1]+self.PADDING*2)
		x2D, y2D = np.meshgrid(range(-self.PADDING, dimensions[0]+self.PADDING), range(dimensions[1]-1+self.PADDING, -1-self.PADDING, -1))
		pts_pix = np.column_stack((x2D.ravel(), y2D.ravel(), np.zeros(num_image_pix), np.ones(num_image_pix)))

		pts_ijk = np.matmul(m_XY_to_IJK, pts_pix.T)[0:3,:]	
		pts_ijk[[0, 2], :] = pts_ijk[[2, 0], :]  # Swap rows as Volume Array is accessed [k, j, i] !!!!!

		if showPoint:
			points_xy = np.matmul(np.linalg.inv(m_XY_to_IJK), np.array(points_ijk).T)[0:2,:].T
		
		x0 = None
		x1 = None
		y0 = None
		y1 = None

		
		for t in range(self.num_time):
			if debug and t > 0:
				break
			voxelArray = self.nrrdFileData[:,:,:,t]
			values = scipy.ndimage.map_coordinates(voxelArray, pts_ijk).reshape((dimensions[0]+self.PADDING*2, dimensions[1]+self.PADDING*2)).astype(dtype=np.uint8)

			if showPoint:
				values = self.drawPointsOnImageArray(values, points_xy)

			if x0 is None:
				try:
					if showPoint:
						mask = values[:,:,0] > 0
					else:
						mask = values > 0
					coords = np.argwhere(mask)
					x0, y0 = coords.min(axis=0)
					x1, y1 = coords.max(axis=0) + 1
					x0 = max(0, x0-5)
					y0 = max(0, y0-5)
					x1 = min(values.shape[0], x1+5)
					y1 = min(values.shape[1], y1+5)
				except:
					x0 = 0
					x1 = values.shape[0]
					y0 = 0
					y1 = values.shape[1]

			if showPoint:
				img = Image.fromarray(values[x0:x1, y0:y1])
			else:
				img = Image.fromarray(values[x0:x1, y0:y1], 'L')
			
			imgOutputName = outputViewName + '_Frame' + str(t).rjust(4, '0') + '.png'
			if uniqueName:
				imgOutputName = uniqueName + '_' + imgOutputName
			if isinstance(exportFilePath, list):
				for path in exportFilePath:
					img.save(os.path.join(path, imgOutputName))
			else:
				img.save(os.path.join(exportFilePath, imgOutputName))

	def exportAll(self, pointData=None, exportFilePath=None, uniqueName=False, showPoint=False, debug=False, planeIfError=False, planeInfoMaps=None):
		if pointData is None or exportFilePath is None:
			return
		for viewName, points in pointData.items():
			outputViewName = viewName.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')


			if isinstance(exportFilePath, list):
				for path in exportFilePath:
					outputPath = os.path.join(path, outputViewName)
					if not os.path.exists(outputPath):
						os.makedirs(outputPath)
			else:
				outputPath = os.path.join(exportFilePath, outputViewName)
				if not os.path.exists(outputPath):
					os.makedirs(outputPath)

			try:
				self.exportFromPoints(points=points, viewName=viewName, exportFilePath=outputPath, uniqueName=uniqueName, showPoint=showPoint, debug=debug)
			except Exception as e:
				print("Error when exporting to", exportFilePath, viewName, ':', e)
				if planeIfError:
					planeData = None
					for plane_info in planeInfoMaps:
						if plane_info['view'] == viewName:
							planeData = plane_info
							break
					
					if planeData is None:
						print('No Plane Data Match')
					else:
						print('Output Using Plane Data')
						self.exportFromPlaneInfo(planeData=planeData, points=points, viewName=viewName, exportFilePath=outputPath, uniqueName=uniqueName, showPoint=showPoint, debug=debug)



if __name__ == '__main__':
	print("Using CV2 Version:", cv2.__version__)

	#NRRD_PATH = 'E:/FYP/Nrrd Spacing/Corrected-Export-gpu/PWHOR191291414W_8Oct2021_CV5YA37X_3DQ.seq.nrrd'
	NRRD_PATH = 'E:/FYP/Nrrd Spacing/Normal-Export-gpu/PWHOR190733599Q_11Oct2021_CWJKF3OP_3DQ.seq.nrrd'
	#ANNOTATION_PATH = 'E:/FYP/Nrrd Spacing/Corrected-Export-gpu/PWHOR191291414W_8Oct2021_CV5YA37X_3DQ.json'
	ANNOTATION_PATH = 'E:/FYP/Nrrd Spacing/Normal-Export-gpu/PWHOR190733599Q_11Oct2021_CWJKF3OP_3DQ.json'
	
	#EXPORT_PATH = 'E:/FYP/Nrrd Spacing/Corrected-Export-gpu/'
	EXPORT_PATH = 'E:/FYP/Nrrd Spacing/Normal-Export-gpu/'

	REFERENCE_FILE_PATH = 'E:/FYP/View Reconstruction/reference_points.json'

	pointData = {}
	with open(ANNOTATION_PATH, 'r') as f:
		labelled_data = json.load(f)
		fidData = labelled_data['adjusted']['points']
		planeData = labelled_data['adjusted']['planes']
		for viewData in fidData:
			view = viewData['View Name']
			if view not in pointData:
				pointData[view] = []
			pointData[view].append({
				'structure': viewData['Structure Name'].replace('.', ''),
				'ijk': viewData['Position-IJK']+[1],
			})

	viewReconstructor = ViewReconstructor()
	viewReconstructor.setup(NRRD_PATH, REFERENCE_FILE_PATH)
	viewReconstructor.exportAll(pointData=pointData, exportFilePath=os.path.join(EXPORT_PATH, 'points'), uniqueName='PWHOR190733102S_11Oct2021_CWJKG6YV_3DQ', showPoint=False, debug=True)
	viewReconstructor.exportAllFromAdjustedPlaneInfo(planeInfoMaps=planeData, exportFilePath=os.path.join(EXPORT_PATH, 'plane'), uniqueName='PWHOR190733102S_11Oct2021_CWJKG6YV_3DQ', debug=True)



	exit(0)
	nrrdPath = 'E:/Datasets/Echocardio/3D_Sample/PatientA.seq.nrrd'
	viewReconstructor = ViewReconstructor()
	viewReconstructor.setup(nrrdFilePath=nrrdPath)
	viewReconstructor.exportReconstructions(
		points=np.array([
		[50, 20, 80, 1],
		[120, 60, 60, 1],
		[50, 30, 40, 1]]), viewName='testView', exportFilePath='C:/Users/user1/Desktop/View Reconstruction/test_export')

	# viewReconstructor.showMatrix()

	# print(getXYToSliceMatrix())
	
	#print(getSliceToRASMatrixFromThreePoints(np.array([
	#	[50, 20, 80],
	#	[120, 60, 60],
	#	[50, 30, 40]])))
