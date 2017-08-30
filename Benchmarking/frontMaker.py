'''
Front Maker
Generate a large number of points on the kursawe pareto front
'''

import numpy
import csv
import matplotlib
import matplotlib.pyplot as plot
from mpl_toolkits.mplot3d import Axes3D
import fastTestingClasses
import dlsoo_mosa
import metrics

#initialise the test enviroment
interactor = fastTestingClasses.interactorFast('fon', 4)
settings_dict_long = {'noAneals': 20000, 'noIterations': 20, 'passInTempDrop': 4*[0.9], 'passOutTempDrop': 2*[0.87], 'failDropCount': 1, 'objCallStop': 100000000000, 'anealPlot': 10000000000, 'add_current_to_individuals': True, 'dumpFlag': False}
a_min_var = 4*[-4]
a_max_var = 4*[4]

#inital long run
optimiser = dlsoo_mosa.optimiser(settings_dict = settings_dict_long, interactor = interactor, store_location = '', a_min_var = a_min_var, a_max_var = a_max_var)
optimiser.optimise()
acturalFrontParams = optimiser.domFrontParam
actualFrontObjectives = optimiser.domFrontObjectives
f = open('fonFront4.csv', 'w')
wr = csv.writer(f)

for x, y in zip(acturalFrontParams, actualFrontObjectives):
    wr.writerow(x + y)

f.close()

#plotting
y1 = [i[0] for i in actualFrontObjectives]
y2 = [i[1] for i in actualFrontObjectives]

plot.scatter(y1, y2)
plot.xlabel('Objective 1')
plot.ylabel('Objective 2')
plot.show()
