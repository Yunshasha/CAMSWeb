import cdsapi
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray
from shapely.geometry import mapping
import uuid
from downloadYear import loopDownoad
import os
import geopandas as gpd


# Below is note.
# nitrogen_dioxide --> no2_conc
# particulate_matter_10um  -->  pm10_conc
# sulphur_dioxide --> so2_conc
# ozone --> o3_conc
# carbon_monoxide --> co_conc
# particulate_matter_2.5um --> pm2p5_conc


def get_mean(ds_name, ds_time, ds_variable, ds_area,ds_bounds,ds_centroid):

    # Download raw data. Currently only support daily timescale.
    
    unique_filename = str(uuid.uuid4().hex)    
    fName = unique_filename    

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
        fName)

    # fName = 'd3c88ea5ec594163ad39b1f20e674d65'

    # Open raw data. This raw data will be used as part of return.
    # rdata = xr.open_dataset(fName)
    # rdata.close()

    with xr.open_dataset(fName) as rdataAll:

        rdataAll.rio.write_crs("epsg:4326", inplace=True)
        # data["pm2p5_conc"][0].rio.to_raster('test.tif')
        rdataAll = rdataAll.assign_coords(longitude=(((rdataAll.longitude + 180) % 360) - 180)).sortby('longitude')  
        try:
            rdata = rdataAll.rio.clip(ds_bounds,'epsg:4326',all_touched=False)

            # Below is note
            # nitrogen_dioxide --> no2_conc
            # particulate_matter_10um  -->  pm10_conc
            # sulphur_dioxide --> so2_conc
            # ozone --> o3_conc
            # carbon_monoxide --> co_conc
            # particulate_matter_2.5um --> pm2p5_conc

            # Now we should retrieve the values of concentration of the input pollutant from raw data.

            if ds_variable == 'nitrogen_dioxide':
                rdata_values = rdata.no2_conc.values
                key_values = 'no2_conc'
            elif ds_variable == 'particulate_matter_10um':
                rdata_values = rdata.pm10_conc.values
                key_values = 'pm10_conc'
            elif ds_variable == 'sulphur_dioxide':
                rdata_values = rdata.so2_conc.values
                key_values = 'so2_conc'
            elif ds_variable == 'ozone':
                rdata_values = rdata.o3_conc.values
                key_values = 'o3_conc'
            elif ds_variable == 'carbon_monoxide':
                rdata_values = rdata.co_conc.values
                key_values = 'co_conc'
            elif ds_variable == 'particulate_matter_2.5um':
                rdata_values = rdata.pm2p5_conc.values
                key_values = 'pm2p5_conc'

            # Below we calculate the mean values. For ozone, we don't really understand how to do with "8-hour maximum daily", so here we just seperate 24 hours into 3 parts, calculate the mean values of each part and select the maximum values among them and create a new dataarray contains these maximum mean values of ozone. We are not sure about this yet.
            if ds_variable == 'ozone':
                H = []
                for k in range(17):
                    start_k = 7 + k
                    end_k = 15 + k
                    h = np.mean(rdata_values[start_k:end_k, :, :, :], axis=0)
                    H.append(h)
                H = np.array(H)
                max_mean = np.mean(H, axis=0)

                mean_data = np.mean(max_mean)

            # For other pollutants, just simply calculate the mean values in one day.
            else:
                mean_data = np.mean(rdata_values[:, :, :, :], axis=0)[0]

            mean_each_time_data = np.reshape(np.nanmean(rdata_values[0:24], axis=(2,3)),(1,-1))[0]
        except:            
            centroid = ds_centroid
            lon_centroid = centroid.x.values[0]
            lat_centroid = centroid.y.values[0]
            rdata = rdataAll.sel(latitude=lat_centroid, longitude=lon_centroid, method='nearest')
            # pass
            # continue            

            if ds_variable == 'nitrogen_dioxide':
                rdata_values = rdata.no2_conc.values
                key_values = 'no2_conc'
            elif ds_variable == 'particulate_matter_10um':
                rdata_values = rdata.pm10_conc.values
                key_values = 'pm10_conc'
            elif ds_variable == 'sulphur_dioxide':
                rdata_values = rdata.so2_conc.values
                key_values = 'so2_conc'
            elif ds_variable == 'ozone':
                rdata_values = rdata.o3_conc.values
                key_values = 'o3_conc'
            elif ds_variable == 'carbon_monoxide':
                rdata_values = rdata.co_conc.values
                key_values = 'co_conc'
            elif ds_variable == 'particulate_matter_2.5um':
                rdata_values = rdata.pm2p5_conc.values
                key_values = 'pm2p5_conc'

            # Below we calculate the mean values. For ozone, we don't really understand how to do with "8-hour maximum daily", so here we just seperate 24 hours into 3 parts, calculate the mean values of each part and select the maximum values among them and create a new dataarray contains these maximum mean values of ozone. We are not sure about this yet.
            if ds_variable == 'ozone':
                H = []
                for k in range(17):
                    start_k = 7 + k
                    end_k = 15 + k
                    h = np.mean(rdata_values[start_k:end_k], axis=0)
                    H.append(h)
                H = np.array(H)
                max_mean = np.mean(H, axis=0)

                mean_data = np.mean(max_mean)

            # For other pollutants, just simply calculate the mean values in one day.
            else:
                # mean_data = np.mean(rdata_values[:, :, :, :], axis=0)
                mean_data = np.mean(rdata_values, axis=0)[0]

            mean_each_time_data = rdata_values[0:24]

    return [mean_data,fName,mean_each_time_data,rdata,key_values]


