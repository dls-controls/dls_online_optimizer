#------SIMPLE SIMULATION OF 2D PARAMETER SCAN------#

from __future__ import division

import pkg_resources
pkg_resources.require('numpy')
pkg_resources.require('matplotlib==1.3.1')

import numpy as np
import matplotlib.pyplot as plt
import time

#-------------------SIMULATION---------------------#

# define zero values+std for each address
values = [0, 0]
standard_dev = [0.1, 0.1]

# function that simulates caput from cothread (dls-python)
def caput(address, new_value):
    global values
    global std
    values[address] = new_value

# function that simulates caget from cothread (dls-python). Note: 'address' variable is not called but is representative of process variable (PV) called upon
def caget(address):
    global values
    global std
    p = np.random.normal(values[0], standard_dev[0])  # generate random 2D coordinates following a simple Gaussian distribution
    q = np.random.normal(values[1], standard_dev[1])
    
    result = 1 / (1 + np.sqrt((p - 5) ** 2 + (q - 5) ** 2))  # return function of generated point with peak at (5,5). This represents the objective/cost function
    return result

# function to measure a parameter setup multiple times and then takes averages.
def measure_objective(objective, measurement_count):
    
    result = measurement_count * [0.]
    std = measurement_count * [0.]
    
    # collect data
    i = 0
    while i < measurement_count:
        measurement = caget(objective)
        result[i] = measurement
        std[i] = measurement ** 2
        i += 1
        # time.sleep(0.000001)

    # calculate mean and standard deviation
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
    return (mean, standard_deviation)


# define PVs to vary and objective to measure (address, delay)
PVs = ((0, 0.0000001), (1, 0.0000001))
OBJECTIVE = ('CS-DI-XFER-01:LB-03-BR', 0.0000001)

#define search space
boundaries = ((0, 10), (0, 10))
point_count = (100, 100)

X = np.linspace(boundaries[0][0], boundaries[0][1], point_count[0])
Y = np.linspace(boundaries[1][0], boundaries[1][1], point_count[1])

x, y = np.meshgrid(X, Y)
results = np.zeros((point_count[0], point_count[1]))
stds = np.zeros((point_count[0], point_count[1]))

#scan search space
for a in range(point_count[0]):
    caput(PVs[0][0], X[a])
    #time.sleep(PVs[0][1])
    print 'a=', a
    for b in range(point_count[1]):
        caput(PVs[1][0], Y[b])
        time.sleep(PVs[1][1])
        measurement = measure_objective(OBJECTIVE[0], 10)
        results[a][b] = measurement[0]
        stds[a][b] = measurement[1]

#plot objective
plt.figure()
plt.subplot(211)
plt.title('LTB Injection efficiency')
plt.xlabel('LB-PC-VSTR-01:SETI')
plt.ylabel('LB-PC-VSTR-02:SETI')
plt.contourf(x, y, results.T)
plt.colorbar()

plt.subplot(212)
plt.title('LTB Injection efficiency standard deviation')
plt.xlabel('LB-PC-VSTR-01:SETI')
plt.ylabel('LB-PC-VSTR-02:SETI')
plt.contourf(x, y, stds.T)
plt.colorbar()

plt.subplots_adjust(hspace=0.4)
plt.show()
