#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MODULE:    r.erosion

AUTHOR(S): Brendan Harmon <brendan.harmon@gmail.com>

PURPOSE:   Erosion modeling in GRASS GIS

COPYRIGHT: (C) 2019 Brendan Harmon and the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

#%module
#% description: Erosion modeling
#% keyword: raster
#% keyword: terrain
#% keyword: erosion
#%end

#%option G_OPT_R_ELEV
#% key: elevation
#% required: yes
#% guisection: Basic
#%end

#%option
#% key: model
#% type: string
#% options: rusle,usped
#% description: RUSLE3D or USPED erosion model
#% descriptions:rusle;RUSLE 3D detachment limited model;usped;USPED transport limited model
#% label: Erosion model
#% required: yes
#% answer: rusle
#% guisection: Basic
#%end

#%option
#% key: r_factor_value
#% type: double
#% description: Erosivity factor constant
#% label: R factor constant
#% answer: 310.0
#% multiple: no
#% guisection: Input
#%end

#%option G_OPT_R_INPUT
#% key: r_factor
#% description: Erosivity factor map
#% label: R factor
#% required: no
#% guisection: Input
#%end

#%option
#% key: rain_intensity
#% type: integer
#% description: Rainfall intensity in mm/hr
#% multiple: no
#% required: no
#% guisection: Input
#%end

#%option
#% key: rain_duration
#% type: integer
#% description: Total duration of storm event in minutes
#% multiple: no
#% required: no
#% guisection: Input
#%end

#%option
#% key: k_factor_value
#% type: double
#% description: Soil erodibility constant
#% label: K factor constant
#% answer: 0.25
#% multiple: no
#% guisection: Input
#%end

#%option G_OPT_R_INPUT
#% key: k_factor
#% description: Soil erodibility factor
#% label: K factor
#% required: no
#% guisection: Input
#%end

#%option
#% key: c_factor_value
#% type: double
#% description: Land cover constant
#% label: C factor constant
#% answer: 0.1
#% multiple: no
#% guisection: Input
#%end

#%option G_OPT_R_INPUT
#% key: c_factor
#% description: Land cover factor
#% label: C factor
#% required: no
#% guisection: Input
#%end

#%option
#% key: m_coeff
#% type: double
#% description: Water flow exponent
#% label: Water flow exponent
#% answer: 1.5
#% required: yes
#% guisection: Input
#%end

#%option
#% key: n_coeff
#% type: double
#% description: Slope exponent
#% label: Slope exponent
#% answer: 1.2
#% required: yes
#% guisection: Input
#%end

#%option G_OPT_R_OUTPUT
#% key: erosion
#% answer: erosion
#% required: yes
#% description: Erosion map
#% guisection: Output
#%end

#%option G_OPT_R_OUTPUT
#% key: flow_accumulation
#% answer: flow_accumulation
#% required: yes
#% description: Flow accumulation map
#% guisection: Output
#%end

#%option G_OPT_R_OUTPUT
#% key: ls_factor
#% answer: ls_factor
#% description: Dimensionless topographic factor map
#% required: yes
#% guisection: Output
#%end


import sys
import atexit
import grass.script as gscript
from grass.exceptions import CalledModuleError

erosion_colors = """\
0% 100 0 100
-100 magenta
-10 red
-1 orange
-0.1 yellow
0 200 255 200
0.1 cyan
1 aqua
10 blue
100 0 0 100
100% black
"""

def main():
    options, flags = gscript.parser()
    elevation = options['elevation']
    model = options['model']
    erosion = options['erosion']
    flow_accumulation = options['flow_accumulation']
    ls_factor = options['ls_factor']
    rain_intensity = options['rain_intensity']
    rain_duration = options['rain_duration']
    r_factor = options['r_factor']
    k_factor = options['k_factor']
    c_factor = options['c_factor']
    r_factor_value = options['r_factor_value']
    k_factor_value = options['k_factor_value']
    c_factor_value = options['c_factor_value']
    m_coeff = options['m_coeff']
    n_coeff = options['n_coeff']

    # check for alternative input parameters
    if not rain_intensity:
        if not r_factor:
            r_factor = 'r_factor'
            gscript.run_command(
                'r.mapcalc',
                expression="r_factor = {r_factor_value}".format(**locals()),
                overwrite=True)
    else:
        # compute event-based erosivity (R) factor (MJ mm ha^-1 hr^-1 yr^-1)
        r_factor = event_based_r_factor(rain_intensity, rain_duration)
    if not c_factor:
        c_factor = 'c_factor'
        gscript.run_command(
            'r.mapcalc',
            expression="c_factor = {c_factor_value}".format(**locals()),
            overwrite=True)
    if not k_factor:
        k_factor = 'k_factor'
        gscript.run_command(
            'r.mapcalc',
            expression="k_factor = {k_factor_value}".format(**locals()),
            overwrite=True)

    # determine type of model and run
    if model == "rusle":
        rusle(elevation, erosion, flow_accumulation, r_factor,
              c_factor, k_factor, ls_factor, m_coeff, n_coeff)
    if model == "usped":
        usped(elevation, erosion, flow_accumulation, r_factor,
              c_factor, k_factor, ls_factor, m_coeff, n_coeff)
    atexit.register(cleanup)
    sys.exit(0)


