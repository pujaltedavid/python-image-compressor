import sys
import os
import math
from PIL import Image, ImageEnhance

def help():
    print(
"""
The program finds any image in child folders and compresses and crops them in new folders made automatically.

To square-crop any image differently, just add -option- to the source filename.
                  
(eg: DSC_1000.JPG -> DSC_1000-2-.JPG)     

                                                                          3 - righter             2 - lefter       
options:  1 - top      2 - higher      3 - lower     4 - bottom       _________________       _________________      
           ________       ________       ________      ________      |     |       |   |     |   |       |     |
          |        |     |        |     |        |    |        |     |     |   xx  |   |     |   |   xx  |     |
          |   xx   |     |________|     |        |    |        |     |     |   xx  |   |     |   |   xx  |     |
          |   xx   |     |        |     |________|    |        |     |_____|_______|___|     |___|_______|_____|
          |________|     |   xx   |     |        |    |        |
          |        |     |   xx   |     |   xx   |    |________|          4 - right                1 - left
          |        |     |________|     |   xx   |    |        |      _________________       _________________    
          |        |     |        |     |________|    |   xx   |     |         |       |     |       |         |  
          |        |     |        |     |        |    |   xx   |     |         |   xx  |     |   xx  |         | 
          |________|     |________|     |________|    |________|     |         |   xx  |     |   xx  |         | 
                                                                     |_________|_______|     |_______|_________|"""
    )


def getCoordinates(originalSize, newMaxSize, sizeDiffer, cropType):
    """Get crop coordinates according to cropType, new size and original size
    """
    print('Entered on getCoordinates:', originalSize, newMaxSize, sizeDiffer, cropType)
    horizontal = originalSize[0] > originalSize[1]
    
    left = sizeDiffer if horizontal else 0
    upper = 0 if horizontal else sizeDiffer
    right = left+newMaxSize if horizontal else originalSize[0]
    lower = originalSize[1] if horizontal else upper+newMaxSize
    
    if cropType:
        if horizontal:
            if cropType == 1:
                left = 0
            elif cropType == 2:
                left -= int(left/2)
            elif cropType == 3:
                left += int(left/2)
            elif cropType == 4:
                left = originalSize[0] - newMaxSize
            right = left + newMaxSize
        else:
            if cropType == 1:
                upper = 0
            elif cropType == 2:
                upper -= int(upper/2)
            elif cropType == 3:
                upper += int(upper/2)
            elif cropType == 4:
                upper = originalSize[1] - newMaxSize
            lower = upper + newMaxSize

    return (left, upper, right, lower)


def cutImage(picture, filename, size, aspectRatio, crop, quality, cropType):
    """Resize the image to a given size and crop the image if the aspect
    ratio does not match perfectly.
    """
    print(
    'Entered on cutImage:',
    picture,
    picture.size,
    size,
    aspectRatio,
    crop,
    quality,
    cropType
  )
    # Crop the image (when the aspect ratio doesn't match)
    if crop:
        horizontal = picture.size[0] > picture.size[1]
        # New integer maximum size according to the aspect ratio
        newMaxSize = (picture.size[1]*aspectRatio if horizontal else
                      picture.size[0]*aspectRatio)
        # Pixel difference between old and new aspectRatio.
        sizeDiffer = math.floor((max(picture.size)-newMaxSize)/2)
        
        left, upper, right, lower = getCoordinates(picture.size,
                                              newMaxSize, sizeDiffer, cropType)
        
        assert(max((right-left),(upper-lower)) / min((right-left),(upper-lower))
               != aspectRatio)
        
        print('COORDINATES:', left, upper, right, lower)
        
        picture = picture.crop((left, upper, right, lower))
        
        print('After crop:', picture.size)
    
    # Resize.
    resizedPicture = picture.resize(size, reducing_gap=3.0, resample=5)
    
    print('After resize:', resizedPicture.size)
    
    # Sharpen image when it is not for lazyLoad
    if quality > 50:
        imgSharpener = ImageEnhance.Sharpness(resizedPicture)
        resizedPicture = imgSharpener.enhance(1.5)

    # Save.
    resizedPicture.save(filename, "JPEG", optimize = True, quality = quality)
    print(' . ')
    

