'''
MOPSO Convergence Testing
'''
from audioop import avg
import numpy
import csv
import time
import matplotlib
import matplotlib.pyplot as plot
import fastTestingClasses
import dlsoo_mopso
import metrics
from usefulFunctions import frontReader

#initialise the test enviroment
interactor = fastTestingClasses.interactorFast('fon', 4)
settings_dict_short = {'swarm_size': 50, 'inertia': 0.45, 'social_param': 1.0, 'cognitive_param': 2.0, 'add_current_to_individuals': True}
iterNums = range(1, 41)
a_min_var = 4*[-4]
a_max_var = 4*[4]
metricData = [[i] for i in range(6)]

acturalFrontParams, actualFrontObjectives = frontReader('fonFront4.csv', 4)

#Now do the convergence test
for i in iterNums:
    settings_dict_short['max_iter'] = i
    m = 6*[0]
    for j in range(50):
        print j
        optimiser = dlsoo_mopso.optimiser(settings_dict = settings_dict_short, interactor = interactor, store_location = '', a_min_var = a_min_var, a_max_var = a_max_var)
        fronts = optimiser.optimise()
        domFrontParam = [k[0] for k in fronts]
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
f = open('mopsoConvergenceDataF4NLong.csv', 'w')
wr = csv.writer(f)
x = [50*i for i in iterNums]

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
