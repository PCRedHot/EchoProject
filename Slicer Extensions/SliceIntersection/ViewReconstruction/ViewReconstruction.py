import os
import unittest
import logging
import vtk
import qt
import ctk
import slicer
import json
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import ScreenCapture
import numpy as np
try:
	import cv2
except:
	slicer.util.pip_install("opencv-python")

#
# ViewReconstruction
#


class ViewReconstruction(ScriptedLoadableModule):
	"""Uses ScriptedLoadableModule base class, available at:
	https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
	"""

	def __init__(self, parent):
		ScriptedLoadableModule.__init__(self, parent)
		# TODO: make this more human readable by adding spaces
		self.parent.title = "ViewReconstruction"
		# TODO: set categories (folders where the module shows up in the module selector)
		self.parent.categories = ["Examples"]
		# TODO: add here list of module names that this module requires
		self.parent.dependencies = []
		# TODO: replace with "Firstname Lastname (Organization)"
		self.parent.contributors = ["John Doe (AnyWare Corp.)"]
		# TODO: update with short description of the module and a link to online module documentation
		self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#ViewReconstruction">module documentation</a>.
"""
		# TODO: replace with organization, grant and thanks
		self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

		# Additional initialization step after application startup is complete
		slicer.app.connect("startupCompleted()", registerSampleData)

#
# Register sample data sets in Sample Data module
#


def registerSampleData():
	"""
	Add data sets to Sample Data module.
	"""
	# It is always recommended to provide sample data for users to make it easy to try the module,
	# but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

	import SampleData
	iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

	# To ensure that the source code repository remains small (can be downloaded and installed quickly)
	# it is recommended to store data sets that are larger than a few MB in a Github release.

	# ViewReconstruction1
	SampleData.SampleDataLogic.registerCustomSampleDataSource(
		# Category and sample name displayed in Sample Data module
		category='ViewReconstruction',
		sampleName='ViewReconstruction1',
		# Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
		# It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
		thumbnailFileName=os.path.join(iconsPath, 'ViewReconstruction1.png'),
		# Download URL and target file name
		uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
		fileNames='ViewReconstruction1.nrrd',
		# Checksum to ensure file integrity. Can be computed by this command:
		#  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
		checksums='SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
		# This node name will be used when the data set is loaded
		nodeNames='ViewReconstruction1'
	)

	# ViewReconstruction2
	SampleData.SampleDataLogic.registerCustomSampleDataSource(
		# Category and sample name displayed in Sample Data module
		category='ViewReconstruction',
		sampleName='ViewReconstruction2',
		thumbnailFileName=os.path.join(iconsPath, 'ViewReconstruction2.png'),
		# Download URL and target file name
		uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
		fileNames='ViewReconstruction2.nrrd',
		checksums='SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
		# This node name will be used when the data set is loaded
		nodeNames='ViewReconstruction2'
	)

#
# ViewReconstructionWidget
#


class ViewReconstructionWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
	"""Uses ScriptedLoadableModuleWidget base class, available at:
	https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
	"""

	def __init__(self, parent=None):
		"""
		Called when the user opens the module the first time and the widget is initialized.
		"""
		ScriptedLoadableModuleWidget.__init__(self, parent)
		# needed for parameter node observation
		VTKObservationMixin.__init__(self)
		self.logic = None
		self._parameterNode = None
		self._updatingGUIFromParameterNode = False

	def setup(self):
		"""
		Called when the user opens the module the first time and the widget is initialized.
		"""
		parametersCollapsibleButton = ctk.ctkCollapsibleButton()
		parametersCollapsibleButton.text = "Parameters"
		self.layout.addWidget(parametersCollapsibleButton)

		# Layout within the dummy collapsible button
		parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

		self.inputNrrdDirSelector = ctk.ctkPathLineEdit()
		self.inputNrrdDirSelector.filters = ctk.ctkPathLineEdit.Dirs
		self.inputNrrdDirSelector.settingKey = 'NrrdInputDir'
		parametersFormLayout.addRow(
			"Input NRRD Directory:", self.inputNrrdDirSelector)

		self.inputAnnotationDirSelector = ctk.ctkPathLineEdit()
		self.inputAnnotationDirSelector.filters = ctk.ctkPathLineEdit.Dirs
		self.inputAnnotationDirSelector.settingKey = 'AnnotationInputDir'
		parametersFormLayout.addRow(
			"Input Annotation Directory:", self.inputAnnotationDirSelector)

		self.outputDirSelector = ctk.ctkPathLineEdit()
		self.outputDirSelector.filters = ctk.ctkPathLineEdit.Dirs
		self.outputDirSelector.settingKey = 'ViewOutputDir'
		parametersFormLayout.addRow(
			"Output Directory:", self.outputDirSelector)

		self.inputReferenceDirSelector = ctk.ctkPathLineEdit()
		self.inputReferenceDirSelector.filters = ctk.ctkPathLineEdit.Files
		self.inputReferenceDirSelector.settingKey = 'ReferenceInputDir'
		parametersFormLayout.addRow(
			"Point Reference File:", self.inputReferenceDirSelector)

		self.enablePlaneInfoCheckBox = qt.QCheckBox()
		self.enablePlaneInfoCheckBox.checked = False
		self.enablePlaneInfoCheckBox.setToolTip(
			"If checked, plane info will be used to reconstruct the views")
		parametersFormLayout.addRow(
			"Export using Plane Info", self.enablePlaneInfoCheckBox)

		
		self.widthLabel = qt.QLabel("Width:")
		self.widthSpinBoxWidget = qt.QSpinBox()
		self.widthSpinBoxWidget.maximum = 2000
		self.widthSpinBoxWidget.minimum = 200
		self.widthSpinBoxWidget.value = 1300
		parametersFormLayout.addRow(self.widthLabel, self.widthSpinBoxWidget)
		
		self.heightLabel = qt.QLabel("Height:")
		self.heightSpinBoxWidget = qt.QSpinBox()
		self.heightSpinBoxWidget.maximum = 2000
		self.heightSpinBoxWidget.minimum = 200
		self.heightSpinBoxWidget.value = 900
		parametersFormLayout.addRow(self.heightLabel, self.heightSpinBoxWidget)

		

		# self.enablePointCheckBox = qt.QCheckBox()
		# self.enablePointCheckBox.checked = False
		# self.enablePointCheckBox.setToolTip(
		# 	"If checked, points will be shown on the reconstructed views")
		# parametersFormLayout.addRow(
		# 	"Show Points in Reconstructed Views", self.enablePointCheckBox)

		#
		# Reconstruct Button
		#
		self.reconstructButton = qt.QPushButton("Patch")
		self.reconstructButton.toolTip = "Reconstruct Views from NRRD Files and Annotations"
		parametersFormLayout.addRow(self.reconstructButton)

		# connections
		self.reconstructButton.connect(
			'clicked(bool)', self.onReconstructButton)

		self.statusLabel = qt.QPlainTextEdit()
		self.statusLabel.setTextInteractionFlags(qt.Qt.TextSelectableByMouse)
		parametersFormLayout.addRow(self.statusLabel)

		# Add vertical spacer
		self.layout.addStretch(1)

		self.logic = ViewReconstructionLogic()
		self.logic.logCallback = self.addLog

	def cleanup(self):
		"""
		Called when the application closes and the module widget is destroyed.
		"""
		pass

	def onReconstructButton(self):
		app_layout = slicer.util.getNode("vtkMRMLLayoutNodevtkMRMLLayoutNode")
		original_view_arragement = app_layout.GetViewArrangement()
		app_layout.SetViewArrangement(app_layout.SlicerLayoutOneUpRedSliceView)
		#slicer.app.setOverrideCursor(qt.Qt.WaitCursor)
		try:
			self.inputNrrdDirSelector.addCurrentPathToHistory()
			self.inputAnnotationDirSelector.addCurrentPathToHistory()
			self.outputDirSelector.addCurrentPathToHistory()
			self.inputReferenceDirSelector.addCurrentPathToHistory()
			self.statusLabel.plainText = ''
			self.logic.reconstruct(self.inputNrrdDirSelector.currentPath, self.inputAnnotationDirSelector.currentPath,
								self.outputDirSelector.currentPath, self.inputReferenceDirSelector.currentPath,
								self.enablePlaneInfoCheckBox.checked, width=self.widthSpinBoxWidget.value, height=self.heightSpinBoxWidget.value)
		except Exception as e:
			import traceback
			traceback.print_exc()
		#slicer.app.restoreOverrideCursor()
		app_layout.SetViewArrangement(original_view_arragement)

	def addLog(self, text):
		"""
		Append text to log window
		"""
		self.statusLabel.appendPlainText(text)
		slicer.app.processEvents() # force update


#
# ViewReconstructionLogic
#

class ViewReconstructionLogic(ScriptedLoadableModuleLogic):
	"""This class should implement all the actual
	computation done by your module.  The interface
	should be such that other python code can import
	this class and make use of the functionality without
	requiring an instance of the Widget.
	Uses ScriptedLoadableModuleLogic base class, available at:
	https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
	"""

	def __init__(self):
		"""
		Called when the logic class is instantiated. Can be used for initializing member variables.
		"""
		ScriptedLoadableModuleLogic.__init__(self)
		self.logCallback = None
		self.reference_data = None

	def reconstruct(self, inputNrrdDir: str, inputAnnotationDir: str, outputDir: str, referenceDir:str, usePlaneInfo: bool, showPointsOnViews: bool=False, width: int=1300, height: int=900):
		NRRD_FILES_PATHS = {}
		for root, dirs, files in os.walk(inputNrrdDir):
			for file in files:
				NRRD_FILES_PATHS[file[0:-9]] = os.path.join(root, file)
		
		JSON_FILES_PATHS = {}
		for root, dirs, files in os.walk(inputAnnotationDir):
			for file in files:
				JSON_FILES_PATHS[file[0:-5]] = os.path.join(root, file)
		
		if referenceDir is not None:
			with open(referenceDir, 'r') as f:
				self.reference_data = json.load(f)

		
		for file_name, json_file_path in JSON_FILES_PATHS.items():
			nrrd_file_path = NRRD_FILES_PATHS[file_name]

			self._reconstruct(nrrd_file_path, json_file_path, outputDir, usePlaneInfo, showPointsOnViews, width, height)


	
	def _reconstruct(self, nrrdFile: str, annotationFile: str, outputDir: str, usePlaneInfo: bool, showPointsOnViews: bool, width: int, height: int):
		slicer.mrmlScene.Clear()
		
		sequenceNode = slicer.util.loadSequence(nrrdFile)

		file_name = os.path.basename(annotationFile)[0:-5]
		output_par_path = os.path.join(outputDir, file_name)
		
		# Load Annotation
		points_data = {}	# view: [{'ijk': ijk, 'structure': structure}, ...]
		planes_data = {}	# view: Slice->IJK if normalised, Slice->RAS if not normalised
		isNormalisedData = False
		with open(annotationFile, 'r') as f:
			annotationData = json.load(f)
			if 'adjusted' in annotationData:
				# Normalised Annotation
				isNormalisedData = True
				for point_data in annotationData['adjusted']['points']:
					view_name = point_data['View Name']
					if view_name not in points_data:
						points_data[view_name] = []
					points_data[view_name].append(
						{'ijk': point_data['Position-IJK'],
						'structure': point_data['Structure Name']})
				for plane_data in annotationData['adjusted']['planes']:
					view_name = plane_data['view']
					planes_data[view_name] = plane_data['SliceToIJK']
			else:
				for point_data in annotationData['fidData']:
					view_name = point_data['View Name']
					if view_name not in points_data:
						points_data[view_name] = []
					points_data[view_name].append(
						{'ijk': point_data['Position-IJK'],
						'structure': point_data['Structure Name']})
				for plane_data in annotationData['planeData']:
					colour = plane_data['colour']
					view_name = plane_data['view']
					planes_data[view_name] = plane_data[colour]['SliceToRAS']



		#fieldOfView = [250, 250, 1]
		#sliceOrigin = [0, 0, 0]
		#dimensions = [512, 512, 1]

		# Use Red Slice to Reconstruct
		red_slice = slicer.util.getNode('vtkMRMLSliceNodeRed')
		m_Slice_RAS = red_slice.GetSliceToRAS()

		volumeNode = sequenceNode.GetNthDataNode(0)
		m_RAS_IJK = vtk.vtkMatrix4x4()
		m_IJK_RAS = vtk.vtkMatrix4x4()

		volumeNode.GetRASToIJKMatrix(m_RAS_IJK)
		volumeNode.GetIJKToRASMatrix(m_IJK_RAS)

		#data_dimensions = slicer.util.arrayFromVolume(sequenceNode.GetNthDataNode(0)).shape	#(k, j, i)
		num_frames = sequenceNode.GetNumberOfDataNodes()
		

		browserNode = slicer.modules.sequences.logic().GetFirstBrowserNodeForSequenceNode(sequenceNode)
		while browserNode is None:
			browserNode = slicer.modules.sequences.logic().GetFirstBrowserNodeForSequenceNode(sequenceNode)
		

		cap = ScreenCapture.ScreenCaptureLogic()
		red_widget = slicer.app.layoutManager().sliceWidget("Red")
		red_slice_view = red_widget.sliceView()
		#width = 1300
		#height = 900
		red_slice_view.size = qt.QSize(width, height)

		red_logic = red_widget.sliceLogic()
		ras_dimensions = [0, 0, 0]
		ras_center = [0, 0, 0]
		red_logic.GetVolumeRASBox(volumeNode, ras_dimensions, ras_center)

		
		
		sliceAnnotations = slicer.modules.DataProbeInstance.infoWidget.sliceAnnotations
		sliceAnnotations.bottomLeftCheckBox.checked = False
		sliceAnnotations.onCornerTextsActivationCheckBox()

	
		if usePlaneInfo:
			for view, matrix in planes_data.items():
				if isNormalisedData:
					data_m_Slice_RAS = vtk.vtkMatrix4x4()
					vtk.vtkMatrix4x4(m_IJK_RAS, self.getVtkMat4x4FromList(matrix), data_m_Slice_RAS)
				else:
					data_m_Slice_RAS = self.getVtkMat4x4FromList(matrix)
				
				for i in range(4):
					for j in range(4):
						m_Slice_RAS.SetElement(i, j, data_m_Slice_RAS.GetElement(i, j))
				
				#red_slice.SetFieldOfView(fieldOfView[0], fieldOfView[1], fieldOfView[2])
				#red_slice.SetSliceOrigin(sliceOrigin[0], sliceOrigin[1], sliceOrigin[2])
				#red_slice.SetDimensions(dimensions[0], dimensions[1], dimensions[2])
								
				#redLogic.FitSliceToAll() 
				
				red_slice.UpdateMatrices()

				for _t in range(num_frames):
					browserNode.SetSelectedItemNumber(_t)
					if self.reconstructResize(red_slice, red_logic, volumeNode, ras_center, height, width):
						break

				view_str = view.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')

				if not os.path.exists(os.path.join(output_par_path, view_str)):
					os.makedirs(os.path.join(output_par_path, view_str))
				
				for time in range(num_frames):
					browserNode.SetSelectedItemNumber(time)

					red_slice_view.forceRender()
					cap.captureImageFromView(red_slice_view, os.path.join(output_par_path, view_str, file_name + '_' + view_str + '_Frame' + str(time).zfill(3) + '.png'))
		else:
			for view, ijk_points_data in points_data.items():
				if len(ijk_points_data) < 3:
					continue
				points = np.array([m_IJK_RAS.MultiplyPoint(pt_data['ijk']+[1]) for pt_data in ijk_points_data[:3]])[:3,:3].T

				p = points.mean(axis=1)
				n = np.cross(points[:,1] - points[:,0], points[:,2] - points[:,0])
				t = points[:,1] - points[:,0]		

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

				for i in range(3):
					m_Slice_RAS.SetElement(i, 3, p[i])
					m_Slice_RAS.SetElement(i, 2, n[i])
					m_Slice_RAS.SetElement(i, 1, c[i])
					m_Slice_RAS.SetElement(i, 0, t[i])

				m_RAS_Slice = self.vtkMatrix4x4DeepCopy(m_Slice_RAS)
				m_RAS_Slice.Invert()

				# Similarity Transform
				m_XY_Slice = red_slice.GetXYToSlice()
				m_Slice_XY = self.vtkMatrix4x4DeepCopy(m_XY_Slice)
				m_Slice_XY.Invert()

				m_IJK_XY = vtk.vtkMatrix4x4()
				vtk.vtkMatrix4x4.Multiply4x4(m_RAS_Slice, m_IJK_RAS, m_IJK_XY)
				#vtk.vtkMatrix4x4.Multiply4x4(m_Slice_XY, self.vtkMatrix4x4DeepCopy(m_IJK_XY), m_IJK_XY)
				vtk.vtkMatrix4x4.Multiply4x4(m_Slice_XY, m_IJK_XY, m_IJK_XY)
				
				VIEW_REF_POINTS = self.reference_data[view]
				ref_points = []
				dst_points = []

				xy_points = []
				for data_point in ijk_points_data:
					structure = data_point['structure']
					xy = np.array(m_IJK_XY.MultiplyPoint(data_point['ijk']+[1])[:2])
					xy_points.append(xy)
					for ref_point_data in VIEW_REF_POINTS:
						if structure == ref_point_data['structure']:
							dst_points.append(xy)
							ref_points.append(np.array(ref_point_data['xy']))
							if structure == 'A4C-LV apex':
								dst_points.append(xy)
								ref_points.append(np.array(ref_point_data['xy']))
								dst_points.append(xy)
								ref_points.append(np.array(ref_point_data['xy']))
							break

				ref_points = np.array(ref_points)
				dst_points = np.array(dst_points)

				xy_mean = np.mean(np.array(xy_points), axis=1)

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
				
				for _t in range(num_frames):
					browserNode.SetSelectedItemNumber(_t)
					m_similarity, _ = cv2.estimateAffinePartial2D(ref_points, dst_points)
					if m_similarity is not None:
						m_similarity = np.array([
							[m_similarity[0,0], m_similarity[0,1], 0, m_similarity[0,2]],
							[m_similarity[1,0], m_similarity[1,1], 0, m_similarity[1,2]],
							[0, 0, 1, 0],
							[0, 0, 0, 1],
						])
						if ref_normal_z * dst_normal_z < 0:		# DIFFERENT NORMAL!! FLIPPINGGG
							m_flipX = np.array([
								[-1, 0, 0, 0],
								[0, 1, 0, 0],
								[0, 0, 1, 0],
								[0, 0, 0, 1],
							])
							m_similarity = np.matmul(m_flipX, m_similarity)
						m_slice_similarity = vtk.vtkMatrix4x4()
						vtk.vtkMatrix4x4.Multiply4x4(self.getVtkMat4x4FromNumpy(m_similarity), m_Slice_XY, m_slice_similarity)
						vtk.vtkMatrix4x4.Multiply4x4(m_XY_Slice, m_slice_similarity, m_slice_similarity)
						vtk.vtkMatrix4x4.Multiply4x4(m_Slice_RAS, m_slice_similarity, m_Slice_RAS)
					else:
						print(os.path.basename(nrrdFile), view, ': Similarity Error')
						continue

					red_slice.UpdateMatrices()

					if not self.reconstructResize(red_slice, red_logic, volumeNode, ras_center, height, width, debug=[os.path.basename(nrrdFile), view]):
						continue
					break

				view_str = view.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')

				if not os.path.exists(os.path.join(output_par_path, view_str)):
					os.makedirs(os.path.join(output_par_path, view_str))

				for time in range(num_frames):
					browserNode.SetSelectedItemNumber(time)

					red_slice_view.forceRender()
					cap.captureImageFromView(red_slice_view, os.path.join(output_par_path, view_str, file_name + '_' + view_str + '_Frame' + str(time).zfill(3) + '.png'))
		


	def reconstructResize(self, red_slice, red_logic, volumeNode, ras_center, height, width, debug=''):
		slice_dimensions = [0, 0, 0]
		slice_center = [0, 0, 0]
		red_logic.GetVolumeSliceDimensions(volumeNode, slice_dimensions, slice_center)

		displayX = fitX = abs(slice_dimensions[0])
		displayY = fitY = abs(slice_dimensions[1])
		fitZ = red_logic.GetVolumeSliceSpacing(volumeNode)[2] * red_slice.GetDimensions()[2]

		if height > width:
			pixel_size = fitX / width
			fitY = pixel_size * height
		else:
			pixel_size = fitY / height
			fitX = pixel_size * width
		
		if displayX > fitX:
			fitY = fitY / (fitX / displayX)
			fitX = displayX
		if displayY > fitY:
			fitX = fitX / (fitY / displayY)
			fitY = displayY
		
		red_slice.SetFieldOfView(fitX, fitY, fitZ)

		m_slice_ras = red_slice.GetSliceToRAS()

		random_pt1_slice = [1, 1, 1, 1]
		random_pt1_ras = np.array(m_slice_ras.MultiplyPoint(random_pt1_slice))[0:3]

		random_pt2_slice = [20, 1, 1, 1]
		random_pt2_ras = np.array(m_slice_ras.MultiplyPoint(random_pt2_slice))[0:3]

		random_pt3_slice = [1, 20, 1, 1]
		random_pt3_ras = np.array(m_slice_ras.MultiplyPoint(random_pt3_slice))[0:3]

		normal = np.cross(random_pt2_ras-random_pt1_ras, random_pt3_ras-random_pt1_ras)
		if np.linalg.norm(normal) != 0:
			normal = normal / np.linalg.norm(normal)

			old_center = np.array(ras_center)
			new_center = np.dot(random_pt1_ras - old_center, normal) * normal + old_center
		else:
			print(debug, 'Centering error')
			new_center = np.array(ras_center)
			return False

		for i in range(3):
			m_slice_ras.SetElement(i, 3, new_center[i])

		red_slice.UpdateMatrices()
		return True


	def getVtkMat4x4FromList(self, m_list):
		rtn = vtk.vtkMatrix4x4()
		for i in range(4):
			for j in range(4):
				rtn.SetElement(i, j, m_list[i*4+j])
		return rtn

	def getVtkMat4x4FromNumpy(self, m_np):
		rtn = vtk.vtkMatrix4x4()
		for i in range(4):
			for j in range(4):
				rtn.SetElement(i, j, m_np[i, j])
		return rtn

	def vtkMatrix4x4DeepCopy(self, mat):
		rtnMat = vtk.vtkMatrix4x4()
		for i in range(4):
			for j in range(4):
				rtnMat.SetElement(i, j, mat.GetElement(i, j))
		return rtnMat


	def addLog(self, text):
		logging.info(text)
		if self.logCallback:
			self.logCallback(text)



#
# ViewReconstructionTest
#

class ViewReconstructionTest(ScriptedLoadableModuleTest):
	"""
	This is the test case for your scripted module.
	Uses ScriptedLoadableModuleTest base class, available at:
	https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
	"""

	def setUp(self):
		""" Do whatever is needed to reset the state - typically a scene clear will be enough.
		"""
		slicer.mrmlScene.Clear()

	def runTest(self):
		"""Run as few or as many tests as needed here.
		"""
		self.setUp()
		self.test_ViewReconstruction1()

	def test_ViewReconstruction1(self):
		""" Ideally you should have several levels of tests.  At the lowest level
		tests should exercise the functionality of the logic with different inputs
		(both valid and invalid).  At higher levels your tests should emulate the
		way the user would interact with your code and confirm that it still works
		the way you intended.
		One of the most important features of the tests is that it should alert other
		developers when their changes will have an impact on the behavior of your
		module.  For example, if a developer removes a feature that you depend on,
		your test should break so they know that the feature is needed.
		"""

		self.delayDisplay("Starting the test")

		# Get/create input data

		import SampleData
		registerSampleData()
		inputVolume = SampleData.downloadSample('ViewReconstruction1')
		self.delayDisplay('Loaded test data set')

		inputScalarRange = inputVolume.GetImageData().GetScalarRange()
		self.assertEqual(inputScalarRange[0], 0)
		self.assertEqual(inputScalarRange[1], 695)

		outputVolume = slicer.mrmlScene.AddNewNodeByClass(
			"vtkMRMLScalarVolumeNode")
		threshold = 100

		# Test the module logic

		logic = ViewReconstructionLogic()

		# Test algorithm with non-inverted threshold
		logic.process(inputVolume, outputVolume, threshold, True)
		outputScalarRange = outputVolume.GetImageData().GetScalarRange()
		self.assertEqual(outputScalarRange[0], inputScalarRange[0])
		self.assertEqual(outputScalarRange[1], threshold)

		# Test algorithm with inverted threshold
		logic.process(inputVolume, outputVolume, threshold, False)
		outputScalarRange = outputVolume.GetImageData().GetScalarRange()
		self.assertEqual(outputScalarRange[0], inputScalarRange[0])
		self.assertEqual(outputScalarRange[1], inputScalarRange[1])

		self.delayDisplay('Test passed')
