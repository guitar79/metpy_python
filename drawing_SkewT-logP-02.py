# Copyright (c) 2015,2016,2017 MetPy Developers.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""
=================
Advanced Sounding
=================

Plot a sounding using MetPy with more advanced features.

Beyond just plotting data, this uses calculations from `metpy.calc` to find the lifted
condensation level (LCL) and the profile of a surface-based parcel. The area between the
ambient profile and the parcel profile is colored as well.

conda install xarray=0.12.1

#https://unidata.github.io/MetPy/latest/api/generated/metpy.calc.html

"""

import matplotlib.pyplot as plt
from glob import glob
import os
import numpy as np
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import metpy.calc as mpcalc
#from metpy.cbook import get_test_data
#from metpy.plots import add_metpy_logo, SkewT
from metpy.plots import SkewT
from metpy.units import units

#%%
add_log = True
if add_log == True :
    log_file = 'metpy_python.log'
    err_log_file = 'metpy_python_err.log'
    
def write_log(log_file, log_str):
    with open(log_file, 'a') as log_f:
        log_f.write(log_str+'\n')
    return print (log_str)
#for checking time
cht_start_time = datetime.now()
def print_working_time():
    working_time = (datetime.now() - cht_start_time) #total days for downloading
    return print('working time ::: %s' % (working_time))

#%%
###########################################
# Upper air data can be obtained using the siphon package, but for this example we will use
# some of MetPy's sample data.
dir_name = '../rawin_data/47138/'
save_dir_name = 'skew_T-log_P-diagram/'

if not os.path.exists(dir_name+save_dir_name):
    os.makedirs(dir_name+save_dir_name)
    print ('*'*80)
    print (dir_name+save_dir_name, 'is created')
else :
    print ('*'*80)
    print (dir_name+save_dir_name, 'is exist')
    
filename = 'UPPER_SONDE_47122_ALL_2018_2018_2019.csv'

#%%
for fullname in sorted(glob(os.path.join(dir_name, '*.csv'))):
    fullname_el = fullname.split('\\')
    filename = fullname_el[-1]
    filename_el = filename.split('_')
    obs_year = int(filename_el[-3])

    #지점,일시(UTC),기압(hPa),고도(gpm),기온(°C),이슬점온도(°C),풍향(deg),풍속(knot),지상 FLAG(null),권계면 FLAG(null),최대풍 FLAG(null)
    df = pd.read_csv(dir_name+filename, skiprows=1, sep=',', header=None, index_col=0,
                       names = ['site', 'time', 'pressure', 'height', 'temperature', 'dewpoint', 'direction', 'speed', 'FLAG1', 'FLAG2', 'FLAG3'],
                       skipfooter=1, engine='python')
    
    df['u_wind'], df['v_wind'] = mpcalc.wind_components(df['speed'],
                                                        np.deg2rad(df['direction']))
    #%%
    # Drop any rows with all NaN values for T, Td, winds
    #df = df.dropna(subset=('temperature', 'dewpoint', 'direction', 'speed', 'u_wind', 'v_wind'), how='all').reset_index(drop=True)
    df = df.dropna(subset=('temperature', 'dewpoint'), how='all').reset_index(drop=True)
    
    #%%
    # Rows that do not meet the condition alpha + num are eliminated
    s_start_date = datetime(obs_year, 1, 1) #convert startdate to date type
    s_end_date = datetime(obs_year, 12, 31)
    
    date1 = s_start_date
    selected_times = []
    while date1 < s_end_date : 
        date1_strf = date1.strftime('%Y-%m-%d %H:%M')
        selected_times.append(date1_strf)
        date1 = date1 + relativedelta(hours=12)
    
    #%%
    for selected_time in selected_times[0:1] :
        print(selected_time)
        
        try : 
            f = lambda s: selected_time in s
            ids  = df['time'].apply(f)
            df_selected_time = df[ids]
            
            #df_selected_time = df_selected_time.dropna()
            df_selected_time = df_selected_time.sort_values('pressure', ascending=False)
            print(df_selected_time)
            
            df_selected_time.to_csv(r'{0}{1}{2}_{3}.csv'.format(dir_name, save_dir_name, filename_el[-5], selected_time[:13]))
            ###########################################
            # We will pull the data out of the example dataset into individual variables and
            # assign units.
            
            p = df_selected_time['pressure'].values * units.hPa
            T = df_selected_time['temperature'].values * units.degC
            Td = df_selected_time['dewpoint'].values * units.degC
            wind_speed = df_selected_time['speed'].values * units.knots
            wind_dir = df_selected_time['direction'].values * units.degrees
            u, v = mpcalc.wind_components(wind_speed, wind_dir)
        
            ###########################################
            # Create a new figure. The dimensions here give a good aspect ratio.
            
            fig = plt.figure(figsize=(10, 15))
            #add_metpy_logo(fig, 115, 100)
            skew = SkewT(fig, rotation=45)
            
            # Plot the data using normal plotting functions, in this case using
            # log scaling in Y, as dictated by the typical meteorological plot
            skew.plot(p, T, 'r')
            skew.plot(p, T, 'ro', markersize=8, fillstyle='none')
            skew.plot(p, Td, 'g', linestyle='--')
            skew.plot(p, Td, 'g^', markersize=8, fillstyle='none')
            
            skew.plot_barbs(p, u, v)
            skew.ax.set_ylim(1050, 100)
            skew.ax.set_xlim(-50, 60)
            
            # Calculate LCL height and plot as black dot
            lcl_pressure, lcl_temperature = mpcalc.lcl(p[0], T[0], Td[0])
            skew.plot(lcl_pressure, lcl_temperature, 'ko', markerfacecolor='black')
            
            plt.text(10, 1400, 'pressure of the LCL : {0:.0f}'.format(lcl_pressure), horizontalalignment='left', verticalalignment='center', fontsize=12)
            plt.text(13.3, 1500, 'temerature of the LCL : {0:.0f}'.format(lcl_temperature), horizontalalignment='left', verticalalignment='center', fontsize=12)
        
            # Calculate full parcel profile and add to plot as black line
            prof = mpcalc.parcel_profile(p, T[0], Td[0]).to('degC')
            skew.plot(p, prof, 'k', linewidth=2)
            
            # Shade areas of CAPE and CIN
            skew.shade_cin(p, T, prof)
            skew.shade_cape(p, T, prof)
            
            # An example of a slanted line at constant T -- in this case the 0
            # isotherm
            skew.ax.axvline(0, color='c', linestyle='-', linewidth=1)
            for i in range(23) :
                for j in range(2,9,2) :
                    skew.ax.axvline(i*10-160+j, color='c', linestyle='--', linewidth=0.3)
                    #print (i*10-40+j)
            
            # Add the relevant special lines
            skew.plot_dry_adiabats(color='green', linestyle='-')
            #skew.plot_dry_adiabats([1, 2], color='green', linestyle='-', linewidth=1)
            skew.plot_moist_adiabats(color='brown', linestyle='-')
            skew.plot_mixing_lines(color='blue', linestyle='--', linewidth=0.3)
            
            plt.title('skew T log p diagram', fontsize=22)
            
            fig.savefig('{0}{1}{2}_{3}.png'.format(dir_name, save_dir_name, filename_el[-5], selected_time[:13]),
                dpi=None, facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None, metadata=None)
            
            # Show the plot
            plt.show()   
        
        except Exception as err :
            write_log(err_log_file, '{4} ::: {0} with {1}{2} on {3}'.format(err, dir_name, filename, selected_time[:13], datetime.now()))