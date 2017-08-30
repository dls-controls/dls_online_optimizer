from __future__ import division

import pkg_resources
from audioop import avg
pkg_resources.require('cothread')
pkg_resources.require('matplotlib==1.3.1')
import matplotlib.pyplot as plt
   
 #Stuff you need to import
from cothread.catools import caget, caput, ca_nothing
from cothread.cadef import CAException

import time
import matplotlib.pyplot as pyplot
from matplotlib import cm
import numpy

# SIMULATION CODE

values = [0, 0]
standard_dev = [0.1, 0.1]

def caput(address, value):
    global values
    global stds
    values[address] = value

def caget(address):
    global values
    global stds
    p = numpy.random.normal(values[0], standard_dev[0])
    q = numpy.random.normal(values[1], standard_dev[1])
    
    ret_res =  1 / (1 + numpy.sqrt((p - 5)**2 + (q - 5)**2))
    
    return ret_res
#-----------------------------------------------------

# This measure_funcs is slightly different to the previous one in measure_obj_func2
# in that it not only measures standard dev, but also takes in tuples rather than dictionaries

def measure_funcs(*measurements): # measurements is a collection of tuples, each of length 3, giving address, measurement count, and measurement delay
    function_count = len(measurements)
    counts = function_count * [0] 
    results = function_count * [0.0] # zeros for measurements to be taken
    std = function_count * [0.0] # zeros for std dev to be taken
    
    runs = function_count * [True] # list of run operations
    run = True #current run
    
    start_time = time.time() # start the timer
    
    while run:
        for i in range(function_count):
            if (time.time() - start_time) >= (counts[i] * measurements[i][2]): #make sure to leave enough time 
                if counts[i] < measurements[i][1]: #????
                    measurement = caget(measurements[i][0]) #get 'efficiency'
                    results[i] += measurement #add new measurement for mean to be calculated 
                    std[i] += measurement**2 #add squares of std for calculation later
                    counts[i] += 1 #increase count number
                else:
                    runs[i] = False #
        run = False
        for i in range(function_count):
            if runs[i]:
                run = True
    
    for i in range(function_count):
        results[i] = results[i] / counts[i] #mean results
        std[i] = std[i] / counts[i]
        std[i] = std[i] - results[i]**2
        std[i] = numpy.sqrt(std[i]) #final std
    
    return (results, std, counts) # Returns a tuple with the mean of each measurement, and a tuple with the std of each measurement




set_ca = ((0, 0.00001), (1, 0.00001)) # Address, delay
measure_ca = ('a', 10, 0.00001)
boundaries = ((0, 10), (0, 10))
point_count = (100, 100)

X = numpy.linspace(boundaries[0][0], boundaries[0][1], point_count[0])
Y = numpy.linspace(boundaries[1][0], boundaries[1][1], point_count[1])

x, y = numpy.meshgrid(X, Y)
results = numpy.zeros((point_count[0], point_count[1]))
stds = numpy.zeros((point_count[0], point_count[1]))

for a in range(point_count[0]):
    caput(set_ca[0][0], X[a])
    time.sleep(set_ca[0][1])
    print a
    for b in range(point_count[1]):
        caput(set_ca[1][0], Y[b])
        time.sleep(set_ca[1][1])
        
        measurement = measure_funcs(measure_ca)
        results[a][b] = measurement[0][0]
        stds[a][b] = measurement[1][0]



pyplot.figure()
pyplot.subplot(211)
pyplot.pcolormesh(x, y, results, cmap=cm.plasma)
pyplot.colorbar()

pyplot.subplot(212)
pyplot.pcolormesh(x, y, stds, cmap=cm.plasma)
pyplot.colorbar()

pyplot.show()
