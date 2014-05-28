#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  

import os
import sys
from configobj4 import ConfigObj
from PIL import Image, ImageDraw, ImageFont

# Pad the positions with this many pixels
NORMALIZATION_PADDING = 100

# The radius of the dot markers placed for landmarks
MARKER_SIZE = 25

# Stores Vars for this running instance.
# This is more a neater way to handle our 
# variables than it is a formality.
Vars = {}


def handleCommandLine():
    """
    Handles command line arguments, printing help where necessary
    and storing values in our Vars object.
    
    """
    
    for index, arg in enumerate(sys.argv):
        if arg == '--help':
            showHelp()
            return False
        elif index > 0:
            Vars['configFile'] = arg
    return True


def loadConfig():
    """
    Load the config file into a dictionary-like object.
    
    """
    
    try:
        Vars['Config'] = ConfigObj(Vars['configFile'], file_error=True)
        return True
    except Exception, e:
        print(e)


def configSanityChecks():
    """
    Process the config values and performs a couple of sanity checks
    to make sure we have everything we need, and that the values
    are within a sane range.
    
    """
    
    config = Vars['Config']
    
    # Test for missing Landmarks
    pointCount = len(config.get('Landmarks'))
    if pointCount == 0:
        print('This config does not have a [Landmarks] section, or there' \
                ' are no Landmarks defined inside of it.')
        return False
    
    # Test for a map scale value
    if config['Map'].has_key('Scale'):
        try:
            mapScale = int(config['Map']['Scale'])
            print('The map scale is %s' % mapScale)
        except ValueError, e:
            print('Invalid map scale. Assuming the default.')
            config['Map']['Scale'] = 1
    else:
        config['Map']['Scale'] = 1
    
    print('Calculating map size...')
    minX, minY, maxX, maxY = (30927, 30927, -30912, -30912)
    Landmarks = config.get('Landmarks')
    for pointName, pointData in Landmarks.items():
        x, y = pointData['position']
        try:
            intX = int(x)
            intY = int(y)
        except ValueError:
            print('The point named "%s" has a bad position value, ' \
                    'I cannot process these.' % pointName)
            return False
        
        # remember the largest and smallest values
        minX = min(minX, intX)
        maxX = max(maxX, intX)
        minY = min(minY, intY)
        maxY = max(maxY, intY)
    
    # map possible negative coordinates to an image by
    # normalize the values using zero as the baseline.
    xOffset = ((minX < 0) and abs(minX) or 0)
    yOffset = ((minY < 0) and abs(minY) or 0)
    print('Normalizing coordinates...')
    landmarks = config.get('Landmarks')
    for pointName, pointData in landmarks.items():
        x, y = pointData['position']
        intX = int(x)
        intY = int(y)
        intX = intX + xOffset
        intY = intY + yOffset
        config['Landmarks'][pointName]['position'] = (intX, intY)
    
    # Test for an unreasonable map size
    mapWidth, mapHeight = (maxX - minX, maxY - minY)
    print('The map size is %sx%s, this scales to %sx%s' % \
            (mapWidth, mapHeight, 
            mapWidth * mapScale, mapHeight * mapScale))
    if (mapWidth < 1 or mapHeight < 1):
        print('The map size does not make sense, I cannot create it.')
        return False
    if (mapWidth > 2000 or mapHeight > 2000):
        reply = raw_input('This is a large map, continue? [Y/n]: ')
        if reply == 'n':
            return False
    Vars['MapSize'] = (mapWidth, mapHeight)
    return True


def generateMapImage():
    """
    Creates a new image canvas and renders the map information to it.
    
    """
    
    
    config = Vars['Config']
    mapScale = int(config['Map']['Scale'])
    mapSize = Vars['MapSize']
    # scale the map
    mapRescaled = (mapSize[0] * mapScale,
                    mapSize[1] * mapScale)
    # add the padding to the image
    mapRescaled = (mapRescaled[0] + NORMALIZATION_PADDING * 2,
                    mapRescaled[1] + NORMALIZATION_PADDING * 2)
    # create the image and drawing objects
    canvas = Image.new('RGB', mapRescaled, color='#ffffff')
    draw = ImageDraw.Draw(canvas)
    # half the marker to center them
    halfway = MARKER_SIZE / 2
    # Process each point
    landmarks = Vars['Config'].get('Landmarks')
    for pointName, pointData in landmarks.items():
        
        # get this point data
        x, y = pointData['position']
        intX = NORMALIZATION_PADDING + (int(x) * mapScale)
        intY = NORMALIZATION_PADDING + (int(y) * mapScale)
        
        # draw the landmark image, or the marker dot if no image
        if pointData.has_key('image'):
            imageFile = pointData['image']
            if not os.path.exists(imageFile):
                print(' * Missing: landmark "%s" image "%s"' % (pointName, imageFile))
            else:
                landmarkImage = Image.open(imageFile)
                # center the image on our point position
                sizeX, sizeY = landmarkImage.size
                imageX = intX - (sizeX / 2)
                imageY = intY - (sizeY / 2)
                canvas.paste(
                    landmarkImage, 
                    (imageX, imageY),
                    mask=landmarkImage
                    )
        else:
            draw.ellipse(
                (intX - halfway, intY - halfway, 
                intX + halfway, intY + halfway),
                fill='#000000')
        
        # print the landmark name
        draw.text(
            (intX + MARKER_SIZE, intY),
            pointName,
            fill='#000000')
        
    # write the image
    canvas.save('/tmp/canvas.png')

if __name__ == "__main__":
    """
    Entry point.
    
    """
    
    if handleCommandLine():
        if loadConfig():
            if configSanityChecks():
                if generateMapImage():
                    print('Done.')