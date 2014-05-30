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
import json
from argparse import ArgumentParser

from PIL import Image, ImageDraw, ImageFont

# The description of this script
DESCRIPTION = u'Minemap is a tool that generates an top-down aerial map from values fed in through a config file.'
# The radius of the dot markers placed for landmarks
MARKER_SIZE = 5
# Maximum map range
MIN_X, MIN_Y, MAX_X, MAX_Y = 30927, 30927, -30912, -30912
# padding indices
LEFT, TOP, RIGHT, BOTTOM = 0, 1, 2, 3
# Map colours
MARKER_COLOR = u'#000000'
TEXT_COLOR = u'#ffffff'
SHADOW_COLOR = u'#000000'
BACKGROUND_COLOR = u'#ffffff'


class MapFileError(Exception):
    """
    A specific exception for when we read through the config file and check if it has all the values we need.
    """
    message = u''

    def __init__(self, message):
        self.message = message


class MapMaker(object):
    """
    Make a map from a map config file.
    """
    map = None
    json_file_name = u''
    json_file_path = u''
    options = None
    verbose = False

    def log(self, text, verbose=False):
        """
        Log the output.

        :param text: The text to output
        :param verbose: If verbose is True, this should only be output if self.verbose is also True.
        """
        if not verbose or (verbose and self.verbose):
            print(text)

    def parse_arguments(self):
        """
        Handles command line arguments, printing help where necessary
        and storing values in our Vars object.
        """
        parser = ArgumentParser(description=DESCRIPTION)
        parser.add_argument('-m', '--map-file', metavar='FILENAME', required=True, help='The map file')
        parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Be verbose')
        self.options = parser.parse_args()
        if self.options.verbose:
            self.verbose = True

    def setup_map_file(self):
        """
        Set up the configuration file and load it into a config object.
        """
        self.json_file_name = os.path.abspath(self.options.map_file)
        self.json_file_path = os.path.dirname(self.json_file_name)
        try:
            with open(self.json_file_name) as json_file:
                self.map = json.loads(json_file.read())
            return True
        except (ValueError, TypeError):
            return False

    def check_config(self):
        """
        Process the config values and performs a couple of sanity checks
        to make sure we have everything we need, and that the values
        are within a sane range.

        """
        # Test for a map section
        if u'map' not in self.map:
            raise MapFileError(u'Map file is missing a [map] section')

        # Test for an output Filename
        if u'filename' not in self.map[u'map']:
            raise MapFileError(u'Config is missing a [map]:[filename] entry.')

        # Test for missing Landmarks
        if u'landmarks' not in self.map:
            raise MapFileError(u'Config is missing a [landmarks] section')

        if not len(self.map[u'landmarks']):
            raise MapFileError(u'There are no landmarks defined in the [landmarks] section of the config')

        for point_name, point_data in self.map[u'landmarks'].iteritems():
            try:
                # X
                int(point_data[u'position'][0])
                # Y
                int(point_data[u'position'][1])
            except ValueError:
                raise MapFileError(u'The point "%s" has a bad position value and cannot be processed' % point_name)

    def parse_map(self):
        """
        Parse the map file and set up various values.
        """
        # check for map scale value
        if u'Scale' in self.map[u'map']:
            if not isinstance(self.map[u'map'][u'scale'], int):
                try:
                    self.map[u'map'][u'scale'] = int(self.map[u'map'][u'scale'])
                except (ValueError, TypeError):
                    self.log(u'Invalid map scale. Assuming the default.', verbose=True)
                    self.map[u'map'][u'scale'] = 1
        else:
            self.log(u'Invalid map scale. Assuming the default.', verbose=True)
            self.map[u'map'][u'scale'] = 1
        self.log(u'The map scale is %s' % self.map[u'map'][u'scale'])

        # Test for map padding
        if u'padding' in self.map[u'map'] and len(self.map[u'map'][u'padding']) == 4:
            for padding_index in range(0, 3):
                try:
                    self.map[u'map'][u'padding'][padding_index] = int(self.map[u'map'][u'padding'][padding_index])
                except ValueError:
                    self.log(u'The map padding has an invalid value. Ignoring.', verbose=True)
                    self.map[u'map'][u'padding'][padding_index] = 0
        else:
            self.log(u'The map padding has an invalid value. Ignoring.', verbose=True)
            self.map[u'map'][u'padding'] = [0, 0, 0, 0]
        self.log(u'The map padding is %s' % self.map[u'map'][u'padding'])

        self.log(u'Calculating map size...')
        min_x, min_y, max_x, max_y = MIN_X, MIN_Y, MAX_X, MAX_Y
        for point_name, point_data in self.map[u'landmarks'].iteritems():
            x, y = point_data[u'position'][0], point_data[u'position'][1]
            # remember the largest and smallest values
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

        y_offset = min_y < 0 and abs(min_y) or 0

        self.log(u'Normalizing coordinates...')
        for point_name, point_data in self.map[u'landmarks'].iteritems():
            x, y = point_data[u'position'][0], point_data[u'position'][1]
            x = max_x - x
            y = y + y_offset
            self.map[u'landmarks'][point_name][u'position'][0] = x
            self.map[u'landmarks'][point_name][u'position'][1] = y

        # Test for an unreasonable map size
        map_width, map_height = (max_x - min_x, max_y + y_offset)
        self.log(u'Map size is %sx%s, which scales to %sx%s' % (map_width, map_height,
                                                                map_width * self.map[u'map'][u'scale'],
                                                                map_height * self.map[u'map'][u'scale']),
                 verbose=True)

        if map_width < 1 or map_height < 1:
            raise MapFileError(u'The map size does not make sense, it cannot be created')

        if map_width > 2000 or map_height > 2000:
            reply = raw_input(u'This is a large map, continue? [Y/n]: ')
            if reply.lower()[0] in [u'n', u'f', u'0']:
                return False
        self.map[u'size'] = [map_width, map_height]
        return True

    def generate_image(self):
        """
        Creates a new image canvas and renders the map information to it.
        """
        # scale the map
        map_rescaled = (
            self.map[u'size'][0] * self.map[u'map'][u'scale'],
            self.map[u'size'][1] * self.map[u'map'][u'scale']
        )

        # add the padding to the image
        map_rescaled = (
            map_rescaled[0] + self.map[u'map'][u'padding'][LEFT] + self.map[u'map'][u'padding'][RIGHT],
            map_rescaled[1] + self.map[u'map'][u'padding'][TOP] + self.map[u'map'][u'padding'][BOTTOM]
        )

        # get or use the default canvas color
        canvas_color = self.map[u'map'].get(u'backcolor', BACKGROUND_COLOR)

        # create the image and drawing objects
        canvas = Image.new(u'RGB', map_rescaled, color=canvas_color)
        draw = ImageDraw.Draw(canvas)

        # half the marker to center image pastes
        halfway = MARKER_SIZE / 2

        # tile a background image
        if u'background_tile' in self.map[u'map']:
            tile_image_file = os.path.join(self.json_file_path, self.map[u'map'][u'background_tile'])
            tile_image = Image.open(tile_image_file)
            self.log(u'Found background tile image: %sx%s, tiling...' % tile_image.size, verbose=True)

            for tile_x in range(0, map_rescaled[0], tile_image.size[0]):
                for tile_y in range(0, map_rescaled[1], tile_image.size[1]):
                    canvas.paste(tile_image, (tile_x, tile_y, tile_x + tile_image.size[0], tile_y + tile_image.size[1]))

        # Process each point
        self.log(u'Drawing landmarks...')
        for point_name, point_data in self.map[u'landmarks'].iteritems():
            # Set up point data
            x = self.map[u'map'][u'padding'][LEFT] + point_data[u'position'][0] * self.map[u'map'][u'scale']
            y = self.map[u'map'][u'padding'][TOP] + point_data[u'position'][1] * self.map[u'map'][u'scale']
            self.log(u'* %s' % point_name, verbose=True)

            # draw the landmark image, or the marker dot if no image
            if u'image' in point_data:
                image_file = os.path.join(self.json_file_path, point_data[u'image'])
                if not os.path.exists(image_file):
                    self.log(u'  [Error] missing "%s"' % image_file)
                else:
                    # Centre the image on our point position
                    landmark_image = Image.open(image_file)
                    size_x, size_y = landmark_image.size
                    image_x = x - (size_x / 2)
                    image_y = y - (size_y / 2)
                    canvas.paste(landmark_image, (image_x, image_y), mask=landmark_image)
            else:
                draw.ellipse((x - halfway, y - halfway, x + halfway, y + halfway), fill=MARKER_COLOR)

            # print the landmark name
            draw.text((x + MARKER_SIZE + 1, y + 1), point_name, fill=TEXT_COLOR)
            draw.text((x + MARKER_SIZE, y), point_name, fill=SHADOW_COLOR)

        # write the image
        output_filename = os.path.realpath(self.map[u'map'][u'filename'])
        canvas.save(output_filename)
        self.log(u'Saved the map as %s' % output_filename)

    def run(self):
        """
        Run the map maker
        """
        self.parse_arguments()
        carry_on = self.setup_map_file()
        if not carry_on:
            return
        try:
            self.check_config()
            carry_on = self.parse_map()
            if not carry_on:
                return
            self.generate_image()
            self.log(u'Done')
        except MapFileError as e:
            self.log(e.message)


if __name__ == u'__main__':
    map_maker = MapMaker()
    map_maker.run()
