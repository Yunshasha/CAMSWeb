import cdsapi
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray
import geojson
from shapely.geometry import mapping

# Below is note.
# nitrogen_dioxide --> no2_conc
# particulate_matter_10um  -->  pm10_conc
# nitrogen_monoxide --> no_conc
# sulphur_dioxide --> so2_conc
# ozone --> o3_conc
# carbon_monoxide --> co_conc
# particulate_matter_2.5um --> pm2p5_conc


def get_mean(ds_name, ds_time, ds_variable, ds_area,ds_bounds):

    # Download raw data. Currently only support daily timescale.

    c = cdsapi.Client()
    c.retrieve(
        ds_name,
        {
            'model': 'ensemble',
            'date': ds_time,
            'format': 'netcdf',
            'variable': ds_variable,
            'level': '0',
            'type': 'analysis',
            'leadtime_hour': '0',
            'time': [
                '00:00', '01:00', '02:00',
                '03:00', '04:00', '05:00',
                '06:00', '07:00', '08:00',
                '09:00', '10:00', '11:00',
                '12:00', '13:00', '14:00',
                '15:00', '16:00', '17:00',
                '18:00', '19:00', '20:00',
                '21:00', '22:00', '23:00',
            ],
            'area': ds_area, # [45.99, 7.16, 37.48, 17.88,]
        },
        'download.nc')

    # Open raw data. This raw data will be used as part of return.
    rdata = xr.open_dataset("download.nc")
    rdata.rio.write_crs("epsg:4326", inplace=True)
    # data["pm2p5_conc"][0].rio.to_raster('test.tif')
    rdata = rdata.assign_coords(longitude=(((rdata.longitude + 180) % 360) - 180)).sortby('longitude')  
    rdata = rdata.rio.clip(ds_bounds,'epsg:4326',all_touched=False)

    # Below is note
    # nitrogen_dioxide --> no2_conc
    # particulate_matter_10um  -->  pm10_conc
    # nitrogen_monoxide --> no_conc
    # sulphur_dioxide --> so2_conc
    # ozone --> o3_conc
    # carbon_monoxide --> co_conc
    # particulate_matter_2.5um --> pm2p5_conc

    # Now we should retrieve the values of concentration of the input pollutant from raw data.

    if ds_variable == 'nitrogen_dioxide':
        rdata_values = rdata.no2_conc.values
    elif ds_variable == 'particulate_matter_10um':
        rdata_values = rdata.pm10_conc.values
    elif ds_variable == 'nitrogen_monoxide':
        rdata_values = rdata.no_conc.values
    elif ds_variable == 'sulphur_dioxide':
        rdata_values = rdata.so2_conc.values
    elif ds_variable == 'ozone':
        rdata_values = rdata.o3_conc.values
    elif ds_variable == 'carbon_monoxide':
        rdata_values = rdata.co_conc.values
    elif ds_variable == 'particulate_matter_2.5um':
        rdata_values = rdata.pm2p5_conc.values

    # Below we calculate the mean values. For ozone, we don't really understand how to do with "8-hour maximum daily", so here we just seperate 24 hours into 3 parts, calculate the mean values of each part and select the maximum values among them and create a new dataarray contains these maximum mean values of ozone. We are not sure about this yet.
    if ds_variable == 'ozone':
        h1 = np.mean(rdata_values[0:8, :, :, :], axis=0)
        h2 = np.mean(rdata_values[8:16, :, :, :], axis=0)
        h3 = np.mean(rdata_values[16:24, :, :, :], axis=0)

        max_mean = np.fmax(h1, h2, h3)

        mean_data = max_mean

    # For other pollutants, just simply calculate the mean values in one day.
    else:

        mean_data = np.mean(rdata_values[:, :, :, :], axis=0)

    # Don't forget that we will need these lats and lons for our plot. So they are returned as well.
    latitude = rdata.latitude.values
    longitude = rdata.longitude.values

    # Return these values
    return [mean_data[0], latitude, longitude, rdata]
