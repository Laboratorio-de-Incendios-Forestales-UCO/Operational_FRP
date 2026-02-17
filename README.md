# OPERATIONAL FRP
Get the Fire Radiative Power detected by the Flexible Combined Imager sensor onboard Meteosat Third Generation satellite in Near Real Time.
Get FRP detected by FCI onboard MTG in NRT.
   
## INFORMATION
FRP data is provided by EUMETSAT LSA SAF ("https://lsa-saf.eumetsat.int/en/data/products/fire-products/") in NRT (~15 min after acquisition).
These are accessible through a Gitlab repository ("https://datalsasaf.lsasvcs.ipma.pt/PRODUCTS/MTG/MTFRPPixel/") for which you need a free account.
Technical documentation is available in Nextcloud ("https://nextcloud.lsasvcs.ipma.pt/s/gb6joMQr4QHHyrC").

  Spatial resolution: 1 km
  Temporal resolution: 10 min
  Units: MW
    
### How to use it:

This example gets the FRP between two dates in UTC (2025-08-15T14:10:00Z and 2025-08-15T16:30:00Z) for a bbox defined by the specified coordinates and saves the results in a csv named "Example.csv". It will not show a map with the bbox (--no-show-map) nor a graph with the results (--no-show-graph). In case that the requests reach the present moment (i.e. the data is not available because has not been acquired yet by the satellite, or has not reached the repository) it will retry every 100 seconds (--waiting-time 100), instead of every 300 seconds (which is the default value). The beeper that warns when new data is available is deactivated (--beeper-off).

        run Launch_me_to_get_FRP.py --name Example --north 42.7 --south 41.7 --east -5.5 --west -8.0 --start 2025-08-15T14:10:00Z --end 2025-08-15T16:30:00Z --no-show-map --no-show-graph --waiting-time 100 --beeper-off

This example gets the FRP between two dates in UTC+02:00 (as in Spain in summer) (2025-08-15T14:10:00+02:00 and 2025-08-15T16:30:00+02:00) for a bbox defined by the specified coordinates and saves the results in a csv with a default name (bacause there is no --name). It will show a map with the bbox and a graph with the results (because these are the default options). In case that the requests reach the present moment, it will retry every 300 seconds and beep when the download is successful.

        run Launch_me_to_get_FRP.py --north 42.7 --south 41.7 --east -5.5 --west -8.0 --start 2025-08-15T14:10:00+02:00 --end 2025-08-15T16:30:00+02:00

This example gets the FRP non-stop from 2025-07-15T12:30:00+01:00 forward, as no end time (--end) is defined.

        run Launch_me_to_get_FRP.py --north 40.8 --south 40.7 --east -7.8 --west -7.95 --start 2025-07-15T12:30:00+01:00

# ⚠️ WARNINGS
    The directory must contain a ".credentials.ini" file with your credentials to log in into Gitlab.
    This file must follow the next structure:
        
      [gitlab]
      username = username@example.org
      password = MyPa5sWoRd

    This repository sets quotas and limitations for the downloads, and you could be temporally blocked after a few unsuccessful pushes (for instance, trying to retrieve FRP data that is not avaialable yet, with a too low --waiting-time). If you plan to use this tool for operational purposes, we strongly recommend you to have a backup user/password.
    
    Note that FRP from MTG is in its demonstration phase, and is thus not fully operational (See "https://lsa-saf.eumetsat.int/en/data/products/fire-products/").
    Note that the FRP product is available since 20250101. If your request starts prior to that date, you will get an error.
    Note that due to its spatial resolution, perimeters estimated through FRP from MTG are wider than real. Make sure that your bbox is not too narrow.
    Note that the spatial coverage of MTG includes Europe, Africa and South America.
    
    If you define a name that already exists, the results will be attached to the end of the previously generated file, corrupting it.
    
## Requirements:

  Python 3.12.9 with:
    - datetime
    - pathlib
    - shapely
    - argparse
    - configparser
    - contextily
    - csv
    - geopandas
    - matplotlib
    - os
    - pandas
    - pyproj
    - requests
    - time
    - sys
    -winsound

# LICENSE
© 2026 Laboratorio de Incendios Forestales (UCO) ["https://labif.es/"]
This repository is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).
Commercial use is not permitted.
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
