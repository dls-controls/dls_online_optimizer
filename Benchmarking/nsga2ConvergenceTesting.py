'''
NSGA2 Convergence Testing
This is the script used to get the data for NSGA2 for benchmarking.
'''
from audioop import avg
import numpy
import csv
import time
import matplotlib
import matplotlib.pyplot as plot
import fastTestingClasses
import dlsoo_nsga2
import metrics
from usefulFunctions import frontReader

#initialise the test enviroment
interactor = fastTestingClasses.interactorFast('fon', 4)
settings_dict_short = {'pop_size': 25, 'pmut': 0.033333, 'pcross': 0.9, 'eta_m': 20, 'eta_c': 20, 'param_count': 4, 'result_count': 2, 'add_current_to_individuals': True, 'seed': time.time()}
genNums = range(1, 80, 2)
a_min_var = 4*[-4]
a_max_var = 4*[4]
metricData = [[i] for i in range(6)]

acturalFrontParams, actualFrontObjectives = frontReader('fonFront4.csv', 4)

#Now do the convergence test
for i in genNums:
    settings_dict_short['max_gen'] = i
    m = 6*[0]
    for j in range(50):
        optimiser = dlsoo_nsga2.optimiser(settings_dict = settings_dict_short, interactor = interactor, store_location = '', a_min_var = a_min_var, a_max_var = a_max_var)
        fronts = optimiser.optimise()
        domFrontParam = [list(k.x) for k in fronts[0]]
        domFrontObjectives = []
        for k in domFrontParam:
            interactor.set_ap(k)
            f = interactor.get_ar(False)
            domFrontObjectives.append([l.mean for l in f])
        m[0] += metrics.metric1(acturalFrontParams, domFrontParam)
        m[1] += metrics.metric2(domFrontParam, 0.5)
        m[2] += metrics.metric3(domFrontParam)
        m[3] += metrics.metric1(actualFrontObjectives, domFrontObjectives)
        m[4] += metrics.metric2(domFrontObjectives, 0.5)
        m[5] += metrics.metric3(domFrontObjectives)
    m = [float(l)/50 for l in m]
    for j in range(6):
        metricData[j].append(m[j])
    print 'Done: {0}'.format(i)

#File saving
f = open('nsga2ConvergenceDataF4NLong.csv', 'w')
wr = csv.writer(f)
x = [25*(1 + i) for i in genNums]

for i in range(len(x)):
    wr.writerow([x[i]] + [metricData[j][i+1] for j in range(len(metricData))])

f.close()

#Now plot the results
labels = ['Paramerter Space Metric1', 'Paramerter Space Metric2', 'Paramerter Space Metric3', 'Objective Space Metric1', 'Objective Space Metric2', 'Objective Space Metric3']

for i in range(6):
    plot.subplot(2,3, i + 1)
    plot.plot(x, metricData[i][1:])
    plot.xlabel('Number of measurements')
    plot.ylabel(labels[i])

plot.show()
