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

# The radius of the dot markers placed for landmarks
MARKER_SIZE = 5

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
            # get the path of the config file
            configPath = os.path.dirname(os.path.realpath(arg))
            Vars['ConfigPath'] = configPath

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

    # Test for a map section
    if not 'Map' in config:
        print('Config is missing a [Map] section.')
        return False

    mapConfig = config['Map']

    # Test for an output Filename
    if not 'Filename' in mapConfig:
        print('Config is missing a [Map][[Filename]] entry.')
        return False

    # Test for missing Landmarks
    pointCount = len(config.get('Landmarks'))
    if pointCount == 0:
        print('There are no  Landmarks defined.')
        return False

    # Test for a map scale value
    if 'Scale' in mapConfig:
        try:
            mapScale = int(mapConfig['Scale'])
            print('The map scale is %s' % mapScale)
        except ValueError, e:
            print('Invalid map scale. Assuming the default.')
            mapConfig['Scale'] = 1
    else:
        mapConfig['Scale'] = 1

    # Test for map padding
    if 'Padding' in mapConfig:
        for n in range(0, 3):
            try:
                nValue = int(mapConfig['Padding'][n])
            except ValueError:
                print('The map Padding has an invalid value. Ignoring.')
                mapConfig['Padding'][n] = 0
    else:
        mapConfig['Padding'] = (0, 0, 0, 0)

    print('Calculating map size...')
    minX, minY, maxX, maxY = (30927, 30927, -30912, -30912)
    Landmarks = config.get('Landmarks')
    for pointName, pointData in Landmarks.items():
        x, y = pointData['position']
        try:
            intX = int(x)
            intY = int(y)
        except ValueError:
            print('The point named "%s" has a bad position value, '
                  'I cannot process these.' % pointName)
            return False

        # remember the largest and smallest values
        minX = min(minX, intX)
        maxX = max(maxX, intX)
        minY = min(minY, intY)
        maxY = max(maxY, intY)

    yOffset = minY < 0 and abs(minY) or 0

    print('Normalizing coordinates...')
    landmarks = config.get('Landmarks')
    for pointName, pointData in landmarks.items():
        x, y = pointData['position']
        intX = int(x)
        intY = int(y)
        intX = maxX - intX
        intY = intY + yOffset
        config['Landmarks'][pointName]['position'] = (intX, intY)

    # Test for an unreasonable map size
    mapWidth, mapHeight = (maxX - minX, maxY + yOffset)
    print('The map size is %sx%s, this scales to %sx%s' %
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

    LEFT, TOP, RIGHT, BOTTOM = (0, 1, 2, 3)
    config = Vars['Config']
    mapConfig = config['Map']
    mapScale = int(mapConfig['Scale'])
    mapSize = Vars['MapSize']

    # scale the map
    mapRescaled = (mapSize[0] * mapScale, mapSize[1] * mapScale)

    # add the padding to the image
    mapRescaled = (
        mapRescaled[0] +
        int(mapConfig['Padding'][LEFT]) +
        int(mapConfig['Padding'][RIGHT]),
        mapRescaled[1] +
        int(mapConfig['Padding'][TOP]) +
        int(mapConfig['Padding'][BOTTOM])
        )

    # get or use the default canvas color
    canvasColor = config['Map'].get('Backcolor', '#ffffff')

    # create the image and drawing objects
    canvas = Image.new('RGB', mapRescaled, color=canvasColor)
    draw = ImageDraw.Draw(canvas)

    # half the marker to center image pastes
    halfway = MARKER_SIZE / 2

    # tile a background image
    if 'BackgroundTile' in config['Map']:
        tileImageFile = os.path.join(Vars['ConfigPath'],
                                     config['Map']['BackgroundTile'])
        tileImage = Image.open(tileImageFile)
        print('Found background tile image: %sx%s, tiling...' % tileImage.size)
        for tileX in range(0, mapRescaled[0], tileImage.size[0]):
            for tileY in range(0, mapRescaled[1], tileImage.size[1]):
                canvas.paste(
                    tileImage,
                    (tileX, tileY,
                     tileX + tileImage.size[0],
                     tileY + tileImage.size[1]))
    # Process each point
    landmarks = Vars['Config'].get('Landmarks')
    print('Drawing landmarks: ')

    for pointName, pointData in landmarks.items():

        # get this point data
        x, y = pointData['position']
        intX = int(mapConfig['Padding'][LEFT]) + (int(x) * mapScale)
        intY = int(mapConfig['Padding'][TOP]) + (int(y) * mapScale)

        print('* %s' % pointName)

        # draw the landmark image, or the marker dot if no image
        if 'image' in pointData:
            imageFile = os.path.join(Vars['ConfigPath'], pointData['image'])
            if not os.path.exists(imageFile):
                print('\t* missing "%s"' % imageFile)
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
            draw.ellipse((
                intX - halfway, intY - halfway,
                intX + halfway, intY + halfway),
                fill='#000000')

        # print the landmark name
        draw.text(
            (intX + MARKER_SIZE + 1, intY + 1),
            pointName,
            fill='#ffffff')
        draw.text(
            (intX + MARKER_SIZE, intY),
            pointName,
            fill='#000000')

    # write the image
    outputFilename = os.path.realpath(config['Map']['Filename'])
    canvas.save(outputFilename)
    print('Saved the map as %s' % outputFilename)

if __name__ == "__main__":
    """
    Entry point.

    """

    if handleCommandLine():
        if loadConfig():
            if configSanityChecks():
                if generateMapImage():
                    print('Done.')
