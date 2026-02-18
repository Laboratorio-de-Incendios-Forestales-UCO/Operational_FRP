# -*- coding: utf-8 -*-
print(
"""
TRACKING:
    Product developped by LABIF-UCO ("https://labif.es/").
    Version 20260217b (last modified by Juanan).
    
OBJECTIVE:
    Get the Fire Radiative Power detected by the Flexible Combined Imager sensor onboard Meteosat Third Generation satellite in Near Real Time.
    Get FRP detected by FCI onboard MTG in NRT.
    
INFORMATION:
    FRP data is provided by EUMETSAT LSA SAF ("https://lsa-saf.eumetsat.int/en/data/products/fire-products/") in NRT (~15 min after acquisition).
    These are accessible through a Gitlab repository ("https://datalsasaf.lsasvcs.ipma.pt/PRODUCTS/MTG/MTFRPPixel/") for which you need a free account.
    Technical documentation is available in Nextcloud ("https://nextcloud.lsasvcs.ipma.pt/s/gb6joMQr4QHHyrC").
    Spatial resolution: 1 km
    Temporal resolution: 10 min
    Units: MW
    

EXAMPLES:
    
    run Launch_me_to_get_FRP.py --name Example --north 42.7 --south 41.7 --east -5.5 --west -8.0 --start 2025-08-15T14:10:00Z --end 2025-08-15T16:30:00Z --no-show-map --no-show-graph --waiting-time 100 --beeper-off
        This example gets the FRP between two dates in UTC (2025-08-15T14:10:00Z and 2025-08-15T16:30:00Z) for a bbox defined by the specified coordinates and saves the results in a csv named "Example.csv". It will not show a map with the bbox (--no-show-map) nor a graph with the results (--no-show-graph). In case that the requests reach the present moment (i.e. the data is not available because has not been acquired yet by the satellite, or has not reached the repository) it will retry every 100 seconds (--waiting-time 100), instead of every 300 seconds (which is the default value). The beeper that warns when new data is available is deactivated (--beeper-off).

    run Launch_me_to_get_FRP.py --north 42.7 --south 41.7 --east -5.5 --west -8.0 --start 2025-08-15T14:10:00+02:00 --end 2025-08-15T16:30:00+02:00
        This example gets the FRP between two dates in UTC+02:00 (as in Spain in summer) (2025-08-15T14:10:00+02:00 and 2025-08-15T16:30:00+02:00) for a bbox defined by the specified coordinates and saves the results in a csv with a default name (bacause there is no --name). It will show a map with the bbox and a graph with the results (because these are the default options). In case that the requests reach the present moment, it will retry every 300 seconds and beep when the download is successful. 

    run Launch_me_to_get_FRP.py --north 40.8 --south 40.7 --east -7.8 --west -7.95 --start 2025-07-15T12:30:00+01:00
        This example gets the FRP non-stop from 2025-07-15T12:30:00+01:00 forward, as no end time (--end) is defined.
        
WARNINGS:
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
"""
)
print("RUN THE SCRIPT:")
print()

# %% IMPORT THE LIBRARIES
print("         Import the libraries")

from datetime import datetime as datetime
from datetime import timedelta as timedelta
from datetime import timezone as timezone
from IPython.display import display as display
from IPython.display import clear_output as clear_output
from pathlib import Path as Path
from shapely.geometry import box as box

import argparse as argparse
import configparser as configparser
import contextily as ctx
import csv as csv
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os as os
import pandas as pd
import pyproj as pyproj
import requests as requests
import time as time
import sys as sys
import winsound as winsound

pyproj.datadir.set_data_dir(os.path.join(sys.prefix, 'share', 'proj'))


# %% DEFINE THE ANCILLARY FUNCTIONS

def f_valid_datetime_tz(dt_str):
    # Get the datetime from the parser (as a string) and transform it into a valid datetime
    print(f"         Running: {f_valid_datetime_tz.__name__}()")

    try:

        # To support Zulu hour "Z"
        if dt_str.endswith("Z"):
            dt_str = dt_str.replace("Z", "+00:00")

        dt = datetime.fromisoformat(dt_str)
        
        # Raise error in case the hour do not include time zone       
        if dt.tzinfo is None:
            raise argparse.ArgumentTypeError(
                "Datetime must include time zone (e.g.: +01:00 or Z)"
            )           
        
        # Transform into UTC
        dt = dt.astimezone(timezone.utc)
        
        return dt

    except ValueError:
        raise argparse.ArgumentTypeError(
            "Invalid format. Use ISO 8601: "
            "YYYY-MM-DDTHH:MM:SS+HH:MM or Z"
        )

        