def compress(picture, filename, square, crop=None):
    """Crop the image if needed and compress it to some resolutions and
    qualities.
    """
    print('Entered on compress:', picture, picture.size[0], picture.size[1], square, crop)
    # Changeable constants
    pictureQuality = 80
    lazyPictureQuality = 10
    
    minSizes = ([['S', 50],
                 ['M', 200],
                 ['L', 400]] if square else [['XS', 480],
                                             ['S', 720],
                                             ['M', 1080],
                                             ['L', 1280],
                                             ['XL', 1440],
                                             ['XXL', 2160]])
    minLazySize = 50 if square else 200
    
    # Make the image compression
    originalSize = picture.size
    horizontal = originalSize[0] > originalSize[1]
    aspectRatio = max(originalSize)/min(originalSize)
    
    # Scale down to nearest multiple of 0.05 (0.05 makes sizes integer)
    newAspectRatio = 1 if square else math.floor(aspectRatio / 0.05) * 0.05
    
    # Compress the image with each resolution.
    for res, minSize in minSizes:
        size = ([minSize*newAspectRatio, minSize] if horizontal else
               [minSize, minSize*newAspectRatio])
        
        prefix = 'SQ-' if square else 'FULL-'
        name = prefix + res + '-' + filename + '.JPEG'
        
        assert(size[0] == round(size[0]) or abs(size[0]-round(size[0])) < 0.000001)
        assert(size[1] == round(size[1]) or abs(size[1]-round(size[1])) < 0.000001)
        size = [int(size[0]), int(size[1])]
        
        cutImage(picture, name, size, newAspectRatio, aspectRatio != newAspectRatio,
                 pictureQuality, crop)
        
    # Make the lazy-load image  compression   
    size = ([minLazySize*newAspectRatio, minLazySize] if horizontal else
               [minLazySize, minLazySize*newAspectRatio])
    
    prefix = 'LZ-SQ-' if square else 'LZ-FULL-' 
    name = prefix + filename + '.JPEG'
    
    assert(size[0] == round(size[0]) or abs(size[0]-round(size[0])) < 0.000001)
    assert(size[1] == round(size[1]) or abs(size[1]-round(size[1])) < 0.000001)
    size = [int(size[0]), int(size[1])]
    
    cutImage(picture, name, size, newAspectRatio, aspectRatio != newAspectRatio,
                 lazyPictureQuality, crop)
    

def compressAll(file, idx, directory, crop):
    """Compress the image and make a miniature, both with a lazy-loading
    version.
    """
    # Get image path and open image
    filepath = os.path.join(directory, file)
    picture = Image.open(filepath)
    
    # Display error if the image is square
    assert(picture.size[0] != picture.size[1])
    
    # Make normal and lazy compression
    compress(picture, idx, square=False)
    compress(picture, idx, square=True, crop=crop)


def main():
    # Display help function
    if len(sys.argv) > 1:
        help()
        return
    
    # finds current working dir
    cwd = os.getcwd()
    
    # Create new directory to save all other image directories
    try:
        os.mkdir(cwd+'\\compressed')
    except:
        print('The directory *compressed* already exists.', end='\n\n')
    
    formats = ('.jpg') 
    
    # Loop through directories
    directories = [x[0] for x in os.walk(cwd)][1:]
    for directory in directories:
        # Create and set New directory to save the images
        os.chdir(cwd+'\\compressed')
        
        try:
            os.mkdir(cwd+'\\compressed'+directory[directory.rfind('\\'):])
        except:
            print('The directory *'+directory[directory.rfind('\\'):]+'* already exists.', end='\n\n')
        
        os.chdir(cwd+'\\compressed'+directory[directory.rfind('\\'):])
        
        # Loop through images in directory
        for idx, file in enumerate(os.listdir(directory)):
            # Check that the file is an image.
            if file.lower()[-4:] in formats:
                # Check for crop type
                if '-1-' in file:
                    crop = 1
                elif '-2-' in file:
                    crop = 2
                elif '-3-' in file:
                    crop = 3
                elif '-4-' in file:
                    crop = 4
                else:
                    crop = None
                
                (print('Analyzing', file, '-> crop type', crop, 'detected.') if crop else
                 print('Analyzing', file))
                compressAll(file, str(idx), directory, crop)
                print('done!\n\n')
                
    print("Done") 
  
# Driver code 
if __name__ == "__main__": 
    main() 