def get_mean_year(ds_name, ds_year, ds_variable, ds_area,ds_bounds,ds_province,ds_centroid):
    #'cams-europe-air-quality-forecasts', 2019, nitrogen_dioxide, 矩形, 省边界不规则
    # Download raw data. Currently only support daily timescale.
    # # filePath = 'F:\\NCFILE\\'
    # # fileIndex = 'Milano_nitrogen_dioxide_2020'
    # # checkFileIndex = ds_province+'_'+ds_variable+'_'+ds_year
    # # if os.path.exists(filePath+checkFileIndex+'_12.nc'):
    # #     fileIndex = checkFileIndex
    # # else:
    # #    fileIndex = loopDownoad(ds_name, ds_year, ds_variable, ds_area, ds_bounds, ds_province)
    fileIndex = loopDownoad(ds_name, ds_year, ds_variable, ds_area, ds_bounds, ds_province)
    if ds_variable == 'ozone':
        rdataAll = xr.open_dataset(fileIndex)
    else:
        rdataAll = xr.open_mfdataset(fileIndex + '*.nc',combine='nested', concat_dim='time')

    rdataAll.rio.write_crs("epsg:4326", inplace=True)
    # data["pm2p5_conc"][0].rio.to_raster('test.tif')
    rdataAll = rdataAll.assign_coords(longitude=(((rdataAll.longitude + 180) % 360) - 180)).sortby('longitude')  
    
    try:
        rdata = rdataAll.rio.clip(ds_bounds,'epsg:4326',all_touched=False)

        if ds_variable == 'nitrogen_dioxide':
            rdata_values = rdata.no2_conc.values
            key_values = 'no2_conc'
        elif ds_variable == 'particulate_matter_10um':
            rdata_values = rdata.pm10_conc.values
            key_values = 'pm10_conc'
        elif ds_variable == 'sulphur_dioxide':
            rdata_values = rdata.so2_conc.values
            key_values = 'so2_conc'
        elif ds_variable == 'ozone':
            rdata_values = rdata.o3_conc.values
            key_values = 'o3_conc'
        elif ds_variable == 'carbon_monoxide':
            rdata_values = rdata.co_conc.values
            key_values = 'co_conc'
        elif ds_variable == 'particulate_matter_2.5um':
            rdata_values = rdata.pm2p5_conc.values
            key_values = 'pm2p5_conc'

        # Below we calculate the mean values. For ozone, we don't really understand how to do with "8-hour maximum daily", so here we just seperate 24 hours into 3 parts, calculate the mean values of each part and select the maximum values among them and create a new dataarray contains these maximum mean values of ozone. We are not sure about this yet.
        if ds_variable == 'ozone':
            mean_all_days = []
            for dd in range(int(len(rdata_values)/24)):
                start_dd = 24 * dd
                end_dd = 24 + 24 * (dd+1)
                rdata_values_2_days = rdata_values[start_dd:end_dd]
                H = []
                for k in range(17):
                    start_k = 7 + k
                    end_k = 15 + k
                    h = np.mean(rdata_values_2_days[start_k:end_k], axis=0)
                    H.append(h)

                mean_all_days.append(np.mean(np.mean(np.array(H), axis=0)))

            mean_each_day_data = np.array(mean_all_days)
            mean_data = np.mean(mean_each_day_data)

        # For other pollutants, just simply calculate the mean values in one day.
        else:
            mean_data = np.mean(rdata_values[:, :, :, :], axis=0)
            mean_every_day = []
            for k in range(int(len(rdata_values)/24)):
                start_k = 24*k
                end_k = 24*(k+1)
                mean_every_day.append(np.mean(mean_each_time_data_province[start_k:end_k]))
            mean_each_day_data = np.array(mean_every_day)

        # mean_each_time_data = np.reshape(np.nanmean(rdata_values, axis=(2,3)),(1,-1))[0]

    except: 
        centroid = ds_centroid
        lon_centroid = centroid.x.values[0]
        lat_centroid = centroid.y.values[0]
        rdata = rdataAll.sel(latitude=lat_centroid, longitude=lon_centroid, method='nearest')
        # pass
        # continue            

        if ds_variable == 'nitrogen_dioxide':
            rdata_values = rdata.no2_conc.values
            key_values = 'no2_conc'
        elif ds_variable == 'particulate_matter_10um':
            rdata_values = rdata.pm10_conc.values
            key_values = 'pm10_conc'
        elif ds_variable == 'sulphur_dioxide':
            rdata_values = rdata.so2_conc.values
            key_values = 'so2_conc'
        elif ds_variable == 'ozone':
            rdata_values = rdata.o3_conc.values
            key_values = 'o3_conc'
        elif ds_variable == 'carbon_monoxide':
            rdata_values = rdata.co_conc.values
            key_values = 'co_conc'
        elif ds_variable == 'particulate_matter_2.5um':
            rdata_values = rdata.pm2p5_conc.values
            key_values = 'pm2p5_conc'

        # Below we calculate the mean values. For ozone, we don't really understand how to do with "8-hour maximum daily", so here we just seperate 24 hours into 3 parts, calculate the mean values of each part and select the maximum values among them and create a new dataarray contains these maximum mean values of ozone. We are not sure about this yet.
        if ds_variable == 'ozone':
            mean_all_days = []
            for dd in range(int(len(rdata_values)/24)):
                start_dd = 24 * dd
                end_dd = 24 + 24 * (dd+1)
                rdata_values_2_days = rdata_values[start_dd:end_dd]
                H = []
                for k in range(17):
                    start_k = 7 + k
                    end_k = 15 + k
                    h = np.mean(rdata_values_2_days[start_k:end_k], axis=0)
                    H.append(h)

                mean_all_days.append(np.mean(np.mean(np.array(H), axis=0)))

            mean_each_day_data = np.array(mean_all_days)
            mean_data = np.mean(mean_each_day_data)

        # For other pollutants, just simply calculate the mean values in one day.
        else:            
            mean_every_day = []
            for k in range(int(len(rdata_values)/24)):
                start_k = 24*k
                end_k = 24*(k+1)
                mean_every_day.append(np.mean(rdata_values[start_k:end_k]))
            mean_each_day_data = np.array(mean_every_day)
            mean_data = np.mean(mean_each_day_data)

        # mean_each_time_data = rdata_values
    

    return [mean_data,mean_each_day_data,rdata,key_values]

