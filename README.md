# Minemap

Minemap is a tool that generates an top-down aerial map from values fed in through a config file. This tool started as a way to map out minetest worlds by recording notable positions and giving them clever names.

# Requirements

* Python 2.7
* Python PIL

# Config file format

The config file simply describes a list of (x, y) positions, each has a name of the landmark at that position, and a couple of other optional attributes that tweak the drawing style of the point in question.

An example config file reads:

    [ Map ]
    Title = "Hello, World."

    [ Points ]

        [[ The Waterfall ]]
        position = 10, 10
        
        [[ The Well ]]
        position = 60, 30
        
        [[ The Lighthouse ]]
        position = 10, 100

Map title is quoted for best results, and a list of points on the map are defined under the Points section. Section names do not require spacing between the brackets, but are encouraged for readability. The number of brackets increase for each level.

The above example is a fully functional configuration for generating the map, albeit a bland one at that. For a full listing of all available map and point settings see the minemap.sample.conf file.

# Generating the map

    python minemap.py <config>

Will create the map image and save it in the same location as the config with the default naming scheme. More on the output name format in the minemap.sample.conf file.

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