def f_parser():
    # Get the arguments from the console
    print(f"         Running: {f_parser.__name__}()")
    
    parser = argparse.ArgumentParser(
        description="Get the inputs from the console: name, coordinates and datetimes."
    )

    parser.add_argument(
        "--name",
        type=str,
        required=False,
        default=str(datetime.now().strftime("%Y%m%d%H%M%S")),
        help="Filename (e.g. fire_379)"
    ) # If no name is defined, it assigns the current datetime

    parser.add_argument(
        "--north",
        type=float,
        required=True,
        help="North latitude in decimal degrees (float)"
    )

    parser.add_argument(
        "--south",
        type=float,
        required=True,
        help="South latitude in decimal degrees (float)"
    )

    parser.add_argument(
        "--east",
        type=float,
        required=True,
        help="East longitude in decimal degrees (float)"
    )

    parser.add_argument(
        "--west",
        type=float,
        required=True,
        help="West longitude in decimal degrees (float)"
    )

    parser.add_argument(
        "--start",
        type=f_valid_datetime_tz,
        required=True,
        help="Start datetime in ISO 8601 format with time zone (e.g.: 2024-01-01T14:30:00+02:00)"
    )
    
    parser.add_argument(
        "--end",
        type=f_valid_datetime_tz,
        required=False,
        default=None,
        help="End datetime in ISO 8601 format with time zone (e.g.: 2024-01-01T16:30:00+02:00)"
    )
    
    parser.add_argument(
        "--waiting-time",
        dest = "waiting_time",
        type=int,
        required=False,
        default=300,
        help="Seconds until the next push"
    )
    
    # Flag to activate show-map (optional)
    parser.add_argument(
        "--show-map",
        dest="show_map",
        action="store_true",
        help="Show a map with the bbox (default: True)"
    )
    
    # Flag to deactivate show-map (optional)
    parser.add_argument(
        "--no-show-map",
        dest="show_map",
        action="store_false",
        help="Do not show a map with the bbox (default: True)"
    )
    
    # Default value for show-map
    parser.set_defaults(show_map=True)
    
    # Flag to activate show-graph (optional)
    parser.add_argument(
        "--show-graph",
        dest="show_graph",
        action="store_true",
        help="Show a graph with the results (default: True)"
    )
    
    # Flag to deactivate show-graph (optional)
    parser.add_argument(
        "--no-show-graph",
        dest="show_graph",
        action="store_false",
        help="Do not show a graph with the results (default: True)"
    )
    
    # Default value for show-map
    parser.set_defaults(show_graph=True)

    # Beeper (optional)
    parser.add_argument(
        "--beeper-on",
        dest="beeper",
        action="store_true",
        help="Switch on the beeper (default: True)"
    )
    
    # Flag to deactivate show-graph (optional)
    parser.add_argument(
        "--beeper-off",
        dest="beeper",
        action="store_false",
        help="Switch off the beeper (default: True)"
    )
    
    # Default value for show-map
    parser.set_defaults(beeper=True)
    
    args = parser.parse_args()
    return args


def f_check_coordinates(lonlat_bbox):
    print(f"         Running: {f_check_coordinates.__name__}()")
    
    W, S, E, N = lonlat_bbox
    
    if W>E:
        raise ValueError("West cannot be easterlier than East :S")

    if S>N:
        raise ValueError("North cannot be southerlier than South :S")


