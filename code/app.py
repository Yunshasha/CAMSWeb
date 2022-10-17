# -*- coding: utf-8 -*-
"""
Created on Mon Apr 12 22:52:38 2021

@author: Yun Shasha
"""
#!/usr/bin/python
from flask import (
    Flask,
    render_template,
    session,
    redirect,
    url_for,
    request,
    Response,
    flash,
    jsonify,
    session
)
import os
import datetime
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import cdsapi
import xarray as xr
import rioxarray
from shapely.geometry import mapping
import getMean
# import requests module
import requests
import config

# create a session object
mySession = requests.Session()


# Create the application instance
app = Flask(__name__, template_folder="templates")

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = '_5#y2L"F4Q8z\n\xec]/'


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/test')
def test():
    return render_template("test.html")


@app.route('/getDayData')
def getDayData():
    sdate = request.args.get('sdate')
    pollutants = request.args.get('pollutants')
    province = request.args.get('province')
    print(province)

    # 5.867697	47.270114	15.04116	55.058165
    # bounds is shape of the country, area is the four bounds of the country in rectangle
    [bounds, area, centroid] = getProvinceBounds(province)

    # capitalCoor = getCapitalCoordinates(province) ##请求polygon的中心点坐标
    NWSE_area = [list(area.maxy.values+0.1)[0], list(area.minx.values-0.1)[
        0], list(area.miny.values-0.1)[0], list(area.maxx.values+0.1)[0]]

    zoomCenter = [(NWSE_area[0]+NWSE_area[2])/2, (NWSE_area[1]+NWSE_area[3])/2]
    # print(zoomCenter)

    [mean_data, mean_each_time_data] = getRawDataDay(
        NWSE_area, bounds, pollutants, sdate, centroid)

    #pd.DataFrame(mean_data).to_csv("clipped23.csv")
    mean_province = np.nanmean(mean_data)
    mean_each_time_data_province = mean_each_time_data

    if pollutants == 'carbon_monoxide':
        mean_province = mean_province/1000
        mean_each_time_data_province = mean_each_time_data/1000

    unitStr, threshold, chartThreshold, AQG_type, x_label_text = getUnitStr(pollutants, 'day')

    data_list = {}
    data_list['meandata'] = mean_province.tolist()
    data_list['unitStr'] = unitStr
    data_list['threshold'] = threshold
    data_list['chartThreshold'] = chartThreshold
    data_list['AQG_type'] = AQG_type
    data_list['x_label_text'] = x_label_text
    data_list['zoomCenter'] = zoomCenter
    data_list['meaneachtimedata'] = mean_each_time_data_province.tolist()
    # data_list['count'] = np.count_nonzero(mean_each_time_data_province >= chartThreshold)
    # print(data_list)

    return Response(json.dumps(data_list), mimetype='application/json')

