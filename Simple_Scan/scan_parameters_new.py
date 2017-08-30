#---------SIMPLE 2D PARAMETER SCAN OF MACHINE------------------------
from __future__ import division
import os

#import modules from dls-python in order to 'talk' to the machine
import pkg_resources
pkg_resources.require('cothread')
pkg_resources.require('matplotlib==1.3.1')
pkg_resources.require('numpy')
import matplotlib.pyplot as plt
import numpy as np
import time
import datetime

import cothread
from cothread.catools import caget, caput, ca_nothing
from cothread.cadef import CAException

#---------FUNCTION THAT COLLECTS OBJECTIVE DATA FROM THE MACHINE------ 
def measure_objective(objective, measurement_count, measurement_delay):
    """
    objective: address of objective function 
    measurement_count: number of times the objective is to be measured in order for the mean to be calculated 
    
    Returns tuple of measurement mean, standard deviation and number of data points used to calculate these, as some may have been discarded.
    """
    
    result = measurement_count * [0.]
    std = measurement_count * [0.]
    
    # collect data
    i = 0
    while i < measurement_count:
        measurement = caget(objective)
        result[i] = measurement
        std[i] = measurement ** 2
        i += 1
        #time.sleep(measurement_delay)

    #calculate mean and standard deviation
    mean = sum(result) / measurement_count
    standard_deviation = (sum(std) / measurement_count) - mean ** 2
    standard_deviation = np.sqrt(standard_deviation)

    #detect and remove any outliers
    anomaly = False
    for i in result:
        if (abs(mean - i)) > 2 * standard_deviation:
            anomaly = True
            index = result.index(i)
            result.remove(i)
            del std[index]

    #recalculate mean if outliers are found
    if anomaly == True:
        mean = sum(result) / len(result)
        standard_deviation = (sum(std) / len(result)) - mean ** 2
        standard_deviation = np.sqrt(standard_deviation)
        
    return (mean, standard_deviation, len(result))

#-----------FUNCTIONS FOR WRITING DATA FILES FROM THE MACHINE-------------#

def write_2d_array(directory, address, data):
    """
    directory: name of new directory to be made
    address: name of new file to be written
    data: linspace of meshgrid which forms one parameter 
    """
    
    #create new directory
    newpath = 'parameter_scan_OUTPUT/{0}'.format(directory)
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    new_file = open(address, 'w+')
    
    #NOTE: file starts with data about size of parameter space. I.e. the start of the file will be 2,3,... 
    #this means the data is of the size 2x3
    new_file.write('{0},{1},'.format(data.shape[0],data.shape[1]))
    
    #now write the data extracted from the PV
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            new_file.write('{0}'.format(data[i][j]))
            new_file.write(',')
    
    new_file.close()

#----------CHOOSE PVS AND OBJECTIVES---------#

#PVs = (('LB-PC-VSTR-05:SETI', 1), ('LB-PC-VSTR-06:SETI', 1)) #address, delay time
PVs = (('LB-PC-VSTR-01:SETI', 0.5), ('LB-PC-VSTR-02:SETI', 0.5)) #address, delay time

#objective = ('LB-DI-EBPM-03:FT:Y', 5, 0.2, 10) #address, delay time, sample size
objective = ('CS-DI-XFER-01:LB-03-BR', 5, 0.2, 10) #address, delay time, sample size

#----------------RUN ALGORITHM---------------#
#define search space
initial_PVs = [caget(PVs[0][0]),caget(PVs[1][0])]
boundaries = ((initial_PVs[0] - 0.5, initial_PVs[0] + 0.5), (initial_PVs[1] - 0.5, initial_PVs[1] + 0.5))
search_space_shape = (10, 10)

X = np.linspace(boundaries[0][0], boundaries[0][1], search_space_shape[0])
Y = np.linspace(boundaries[1][0], boundaries[1][1], search_space_shape[1])

x, y = np.meshgrid(X, Y)
results = np.zeros((search_space_shape[0], search_space_shape[1]))
stds = np.zeros((search_space_shape[0], search_space_shape[1]))

#scan search space
for a in range(search_space_shape[0]):
    #caput(PVs[0][0], X[a])
    #time.sleep(PVs[0][1])
    print 'a=', a
    for b in range(search_space_shape[1]):
        #caput(PVs[1][0], Y[b])
        #time.sleep(PVs[1][1])
        measurement = measure_objective(objective[0], objective[1], objective[2])
        results[a][b] = measurement[0]
        stds[a][b] = measurement[1]
print results
#------------------SET MACHINE BACK TO INITIAL CONDITIONS-----------------------------#
#caput(PVs[0][0], initial_PVs[0])
#caput(PVs[1][0], initial_PVs[1])
#cothread.Sleep(1)
#------------------WRITE FILES WITH RAW DATA FROM THE MACHINE-------------------------#
current_time_string = datetime.datetime.fromtimestamp(time.time()).strftime('%d.%m.%Y_%H.%M.%S')
write_2d_array(current_time_string,'./parameter_scan_OUTPUT/{0}/x - {1}.data'.format(current_time_string, PVs[0][0]), x)
write_2d_array(current_time_string,'./parameter_scan_OUTPUT/{0}/y - {1}.data'.format(current_time_string, PVs[1][0]), y)
write_2d_array(current_time_string,'./parameter_scan_OUTPUT/{0}/results - {1}.data'.format(current_time_string, objective[0]), results)
write_2d_array(current_time_string,'./parameter_scan_OUTPUT/{0}/stds - {1}.data'.format(current_time_string, objective[0]), stds)
#------------------PLOT OBJECTIVE-----------------------------------------------------#
plt.figure()
plt.subplot(211)
plt.title('{0}'.format(objective[0]))
plt.xlabel('{0}'.format(PVs[0][0]))
plt.ylabel('{0}'.format(PVs[1][0]))
plt.pcolormesh(x, y, results)
plt.colorbar()

plt.subplot(212)
plt.title('{0} standard deviation'.format(objective[0]))
plt.xlabel('{0}'.format(PVs[0][0]))
plt.ylabel('{0}'.format(PVs[1][0]))
plt.pcolormesh(x, y, stds)
plt.colorbar()

plt.subplots_adjust(hspace=0.4)
plt.show()