def f_check_start_datetime(start_time):
    # Check the start time
    print(f"         Running: {f_check_start_datetime.__name__}()")
            
    if start_time >= datetime.now(tz=timezone.utc):
        raise ValueError("Take it easy, McFly. Ignition cannot be in the future")
    
    if (start_time.minute not in {0, 10, 20, 30, 40, 50}
        or start_time.second != 0
        or start_time.microsecond != 0):
          
        print("          - WARNING: MTG captures data every 10 min. Start time modified:")
        print(f"              FROM {start_time.isoformat()}")
        new_minute_value = start_time.minute//10*10
        start_time = start_time.replace(minute=new_minute_value, second=0, microsecond=0)
        print(f"              TO {start_time.isoformat()}")

    return start_time


def f_show_the_bbox(bbox):
    # Show the area of interest (aka bbox)
    print(f"         Running: {f_show_the_bbox.__name__}()")
    
    try:            
               
        # Create the geometry for the bbox
        geom = box(*bbox)
        gdf = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")
        
        # Convert to metric projection (Web Mercator) to use with contextily
        gdf_web = gdf.to_crs(epsg=3857)
        
        # Graphicate
        ax = gdf_web.plot(edgecolor='red', facecolor='none', linewidth=2, figsize=(8, 8))
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
        plt.title("Bounding Box")
        plt.show()
        
    except Exception as e:
        print(f"         Error: {e}")
        # Abort in case of critical error
        sys.exit(1)


def f_define_the_directories():
    """
    Returns
    -------
    Directories : dict
        Dictionary with the routes to the defined directories.
    """
    print(f"         Running: {f_define_the_directories.__name__}()")
    
    Directory_general = Path(__file__).resolve().parent.parent

    Directories = {
        "General": Directory_general,
        "Ancillary": Directory_general / "Ancillary",
        "Inputs": Directory_general / "Inputs",
        "Outputs": Directory_general / "Outputs",
        "Raw_data": Directory_general / "Outputs" / "Raw_data",
        "Scripts": Directory_general / "Scripts",
    }  # Add new lines if nedded
    
    # Make sure that these directories exist. If not, create them.
    for directory_name, directory_path in Directories.items():
        if not directory_path.exists():
            directory_path.mkdir(parents=True)
            print(f"          - Created directory: {directory_name} → {directory_path}")

    return Directories


def f_define_the_filename(datetime):
    # Define the web route to the file (link_to_filename), and its name (filename), following the next convention:
    # https://datalsasafwd.lsasvcs.ipma.pt/PRODUCTS/<satellite>/<product>/<format>/<year>/<month>/<day>/filename
    # filename: LSA-509_MTG_MTFRPPIXEL-ListProduct_MTG-FD_YYYYMMDDHHMM.csv.gz
    print(f"         Running: {f_define_the_filename.__name__}()") 
    
    Anc_web = "https://datalsasaf.lsasvcs.ipma.pt"
    Anc_section = "PRODUCTS"
    Anc_satellite = "MTG"
    Anc_product = "MTFRPPixel"
    Anc_format = "NATIVE"
    Anc_YYYY = str(datetime.year).zfill(4)
    Anc_MM = str(datetime.month).zfill(2)
    Anc_DD = str(datetime.day).zfill(2)
    Anc_HH = str(datetime.hour).zfill(2)
    Anc_mm = str(datetime.minute).zfill(2)

    webRoute = os.path.join(Anc_web,
                            Anc_section,
                            Anc_satellite,
                            Anc_product,
                            Anc_format,
                            Anc_YYYY,
                            Anc_MM,
                            Anc_DD).replace("\\", "/")

    filename = "LSA-509_MTG_MTFRPPIXEL-ListProduct_MTG-FD_{}{}{}{}{}.csv.gz".format(
        Anc_YYYY, Anc_MM, Anc_DD, Anc_HH, Anc_mm
    )

    link_to_download_file = os.path.join(webRoute,filename).replace("\\", "/")
   
    return link_to_download_file, filename

# def f_get_password(user, password):
    
#         # Load env variables
#         dotenv.load_dotenv()  
        
#         # Read env variables
#         _user = os.getenv(user)
#         _password = os.getenv(password)
        
#         if not _user or not _password:
#             raise RuntimeError("User and/or password cannot be found")
        
#         return _user, _password


