# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 16:51:54 2013
@author:Sagy Cohen, Uni of Alabama
Calculates long-term mean raster layer (ESRI ASCII) for the WBMsed model output
layers (NetCDF) 
"""
import scipy
from scipy.io import netcdf 
import numpy as np
import matplotlib.pyplot as plt

sim_first = 2009
sim_last = 2009

nutrient = 'Precipitation'#'QxT_WaterTemp'#'Discharge'#'precipitation'#'Discharge'

NetCDF_fn1 = r'/media/scohen2/Data/WindowsShare/TropicalCyclones/GPCCfull_NCEP/Global_Precipitation_GPCCfull_NCEP_30min_dTS'
            #r'/Volumes/LaCie/Data/Cyc_adjusted_files2/Global_'+nutrient+'_Bedload+Dist_30min_dTS'

Output_fn0 = NetCDF_fn1

   #set the output ASCII file header
#header=['ncols  3600\n']
#header.append('nrows  1500\n')
header=['ncols  720\n']# % 30min
header.append('nrows  360')# % 30min
header.append('xllcorner -180\n')
header.append('yllcorner -60\n')
#header.append('cellsize  0.1\n')
header.append('cellsize  0.5\n')# %30min
header.append('NODATA_value  -9999\n')
   # open and write the header to the output file
Output_fn = Output_fn0[:-3]+'Average'+str(sim_first)+'-'+str(sim_last)+'.asc'
of = open(Output_fn, 'w')
of.writelines(header)

NetCDF_fn = NetCDF_fn1+str(sim_first)+'.nc'  # set input netcdf name
f = netcdf.netcdf_file(NetCDF_fn, 'r')
tmp = f.variables['precipitation'][:]
#print tmp.shape
avee = np.average(tmp, 0)
#print avee.shape

for c in range(720):
    for r in range(360):
        print c,r
        for sim_yr in range(sim_first, sim_last + 1):
            print sim_yr
            year_arr = np.zeros((720, 360))
            NetCDF_fn = NetCDF_fn1 + str(sim_yr) + '.nc'  # set input netcdf name
            f = netcdf.netcdf_file(NetCDF_fn, 'r')
            arr = np.array([])
            tmp = f.variables['precipitation'][:]
           # tmp = f.variables['precipitation'][c][r]
       # print tmp.shape
        tmp_ave = np.average(tmp, 0)
       # print tmp_ave.shape
       # print avee.shape
        avee = np.dstack((avee, tmp_ave))
       # print avee.shape
    
#aver_max = np.average(maxx,2)
avri = np.average(avee, 2)
#print aver_max.shape
#plt.imshow(aver_max)
#plt.show()
avri=avri[::-1] #flip
#aver_max=aver_max[::-1] #flip    
np.savetxt(of, avri, fmt='%1.4f')
#of.writelines(format(out))
of.close()