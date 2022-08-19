#Created on Thu Oct 17 16:51:54 2013
#@author:Sagy Cohen, Uni of Alabama
import scipy    
from scipy.io import netcdf 
from numpy import *
import datetime 
import numpy as np

#file_name = r'/Volumes/Data2/WBMsed_newDams/Feb28_2014/RGISresults/Global/SedimentFlux/Subtracted_Catalog3.txt'
#file_name = r'/media/scohen2/Data/WindowsShare/ValidationDatasets/USGS_Discharge_Mississippi.csv'
#file_name =r'/Users/scohen2/Dropbox/TropicalCyclones/gauge_coords2.csv'
file_name =r'/Volumes/Pegasus32 R6/WindowsShared/SedimentProbability/NWIS_sites_adjusted.csv'
parameter = "SedimentFlux"#"discharge"#"SedimentFlux"#"DeltaQs"
first = 1980
last = 2019

NetCDF_fn1=r'/Volumes/Pegasus32 R6/Data3/Oct27_2021_4p4p1/SedimentFlux/Daily/Global_SedimentFlux_4p4p1+Dist_06min_dTS'
   
output_path= r'/Volumes/Pegasus32 R6/WindowsShared/SedimentProbability/WBMsedtimeseries/'
  
ncid_a= r'/Volumes/Pegasus32 R6/WindowsShared/Global_bqart_a_Lammars+Dist_06min_aTS1980.nc'
ncid = netcdf.netcdf_file(ncid_a,'r')
NetCDF_A = ncid.variables['BQART_A'][:]
ncid.close()


stations_data = np.loadtxt(file_name, delimiter=',', skiprows=1, usecols=(0, 1, 2), dtype=float64) #id,lat,long -> [row][col]

    
def NetCDFtimeseries(station_data,lat_arr,long_arr,NetCDFQ,NetCDF_A):

    for i in range(0, len(lat_arr)):
        if mean(lat_arr[i]) > station_data[1]:
            lat_id = i
            break
        
    if station_data[1] > 0: #fix for negative coordinates
       if (mean(lat_arr[lat_id])-station_data[1]) > (station_data[1]-mean(lat_arr[lat_id-1])):
           lat_id = lat_id - 1
    elif (mean(lat_arr[lat_id])-station_data[1]) > (station_data[1]-mean(lat_arr[lat_id-1])):
           lat_id = lat_id - 1

    #long
    for i in range(0,len(long_arr)):
        if mean(long_arr[i]) > station_data[2]:
            long_id = i
            break
    
    if station_data[2] > 0: #fix for negative coordinates
       if (mean(long_arr[long_id]) -station_data[2]) > (station_data[2]-mean(long_arr[long_id-1])):
           long_id = long_id-1
    elif (mean(long_arr[long_id]) -station_data[2]) > (station_data[2]-mean(long_arr[long_id-1])):
        long_id = long_id-1

    NetCDF_A = NetCDF_A[0][lat_id][long_id] #get area value for these coordinates

    param = []    
    for j in range(0, 365):
        param.append(NetCDFQ[j][lat_id][long_id]) #writing a vector array with the Q time series
    
    return param, NetCDF_A, max(param)

sizz = len(stations_data)

for y in range(first, last+1): # years loop
    print(y)
    NetCDF_fn = '{0}{1}.nc'.format(NetCDF_fn1, y)

    ncid = netcdf.netcdf_file(NetCDF_fn,'r')
    lat = ncid.variables['latitude_bnds'][:]
    longt = ncid.variables['longitude_bnds'][:]
    NetCDFQ= ncid.variables[ncid.subject.decode()][:]
    ncid.close()

    for s_id in range(0,sizz):   #sites loop
        station_data = stations_data[s_id]
        param,area,max_param = NetCDFtimeseries(station_data,lat,longt,NetCDFQ,NetCDF_A)
        #param, max_param = NetCDFtimeseries(station_data, lat, longt, NetCDFQ)  # ,NetCDF_A)
        out_file_name = "{0}{1}_{2}_{3}-{4}.csv".format(output_path,(int(station_data[0])),parameter,first,last)
        #max_file_name = "{0}{1}_{2}_{3}-{4}_Maximum.csv".format(output_path,int(station_data[0]),parameter,first,last)
        if y == first:
            outf = open(out_file_name,'w')
            #maxf = open(max_file_name,'w')
            day = '{0} {1}'.format(str(y),str(0+1))
            date = datetime.datetime.strptime(day, '%Y %j')
            date2 = date.strftime('%d/%m/%Y')
            
            outf.write("{0}\n".format(area))
            #maxf.write("{0},{1},{2}\n".format(date2,str(max_param),area))
            outf.write("{0},{1}\n".format(date2,str(param[0])))
            #maxf.write("{0},{1}\n".format(date2,str(max_param)))
            
            outf.close()
            #maxf.close()
        outf = open(out_file_name,'a')
        #maxf = open(max_file_name,'a')
        
        day = '{0} {1}'.format(str(y),str(0+1))
        date = datetime.datetime.strptime(day, '%Y %j')
        date2 = date.strftime('%d/%m/%Y')
       # maxf.write("{0},{1}\n".format(date2,str(max_param)))
        for i in range(len(param)):
            day = '{0} {1}'.format(str(y),str(i+1))
            date = datetime.datetime.strptime(day, '%Y %j')
            date2 = date.strftime('%d/%m/%Y')
            
            outf.write("{0},{1}\n".format(date2,str(param[i])))
        outf.close()