def f_get_credentials(filename=".credentials.ini"):
    # Get credentials from an ini file located in the same directory than the script
    print(f"         Running: {f_get_credentials.__name__}()")
    
    config = configparser.ConfigParser()

    cred_path = Path(__file__).parent / filename

    if not cred_path.exists():
        raise FileNotFoundError(
            f"           - Credentials file not found: {cred_path}"
        )

    config.read(cred_path)

    try:
        _username = config["gitlab"]["username"]
        _password = config["gitlab"]["password"]
        
    except KeyError as e:
        raise KeyError(
            "           - Missing [cdse] section or keys in credentials file"
        ) from e
    
    return _username, _password
    
def f_scheduler(link_to_download_file, filename, directories, beeper, waiting_time):
    # Wait and launch back f_call_to_lsasaf
    print(f"         Running: {f_scheduler.__name__}()")
    
    print(f"          - Waiting {waiting_time} seconds")
    print(f"          - New try at {datetime.now()+timedelta(seconds=waiting_time)}")

    time.sleep(waiting_time)

    f_call_to_lsasaf(link_to_download_file, filename, directories, beeper, waiting_time)
    
    
def f_call_to_lsasaf(link_to_download_file, filename, directories, beeper, waiting_time):
    # Request the FRP data to its repository in gitlab and save it
    print(f"         Running: {f_call_to_lsasaf.__name__}()") 

    # Define the route to download the file (including its name and format)
    Route_to_download_file = os.path.join(directories["Raw_data"],filename)
        
    # Check if the file already exists in the directory. Note that the product
    # that this section downloads is the whole view from the satellite, not just 
    # the area within the bbox. If it already exists, return to the main function.
    if os.path.isfile(Route_to_download_file):
        print(f"          - {filename} already exists in {directories["Raw_data"]}. Not requesting it.")
        return       
    
    # Get user and password to access gitlab repository
    _user, _password = f_get_credentials()  
    
    # Request the file 
    req = requests.get(link_to_download_file, auth=(_user, _password))
    
    # If the file exists in the repository
    if req.status_code==200: # 200 is the code for "everything went OK"
        if beeper: # If beeper is on
            winsound.Beep(1000, 500)  # BEEEP freq=1000 Hz, duration=500 ms
            
        with open(Route_to_download_file, "wb") as f:
            f.write(req.content) # Write it in the appropriate directory
    
    # If the file doesn't exist yet (is not yet available at the repository)        
    elif req.status_code==404:
        print("          - Timestep not available yet")
        # Launch the sceduler
        f_scheduler(link_to_download_file, filename, directories, beeper, waiting_time) # Go into the Scheduler function, which will launch f_call_to_lsasaf back in [waiting_time] seconds
        
    else: # If the error is neither 200 nor 404
        raise RuntimeError(f"          - Error for {link_to_download_file}: code {req.status_code}")
    

def f_get_frp(route_to_the_file, name_of_the_file, lonlat_bbox):
    # Open the compressed csv that contains the FRP data for the full disk and extract the data from inside the bbox
    print(f"         Running: {f_get_frp.__name__}()")
    
    # Open the file with the FRP data
    filename = os.path.join(route_to_the_file,name_of_the_file)
    frp = pd.read_csv(filename, compression='gzip')
    
    # Extract the frp data inside the bbox
    W, S, E, N = lonlat_bbox
    filtered_frp = frp[
    (frp['LONGITUDE'] >= W) & (frp['LONGITUDE'] <= E) &
    (frp['LATITUDE']  >= S) & (frp['LATITUDE']  <= N)
        ]   # Filter the data that fits with the bbox
    
    number_of_pixels = len(filtered_frp) # Count the number of rows, that equals the number of excited pixels within the bbox
    sum_frp = filtered_frp['FRP'].sum() # Sum the FRP (in MW) detected in all the pixels
    
    print(f"          - Active wildfire in {number_of_pixels} pixels")
    print(f"          - Total FRP: {sum_frp:.2f} MW")
    
    return sum_frp

    
