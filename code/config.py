
# you can specify the shape file to query different region, e.g. Lombardia, Piemonte , etc..
baseLayersPath = 'data/Lombardy/lombardy_municipalities.shp'

# in order to reduce the query time for year data, we will download them and do search history
# if they exist, use them directly, else download
# so you have to specify the file save path and the download area bounds
yearDataPath = 'data/NCFILE/'



# you have to specify the region bounds
ds_area = [46.634675, 8.498355, 44.680136, 11.426766,] #lombardia

