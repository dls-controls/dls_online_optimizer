from __future__ import division

import pkg_resources
from audioop import avg
pkg_resources.require('cothread')
pkg_resources.require('matplotlib==1.3.1')
pkg_resources.require('numpy')
import matplotlib.pyplot as pyplot
import numpy

# Stuff you need to import
from cothread.catools import caget, caput, ca_nothing
from cothread.cadef import CAException
import cothread

import time
import datetime
import math
#import matplotlib.pyplot as pyplot
#import numpy



# SIMULATION CODE
'''
values = [10, 4]
standard_dev = [1, 1]

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
'''








#-----------------------------------------------------

# This measure_funcs is slightly different to the previous one in measure_obj_func2
# in that it not only measures standard dev, but also takes in tuples rather than dictionaries
def measure_funcs(*measurements): # measurements is a collection of tuples, each of length 3, giving address, measurement count, and measurement delay
    function_count = len(measurements)
    counts = function_count * [0]
    results = function_count * [0.0]
    std = function_count * [0.0]
    
    runs = function_count * [True]
    run = True
    
    start_time = time.time()
    
    while run:
        for i in range(function_count):
            if (time.time() - start_time) >= (counts[i] * measurements[i][2]):
                if counts[i] < measurements[i][1]:
                    measurement = caget(measurements[i][0])
                    results[i] += measurement
                    std[i] += measurement**2
                    counts[i] += 1
                else:
                    runs[i] = False
        run = False
        for i in range(function_count):
            if runs[i]:
                run = True
    
    for i in range(function_count):
        results[i] = results[i] / counts[i]
        std[i] = std[i] / counts[i]
        std[i] = std[i] - results[i]**2
        std[i] = numpy.sqrt(std[i])
    
    return (results, std, counts) # Returns a tuple with the mean of each measurement, and a tuple with the std of each measurement

def write_2d_array(address, data):
    write_file = open(address, 'w+')
    
    write_file.write('{0}'.format(data.shape[0]))
    write_file.write('-')
    write_file.write('{0}'.format(data.shape[1]))
    write_file.write('=')
    
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            write_file.write('{0}'.format(data[i][j]))
            write_file.write(',')
        
        #write_file.write(';')
    
    write_file.close()

def read_2d_array(address):
    read_file = open(address, 'r')
    
    content = read_file.read()
    
    width = 0
    height = 0
    
    run = True
    current = ''
    stage = '/'
    i = 0
    
    while run:
        if stage == '/':
            if content[i] == '-':
                width = int(current)
                current = ''
                stage = '-'
            else:
                current += content[i]
        elif stage == '-':
            if content[i] == '=':
                height = int(current)
                current = ''
                stage = '='
                run = False
            else:
                current += content[i]
        
        i += 1
    
    data = numpy.zeros((width, height))
    
    run = True
    x = 0
    y = 0
    
    for x in range(width):
        for y in range(height):
            run = True
            
            while run:
                if content[i] == ',':
                    data[x, y] = current
                    run = False
                    current = ''
                else:
                    current += content[i]
                
                i += 1
            
    
    read_file.close()
    return data


#set_ca = (('LB-PC-VSTR-05:SETI', 1), ('LB-PC-VSTR-06:SETI', 1)) # Address, delay
set_ca = (('LB-PC-VSTR-01:SETI', 0.5), ('LB-PC-VSTR-02:SETI', 0.5)) # Address, delay
#measure_ca = ('CS-DI-XFER-01:LB-03-BR', 5, 0.2) # Address, number, delay
measure_ca = ('LB-DI-EBPM-03:FT:Y', 5, 0.2) # Address, number, delay

# Read initial configuration
initial = [0, 0]
initial[0] = caget(set_ca[0][0])
initial[1] = caget(set_ca[1][0])

boundaries = ((initial[0] - 0.5, initial[0] + 0.5), (initial[1] - 0.5, initial[1] + 0.5))
point_count = (2, 2)

X = numpy.linspace(boundaries[0][0], boundaries[0][1], point_count[0])
Y = numpy.linspace(boundaries[1][0], boundaries[1][1], point_count[1])

x, y = numpy.meshgrid(X, Y)
results = numpy.zeros((point_count[0], point_count[1]))
stds = numpy.zeros((point_count[0], point_count[1]))

for a in range(point_count[0]):
    #caput(set_ca[0][0], X[a])
    #caput(set_ca[1][0], Y[0])
    print 'Set {0} to {1}'.format(set_ca[0][0], X[a])
    cothread.Sleep(set_ca[0][1])    

    for b in range(point_count[1]):
        #caput(set_ca[1][0], Y[b])
        print 'Set {0} to {1}'.format(set_ca[1][0], Y[b])
        cothread.Sleep(set_ca[1][1])
        
        measurement = measure_funcs(measure_ca)
        results[a][b] = measurement[0][0]
        stds[a][b] = measurement[1][0]

current_time_string = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d %H_%M_%S')
write_2d_array('x {0} - {1}.data'.format(current_time_string, set_ca[0][0]), x)
write_2d_array('y {0} - {1}.data'.format(current_time_string, set_ca[1][0]), y)
write_2d_array('results {0} - {1} - {2}.data'.format(current_time_string, set_ca[0][0], set_ca[1][0]), results)
write_2d_array('stds {0} - {1} - {2}.data'.format(current_time_string, set_ca[0][0], set_ca[1][0]), stds)

#rx = read_2d_array('x.data')
#ry = read_2d_array('y.data')
#rres = read_2d_array('results.data')
#rstds = read_2d_array('stds.data')


#Set back to initial position
#caput(set_ca[0][0], initial[0])
#caput(set_ca[1][0], initial[1])
cothread.Sleep(1)


pyplot.figure()
pyplot.subplot(211)
pyplot.pcolormesh(x, y, results)
pyplot.colorbar()
pyplot.xlabel(set_ca[0][0])
pyplot.ylabel(set_ca[1][0])

pyplot.subplot(212)
pyplot.pcolormesh(x, y, stds)
pyplot.colorbar()
pyplot.xlabel(set_ca[0][0])
pyplot.ylabel(set_ca[1][0])

pyplot.show()