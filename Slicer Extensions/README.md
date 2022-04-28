# Slicer Extension
This extension is named SliceIntersection (not important thou)
This includes
* IntersectionControls (for record)
* SliceFlipping (for record)
* RegionPainter (not used)
* PhilipsDicomPatcher (in use)
* ViewReconstruction (in use)

Please use Slicer 4.13 for ViewReconstruction.

PhilipsDicomPatcher could be used in v4.11 or v4.13.

## PhilipsDicomPatcher
* Check the box to Export NRRD Files
* Others options are useless xd

![image](https://user-images.githubusercontent.com/43814396/164056584-93dc4424-5f12-4254-9566-d0d6cfdc1226.png)

PhilisDicomPatcher.py
* Line 254 - 260: Rotate the Data
* Line 263 - 272: Center the Data

## ViewReconstruction
![image](https://user-images.githubusercontent.com/43814396/164058018-96ecb72b-dd37-48f6-84a3-ac68c355d970.png)

* Point Reference File: reference_points.json
* Width and Height for output images  (range: 200 - 2000) (Line 166 - 178)

Features:
* Recursive check in directories, matching the file name between NRRD and Annotation
* Automatic use normalised annotation to reconstruct if found