def event_based_r_factor(rain_intensity, rain_duration):
    """compute event-based erosivity (R) factor (MJ mm ha^-1 hr^-1 yr^-1)"""

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
    * (rainfall duration (min)
    * (1 hr / 60 min))
    """
    gscript.run_command(
        'r.mapcalc',
        expression="{rain_volume}"
        "= {rain_intensity}"
        "*({rain_duration}"
        "/60.)".format(
            rain_volume=rain_volume,
            rain_intensity=rain_intensity,
            rain_duration=rain_duration),
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

    # multiply by rainfall duration in seconds (MJ mm ha^-1 hr^-1 s^-1)
    gscript.run_command(
        'r.mapcalc',
        expression="{r_factor}"
        "={erosivity}"
        "/({rain_duration}"
        "*60.)".format(
            r_factor=r_factor,
            erosivity=erosivity,
            rain_duration=rain_duration),
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
        "/({rain_duration}"
        "/525600.)".format(
            r_factor=r_factor,
            erosivity=erosivity,
            rain_duration=rain_duration),
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


def rusle(elevation, erosion, flow_accumulation, r_factor,
          c_factor, k_factor, ls_factor, m_coeff, n_coeff):
    """The RUSLE3D
    (Revised Universal Soil Loss Equation for Complex Terrain) model
    for detachment limited soil erosion regimes"""

    # assign variables
    slope = 'slope'
    grow_slope = 'grow_slope'
    flowacc = 'flowacc'
    sedflow = 'sedflow'

    # compute slope
    gscript.run_command(
        'r.slope.aspect',
        elevation=elevation,
        slope=slope,
        overwrite=True)

    # grow border to fix edge effects of moving window computations
    gscript.run_command(
        'r.grow.distance',
        input=slope,
        value=grow_slope,
        overwrite=True)
    gscript.run_command(
        'r.mapcalc',
        expression="{slope}={grow_slope}".format(
            slope=slope,
            grow_slope=grow_slope),
        overwrite=True)

    # compute flow accumulation
    gscript.run_command(
        'r.watershed',
        elevation=elevation,
        accumulation=flowacc,
        flags="a",
        overwrite=True)
    region = gscript.parse_command(
        'g.region', flags='g')
    res = region['nsres']
    gscript.run_command(
        'r.mapcalc',
        expression="{depth}"
        "=({flowacc}*{res})".format(
            depth=flow_accumulation,
            flowacc=flowacc,
            res=res),
        overwrite=True)

    # compute dimensionless topographic factor
    gscript.run_command(
        'r.mapcalc',
        expression="{ls_factor}"
        "=({m}+1.0)"
        "*(({flowacc}/22.1)^{m})"
        "*((sin({slope})/5.14)^{n})".format(
            ls_factor=ls_factor,
            m=m_coeff,
            flowacc=flow_accumulation,
            slope=slope,
            n=n_coeff),
        overwrite=True)

    # compute sediment flow
    """E = R * K * LS * C * P
    where
    E is average annual soil loss
    R is erosivity factor
    K is soil erodibility factor
    LS is a dimensionless topographic (length-slope) factor
    C is a dimensionless land cover factor
    P is a dimensionless prevention measures factor
    """
    gscript.run_command(
        'r.mapcalc',
        expression="{sedflow}"
        "={r_factor}"
        "*{k_factor}"
        "*{ls_factor}"
        "*{c_factor}".format(
            sedflow=sedflow,
            r_factor=r_factor,
            k_factor=k_factor,
            ls_factor=ls_factor,
            c_factor=c_factor),
        overwrite=True)

    # convert sediment flow from tons/ha to kg/ms
    gscript.run_command(
        'r.mapcalc',
        expression="{converted_sedflow}"
        "={sedflow}*{ton_to_kg}/{ha_to_m2}".format(
            converted_sedflow=erosion,
            sedflow=sedflow,
            ton_to_kg=1000.,
            ha_to_m2=10000.),
        overwrite=True)

    # # convert sediment flow from tons/ha/yr to kg/m^2s
    # gscript.run_command(
    #     'r.mapcalc',
    #     expression="{converted_sedflow}"
    #     "={sedflow}"
    #     "*{ton_to_kg}"
    #     "/{ha_to_m2}"
    #     "/{yr_to_s}".format(
    #         converted_sedflow=erosion,
    #         sedflow=sedflow,
    #         ton_to_kg=1000.,
    #         ha_to_m2=10000.,
    #         yr_to_s=31557600.),
    #     overwrite=True)

    # set color table
    gscript.write_command(
        'r.colors',
        map=erosion,
        rules='-',
        stdin=erosion_colors)

    # remove temporary maps
    gscript.run_command(
        'g.remove',
        type='raster',
        name=['slope',
              'grow_slope',
              'flowacc',
              'sedflow'],
        flags='f')


def usped(elevation, erosion, flow_accumulation, r_factor, c_factor, k_factor, ls_factor, m_coeff, n_coeff):
    """The USPED (Unit Stream Power Erosion Deposition) model
    for transport limited erosion regimes"""

    # assign variables
    slope = 'slope'
    aspect = 'aspect'
    flowacc = 'flowacc'
    qsx = 'qsx'
    qsxdx = 'qsxdx'
    qsy = 'qsy'
    qsydy = 'qsydy'
    grow_slope = 'grow_slope'
    grow_aspect = 'grow_aspect'
    grow_qsxdx = 'grow_qsxdx'
    grow_qsydy = 'grow_qsydy'
    sedflow = 'sedflow'
    sediment_flux = 'sediment_flux'

    # compute slope and aspect
    gscript.run_command(
        'r.slope.aspect',
        elevation=elevation,
        slope=slope,
        aspect=aspect,
        overwrite=True)

    # grow border to fix edge effects of moving window computations
    gscript.run_command(
        'r.grow.distance',
        input=slope,
        value=grow_slope,
        overwrite=True)
    gscript.run_command(
        'r.mapcalc',
        expression="{slope}={grow_slope}".format(
            slope=slope,
            grow_slope=grow_slope),
        overwrite=True)
    gscript.run_command(
        'r.grow.distance',
        input=aspect,
        value=grow_aspect,
        overwrite=True)
    gscript.run_command(
        'r.mapcalc',
        expression="{aspect}={grow_aspect}".format(
            aspect=aspect,
            grow_aspect=grow_aspect),
        overwrite=True)

    # compute flow accumulation
    gscript.run_command(
        'r.watershed',
        elevation=elevation,
        accumulation=flowacc,
        flags="a",
        overwrite=True)
    region = gscript.parse_command(
        'g.region', flags='g')
    res = region['nsres']
    gscript.run_command(
        'r.mapcalc',
        expression="{depth}"
        "=({flowacc}*{res})".format(
            depth=flow_accumulation,
            flowacc=flowacc,
            res=res),
        overwrite=True)
    # add depression parameter to r.watershed
    # derive from landcover class

    # compute dimensionless topographic factor
    gscript.run_command(
        'r.mapcalc',
        expression="{ls_factor}"
        "=({flowacc}^{m})*(sin({slope})^{n})".format(
            ls_factor=ls_factor,
            m=m_coeff,
            flowacc=flow_accumulation,
            slope=slope,
            n=n_coeff),
        overwrite=True)

    # compute sediment flow at sediment transport capacity
    """
    T = R * K * C * P * LST
    where
    T is sediment flow at transport capacity
    R is rainfall factor
    K is soil erodibility factor
    C is a dimensionless land cover factor
    P is a dimensionless prevention measures factor
    LST is the topographic component of sediment transport capacity
    of overland flow
    """
    gscript.run_command(
        'r.mapcalc',
        expression="{sedflow}"
        "={r_factor}"
        "*{k_factor}"
        "*{c_factor}"
        "*{ls_factor}".format(
            r_factor=r_factor,
            k_factor=k_factor,
            c_factor=c_factor,
            ls_factor=ls_factor,
            sedflow=sedflow),
        overwrite=True)

    # convert sediment flow from tons/ha to kg/ms
    gscript.run_command(
        'r.mapcalc',
        expression="{converted_sedflow}"
        "={sedflow}"
        "*{ton_to_kg}"
        "/{ha_to_m2}".format(
            converted_sedflow=sediment_flux,
            sedflow=sedflow,
            ton_to_kg=1000.,
            ha_to_m2=10000.),
        overwrite=True)

    # # convert sediment flow from tons/ha/yr to kg/m^2s
    # gscript.run_command(
    #     'r.mapcalc',
    #     expression="{converted_sedflow}"
    #     "={sedflow}"
    #     "*{ton_to_kg}"
    #     "/{ha_to_m2}"
    #     "/{yr_to_s}".format(
    #         converted_sedflow=sediment_flux,
    #         sedflow=sedflow,
    #         ton_to_kg=1000.,
    #         ha_to_m2=10000.,
    #         yr_to_s=31557600.),
    #     overwrite=True)

    # compute sediment flow rate in x direction (m^2/s)
    gscript.run_command(
        'r.mapcalc',
        expression="{qsx}={sedflow}*cos({aspect})".format(
            sedflow=sediment_flux,
            aspect=aspect, qsx=qsx),
        overwrite=True)

    # compute sediment flow rate in y direction (m^2/s)
    gscript.run_command(
        'r.mapcalc',
        expression="{qsy}={sedflow}*sin({aspect})".format(
            sedflow=sediment_flux,
            aspect=aspect,
            qsy=qsy),
        overwrite=True)

    # compute change in sediment flow in x direction
    # as partial derivative of sediment flow field
    gscript.run_command(
        'r.slope.aspect',
        elevation=qsx,
        dx=qsxdx,
        overwrite=True)

    # compute change in sediment flow in y direction
    # as partial derivative of sediment flow field
    gscript.run_command(
        'r.slope.aspect',
        elevation=qsy,
        dy=qsydy,
        overwrite=True)

    # grow border to fix edge effects of moving window computations
    gscript.run_command(
        'r.grow.distance',
        input=qsxdx,
        value=grow_qsxdx,
        overwrite=True)
    gscript.run_command(
        'r.mapcalc',
        expression="{qsxdx}={grow_qsxdx}".format(
            qsxdx=qsxdx,
            grow_qsxdx=grow_qsxdx),
        overwrite=True)
    gscript.run_command(
        'r.grow.distance',
        input=qsydy,
        value=grow_qsydy,
        overwrite=True)
    gscript.run_command(
        'r.mapcalc',
        expression="{qsydy}={grow_qsydy}".format(
            qsydy=qsydy,
            grow_qsydy=grow_qsydy),
        overwrite=True)

    # compute net erosion-deposition (kg/m^2s)
    # as divergence of sediment flow
    gscript.run_command(
        'r.mapcalc',
        expression="{erdep} = {qsxdx} + {qsydy}".format(
            erdep=erosion,
            qsxdx=qsxdx,
            qsydy=qsydy),
        overwrite=True)

    # set color table
    gscript.write_command(
        'r.colors',
        map=erosion,
        rules='-',
        stdin=erosion_colors)

    # remove temporary maps
    gscript.run_command(
        'g.remove',
        type='raster',
        name=['slope',
              'aspect',
              'flowacc',
              'qsx',
              'qsy',
              'qsxdx',
              'qsydy',
              'grow_slope',
              'grow_aspect',
              'grow_qsxdx',
              'grow_qsydy',
              'sedflow',
              'sediment_flux'],
        flags='f')


def cleanup():
    try:
        # remove temporary maps
        gscript.run_command(
            'g.remove',
            type='raster',
            name=['rain_volume',
                  'rain_energy',
                  'slope',
                  'aspect',
                  'flowacc',
                  'qsx',
                  'qsy',
                  'qsxdx',
                  'qsydy',
                  'grow_slope',
                  'grow_aspect',
                  'grow_qsxdx',
                  'grow_qsydy',
                  'sedflow',
                  'sediment_flux'],
            flags='f')

    except CalledModuleError:
        pass

if __name__ == '__main__':
    main()
