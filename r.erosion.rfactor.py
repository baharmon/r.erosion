#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import atexit
from math import exp
import grass.script as gscript
from grass.exceptions import CalledModuleError


def main():

    rain_intensity = 'rain_intensity'
    rain_intensity_value = 50.0
    rain_interval = 5.0
    gscript.run_command(
        'r.mapcalc',
        expression="rain_intensity = {rain_intensity_value}".format(**locals()),
        overwrite=True)

    r_factor = event_based_r_factor(rain_intensity, rain_interval)

    # print statistics
    univar = gscript.parse_command('r.univar',
        map=r_factor,
        separator='newline',
        flags='g')
    print univar

    # print mean kg/m2s

    atexit.register(cleanup)
    sys.exit(0)


def event_based_r_factor(rain_intensity, rain_interval):
    """compute event-based erosivity (R) factor (MJ mm ha^-1 hr^-1)"""
    # assign variables
    rain_energy = 'rain_energy'
    rain_volume = 'rain_volume'
    erosivity = 'erosivity'
    r_factor = 'r_factor'

    # derive rainfall energy (MJ ha^-1 mm^-1)
    gscript.run_command(
        'r.mapcalc',
        expression="{rain_energy}"
        "=0.29*(1.-(0.72*exp(-0.05*{rain_intensity})))".format(
            rain_energy=rain_energy,
            rain_intensity=rain_intensity),
        overwrite=True)

    # derive rainfall volume
    """
    rainfall volume (mm)
    = rainfall intensity (mm/hr)
    * (rainfall interval (min)
    * (1 hr / 60 min))
    """
    gscript.run_command(
        'r.mapcalc',
        expression="{rain_volume}"
        "= {rain_intensity}"
        "*({rain_interval}"
        "/60.)".format(
            rain_volume=rain_volume,
            rain_intensity=rain_intensity,
            rain_interval=rain_interval),
        overwrite=True)

    # derive event erosivity index (MJ mm ha^-1 hr^-1)
    gscript.run_command(
        'r.mapcalc',
        expression="{erosivity}"
        "=({rain_energy}"
        "*{rain_volume})"
        "*{rain_intensity}"
        "*1.".format(
            erosivity=erosivity,
            rain_energy=rain_energy,
            rain_volume=rain_volume,
            rain_intensity=rain_intensity),
        overwrite=True)

    # derive R factor (MJ mm ha^-1 hr^-1 yr^1)
    """
    R factor (MJ mm ha^-1 hr^-1 yr^1)
    = EI (MJ mm ha^-1 hr^-1)
    / (rainfall interval (min)
    * (1 yr / 525600 min))
    """
    gscript.run_command(
        'r.mapcalc',
        expression="{r_factor}"
        "={erosivity}"
        "/({rain_interval}"
        "/525600.)".format(
            r_factor=r_factor,
            erosivity=erosivity,
            rain_interval=rain_interval),
        overwrite=True)

    # remove temporary maps
    gscript.run_command(
        'g.remove',
        type='raster',
        name=['rain_energy',
            'rain_volume',
            'erosivity'],
        flags='f')

    return r_factor


def cleanup():
    try:
        # remove temporary maps
        gscript.run_command(
            'g.remove',
            type='raster',
            name=['rain_energy',
                'rain_volume',
                'erosivity',
                'rain_intensity'],
            flags='f')

    except CalledModuleError:
        pass

if __name__ == '__main__':
    main()
