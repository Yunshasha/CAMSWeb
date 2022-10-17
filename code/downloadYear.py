import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import contextily as ctx
import numpy as np
import xarray as xr
from shapely.geometry import mapping
import cdsapi
import os
import config


def loopDownoad(ds_name, ds_year, ds_variable, ds_area, ds_bounds, ds_province):
    #'cams-europe-air-quality-forecasts', 2019, nitrogen_dioxide, 矩形, 省边界不规则, Milano
    filePath = config.yearDataPath
    my_year = ds_year

    months = ['01', '02', '03', '04', '05',
              '06', '07', '08', '09', '10', '11', '12']

    month_with_days_30 = ['04', '06', '09', '11']
    month_with_days_31 = ['01', '03', '05', '07', '08', '10', '12']

    if ds_variable == 'ozone':
        ds_time = my_year+'-04-01/' + my_year+'-10-01'
        fileName = my_year+'_'+ds_variable+'_04_09.nc'

        if os.path.exists(filePath + fileName):
            fileIndex = filePath+fileName
            return fileIndex
        else:            
            downloadOriginalFile(ds_name, ds_variable, ds_time, ds_area, fileName,filePath)
    else:
        for m in range(len(months)):
            my_month = months[m]
            if my_month in month_with_days_30:
                ds_time = my_year+'-'+my_month+'-01/' + my_year+'-'+my_month+'-30'
                fileName = my_year+'_'+ds_variable+'_'+my_month+'.nc'
            elif my_month in month_with_days_31:
                ds_time = my_year+'-'+my_month+'-01/' + my_year+'-'+my_month+'-31'
                fileName = my_year+'_'+ds_variable+'_'+my_month+'.nc'
            else:
                my_year_int = int(my_year)
                if (my_year_int % 4 == 0) and (my_year_int % 100 != 0) or (my_year_int % 400) == 0:
                    ds_time = my_year+'-'+my_month+'-01/' + my_year+'-'+my_month+'-29'
                    fileName = my_year+'_'+ds_variable+'_'+my_month+'.nc'
                else:
                    ds_time = my_year+'-'+my_month+'-01/' + my_year+'-'+my_month+'-28'
                    fileName = my_year+'_'+ds_variable+'_'+my_month+'.nc'
            
            if os.path.exists(filePath + fileName):
                continue
            else:
                downloadOriginalFile(ds_name, ds_variable, ds_time, ds_area, fileName,filePath)


    fileIndex = filePath + my_year +'_'+ ds_variable
    return fileIndex


def downloadOriginalFile(ds_name, ds_variable, ds_time, ds_area, fileName,filePath):
    # filePath = 'F:\\NCFILE\\'
    # fileName = ds_province+'_'+ds_variable+'_'+my_year+'_'+my_month+'.nc'

    c = cdsapi.Client()
    c.retrieve(
        ds_name,
        {
            'variable': ds_variable,
            'model': 'ensemble',
            'level': '0',
            'date': ds_time,
            'type': 'analysis',
            'leadtime_hour': '0',
            'format': 'netcdf',
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
            'area': config.ds_area     # 请求查询区域自身 ds_area 
        },
        filePath+fileName)

    return