def getRawDataDay(NWSE_area, bounds, pollutants, sdate, centroid):
    if pollutants == 'ozone':
        ds_time = sdate + '/' + (datetime.datetime.strptime(sdate,'%Y-%m-%d').date() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        ds_time = sdate + '/' + sdate

    ds_name = 'cams-europe-air-quality-forecasts'
    
    ds_variable = pollutants
    ds_area = NWSE_area
    ds_bounds = bounds
    ds_centroid = centroid

    [mean_data, fName, mean_each_time_data, rdata, dsVariable] = getMean.get_mean(
        ds_name=ds_name, ds_time=ds_time, ds_variable=ds_variable, ds_area=ds_area, ds_bounds=ds_bounds, ds_centroid=ds_centroid)

    global sessionRdata
    global sessionDsVariable
    sessionRdata = rdata
    sessionDsVariable = dsVariable

    if os.path.exists(fName):
        os.remove(fName)

    return [mean_data, mean_each_time_data]


@app.route('/getYearData')
def getYearData():
    syear = request.args.get('syear')
    pollutants = request.args.get('pollutants')
    province = request.args.get('province')

    # 5.867697	47.270114	15.04116	55.058165
    # bounds is shape of the country, area is the four bounds of the country in rectangle
    [bounds, area, centroid] = getProvinceBounds(province)

    # capitalCoor = getCapitalCoordinates(province) ##请求polygon的中心点坐标
    NWSE_area = [list(area.maxy.values+0.1)[0], list(area.minx.values-0.1)[
        0], list(area.miny.values-0.1)[0], list(area.maxx.values+0.1)[0]]

    zoomCenter = [(NWSE_area[0]+NWSE_area[2])/2, (NWSE_area[1]+NWSE_area[3])/2]
    # print(zoomCenter)

    [mean_data, mean_each_day_data] = getRawDataYear(
        NWSE_area, bounds, pollutants, syear, province, centroid)

    #pd.DataFrame(mean_data).to_csv("clipped23.csv")
    mean_province = np.nanmean(mean_data)
    mean_each_time_data_province = mean_each_day_data

    if pollutants == 'carbon_monoxide':
        mean_province = mean_province/1000
        mean_each_time_data_province = mean_each_day_data/1000

    unitStr, threshold, chartThreshold, AQG_type, x_label_text = getUnitStr(pollutants, 'year')

    # # 求每天24小时的均值
    # if pollutants == 'ozone':
    #     aa = mean_each_time_data_province
    # else:
    #     mean_every_day = []
    #     for k in range(int(len(mean_each_time_data_province)/24)):
    #         start_k = 24*k
    #         end_k = 24*(k+1)
    #         mean_every_day.append(np.mean(mean_each_time_data_province[start_k:end_k]))
    #     mean_every_day = np.array(mean_every_day)

    data_list = {}
    data_list['meandata'] = mean_province.tolist()
    data_list['unitStr'] = unitStr
    data_list['threshold'] = threshold
    data_list['chartThreshold'] = chartThreshold
    data_list['AQG_type'] = AQG_type
    data_list['x_label_text'] = x_label_text
    data_list['zoomCenter'] = zoomCenter
    data_list['meaneachtimedata'] = mean_each_time_data_province.tolist()
    data_list['count'] = np.count_nonzero(mean_each_time_data_province >= chartThreshold)
    # print(mySession.sessionRdata)

    return Response(json.dumps(data_list), mimetype='application/json')

def getRawDataYear(NWSE_area, bounds, pollutants, syear, province, centroid):
    ds_name = 'cams-europe-air-quality-forecasts'
    ds_year = syear
    ds_variable = pollutants
    ds_area = NWSE_area
    ds_bounds = bounds
    ds_province = province
    ds_centroid = centroid

    [mean_data, mean_each_day_data, rdata, dsVariable] = getMean.get_mean_year(
        ds_name=ds_name, ds_year=ds_year, ds_variable=ds_variable, ds_area=ds_area, ds_bounds=ds_bounds, ds_province=ds_province, ds_centroid=ds_centroid)

    global sessionRdata
    global sessionDsVariable
    sessionRdata = rdata
    sessionDsVariable = dsVariable

    return [mean_data, mean_each_day_data]


@app.route('/queryByPixel')
def queryByPixel():
    lat_pixel = request.args.get('lat_pixel')
    lon_pixel = request.args.get('lon_pixel')

    try:
        NearGrid = sessionRdata.sel(
            latitude=lat_pixel, longitude=lon_pixel, method='nearest')
    except:  # 这里执行只有一个网格的数据 不确定 待验证
        NearGrid = sessionRdata

    # xdata = np.float64(NearGrid.time.values/3600000000000)
    ydata = np.reshape(np.float64(
        NearGrid[sessionDsVariable].values), (1, -1))[0]

    if sessionDsVariable == 'co_conc':
        ydata = ydata/1000

    
    if len(ydata) > 48: # 这个if是求year数据中的天均值; 大于48说明一定是年数据, 而大于24不一定, 因为臭氧的day数据是两天, 长度为48;
        if sessionDsVariable == 'co_conc': # 如果是臭氧
            aa = ydata
        else:
            mean_every_day = []
            for k in range(int(len(ydata)/24)):
                start_k = 24*k
                end_k = 24*(k+1)
                mean_every_day.append(np.mean(ydata[start_k:end_k]))
            mean_every_day = np.array(mean_every_day)
            ydata = mean_every_day
    else: # 这里保证了day数据显示为1天的数据; 因为臭氧的是两天数据, 长度为48
        ydata = ydata[0:24]


    data_list = {}
    # data_list['xdata'] = xdata.tolist()
    data_list['ydata'] = ydata.tolist()

    return Response(json.dumps(data_list), mimetype='application/json')


def getUnitStr(pollutants, time):
    if time == 'day':
        AQG_type = ' (Day average reference value)'
        x_label_text = 'Time (hours)'

        if pollutants == 'carbon_monoxide':
            # Concentration: unit
            unitStr = '  mg/m3'
            threshold = 4
            chartThreshold = 4
        else:
            unitStr = '  ug/m3'
            if pollutants == 'sulphur_dioxide':
                threshold = 40
                chartThreshold = 40
            elif pollutants == 'nitrogen_dioxide':
                threshold = 25
                chartThreshold = 25
            elif pollutants == 'particulate_matter_2.5um':
                threshold = 15
                chartThreshold = 15
            elif pollutants == 'particulate_matter_10um':
                threshold = 45
                chartThreshold = 45
            elif pollutants == 'ozone':
                threshold = 100  # 还没写
                chartThreshold = 100  # 还没写

    elif time == 'year':
        AQG_type = ' (Annual average reference value)'
        x_label_text = 'Time (days)'

        if pollutants == 'carbon_monoxide':
            # Concentration: unit
            unitStr = '  mg/m3'
            threshold = -1  # 表示这个没有threshold
            chartThreshold = 4
        else:
            unitStr = '  ug/m3'
            if pollutants == 'sulphur_dioxide':
                threshold = -1
                chartThreshold = 40
            elif pollutants == 'nitrogen_dioxide':
                threshold = 10
                chartThreshold = 25
            elif pollutants == 'particulate_matter_2.5um':
                threshold = 5
                chartThreshold = 15
            elif pollutants == 'particulate_matter_10um':
                threshold = 15
                chartThreshold = 45
            elif pollutants == 'ozone':
                # if is day dont have threshold
                threshold = 60
                chartThreshold = 100  # 还没写

    return unitStr, threshold, chartThreshold, AQG_type, x_label_text


def getProvinceBounds(province):
    code = province
    path_rg = config.baseLayersPath
    gdf_rg = gpd.read_file(path_rg)
    gdf_rg.crs = "EPSG:4326"
    #gdf_rg = gdf.to_crs("EPSG:4326")
    gdf_nation = gdf_rg[gdf_rg.PRO_COM == int(code)]

    centroid = gdf_nation.geometry.centroid

    area = gdf_nation.bounds
    # print(area)

    bounds = gdf_nation.geometry.apply(mapping)

    return bounds, area, centroid


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        debug=True)
