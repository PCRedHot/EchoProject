import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import numpy as np

try:
  import pydicom as dicom
except:
  # Slicer-4.10 backward compatibility
  import dicom

#
# PhilipsDicomPatcher
#

class PhilipsDicomPatcher(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "PhilipsDicomPatcher"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#PhilipsDicomPatcher">module documentation</a>.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

#
# PhilipsDicomPatcherWidget
#

class PhilipsDicomPatcherWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.logic = None

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    self.inputDirSelector = ctk.ctkPathLineEdit()
    self.inputDirSelector.filters = ctk.ctkPathLineEdit.Dirs
    self.inputDirSelector.settingKey = 'Philips4dUsDicomPatcherInputDir'
    parametersFormLayout.addRow("Input DICOM directory:", self.inputDirSelector)

    self.outputDirSelector = ctk.ctkPathLineEdit()
    self.outputDirSelector.filters = ctk.ctkPathLineEdit.Dirs
    self.outputDirSelector.settingKey = 'Philips4dUsDicomPatcherOutputDir'
    parametersFormLayout.addRow("Output DICOM directory:", self.outputDirSelector)

    self.enableDicomOutputCheckBox = qt.QCheckBox()
    self.enableDicomOutputCheckBox.checked = True
    self.enableDicomOutputCheckBox.setToolTip("If checked, patched 4D US DICOM files will be saved as DICOM files")
    parametersFormLayout.addRow("Export to DICOM files", self.enableDicomOutputCheckBox)

    self.anonymizeDicomCheckBox = qt.QCheckBox()
    self.anonymizeDicomCheckBox.checked = False
    self.anonymizeDicomCheckBox.setToolTip(
      "If checked, then patient identifiable information will be removed from the patched DICOM files")
    parametersFormLayout.addRow("     Anonymize DICOM files", self.anonymizeDicomCheckBox)

    self.enableNrrdOutputCheckBox = qt.QCheckBox()
    self.enableNrrdOutputCheckBox.checked = False
    self.enableNrrdOutputCheckBox.setToolTip("If checked, 4D US DICOM files will be saved as NRRD files")
    parametersFormLayout.addRow("Export to NRRD files", self.enableNrrdOutputCheckBox)

    #
    # Patch Button
    #
    self.patchButton = qt.QPushButton("Patch")
    self.patchButton.toolTip = "Fix and optionally anonymize DICOM files"
    parametersFormLayout.addRow(self.patchButton)

    # connections
    self.patchButton.connect('clicked(bool)', self.onPatchButton)

    self.statusLabel = qt.QPlainTextEdit()
    self.statusLabel.setTextInteractionFlags(qt.Qt.TextSelectableByMouse)
    parametersFormLayout.addRow(self.statusLabel)

    # Add vertical spacer
    self.layout.addStretch(1)

    self.logic = PhilipsDicomPatcherLogic()
    self.logic.logCallback = self.addLog

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    pass

  def onPatchButton(self):
    slicer.app.setOverrideCursor(qt.Qt.WaitCursor)
    try:
      self.inputDirSelector.addCurrentPathToHistory()
      self.outputDirSelector.addCurrentPathToHistory()
      self.statusLabel.plainText = ''
      self.logic.patchDicomDir(self.inputDirSelector.currentPath, self.outputDirSelector.currentPath, self.enableDicomOutputCheckBox.checked, self.anonymizeDicomCheckBox.checked, self.enableNrrdOutputCheckBox.checked)
    except Exception as e:
      print("Unexpected error: {0}".format(e.msg))
      import traceback
      traceback.print_exc()
    slicer.app.restoreOverrideCursor()
    
  
  def addLog(self, text):
    """
    Append text to log window
    """
    self.statusLabel.appendPlainText(text)
    slicer.app.processEvents() # force update
 
#
# PhilipsDicomPatcherLogic
#

class PhilipsDicomPatcherLogic(ScriptedLoadableModuleLogic):
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

  def generateUid(self):
    if slicer.app.majorVersion == 4 and slicer.app.minorVersion <= 10:
      import dicom
      return dicom.UID.generate_uid(None)
    else:
      import pydicom as dicom
      return dicom.uid.generate_uid(None)

  def addLog(self, text):
    logging.info(text)
    if self.logCallback:
      self.logCallback(text)

  def isDicomUltrasoundFile(self, inputDicomFilePath):
    from DICOMLib import DICOMLoadable
    dicomPlugin = slicer.modules.dicomPlugins['DicomUltrasoundPlugin']()
    files = [inputDicomFilePath]
    loadables = dicomPlugin.examineFiles(files)
    return len(loadables) > 0

  def convertUltrasoundDicomToNrrd(self, inputDicomFilePath, outputNrrdFilePath):
    from DICOMLib import DICOMLoadable
    # Load from DICOM
    loadable = DICOMLoadable()
    loadable.files = [inputDicomFilePath]
    loadable.name = os.path.basename(inputDicomFilePath)
    loadable.tooltip = ''
    loadable.selected = True
    loadable.confidence = 1.
    loadable.createBrowserNode = False  # don't create browser nodes (it would clutter the scene when batch processing)
    sequenceNode = self.loadPhilips4DUSAsSequence(loadable)

    for volumeIndex in range(sequenceNode.GetNumberOfDataNodes()):
      volumeNode = sequenceNode.GetNthDataNode(volumeIndex)
      a = slicer.util.arrayFromVolume(volumeNode)
      
      slicer.util.arrayFromVolumeModified(volumeNode)
  
    # Write to NRRD
    storageNode = sequenceNode.GetStorageNode()
    storageNode.SetFileName(outputNrrdFilePath)
    success = storageNode.WriteData(sequenceNode)
  
    # Clean up
    slicer.mrmlScene.RemoveNode(sequenceNode)
  
    return success

  def loadPhilips4DUSAsSequence(self,loadable):
    """Load the selection as an Ultrasound, store in a Sequence node
    """

    # get the key info from the "fake" dicom file
    filePath = loadable.files[0]
    ds = dicom.read_file(filePath, stop_before_pixels=True)
    columns = ds.Columns
    rows = ds.Rows
    slices = ds[(0x3001,0x1001)].value # private tag!
    spacing = (
            ds.PhysicalDeltaX * 10,
            ds.PhysicalDeltaY * 10,
            ds[(0x3001,0x1003)].value * 10 # private tag!
            )
    frames  = int(ds.NumberOfFrames)
    imageComponents = frames
    frameTimeMsec = ds.FrameTime

    pixelShape = (frames, slices, rows, columns)
    pixelSize = pixelShape[0] * pixelShape[1] * pixelShape[2] * pixelShape[3]
    totalFileSize = os.path.getsize(filePath)
    headerSize = totalFileSize-pixelSize

    outputSequenceNode = slicer.vtkMRMLSequenceNode()
  
    centerRAS = None
    for frame in range(frames):

      imgReader = vtk.vtkImageReader()
      imgReader.SetFileDimensionality(3)
      imgReader.SetFileName(filePath)
      imgReader.SetNumberOfScalarComponents(1)
      imgReader.SetDataScalarTypeToUnsignedChar()
      imgReader.SetDataExtent(0,columns-1, 0,rows-1, 0,slices-1)
      imgReader.SetHeaderSize(headerSize+frame*slices*rows*columns)
      imgReader.FileLowerLeftOn()
      imgReader.Update()

      outputNode = slicer.vtkMRMLScalarVolumeNode()
      outputNode.SetAndObserveImageData(imgReader.GetOutput())
      outputNode.SetSpacing(spacing)
      
      
      # Flip Data
      array = slicer.util.arrayFromVolume(outputNode)
      temp = np.copy(array)
      for k in range(slices):
        for j in range(rows):
          array[k, j, :] = temp[slices - k - 1, rows - j - 1,:]
      slicer.util.arrayFromVolumeModified(outputNode)
      
      
      # centering the Data
      if centerRAS is None:
        m_IJK_to_RAS = vtk.vtkMatrix4x4()
        outputNode.GetIJKToRASMatrix(m_IJK_to_RAS)
        origin_ijk = [(slices-1)/2, (rows-1)/2, (columns-1)/2, 1]
        origin_ras = [0, 0, 0, 1]
        m_IJK_to_RAS.MultiplyPoint(origin_ijk, origin_ras)
        centerRAS = origin_ras
      
      outputNode.SetOrigin(-centerRAS[0], -centerRAS[1], -centerRAS[2])
      #outputNode.SetOrigin(0, 0, 0)
      
      timeStampSec = "{:.3f}".format(frame * frameTimeMsec * 0.001)
      outputSequenceNode.SetDataNodeAtValue(outputNode, timeStampSec)

    outputSequenceNode.SetName(slicer.mrmlScene.GenerateUniqueName(loadable.name))
    slicer.mrmlScene.AddNode(outputSequenceNode)

    # Create storage node that allows saving node as nrrd
    outputSequenceStorageNode = slicer.vtkMRMLVolumeSequenceStorageNode()
    slicer.mrmlScene.AddNode(outputSequenceStorageNode)
    outputSequenceNode.SetAndObserveStorageNodeID(outputSequenceStorageNode.GetID())

    if not hasattr(loadable, 'createBrowserNode') or loadable.createBrowserNode:
      # Add a browser node and show the volume in the slice viewer for user convenience
      outputSequenceBrowserNode = slicer.vtkMRMLSequenceBrowserNode()
      outputSequenceBrowserNode.SetName(slicer.mrmlScene.GenerateUniqueName(outputSequenceNode.GetName()+' browser'))
      slicer.mrmlScene.AddNode(outputSequenceBrowserNode)
      outputSequenceBrowserNode.SetAndObserveMasterSequenceNodeID(outputSequenceNode.GetID())
      masterOutputNode = outputSequenceBrowserNode.GetProxyNode(outputSequenceNode)

      # Automatically select the volume to display
      appLogic = slicer.app.applicationLogic()
      selNode = appLogic.GetSelectionNode()
      selNode.SetReferenceActiveVolumeID(masterOutputNode.GetID())
      appLogic.PropagateVolumeSelection()
      appLogic.FitSliceToAll()
      slicer.modules.sequences.setToolBarActiveBrowserNode(outputSequenceBrowserNode)

      # create Subject hierarchy nodes for the loaded series
      self.addSeriesInSubjectHierarchy(loadable, masterOutputNode)

    return outputSequenceNode

  def patchDicomDir(self, inputDirPath, outputDirPath, exportDicom=True, anonymizeDicom=False,
                    exportUltrasoundToNrrd=False):
    """
    Since CTK (rightly) requires certain basic information [1] before it can import
    data files that purport to be dicom, this code patches the files in a directory
    with some needed fields.  Apparently it is possible to export files from the
    Philips PMS QLAB system with these fields missing.

    Calling this function with a directory path will make a patched copy of each file.
    Importing the old files to CTK should still fail, but the new ones should work.

    The directory is assumed to have a set of instances that are all from the
    same study of the same patient.  Also that each instance (file) is an
    independent (multiframe) series.

    [1] https://github.com/commontk/CTK/blob/16aa09540dcb59c6eafde4d9a88dfee1f0948edc/Libs/DICOM/Core/ctkDICOMDatabase.cpp#L1283-L1287
    """
  
    if slicer.app.majorVersion == 4 and slicer.app.minorVersion <= 10:
      import dicom
    else:
      import pydicom as dicom
  
    if not outputDirPath:
      outputDirPath = inputDirPath
  
    self.addLog('DICOM patching started...')
    logging.debug('DICOM patch input directory: ' + inputDirPath)
    logging.debug('DICOM patch output directory: ' + outputDirPath)
  
    patientIDToRandomIDMap = {}
    studyUIDToRandomUIDMap = {}
    seriesUIDToRandomUIDMap = {}
    numberOfSeriesInStudyMap = {}
  
    # All files without a patient ID will be assigned to the same patient
    randomPatientID = self.generateUid()
  
    requiredTags = ['PatientName', 'PatientID', 'StudyInstanceUID', 'SeriesInstanceUID', 'SeriesNumber']
    for root, subFolders, files in os.walk(inputDirPath):
    
      # Assume that all files in a directory belongs to the same study
      randomStudyUID = self.generateUid()
    
      currentSubDir = os.path.relpath(root, inputDirPath)
      rootOutput = os.path.join(outputDirPath, currentSubDir)
    
      for file in files:
        filePath = os.path.join(root, file)
        self.addLog('Examining %s...' % os.path.join(currentSubDir, file))
        try:
          ds = dicom.read_file(filePath)
        except (IOError, dicom.filereader.InvalidDicomError):
          self.addLog('  Not DICOM file. Skipped.')
          continue
      
        if not hasattr(ds, 'SOPClassUID'):
          self.addLog('  No SOPClassUID tag found. Skipped.')
          continue
      
        if ds.SOPClassUID != '1.2.840.113543.6.6.1.3.10002':
          self.addLog('  Not recognized as Philips Cartesian 4D ultrasound DICOM file. Skipped.')
          continue
      
        self.addLog('  Patching...')
      
        for tag in requiredTags:
          if not hasattr(ds, tag):
            setattr(ds, tag, '')
      
        # Generate a new SOPInstanceUID to avoid different files having the same SOPInstanceUID
        ds.SOPInstanceUID = self.generateUid()
      
        if ds.PatientName == '':
          ds.PatientName = "Unspecified Patient"
        if ds.PatientID == '':
          ds.PatientID = randomPatientID
        if ds.StudyInstanceUID == '':
          ds.StudyInstanceUID = randomStudyUID
        if ds.SeriesInstanceUID == '':
          ds.SeriesInstanceUID = self.generateUid()
      
        # Generate series number to make it easier to identify a sequence within a study
        if ds.SeriesNumber == '':
          if ds.StudyInstanceUID not in numberOfSeriesInStudyMap:
            numberOfSeriesInStudyMap[ds.StudyInstanceUID] = 0
          numberOfSeriesInStudyMap[ds.StudyInstanceUID] = numberOfSeriesInStudyMap[ds.StudyInstanceUID] + 1
          ds.SeriesNumber = numberOfSeriesInStudyMap[ds.StudyInstanceUID]
      
        if anonymizeDicom:
        
          self.addLog('  Anonymizing...')
        
          ds.StudyDate = ''
          ds.StudyTime = ''
          ds.ContentDate = ''
          ds.ContentTime = ''
          ds.AccessionNumber = ''
          ds.ReferringPhysiciansName = ''
          ds.PatientsBirthDate = ''
          ds.PatientsSex = ''
          ds.StudyID = ''
          ds[(0x3001, 0x1004)].value = ''  # Some ID in a private tag - clear it, just in case
          ds.PatientName = "Unspecified Patient"
        
          # replace ids with random values - re-use if we have seen them before
          if ds.PatientID not in patientIDToRandomIDMap:
            patientIDToRandomIDMap[ds.PatientID] = self.generateUid()
          ds.PatientID = patientIDToRandomIDMap[ds.PatientID]
          if ds.StudyInstanceUID not in studyUIDToRandomUIDMap:
            studyUIDToRandomUIDMap[ds.StudyInstanceUID] = self.generateUid()
          ds.StudyInstanceUID = studyUIDToRandomUIDMap[ds.StudyInstanceUID]
          if ds.SeriesInstanceUID not in studyUIDToRandomUIDMap:
            seriesUIDToRandomUIDMap[ds.SeriesInstanceUID] = self.generateUid()
          ds.SeriesInstanceUID = seriesUIDToRandomUIDMap[ds.SeriesInstanceUID]
      
        if inputDirPath == outputDirPath:
          (name, ext) = os.path.splitext(filePath)
          patchedFilePath = name + ('-anon' if anonymizeDicom else '') + '-patched' + ext
          nrrdFilePath = name + '.seq.nrrd'
        else:
          patchedFilePath = os.path.abspath(os.path.join(rootOutput, file))
          nrrdFilePath = os.path.splitext(patchedFilePath)[0] + '.seq.nrrd'
          if not os.path.exists(rootOutput):
            os.makedirs(rootOutput)
      
        self.addLog('  Writing DICOM...')
        dicom.write_file(patchedFilePath, ds)
        self.addLog('  Created DICOM file: %s' % patchedFilePath)
      
        if exportUltrasoundToNrrd and self.isDicomUltrasoundFile(patchedFilePath):
          self.addLog('  Writing NRRD...')
        
          if self.convertUltrasoundDicomToNrrd(patchedFilePath, nrrdFilePath):
            self.addLog('  Created NRRD file: %s' % nrrdFilePath)
          else:
            self.addLog('  NRRD file save failed')
      
        if not exportDicom:
          os.remove(patchedFilePath)
          self.addLog('  Deleted temporary DICOM file')
  
    self.addLog('DICOM patching completed.')
    
#
# PhilipsDicomPatcherTest
#

class PhilipsDicomPatcherTest(ScriptedLoadableModuleTest):
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
    self.test_PhilipsDicomPatcher1()

  def test_PhilipsDicomPatcher1(self):
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
    inputVolume = SampleData.downloadSample('PhilipsDicomPatcher1')
    self.delayDisplay('Loaded test data set')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 695)

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    threshold = 100

    # Test the module logic

    logic = PhilipsDicomPatcherLogic()

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
