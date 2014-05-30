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
TEXT_COLOR = u'#000000'
SHADOW_COLOR = u'#aaaaaa'
BACKGROUND_COLOR = u'#ffffff'


class MapFileError(Exception):
    """
    A specific exception for when we read through the config file and check if it has all the values we need.
    """
    message = u''

    def __init__(self, message):
        self.message = message


class MapConfig(object):
    """
    Wraps the json data into a neat object.
    """
    def __init__(self, json_file_name):
        """
        Reads a json config file and validates some of the required values.
        """
        self.json_file_name = json_file_name
        self.base_path = os.path.dirname(self.json_file_name)
        self.json_data = None
        self.messages = []
        with open(self.json_file_name) as json_file:
            self.json_data = json.loads(json_file.read())
        self.check_config()

    @property
    def map(self):
        return self.json_data['map']

    @property
    def title(self):
        return self.map[u'title']

    @property
    def filename(self):
        return self.map[u'filename']

    @property
    def scale(self):
        return self.map[u'scale']

    @property
    def background_color(self):
        return self.map.get(u'background_color', BACKGROUND_COLOR)

    @property
    def background_tile(self):
        return self.map.get(u'background_tile', None)

    @property
    def padding(self):
        return self.map[u'padding']

    @property
    def landmarks(self):
        return self.json_data[u'landmarks']

    @property
    def size(self):
        return self.map[u'size']

    @size.setter
    def size(self, value):
        self.map[u'size'] = value

    @property
    def landmark_font(self):
        return self.relative_path(self.map[u'landmark_font'].split(' ')[0])

    @property
    def landmark_font_size(self):
        return int(self.map[u'landmark_font'].split(' ')[1])

    def is_integer(self, test_value):
        """
        Tests if a value is a number.
        """
        try:
            int(test_value)
            return True
        except (ValueError):
            return False

    def relative_path(self, path):
        """
        Returns a path relative to the json data file.
        """
        return os.path.join(self.base_path, path)

    def check_config(self):
        """
        Do basic value validation.
        """
        for point_name, point_data in self.landmarks.iteritems():
            x, y = point_data[u'position']
            if not self.is_integer(x) or not self.is_integer(y):
                raise MapFileError(u'The point "%s" has a bad position value and cannot be processed' % point_name)

        self.messages.append(u'Calculating map size...')
        min_x, min_y, max_x, max_y = MIN_X, MIN_Y, MAX_X, MAX_Y
        for point_name, point_data in self.landmarks.iteritems():
            x, y = point_data[u'position'][0], point_data[u'position'][1]
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

        y_offset = min_y < 0 and abs(min_y) or 0

        self.messages.append(u'Normalizing coordinates...')
        for point_name, point_data in self.landmarks.iteritems():
            x, y = point_data[u'position'] #[0], point_data[u'position'][1]
            x = max_x - x
            y = y + y_offset
            self.landmarks[point_name][u'position'][0] = x
            self.landmarks[point_name][u'position'][1] = y

        # Test for an unreasonable map size
        map_width, map_height = (max_x - min_x, max_y + y_offset)
        self.messages.append(u'Map scales to %sx%s' % (map_width * self.scale, map_height * self.scale))

        if map_width < 1 or map_height < 1:
            raise MapFileError(u'The map size does not make sense, it cannot be created.')

        self.size = [map_width, map_height]


class MapMaker(object):
    """
    Make a map from a map config file.
    """
    config = None
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
        parser.add_argument('-m', '--map-file', metavar='FILENAME', required=True, help='The map definition (json)')
        parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Be verbose')
        self.options = parser.parse_args()
        if self.options.verbose:
            self.verbose = True

    def generate_image(self):
        """
        Creates a new image canvas and renders the map information to it.
        """
        # scale the map
        map_rescaled = (
            self.config.size[0] * self.config.scale,
            self.config.size[1] * self.config.scale
        )

        # add the padding to the image
        map_rescaled = (
            map_rescaled[0] + self.config.padding[LEFT] + self.config.padding[RIGHT],
            map_rescaled[1] + self.config.padding[TOP] + self.config.padding[BOTTOM]
        )

        # create the image and drawing objects
        canvas = Image.new(u'RGB', map_rescaled, color=self.config.background_color)
        draw = ImageDraw.Draw(canvas)

        # half the marker to center image pastes
        halfway = MARKER_SIZE / 2

        # tile a background image
        if self.config.background_tile:
            tile_image_file = self.config.relative_path(self.config.background_tile)
            tile_image = Image.open(tile_image_file)
            self.log(u'Found background tile image: %sx%s, tiling...' % tile_image.size, verbose=True)

            for tile_x in range(0, map_rescaled[0], tile_image.size[0]):
                for tile_y in range(0, map_rescaled[1], tile_image.size[1]):
                    canvas.paste(tile_image, (tile_x, tile_y, tile_x + tile_image.size[0], tile_y + tile_image.size[1]))

        landmark_font = ImageFont.truetype(self.config.landmark_font, self.config.landmark_font_size)

        self.log(u'Drawing landmarks...')
        for point_name, point_data in self.config.landmarks.iteritems():
            x, y = point_data[u'position']
            # scale up
            x *= self.config.scale
            y *= self.config.scale
            # apply padding
            x += self.config.padding[LEFT]
            y += self.config.padding[TOP]
            self.log(u'* %s' % point_name, verbose=True)

            # draw the landmark image
            if u'image' in point_data:
                image_file = self.config.relative_path(point_data[u'image'])
                if not os.path.exists(image_file):
                    self.log(u'  [Error] missing "%s"' % image_file)
                else:
                    # center the image on our point position
                    landmark_image = Image.open(image_file)
                    size_x, size_y = landmark_image.size
                    image_x = x - (size_x / 2)
                    image_y = y - (size_y / 2)
                    canvas.paste(landmark_image, (image_x, image_y), mask=landmark_image)
            else:
                draw.ellipse((x - halfway, y - halfway, x + halfway, y + halfway), fill=MARKER_COLOR)

            # print the landmark name
            draw.text((x + MARKER_SIZE + 1, y + 1), point_name, fill=SHADOW_COLOR, font=landmark_font)
            draw.text((x + MARKER_SIZE, y), point_name, fill=TEXT_COLOR, font=landmark_font)

        # write the image
        output_filename = self.config.relative_path(self.config.filename)
        canvas.save(output_filename)
        self.log(u'Saved the map as %s' % output_filename)

    def run(self):
        """
        Run the map maker
        """
        self.parse_arguments()
        try:
            self.config = MapConfig(self.options.map_file)
            self.generate_image()
            self.log(u'Done')
        except MapFileError as e:
            self.log(e.message)


if __name__ == u'__main__':
    #c = MapConfig('maps/example-map/minemap.json')
    #print(c.scale)
    map_maker = MapMaker()
    map_maker.run()
