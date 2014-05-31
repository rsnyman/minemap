# MineMap

Minemap is a tool that generates an top-down aerial map from values fed in through a config file. This tool started as a way to map out minetest worlds by recording notable positions and giving them clever names.

# Requirements

* Python 2.7
* Python PIL

# Installing

_Steps for non git users._

    # download latest version and unzip to the "minemap" directory and symlink minemap into your path
    wget -O minemap.zip https://github.com/wesleywerner/minemap/archive/master.zip && \
    unzip minemap.zip && \
    mv minemap-master minemap && cd minemap && \
    sh link.sh

# Map definition

The map is defined as a json formatted file:

    {
        "map": {
            "title": "Hello World",
            "filename": "hello-world.png",
            "scale": 2,
            "background_color": "#dddddd",
            "background_tile": "tile.png",
            "landmark_font": "font.ttf 24",
            "padding": [100, 100, 100, 100]
        },
        "landmarks": {
            "Water Falls": {
                "position": [-295, 274]
            },
            "Wheat Farm": {
                "position": [-355, 261]
            },
            "Swimming Pond": {
                "position": [-300, 224]
            },
            "Brick house": {
                "position": [-316, 78],
                "image": "house.png"
            },
            "Castle": {
                "position": [-311, 50],
                "image": "house.png"
            },
        }
    }

 * the map section sets:
    * title: Your map title, currently not used.
    * filename: Save the map image as this, in the same directory as the json definition.
    * scale: Size the map by this factor, useful when points are very near another and their titles overlap.
    * background_color and background_tile (optional): Tile an image as the background, or use a color if no image set or found.
    * landmark_font (optional): Use a true type font for the landmark titles, the font size is given as the second value.
    * padding (optional): Pad the map by [Left, Top, Right, Bottom] pixels, useful to avoid landmark titles from being cropped.
 * the landmarks section lists each by name:
    * position: The coordinate as [x, y].
    * image (optional): Use an image instead of drawing a dot marker.

# Supported image formats

The prominent formats are `png` and `jpg`, with `pdf` and `gif` also supported. For the complete list see http://www.effbot.org/imagingbook/formats.htm

# Suggested map structure

When you start loading in images I recommend you put each map in it's own directory, to keep things tidy:

     ./maps
     |
     hello-world-map
     |  |
     |  hello-world.json
     |  waterfall.png
     |  well.png
     |  hill.png
     |  myfont.ttf
     |
     online-world-map
     |  |
     |  online-world.json
     |  river.png
     |  castle.png

# Generating the map image

    python minemap.py -m hello-world.json

Also see:

    python minemap.py --help

# License

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
