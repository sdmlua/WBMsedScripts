# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 16:51:54 2013
@author:Sagy Cohen, Uni of Alabama
Calculates long-term mean raster layer (ESRI ASCII) for the WBMsed model output
layers (NetCDF) 
"""
from scipy.io import netcdf
import numpy as np

sim_first = 1980
sim_last = 2010

nutrient = 'QxT_WaterTemp'#'QxT_WaterTemp'#'Discharge'#'precipitation'#'Discharge'

NetCDF_fn1 = r'/media/scohen2/Data/Data3/Aug1_2018_WaterTemp/Daily/GlobalWaterTemps/Temp/Global_qxt_watertemp_Pristine__dTS'
            #r'/Volumes/LaCie/Data/Cyc_adjusted_files2/Global_'+nutrient+'_Bedload+Dist_30min_dTS'

Output_fn0 = NetCDF_fn1

#set the output ASCII file header
header=['ncols  3600\n']
header.append('nrows  1500\n')
#header=['ncols  720\n']# % 30min
#header.append('nrows  360')# % 30min
header.append('xllcorner -180\n')
header.append('yllcorner -60\n')
header.append('cellsize  0.1\n')
#header.append('cellsize  0.5\n')# %30min
header.append('NODATA_value  -9999\n')

NetCDF_fn = NetCDF_fn1+str(sim_first+1)+'.nc'  # set input netcdf name
f = netcdf.netcdf_file(NetCDF_fn, 'r')
#if nutrient == 'Discharge':
 #   valueAcc = f.variables['discharge'][:].astype(np.float32)
#else:
#    valueAcc = f.variables[nutrient][:].astype(np.float16)/1000
#print valueAcc.shape
value = f.variables[nutrient][[0][:][:]].astype(np.float32)#/1000
averageRas = np.concatenate(value)
f.close()
np.putmask(averageRas, averageRas > 0, 0)
stdRas = np.copy(averageRas)
rangeRas = np.copy(averageRas)

for r in range(44, 1500):
    print r
    for c in range(3600):
        if averageRas[r][c] > -9999:
            accum = np.array([])
            for sim_yr in range(sim_first, sim_last + 1):
                #print sim_yr
                NetCDF_fn = NetCDF_fn1 + str(sim_yr) + '.nc'  # set input netcdf name
                f = netcdf.netcdf_file(NetCDF_fn, 'r')
                tmp = f.variables[nutrient][:, r, c].astype(np.float32)
                accum = np.append(accum, tmp)

            averageRas[r][c] = accum.mean()
            stdRas[r][c] = accum.std()
            rangeRas[r][c] = accum.max() - accum.min()

#open and write the header to the output file
Output_fn = Output_fn0[:-3]+'Average'+str(sim_first)+'-'+str(sim_last)+'.asc'
of1 = open(Output_fn, 'w')
of1.writelines(header)
averageRas = averageRas[::-1] #flip
np.savetxt(of1, averageRas, fmt='%1.4f')
of1.close()

Output_fn = Output_fn0[:-3]+'Std'+str(sim_first)+'-'+str(sim_last)+'.asc'
of2 = open(Output_fn, 'w')
of2.writelines(header)
stdRas = stdRas[::-1] #flip
np.savetxt(of2, stdRas, fmt='%1.4f')
of2.close()

Output_fn = Output_fn0[:-3]+'Range'+str(sim_first)+'-'+str(sim_last)+'.asc'
of3 = open(Output_fn, 'w')
of3.writelines(header)
rangeRas = rangeRas[::-1] #flip
np.savetxt(of3, rangeRas, fmt='%1.4f')
of3.close()
