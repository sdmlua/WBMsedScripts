"""
Created on Thu Oct 17 16:51:54 2013
@author:Sagy Cohen, Uni of Alabama
Calculates long-term mean raster layer (ESRI ASCII) for the WBMsed model output layers (NetCDF)
"""
import scipy
import numpy
from numpy import *
from scipy.io import netcdf

sim_first = 1990
sim_last = 2019
interval = (sim_last-sim_first)+1
#nutrient = 'BedloadFlux'
#nutrientList = ['SedimentFlux','Discharge,BedloadFlux,RiverbedVelocityMean,ParticleSize]

NetCDF_fn1= r'/Volumes/Pegasus32 R6/Data3/Oct27_2021_4p4p1/BedloadFlux/Global_BedloadFlux_4p4p1+Dist_06min_aTS'
#r'/media/scohen2/Data/Data3/Dec20_2018_Bedload/{0}/Annual/Global_{0}_NewQbf+Dist_06min_aTS'.format(nutrient)
             #/media/scohen2/Data/Data3/Dec20_2018_Bedload/bedloadflux/RiverSlope2p0+Prist/06min/Annual/Global_bedloadflux_RiverSlope2p0+Prist_06min_aTS1980.nc

Output_fn0 = NetCDF_fn1

#set the output ASCII file header
header=['ncols  3600\n']
header.append('nrows  1500\n')
#header=['ncols  720\n']# % 30min
#header.append('nrows  360\n')# % 30min
header.append('xllcorner -180\n')
header.append('yllcorner -60\n')
header.append('cellsize  0.1\n')
#header.append('cellsize  0.5\n')# %30min
header.append('NODATA_value  -9999\n')

'''#Oahu 30m
header=['ncols  2773\n']
header.append('nrows  2053\n')
header.append('xllcorner -158.40027777733\n')
header.append('yllcorner 21.22999999938\n')
header.append('cellsize  0.000277777778\n') #01sec (30m)
header.append('NODATA_value  -9999\n')
'''
count = 0
for sim_yr in range(sim_first,sim_last+1):
    first=(sim_first+count)
    if first > sim_last:
        break
    last=first+interval
    if last>sim_last:
        last=sim_last
   # open and write the header to the output file         
    Output_fn = Output_fn0+str(first)+'-'+str(last)+'.asc'
    of= open(Output_fn,'w')
    of.writelines(header)
    
#read loop     
    for yr in range(first,last+1):
        print(yr)
        NetCDF_fn=NetCDF_fn1+str(yr)+'.nc'  # set input netcdf name          
        f = netcdf.netcdf_file(NetCDF_fn,'r')
        tmp= f.variables[f.subject.decode()][:]
        if yr==first:
            NetCDFQ = [tmp]
        else:
            NetCDFQ.append(tmp)
        f.close

    means=numpy.mean(NetCDFQ,axis=0)
    out=means[0,:,:]
    #[-9999 if x=='inf' else x for x in out]
    out=out[::-1] #flip
    tmps=(isinf(out))*1
    out[tmps==1]=-9999.0
    tmps=(isnan(out))*1
    out[tmps==1]=-9999.0
   # pcolor(out, cmap='RdBu', vmin=0, vmax=1000)
    savetxt(of,out,fmt='%f')
    #of.writelines(format(out))
    of.close()
    count=count+interval+1
    #xx=f.variables['SedimentFlux'][0,39,-100]
    print('Done!')