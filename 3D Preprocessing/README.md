# 3D Preprocessing

![image](https://user-images.githubusercontent.com/43814396/165740688-e0036b69-d34c-466c-8b80-940c26a17437.png)
![image](https://user-images.githubusercontent.com/43814396/165741006-939be8e8-b35b-499f-88a6-8aa2593d14eb.png)

## Rotating and Centering
Done in Slicer Module `PhilipsDicomPatcher`

## Normalising
 * Two Scripts
   * NrrdSpacing.py: define the function (xd
   * SpacingAdjusting.py: apply the function

### NrrdSpacing
 * exportNormalisedNrrdAndAnnotation()
 * Apply normalisation
    * Skip if output file found

### SpacingAdjusting
 * Inputs
    * `NRRD_PATH`: path to nrrd folder (recursive)
    * `ANNOTATION_PATH`: path to annotation folder (recursive)
 
 * Outputs
    * `ADJUSTED_NRRD_EXPORT_PATH`
    * `ADJUSTED_ANNOTATION_EXPORT_PATH`
