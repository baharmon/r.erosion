[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)

# r.erosion

*r.erosion* is a add-on module for modeling erosion in
[GRASS GIS](https://grass.osgeo.org/) with either
the Revised Universal Soil Loss Equation for Complex Terrain (RUSLE3D) model
or the Unit Stream Power Erosion Deposition (USPED) model.

## Installation
* Launch GRASS GIS
* Install using the GRASS Console / Command Line Interface (CLI) with
`g.extension  extension=r.erosion url=github.com/baharmon/r.erosion`
* Launch from the CLI with `r.erosion --ui`

## Documentation
* [Manual page](r.erosion.html)

## Sample dataset
Clone or download the
[sample dataset](https://github.com/baharmon/landscape_evolution_dataset)
with a time series of lidar-based digital elevation models
and orthoimagery
for a highly eroded subwatershed of Patterson Branch Creek, Fort Bragg, NC, USA.

## License
GNU General Public License Version 2
