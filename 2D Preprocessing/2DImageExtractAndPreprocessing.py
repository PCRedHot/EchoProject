import os, shutil
from tensorflow import keras
import numpy as np
from PIL import Image, ImageOps


MULTI_VIEW_MODEL_PATH = 'E:/Datasets/Echocardio/CNN test/multi view/saved/15 horizontal save_at_30.h5'
RAW_PNG_PATH = 'D:/EchoPatient2DData/2021-10-08/Raw PNG'
RNG_OUTPUT_PATH = 'D:/EchoPatient2DData/2021-10-08/PNG Output'
MASK_OUTPUT_PATH = 'D:/EchoPatient2DData/2021-10-08/Mask Output'



multi_view_model = keras.models.load_model(MULTI_VIEW_MODEL_PATH)



def getAllImagesColourArray(path=None, sequenceName=None):
	if path is None or sequenceName is None:
		return None
	fileNames = os.listdir(path)
	listArray = []
	for fileName in fileNames:
		if not fileName.startswith(sequenceName):
			continue
		img = Image.open(os.path.join(path, fileName))
		img_array = np.asarray(img)
		listArray.append(img_array)
	return np.array(listArray)

def getAllImagesArray(path=None, sequenceName=None):
    if path is None or sequenceName is None:
        return None
    fileNames = os.listdir(path)
    listArray = []
    is_colour_img = False
    colour_tested = False


    for fileName in fileNames:
        if not fileName.startswith(sequenceName):
            continue
        img = Image.open(os.path.join(path, fileName))
        img_array = np.asarray(img)

        img_crop_array = img_array[0:int(img_array.shape[0]/2),int(img_array.shape[1]*4/5):]

        if not colour_tested:
            colour_tested = True
            if np.any(np.all(img_crop_array.reshape((img_crop_array.shape[0]*img_crop_array.shape[1], 4)) == [247,230,0,255], axis=1)): # Colour Sequence -> ignore
                is_colour_img = True
                break
        

        grey_img = img.convert('L')
        grey_img_array = np.asarray(grey_img)
        listArray.append(grey_img_array)
    return is_colour_img, np.array(listArray)

def getMasks(path=None, sequenceName=None, outputPath=None):
    if path is None or sequenceName is None:
        return
    if outputPath is None:
        outputPath = ''
    is_Colour_img, imageArray = getAllImagesArray(path=path, sequenceName=sequenceName)
    if is_Colour_img: # Colour Sequence -> ignore
        return is_Colour_img, None

    minArray = np.amin(imageArray, axis=0)
    minArray[minArray < 50] = 0
    minArray[minArray != 0] = 255

    invertMinArray = minArray.copy()
    invertMinArray[minArray == 0] = 255
    invertMinArray[minArray == 255] = 0

    stdArray = np.std(imageArray, axis=0)
    div = np.ptp(stdArray)
    if div == 0:
        return is_Colour_img, None
    stdArray = (255 * (stdArray - np.min(stdArray)) / div).astype('uint8')
    stdArray[stdArray > 10] = 255

    std_img = Image.fromarray(stdArray, 'L')
    std_img_invert = ImageOps.invert(std_img)

    maskArray = np.amax(np.stack([stdArray, invertMinArray], axis=0), axis=0)
    img = Image.fromarray(maskArray, 'L')
    return is_Colour_img, img

def getAllSequenceName(path=None):
    if path is None:
        return []
    fileNames = os.listdir(path)
    listArray = []
    pre_name = ''
    for fileName in fileNames:
        name = fileName[:-4].split('_')[0]
        if pre_name == name:
            continue
        pre_name = name
        if name not in listArray:
            listArray.append(name)
    return listArray
    
if __name__ == '__main__':
    
    if not os.path.exists(RNG_OUTPUT_PATH):
        os.makedirs(RNG_OUTPUT_PATH)
    if not os.path.exists(MASK_OUTPUT_PATH):
        os.makedirs(MASK_OUTPUT_PATH)

    patientList = os.listdir(path=RAW_PNG_PATH)

    existedOutput = []

    for root, dirs, files in os.walk(MASK_OUTPUT_PATH):
        for name in files:
            existedOutput.append(name.split('_')[0])

    for patient in patientList:
        patientPath = os.path.join(RAW_PNG_PATH, patient)
        print(patient)
        studyList = os.listdir(path=patientPath)
        for study in studyList:
            studyPath = os.path.join(patientPath, study)
            seriesList = os.listdir(path=studyPath)
            for series in seriesList:
                seriesPath = os.path.join(studyPath, series)

                sequenceNames = getAllSequenceName(seriesPath)
                fileNames = os.listdir(seriesPath)

                for sequenceName in sequenceNames:
                    if sequenceName in existedOutput:
                        print(sequenceName, 'Already Exist')
                        continue


                    outputPath = os.path.join(RNG_OUTPUT_PATH, patient)
                    

                    if not os.path.isdir(outputPath):
                        os.makedirs(outputPath)
                    
                    
                    is_Colour_img, maskImage = getMasks(path=seriesPath, sequenceName=sequenceName, outputPath=outputPath)
                    if is_Colour_img:   # Colour Sequence -> ignore
                        print(sequenceName, 'Colour Sequence, Ignored')
                        continue
                    if maskImage is None:
                        print(sequenceName, 'Mask is None')
                        continue
                    
                    maskImageArray = np.asarray(maskImage)
                    mask_binary_array = maskImageArray > 200


                    imagesInSequence = []
                    for f in fileNames:
                        if f.startswith(sequenceName):
                            imagesInSequence.append(f)
                    
                    # Test Multi-view for the first frame
                    test_image = np.asarray(Image.open(os.path.join(seriesPath, imagesInSequence[0])).convert('L'))
                    test_image[mask_binary_array == False] = 0
                    test_image = test_image.reshape((1, test_image.shape[0], test_image.shape[1], 1))
                    resized_test_image = keras.preprocessing.image.smart_resize(test_image, (60, 80), interpolation='bilinear')

                    is_multi = multi_view_model.predict(resized_test_image) < 0.5

                    if is_multi:
                        print(sequenceName, 'Multi View Sequence, Ignored')
                        continue
                    
                    print(sequenceName, 'OK')

                    if MASK_OUTPUT_PATH is not None:
                        maskOutputPath = os.path.join(MASK_OUTPUT_PATH, patient)
                        if not os.path.isdir(maskOutputPath):
                            os.makedirs(maskOutputPath)
                        maskImage.save(os.path.join(maskOutputPath, sequenceName + '_mask.png'))
                    
                                        
                    for imageName in imagesInSequence:
                        if len(imageName.split('_')) != 2:
                            print(imageName, 'Inconsistent ImageName')
                            continue
                        imagePath = os.path.join(seriesPath, imageName)
                    
                        imageArray = np.asarray(Image.open(imagePath).convert('L'))
                        imageArray[mask_binary_array == False] = 0
                        
                        i = imageName.split('_')[1][5:-4].zfill(4)

                        sequence_str, frame_str = imageName.split('_')
                        frame_number = frame_str[5:-4].zfill(3)
                        
                        new_image_name = sequence_str + '_Frame' + frame_number + '_out.png'

                        #print(i, imageName)
                        #print(sequence_str, frame_number)
                        img = Image.fromarray(imageArray, 'L')
                        img.save(os.path.join(outputPath, new_image_name))
                    
            


