import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

#
# SliceFlipping
#

class SliceFlipping(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "SliceFlipping"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#SliceFlipping">module documentation</a>.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

#
# SliceFlippingWidget
#

class SliceFlippingWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/SliceFlipping.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = SliceFlippingLogic()

    # Buttons
    self.ui.flipXButton.connect('clicked(bool)', self.onClickFlipX)
    self.ui.flipYButton.connect('clicked(bool)', self.onClickFlipY)

    layoutManager = slicer.app.layoutManager()
    for sliceViewName in layoutManager.sliceViewNames():
      controller = layoutManager.sliceWidget(sliceViewName).sliceController()
      controller.setSliceVisible(True)
      
    threeDWidget = layoutManager.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    threeDView.resetFocalPoint()

  def onClickFlipX(self):
    sliceNode = self.logic.sliceColourToNode[self.ui.sliceFlipComboBox.currentText]
    m_Slice_To_RAS = sliceNode.GetSliceToRAS()
    
    m_x_rotation = vtk.vtkMatrix4x4()
    m_x_rotation.SetElement(0, 0, -1)
    m_x_rotation.SetElement(0, 1, 0)
    m_x_rotation.SetElement(0, 2, 0)
    m_x_rotation.SetElement(0, 3, 0)
    m_x_rotation.SetElement(1, 0, 0)
    m_x_rotation.SetElement(1, 1, 1)
    m_x_rotation.SetElement(1, 2, 0)
    m_x_rotation.SetElement(1, 3, 0)
    m_x_rotation.SetElement(2, 0, 0)
    m_x_rotation.SetElement(2, 1, 0)
    m_x_rotation.SetElement(2, 2, -1)
    m_x_rotation.SetElement(2, 3, 0)
    m_x_rotation.SetElement(3, 0, 0)
    m_x_rotation.SetElement(3, 1, 0)
    m_x_rotation.SetElement(3, 2, 0)
    m_x_rotation.SetElement(3, 3, 1)

    vtk.vtkMatrix4x4().Multiply4x4(m_Slice_To_RAS, m_x_rotation, m_Slice_To_RAS)
    sliceNode.UpdateMatrices()
  
  
  def onClickFlipY(self):
    sliceNode = self.logic.sliceColourToNode[self.ui.sliceFlipComboBox.currentText]
    m_Slice_To_RAS = sliceNode.GetSliceToRAS()

    m_y_rotation = vtk.vtkMatrix4x4()
    m_y_rotation.SetElement(0, 0, 1)
    m_y_rotation.SetElement(0, 1, 0)
    m_y_rotation.SetElement(0, 2, 0)
    m_y_rotation.SetElement(0, 3, 0)
    m_y_rotation.SetElement(1, 0, 0)
    m_y_rotation.SetElement(1, 1, -1)
    m_y_rotation.SetElement(1, 2, 0)
    m_y_rotation.SetElement(1, 3, 0)
    m_y_rotation.SetElement(2, 0, 0)
    m_y_rotation.SetElement(2, 1, 0)
    m_y_rotation.SetElement(2, 2, -1)
    m_y_rotation.SetElement(2, 3, 0)
    m_y_rotation.SetElement(3, 0, 0)
    m_y_rotation.SetElement(3, 1, 0)
    m_y_rotation.SetElement(3, 2, 0)
    m_y_rotation.SetElement(3, 3, 1)

    vtk.vtkMatrix4x4().Multiply4x4(m_Slice_To_RAS, m_y_rotation, m_Slice_To_RAS)
    sliceNode.UpdateMatrices()
    

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def enter(self):
    """
    Called each time the user opens this module.
    """
    pass

  def exit(self):
    """
    Called each time the user opens a different module.
    """
    pass

  def onSceneStartClose(self, caller, event):
    """
    Called just before the scene is closed.
    """
    pass

  def onSceneEndClose(self, caller, event):
    """
    Called just after the scene is closed.
    """
    pass


#
# SliceFlippingLogic
#

class SliceFlippingLogic(ScriptedLoadableModuleLogic):
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
    self.sliceColourToID = {
      'Red': 'vtkMRMLSliceNodeRed',
      'Green': 'vtkMRMLSliceNodeGreen',
      'Yellow': 'vtkMRMLSliceNodeYellow',
    }
    self.sliceColourToNode = {c: slicer.util.getNode(nodeID) for c, nodeID in self.sliceColourToID.items()}

#
# SliceFlippingTest
#

class SliceFlippingTest(ScriptedLoadableModuleTest):
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
    pass

  def test_SliceFlipping1(self):
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
    pass
