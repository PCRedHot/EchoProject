import os
import unittest
from typing import BinaryIO

import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from threading import Thread
import numpy as np

#
# RegionPainter
#

class RegionPainter(ScriptedLoadableModule):
	"""Uses ScriptedLoadableModule base class, available at:
https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
"""

	def __init__(self, parent):
		ScriptedLoadableModule.__init__(self, parent)
		self.parent.title = "RegionPainter"  # TODO: make this more human readable by adding spaces
		self.parent.categories = [
			"Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
		self.parent.dependencies = []  # TODO: add here list of module names that this module requires
		self.parent.contributors = [
			"John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
		# TODO: update with short description of the module and a link to online module documentation
		self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#RegionPainter">module documentation</a>.
"""
		# TODO: replace with organization, grant and thanks
		self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

	def setup(self):
		# Register subject hierarchy plugin
		import SubjectHierarchyPlugins
		scriptedPlugin = slicer.qSlicerSubjectHierarchyScriptedPlugin(None)
		scriptedPlugin.setPythonSource(SubjectHierarchyPlugins.SegmentEditorSubjectHierarchyPlugin.filePath)


#
# RegionPainterWidget
#

class RegionPainterWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
	"""Uses ScriptedLoadableModuleWidget base class, available at:
https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
"""

	def __init__(self, parent):
		ScriptedLoadableModuleWidget.__init__(self, parent)
		VTKObservationMixin.__init__(self)

		# Members
		self.parameterSetNode = None
		self.editor = None
		
		self.logic = None
		self._parameterNode = None
		self._updatingGUIFromParameterNode = False
		
		self.regions = {
			"view 1": ["Region 1", "Region 2", "Region 3"],
			"view 2": ["Region 1", "Region 2"],
			"view 3": ["Region 1"],
			"view 4": ["Region 1", "Region 2"],
			"view 5": ["Region 1", "Region 2"],
			"view 6": ["Region 1", "Region 2"],
			"view 7": ["Region 1", "Region 2"],
			"view 8": ["Region 1", "Region 2"],
			"view 9": ["Region 1", "Region 2"],
			"view 10": ["Region 1", "Region 2"],
			"view 11": ["Region 1", "Region 2"],
			"view 12": ["Region 1", "Region 2"],
			"view 13": ["Region 1", "Region 2"],
			"view 14": ["Region 1", "Region 2"],
			"view 15": ["Region 1", "Region 2"],
		}
		

	def setup(self):
		ScriptedLoadableModuleWidget.setup(self)

		# Add margin to the sides
		self.layout.setContentsMargins(4, 0, 4, 0)
		
		uiWidget = slicer.util.loadUI(self.resourcePath('UI/RegionPainter.ui'))
		self.layout.addWidget(uiWidget)
		self.ui = slicer.util.childWidgetVariables(uiWidget)
		
		uiWidget.setMRMLScene(slicer.mrmlScene)
		
		self.logic = RegionPainterLogic()
		
		#
		# Segment editor widget
		#
		import qSlicerSegmentationsModuleWidgetsPythonQt
		self.editor = qSlicerSegmentationsModuleWidgetsPythonQt.qMRMLSegmentEditorWidget()
		self.editor.setMaximumNumberOfUndoStates(10)
		# Set parameter node first so that the automatic selections made when the scene is set are saved
		self.selectParameterNode()
		self.editor.setMRMLScene(slicer.mrmlScene)
		
		self.ui.regionCollapsibleButton.layout().addWidget(self.editor)

		# Connect observers to scene events
		self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
		self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
		self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndImportEvent, self.onSceneEndImport)

		# Set Effect
		self.editor.setEffectNameOrder(["Paint", "Erase"])
		self.editor.unorderedEffectsVisible = False

		# Hide Extra Buttons
		self.editor.findChild(ctk.ctkMenuButton, "Show3DButton").hide()
		self.editor.findChild(ctk.ctkMenuButton, "SwitchToSegmentationsButton").hide()
		self.editor.findChild(qt.QPushButton, "AddSegmentButton").hide()
		self.editor.findChild(qt.QPushButton, "RemoveSegmentButton").hide()
		
		self.editor.findChild(qt.QLabel, "SegmentationNodeLabel").hide()
		self.editor.findChild(qt.QLabel, "MasterVolumeNodeLabel").hide()
		self.editor.findChild(slicer.qMRMLNodeComboBox, "MasterVolumeNodeComboBox").hide()
		self.editor.findChild(slicer.qMRMLNodeComboBox, "SegmentationNodeComboBox").hide()
		self.editor.findChild(qt.QToolButton, "SpecifyGeometryButton").hide()
		
		exportCollapsibleButton = ctk.ctkCollapsibleButton()
		exportCollapsibleButton.text = "Export"
		self.layout.addWidget(exportCollapsibleButton)
		
		exportFormLayout = qt.QFormLayout(exportCollapsibleButton)
		
		self.exportDirSelector = ctk.ctkPathLineEdit()
		self.exportDirSelector.filters = ctk.ctkPathLineEdit.Dirs
		self.exportDirSelector.settingKey = 'ExportDir'
		exportFormLayout.addRow("Export directory:", self.exportDirSelector)
		
		self.exportButton = qt.QPushButton("Export")
		self.exportButton.toolTip = "Export to Export Directory"
		exportFormLayout.addRow(self.exportButton)
		
		verticalSpacer = qt.QSpacerItem(20, 40, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
		self.layout.addItem(verticalSpacer)
		
		# Connect observers for widgets
		self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
		self.ui.ViewBox.currentIndexChanged.connect(self.updateGUIFromParameterNode)
		for view in self.regions.keys():  # TODO: TEMP
			self.ui.ViewBox.addItem(view)
		self.ui.addSegmentButton.connect("clicked(bool)", self.onAddSegmentButton)
		self.exportButton.connect('clicked(bool)', self.onExportButton)
		
		
		self.initializeParameterNode()
	
	
	def onExportButton(self):
		slicer.app.setOverrideCursor(qt.Qt.BusyCursor)
		
		exportPath = self.exportDirSelector.currentPath
		sequenceNode = self.ui.inputSelector.currentNode()
		name = sequenceNode.GetName()
		
		exportFile = exportPath+'/'+name+' Region'
		if not os.path.exists(exportFile):
			os.makedirs(exportFile)
		
		segmentationNodesCollection = slicer.mrmlScene.GetNodesByClass("vtkMRMLSegmentationNode")
		
		#Export
		for i in range(segmentationNodesCollection.GetNumberOfItems()):
			segmentationNode = segmentationNodesCollection.GetItemAsObject(i)
			filepath = exportFile + "/" + segmentationNode.GetName() + ".seg.nrrd"
			slicer.util.saveNode(segmentationNode, filepath)
		
		slicer.app.restoreOverrideCursor()
		
	
	def onAddSegmentButton(self):
		self.initializeSegmentationNodeAtCurrentTime()
		

	def selectParameterNode(self):
		# Select parameter set node if one is found in the scene, and create one otherwise
		segmentEditorSingletonTag = "RegionPainter"
		segmentEditorNode = slicer.mrmlScene.GetSingletonNode(segmentEditorSingletonTag, "vtkMRMLSegmentEditorNode")
		if segmentEditorNode is None:
			segmentEditorNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLSegmentEditorNode")
			segmentEditorNode.UnRegister(None)
			segmentEditorNode.SetSingletonTag(segmentEditorSingletonTag)
			segmentEditorNode = slicer.mrmlScene.AddNode(segmentEditorNode)
		if self.parameterSetNode == segmentEditorNode:
			# nothing changed
			return
		segmentEditorNode.SetMaskMode(segmentEditorNode.PaintAllowedEverywhere)
		segmentEditorNode.SetOverwriteMode(segmentEditorNode.OverwriteNone)
		self.parameterSetNode = segmentEditorNode
		self.editor.setMRMLSegmentEditorNode(self.parameterSetNode)
		

	def getDefaultMasterVolumeNodeID(self):
		layoutManager = slicer.app.layoutManager()
		firstForegroundVolumeID = None
		# Use first background volume node in any of the displayed layouts.
		# If no beackground volume node is in any slice view then use the first
		# foreground volume node.
		for sliceViewName in layoutManager.sliceViewNames():
			sliceWidget = layoutManager.sliceWidget(sliceViewName)
			if not sliceWidget:
				continue
			compositeNode = sliceWidget.mrmlSliceCompositeNode()
			if compositeNode.GetBackgroundVolumeID():
				return compositeNode.GetBackgroundVolumeID()
			if compositeNode.GetForegroundVolumeID() and not firstForegroundVolumeID:
				firstForegroundVolumeID = compositeNode.GetForegroundVolumeID()
		# No background volume was found, so use the foreground volume (if any was found)
		return firstForegroundVolumeID


	def enter(self):
		"""Runs whenever the module is reopened
"""
		self.initializeParameterNode()
		if self.editor.turnOffLightboxes():
			slicer.util.warningDisplay('Segment Editor is not compatible with slice viewers in light box mode.'
									   'Views are being reset.', windowTitle='Segment Editor')

		# Allow switching between effects and selected segment using keyboard shortcuts
		self.editor.installKeyboardShortcuts()

		# Set parameter set node if absent
		self.selectParameterNode()
		self.editor.updateWidgetFromMRML()

	
	def exit(self):
		self.editor.setActiveEffect(None)
		self.editor.uninstallKeyboardShortcuts()
		self.editor.removeViewObservations()
		self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

	def onSceneStartClose(self, caller, event):
		self.parameterSetNode = None
		self.editor.setSegmentationNode(None)
		self.editor.removeViewObservations()
		self.setParameterNode(None)

	def onSceneEndClose(self, caller, event):
		if self.parent.isEntered:
			self.selectParameterNode()
			self.editor.updateWidgetFromMRML()
			self.initializeParameterNode()

	def onSceneEndImport(self, caller, event):
		if self.parent.isEntered:
			self.selectParameterNode()
			self.editor.updateWidgetFromMRML()

	def cleanup(self):
		self.removeObservers()
		
	
	def initializeSegmentationNodeAtCurrentTime(self):
		_, t = self.getCurrentTimeInSequence()
		name = self._parameterNode.GetNodeReference("InputSequence").GetName()
		"""
		segmentationNodeCollection = slicer.mrmlScene.GetNodesByClassByName("vtkMRMLSegmentationNode",
																			name + " Segmentation")
		if segmentationNodeCollection.GetNumberOfItems() != 0:
			segmentationNode = segmentationNodeCollection.GetItemAsObject(0)
		else:
			print("Asset Warning: no mrml segmentation node for current time found! Creating new one...")
			segmentationNode = slicer.vtkMRMLSegmentationNode()
			slicer.mrmlScene.AddNode(segmentationNode)
			segmentationNode.SetName(name + " Segmentation")
			
		vtkSegmentationNode = segmentationNode.GetSegmentation()
		# Name Format: View_Name Region_Name at time_index
		for view, regions in self.regions.items():
			for region in regions:
				segmentName = view + " " + region + " at " + str(t)
				if vtkSegmentationNode.GetSegmentIdBySegmentName(segmentName) == "":
					segmentID = segmentName.replace(" ", "_")
					segmentID = vtkSegmentationNode.AddEmptySegment(segmentID, segmentName)
					if segmentID != "":
						# Success Creation
						segment = vtkSegmentationNode.GetSegment(segmentID)
						segment.SetTag("view", view)
						segment.SetTag("region", region)
						segment.SetTag("time", str(t))
		"""
		segmentationNodeCollection = slicer.mrmlScene.GetNodesByClassByName("vtkMRMLSegmentationNode",
																			name + " Segmentation " + str(t))
		if segmentationNodeCollection.GetNumberOfItems() != 0:
			segmentationNode = segmentationNodeCollection.GetItemAsObject(0)
		else:
			print("Creating new segmentation node...")
			segmentationNode = slicer.vtkMRMLSegmentationNode()
			slicer.mrmlScene.AddNode(segmentationNode)
			segmentationNode.SetName(name + " Segmentation " + str(t))
			
			segmentationComboBox = self.editor.findChild(slicer.qMRMLNodeComboBox, "SegmentationNodeComboBox")
			
			segmentationComboBox.setCurrentNode(segmentationNode)

			
		vtkSegmentationNode = segmentationNode.GetSegmentation()
		# Name Format: View_Name Region_Name
		for view, regions in self.regions.items():
			for region in regions:
				segmentName = view + " " + region
				if vtkSegmentationNode.GetSegmentIdBySegmentName(segmentName) == "":
					segmentID = segmentName.replace(" ", "_")
					segmentID = vtkSegmentationNode.AddEmptySegment(segmentID, segmentName)
					if segmentID != "":
						# Success Creation
						segment = vtkSegmentationNode.GetSegment(segmentID)
						segment.SetTag("view", view)
						segment.SetTag("region", region)
						
		self.refreshSegmentTable()


	def refreshSegmentTable(self, caller=None, event=None):
		self.updateGUIFromParameterNode()
				
				
	
	def initializeParameterNode(self):
		"""
		Ensure parameter node exists and observed.
		"""
		# Parameter node stores all user choices in parameter values, node selections, etc.
		# so that when the scene is saved and reloaded, these settings are restored.
		
		self.setParameterNode(self.logic.getParameterNode())
		
		# Select default input nodes if nothing is selected yet to save a few clicks for the user
		"""
		if not self._parameterNode.GetNodeReference("InputSequence"):
			firstSequenceNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLSequenceNode")
			if firstSequenceNode:
				self._parameterNode.SetNodeReferenceID("InputSequence", firstSequenceNode.GetID())
	"""
	
	def setParameterNode(self, inputParameterNode):
		"""
		Set and observe parameter node.
		Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
		"""
		
		if inputParameterNode:
			self.logic.setDefaultParameters(inputParameterNode)
		
		# Unobserve previously selected parameter node and add an observer to the newly selected.
		# Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
		# those are reflected immediately in the GUI.
		if self._parameterNode is not None:
			self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
		self._parameterNode = inputParameterNode
		if self._parameterNode is not None:
			self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
		
		# Initial GUI update
		self.updateGUIFromParameterNode()
		
	
	def waitForLoading(self, seconds):
		from time import sleep
		sleep(seconds)
		self.updateGUIFromParameterNode()
	
	def updateGUIFromParameterNode(self, caller=None, event=None):
		"""
		This method is called whenever parameter node is changed.
		The module GUI is updated to show the current state of the parameter node.
		"""
		
		if self._parameterNode is None or self._updatingGUIFromParameterNode:
			return
		
		# Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
		self._updatingGUIFromParameterNode = True
		
		# Update node selectors and sliders
		sequenceNode = self._parameterNode.GetNodeReference("InputSequence")
		volumeComboBox = self.editor.findChild(slicer.qMRMLNodeComboBox, "MasterVolumeNodeComboBox")
		segmentationComboBox = self.editor.findChild(slicer.qMRMLNodeComboBox, "SegmentationNodeComboBox")
		
		self.ui.inputSelector.setCurrentNode(sequenceNode)
		
		if sequenceNode:
			name = sequenceNode.GetName()
			browserNode = slicer.modules.sequences.logic().GetFirstBrowserNodeForSequenceNode(sequenceNode)
			if browserNode is None:
				Thread(target=self.waitForLoading, args=(1,)).start()
				self._updatingGUIFromParameterNode = False
				return
			
			self.exportButton.enabled = True
			self.ui.addSegmentButton.enabled = True
			
			self.removeObserver(browserNode, vtk.vtkCommand.ModifiedEvent,
								self.refreshSegmentTable)
			self.addObserver(browserNode, vtk.vtkCommand.ModifiedEvent,
							 self.refreshSegmentTable)
			volumeNode = browserNode.GetProxyNode(sequenceNode)
			
			"""
			targetName = name + " Segmentation"
			segmentationNodeCollection = slicer.mrmlScene.GetNodesByClassByName("vtkMRMLSegmentationNode", targetName)
			if segmentationNodeCollection.GetNumberOfItems() == 0:
				# Create Master Segmentation Node
				segmentationNode = slicer.vtkMRMLSegmentationNode()
				slicer.mrmlScene.AddNode(segmentationNode)
				segmentationNode.SetName(name + " Segmentation")
			else:
				segmentationNode = segmentationNodeCollection.GetItemAsObject(0)
			
			segmentationComboBox.setCurrentNode(segmentationNode)
			volumeComboBox.setCurrentNode(volumeNode)
			
			# Filter Segment Table
			currentView = self.ui.ViewBox.currentText
			currentTime = browserNode.GetSelectedItemNumber()
			displayNode = segmentationNode.GetDisplayNode()
			if displayNode:
				currentShowAllView = currentView == "ShowAll"
				displayNode.SetAllSegmentsVisibility(False)
				vtkSegmentationNode = segmentationNode.GetSegmentation()
				for i in range(vtkSegmentationNode.GetNumberOfSegments()):
					segment = vtkSegmentationNode.GetNthSegment(i)
					segmentID = vtkSegmentationNode.GetNthSegmentID(i)
					referenceView = vtk.reference("")
					referenceTime = vtk.reference("")
					if segment.GetTag("view", referenceView) == "" or segment.GetTag("time", referenceTime) == "":
						continue
					
					if (str(referenceView) == str(currentView) or currentShowAllView) and str(referenceTime) == str(currentTime):
						print("Show")
						displayNode.SetSegmentVisibility(segmentID, True)
			"""
			t = browserNode.GetSelectedItemNumber()
			targetName = name + " Segmentation " + str(t)
			segmentationNodeCollection = slicer.mrmlScene.GetNodesByClassByName("vtkMRMLSegmentationNode", targetName)
			segmentationNodesCollection = slicer.mrmlScene.GetNodesByClass("vtkMRMLSegmentationNode")
			
			# Set all segmentations to Invisible
			for i in range(segmentationNodesCollection.GetNumberOfItems()):
				segmentationNodeAtOtherT = segmentationNodesCollection.GetItemAsObject(i)
				segmentationNodeAtOtherT.SetDisplayVisibility(0)
				displayNodeAtOtherT = segmentationNodeAtOtherT.GetDisplayNode()
				if displayNodeAtOtherT:
					displayNodeAtOtherT.SetAllSegmentsVisibility(False)
			
			# If no segmentation node for current t
			if segmentationNodeCollection.GetNumberOfItems() == 0:
				""" DO NOT CREATE NEW NODE HERE
				# Create Segmentation Node at t
				segmentationNode = slicer.vtkMRMLSegmentationNode()
				slicer.mrmlScene.AddNode(segmentationNode)
				segmentationNode.SetName(targetName)
				"""
				segmentationComboBox.setCurrentNode(None)
				self._updatingGUIFromParameterNode = False
				return
			
			# Segmentation Node of current t is found
			segmentationNode = segmentationNodeCollection.GetItemAsObject(0)
			segmentationComboBox.setCurrentNode(segmentationNode)
			volumeComboBox.setCurrentNode(volumeNode)
		
			segmentationNode.SetDisplayVisibility(1)     # Correct Segmentation Node
			
			# Filter Segment Table
			currentView = self.ui.ViewBox.currentText
			displayNode = segmentationNode.GetDisplayNode()
			if displayNode:
				currentShowAllView = currentView == "ShowAll"
				displayNode.SetAllSegmentsVisibility(False)
				vtkSegmentationNode = segmentationNode.GetSegmentation()
				for i in range(vtkSegmentationNode.GetNumberOfSegments()):
					segment = vtkSegmentationNode.GetNthSegment(i)
					segmentID = vtkSegmentationNode.GetNthSegmentID(i)
					referenceView = vtk.reference("")
					if segment.GetTag("view", referenceView) == "":
						continue
					
					if str(referenceView) == str(currentView) or currentShowAllView:
						#print("Show")
						displayNode.SetSegmentVisibility(segmentID, True)
			
		else:
			volumeComboBox.setCurrentNode(None)
			segmentationComboBox.setCurrentNode(None)
			self.exportButton.enabled = False
			self.ui.addSegmentButton.enabled = False
		
		# All the GUI updates are done
		self._updatingGUIFromParameterNode = False
	
	
	def updateParameterNodeFromGUI(self, caller=None, event=None):
		"""
		This method is called when the user makes any change in the GUI.
		The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
		"""
		
		if self._parameterNode is None or self._updatingGUIFromParameterNode:
			return
		
		wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch
		
		self._parameterNode.SetNodeReferenceID("InputSequence", self.ui.inputSelector.currentNodeID)
		
		self._parameterNode.EndModify(wasModified)
		
	def getCurrentTimeInSequence(self):
		"""
		return: current time value and time index of the displaying sequence node
		"""
		currentSequenceNode = self.ui.inputSelector.currentNode()
		browserNode = slicer.modules.sequences.logic().GetFirstBrowserNodeForSequenceNode(currentSequenceNode)
		if browserNode is None:
			return 0, 0
		index = browserNode.GetSelectedItemNumber()
		t = currentSequenceNode.GetNthIndexValue(index)
		return t, index


class RegionPainterLogic(ScriptedLoadableModuleLogic):
	
	def __init__(self):
		"""
		Called when the logic class is instantiated. Can be used for initializing member variables.
		"""
		ScriptedLoadableModuleLogic.__init__(self)
	
	def setDefaultParameters(self, parameterNode):
		"""
		Initialize parameter node with default settings.
		"""
		pass
	

#
# RegionPainterTest
#

class RegionPainterTest(ScriptedLoadableModuleTest):
	"""
This is the test case for your scripted module.
Uses ScriptedLoadableModuleTest base class, available at:
https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
"""

	def setUp(self):
		""" Do whatever is needed to reset the state - typically a scene clear will be enough.
"""
		slicer.mrmlScene.Clear(0)

	def runTest(self):
		"""Currently no testing functionality.
"""
		self.setUp()
		self.test_SegmentEditor1()

	def test_SegmentEditor1(self):
		"""Add test here later.
"""
		self.delayDisplay("Starting the test")
		self.delayDisplay('Test passed!')