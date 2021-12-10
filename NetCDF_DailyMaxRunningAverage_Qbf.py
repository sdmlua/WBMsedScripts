# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 16:51:54 2013
@author:Sagy Cohen, Uni of Alabama
Calculates Bankfull Disharge based on the Cohen et al. (2014) (modified from Yamazaki et al. (2011))
Use daily model prediction to calculate R_up - maximum value of a 30 days running average.
"""
from scipy.io import netcdf
import numpy as np

sim_first = 1980
sim_last = 2010

nutrient = 'discharge'#'QxT_WaterTemp'#'Discharge'#'precipitation'#'Discharge'

NetCDF_fn1 = r'/media/scohen2/Seagate - S/Data3/Sept28_2018_Cyclones_discharge/WithCyclons+Prist/06min/Daily/Global_Discharge_WithCyclons+Prist_06min_dTS'
#r'/media/scohen2/Data/Data3/Dec22_2018_Oahu_Precip_fixRelief/Discharge/UH_Prec_Oahu_Relief_fix+Prist/01sec/Daily/Oahu_Discharge_UH_Prec_Oahu_Relief_fix+Prist_01sec_dTS'
#r'/media/scohen2/Data/Data3/Aug1_2018_WaterTemp/Daily/GlobalWaterTemps/Temp/Global_qxt_watertemp_Pristine__dTS'
            #r'/Volumes/LaCie/Data/Cyc_adjusted_files2/Global_'+nutrient+'_Bedload+Dist_30min_dTS'

Output_fn0 = NetCDF_fn1

#set the output ASCII file header
#header=['ncols  2773\n'] #Oahu
header=['ncols  3600\n']
#header.append('nrows  2053\n') #Oahu
header.append('nrows  1500\n')
#header=['ncols  720\n']# % 30min
#header.append('nrows  360\n')# % 30min
#header.append('xllcorner -158.40027777733\n') #Oahu
#header.append('yllcorner 21.22999999938\n') #Oahu
header.append('xllcorner -180\n')
header.append('yllcorner -60\n')
#header.append('cellsize  0.000277777778\n')
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
maxRunAvr = np.concatenate(value)
f.close()
np.putmask(maxRunAvr, maxRunAvr > 0, 0)
#stdRas = np.copy(averageRas)
#rangeRas = np.copy(averageRas)

for r in range(0, 1500):
#for r in range(0, 2053): #Oahu
    print r
    for c in range(3600):
    #for c in range(2773): #Oahu
        if maxRunAvr[r][c] > -9999:
            accum = np.array([])
            runAverage = np.array([])
            for sim_yr in range(sim_first, sim_last + 1):
                #print sim_yr
                NetCDF_fn = NetCDF_fn1 + str(sim_yr) + '.nc'  # set input netcdf name
                f = netcdf.netcdf_file(NetCDF_fn, 'r')
                tmp = f.variables[nutrient][:, r, c].astype(np.float32)
                accum = np.append(accum, tmp)

            for i in range(accum.size-30): #calculate 30 days running average
                rangeWin = i + 30
                if rangeWin < accum.size-1:
                    tmpAver = np.mean(accum[i:rangeWin])
                else:
                    tmpAver = np.mean(accum[i:])

                runAverage = np.append(runAverage, tmpAver)

            maxRunAvr[r][c] = runAverage.max()
    #        stdRas[r][c] = accum.std()
    #        rangeRas[r][c] = accum.max() - accum.min()

#open and write the header to the output file
Output_fn = Output_fn0[:-3]+'maxRunAvr'+str(sim_first)+'-'+str(sim_last)+'.asc'
of1 = open(Output_fn, 'w')
of1.writelines(header)
maxRunAvr = maxRunAvr[::-1] #flip
np.savetxt(of1, maxRunAvr, fmt='%1.4f')
of1.close()

'''Output_fn = Output_fn0[:-3]+'Std'+str(sim_first)+'-'+str(sim_last)+'.asc'
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
'''