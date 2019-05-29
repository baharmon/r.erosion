#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AUTHOR:    Brendan Harmon <brendan.harmon@gmail.com>

PURPOSE:   Rendering 2D and 3D maps of landscape evolution model sample data

COPYRIGHT: (C) 2017 Brendan Harmon

LICENSE:   This program is free software under the GNU General Public
           License (>=v2).
"""

import os
import sys
import atexit
import grass.script as gscript
from grass.exceptions import CalledModuleError

# set graphics driver
driver = "cairo"

# temporary region
gscript.use_temp_region()

# set environment
env = gscript.gisenv()

overwrite = True
env['GRASS_OVERWRITE'] = overwrite
env['GRASS_VERBOSE'] = False
env['GRASS_MESSAGE_FORMAT'] = 'standard'
gisdbase = env['GISDBASE']
location = env['LOCATION_NAME']
mapset = env['MAPSET']
res=1

# set 2D rendering parameters
legend_coord = (2, 32, 2, 4)
border = 400
width = 1600
height = 1600
font = 'Lato-Regular'
fontsize = 26
vector_width = 3

# create rendering directory
render = os.path.join(gisdbase, 'images', 'erosion')
if not os.path.exists(render):
    os.makedirs(render)

# set region
gscript.run_command('g.region', region='region', res=res, align='elevation_2012')

# set mask
gscript.run_command('r.mask', vector='watershed')

# render sediment flow
gscript.run_command('d.mon',
    start=driver,
    width=width,
    height=height,
    output=os.path.join(render, 'sediment_flow_2012.png'),
    overwrite=overwrite)
gscript.run_command('d.shade',
    shade='relief_2012',
    color='erosion',
    brighten=0)
gscript.run_command('d.legend',
    raster='erosion',
    font=font,
    fontsize=fontsize,
    at=legend_coord)
gscript.run_command('d.mon', stop=driver)

# remove mask
gscript.run_command('r.mask', flags='r')

# create rendering directory
render = os.path.join(gisdbase, 'images', 'erosion_detail')
if not os.path.exists(render):
    os.makedirs(render)

# set region
gscript.run_command('g.region', region='subregion', res=res, align='elevation_2012')

# set mask
gscript.run_command('r.mask', vector='subwatershed')

# render sediment flow
gscript.run_command('d.mon',
    start=driver,
    width=width,
    height=height,
    output=os.path.join(render, 'sediment_flow_2012.png'),
    overwrite=overwrite)
gscript.run_command('d.shade',
    shade='relief_2012',
    color='erosion',
    brighten=0)
gscript.run_command('d.legend',
    raster='erosion',
    font=font,
    fontsize=fontsize,
    at=legend_coord)
gscript.run_command('d.mon', stop=driver)

# remove mask
gscript.run_command('r.mask', flags='r')