def f_save_frp(route_to_save_file, name_of_the_file, acquisition_time, frp):
    # Save frp data into a csv.
    # If the csv already exists, add a new line.
    print(f"         Running: {f_save_frp.__name__}()")
    
    # Define the route and name of the file
    filename = str(route_to_save_file)+"\\"+str(name_of_the_file)+".csv"
    
    # Check if the file already exists
    exist_file = os.path.isfile(filename)
    
    # Start writing the file
    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")

        # If this is the first entry, write the header
        if not exist_file:
            writer.writerow(["Date_UTC", "FRP_MTG_MW"])

        # Write new line
        Date = acquisition_time.replace(tzinfo=None) # Transform form datetime aware into datetime naive
        Value = frp
        writer.writerow([Date, Value])

           
    print("          - Results saved in:")
    print(f"            {filename}")

    
def f_plot_results(route_to_save_file, name_of_the_file, fig, ax, line):
    # Plot the results
    print(f"         Running: {f_plot_results.__name__}()")
    
    # Define the route and name of the file that contains the data to plot
    filename = str(route_to_save_file)+"\\"+str(name_of_the_file)+".csv"
    
    dts = []
    values = []
    
    # Read the csv that contains the data to plot
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        col_datetime, col_value = header[0], header[1]

        for row in reader:
            dts.append(datetime.fromisoformat(row[0]))
            values.append(float(row[1]))

    line.set_xdata(dts)
    line.set_ydata(values)

    if not ax.get_xlabel():
        ax.grid(True)
        ax.set_xlabel(col_datetime)
        ax.set_ylabel(col_value)
        ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 10, 20, 30, 40, 50]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        fig.autofmt_xdate()
        fig.suptitle(name_of_the_file)

    ax.relim()
    ax.autoscale_view()

    clear_output(wait=True)
    display(fig)

    return fig, ax, line
    
    
# %% DEFINE THE MAIN FUNCTION
def main():
    
    # Get the arguments
    args = f_parser()
    
    # Define the bbox
    lonlat_bbox = [args.west, args.south, args.east, args.north] # in decimal degrees

    # Validate the coordinates
    f_check_coordinates(lonlat_bbox)
    
    # Validate the start time
    args.start = f_check_start_datetime(args.start)
    
    # Show the area defined by the bbox (if show_map is True)
    if args.show_map:
        f_show_the_bbox(lonlat_bbox)

    # Define the directories
    directories = f_define_the_directories()
       
    # Define the datetime (that will incrase by 10 min in every loop)
    dt = args.start
    
    # Define the end datetime:
    if args.end is not None: # If args.end was defined ...
        dt_end = args.end # ... directly pass it
        Infinite_loop = False # and create a boolean that will inform that there is an end datetime
    else: # If it was not defined (i.e. its value is defult=None) ...
        dt_end = dt + timedelta(minutes=10) # ... force it to be larger than dt (for the very first loop)
        Infinite_loop = True # and create a boolean that will inform that there is no end datetime
    
    # Prepare the figure
    if args.show_graph:
        plt.ion()  # interactive mode
        fig, ax = plt.subplots(figsize=(10, 5))
        line, = ax.plot([], [], color="red")
    else:
        fig = ax = line = None
    
    # While current-time is older than end-time, keep iterating
    # If no end-time is defined, it will always be larger than dt
    while dt < dt_end:
        print()
        print(f"         ** Time step {dt}")

        # Define the filename of the FRP data and the link to access it
        link_to_download_file, filename = f_define_the_filename(dt)
    
        # Request the FRP data to its repository in gitlab and save it (as an CSV compressed file).
        # If the FRP is not yet available in the repository, this function launchs a scheduler that will wait and try again
        f_call_to_lsasaf(link_to_download_file, filename, directories, args.beeper, args.waiting_time)
        
        # Read the CSV compressed file to get the FRP data inside the bbox
        frp = f_get_frp(directories["Raw_data"], filename, lonlat_bbox)
    
        # Save the FRP data
        f_save_frp(directories["Outputs"], args.name, dt, frp)
               
        # Plot the frp (if show_graph is True)
        if args.show_graph:
            fig, ax, line = f_plot_results(directories["Outputs"], args.name, fig, ax, line)

        # If it is a non-stop loop, add 20 min to end_time 
        if Infinite_loop:
            dt_end = dt + timedelta(minutes=20)
        
        # Add 10 min and go to the next loop in the while bucle
        dt = dt + timedelta(minutes=10)

    # Endscript
    print()
    print("         Endscript")
    
    
# %% RING BELL
if __name__ == "__main__":

    main()
