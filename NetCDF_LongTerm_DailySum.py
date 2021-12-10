# -*- coding: utf-8 -*-
"""
@author:Sagy Cohen, Uni of Alabama
Calculates long-term mean raster layer (ESRI ASCII) for the WBMsed model output
layers (NetCDF) 
"""
from scipy.io import netcdf
import numpy as np

sim_first = 1980
sim_last = 2010

nutrient = 'Discharge' #'QxT_WaterTemp'#'Discharge'#'precipitation'#'Discharge'

NetCDF_fn1 = r'/media/scohen2/Seagate - S/Data3/Sept28_2018_Cyclones_discharge/WithCyclons+Prist/06min/Daily/Global_Discharge_WithCyclons+Prist_06min_dTS'
             # /media/scohen2/Data/Data3/July21_2018_Cyclones/Global/Discharge/WithOutCyclons+Dist/06min/Daily/Global_Discharge_WithOutCyclons+Dist_06min_dTS1981.nc         # r'/Volumes/LaCie/Data3/Feb29_2017_Density_Daily/RGISresults/Global/QxT_WaterTemp/Global_QxT_WaterTemp_Density2+Dist_06min_dTS'
            #r'/media/scohen2/Data/Data3/Aug1_2018_WaterTemp/GlobalWaterTemps/Temp/Monthly/Global_qxt_watertemp_Pristine__mTS2010.nc'

Output_fn0 = NetCDF_fn1
   
#set the output ASCII file header
header=['ncols  2773\n'] #Oahu
#header=['ncols  3600\n']
header.append('nrows  2053\n') #Oahu
#header.append('nrows  1500\n')
#header=['ncols  720\n']# % 30min
#header.append('nrows  360\n')# % 30min
header.append('xllcorner -158.40027777733\n') #Oahu
header.append('yllcorner 21.22999999938\n') #Oahu
#header.append('xllcorner -180\n')
#header.append('yllcorner -60\n')
header.append('cellsize  0.000277777778\n')
#header.append('cellsize  0.1\n')
#header.append('cellsize  0.5\n')# %30min
header.append('NODATA_value  -9999\n')

NetCDF_fn = NetCDF_fn1+str(sim_first)+'.nc'  # set input netcdf name
f = netcdf.netcdf_file(NetCDF_fn, 'r')
if nutrient == 'Discharge':
    tmpVal = f.variables['discharge'][:].astype(np.float32)
else:
    tmpVal = f.variables[nutrient][:].astype(np.float64)/1000

sumValue = np.nansum(tmpVal, 0, dtype='float64')
print sumValue.shape
f.close()

for sim_yr in range(sim_first, sim_last + 1):
    print sim_yr
    NetCDF_fn = NetCDF_fn1 + str(sim_yr) + '.nc'  # set input netcdf name
    f = netcdf.netcdf_file(NetCDF_fn, 'r')
    if nutrient == 'Discharge':
        tmpVal = f.variables['discharge'][:].astype(np.float32)
    else:
        tmpVal = f.variables[nutrient][:].astype(np.float64)/1000
    f.close()
    np.putmask(tmpVal, tmpVal < 0, np.nan)
    #valueAcc = np.concatenate((valueAcc, tmpVal), axis=0)/1000
    tmpSum = np.nansum(tmpVal, 0, dtype='float64')
    #print tmpSum.shape
    sumValue = sumValue + tmpSum
    #print sumValue.shape

#np.putmask(valueAcc, valueAcc > 40, -9999.0) #!!! For Water Temperature!!0!!!
#np.putmask(valueAcc, valueAcc < 0, np.nan)

sumValue = sumValue[::-1]#*1000 #flip
np.putmask(sumValue, np.isnan(sumValue), -9999.0)
np.putmask(sumValue, sumValue <= 0, -9999.0)
#stat[f.variables[nutrient][:][0] < 0] = -9999.0
Output_fn = Output_fn0[:-3]+'Sum'+str(sim_first)+'-'+str(sim_last)+'.asc'
of = open(Output_fn, 'w')
of.writelines(header)
np.savetxt(of, sumValue, fmt='%1.4f')
of.close()
print 'Done!'
