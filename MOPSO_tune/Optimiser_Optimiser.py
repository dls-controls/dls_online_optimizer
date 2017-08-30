'''
Created on 7 Aug 2017

@author: qvi61384
'''

from __future__ import division
import csv

import pkg_resources
pkg_resources.require('scipy')
pkg_resources.require('numpy')
pkg_resources.require('matplotlib')

import MOPSO
import Metrics
import Test_Functions
import Front_plotter
import usefulFunctions
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
import matplotlib.patches as pat

def get_pareto_objectives(swarm):
    objectives = [particle[1] for particle in swarm]
    return objectives

def get_pareto_parameters(swarm):
    parameters = [particle[0] for particle in swarm]
    return parameters

#-----------------------------------------------------PERFORM ALGORITHM------------------------------#

iteration = 20
#bounds = [[0,1] for i in range(30)]                    #T1 + T2 + T3 bounds
#bounds = [[0,1]] + [[-5,5] for i in range(9)]          #T4
#bounds = [[0,1] for i in range(10)]                    #T6
bounds = [[-4,4] for i in range(3)]                    #Kursawe

# algorithm = MOPSO.MOPSO(swarm_size=50,
#                   functions=Test_Functions.T2,
#                   par_bounds=bounds,
#                   maxiter=iteration,
#                   inertia=0.4,
#                   cognitive_parameter=2.0, 
#                   social_parameter=2.0
#                   ) 
# 
# algorithm.optimise()
#-----------------------------------------------------NOW PLOT-----------------------------------------#

#Front_plotter.plot(store_location)

#------------------------------------------------------METRIC TESTING-----------------------------------#

#read csv file with analytic front
analytic_front = usefulFunctions.frontReader('analytic_front.csv')

analytic_objectives = analytic_front[1]
analytic_parameters = analytic_front[0]

####################   find optimal inertia    ######################

#inertia = np.linspace(0.0, 0.7, 100)
# metric_1 = []
# metric_2 = []
# metric_3 = []
# 
# for i in range(100):
#     
#     algorithm_run = MOPSO.MOPSO(swarm_size=50,
#                                 functions=Test_Functions.kursawe,
#                                 par_bounds=bounds,
#                                 maxiter=40,
#                                 inertia=inertia[i],
#                                 cognitive_parameter=2.0, 
#                                 social_parameter=2.0
#                                 )
#     
#     metric_1_to_be_averaged = []
#     metric_2_to_be_averaged = []
#     metric_3_to_be_averaged = []
#     
#     for j in range(8):
#         
#         print 'inertia number=', i
#         print 'average no.', j+1
#         
#         pareto_front = algorithm_run.optimise()
#         pareto_objectives = get_pareto_objectives(pareto_front)
#         
#         metric_1_result = Metrics.metric1(analytic_objectives, pareto_objectives)
#         metric_2_result = Metrics.metric2(pareto_objectives, 0.5)
#         metric_3_result = Metrics.metric3(pareto_objectives)
#         
#         metric_1_to_be_averaged.append(metric_1_result)
#         metric_2_to_be_averaged.append(metric_2_result)
#         metric_3_to_be_averaged.append(metric_3_result)
#     
#     metric_1_average = sum(metric_1_to_be_averaged)/8
#     metric_2_average = sum(metric_2_to_be_averaged)/8
#     metric_3_average = sum(metric_3_to_be_averaged)/8
#     
#     metric_1.append(metric_1_average)
#     metric_2.append(metric_2_average)
#     metric_3.append(metric_3_average)
# 
# print 'inertia', inertia
# print 'metric 1', metric_1
# print 'metric 2', metric_2
# print 'metric 3', metric_3
# 
# plt.subplot(311)
# plt.plot(inertia, metric_1, 'b')
# plt.xlabel('Particle Inertia')
# plt.ylabel('Metric 1')
# 
# plt.subplot(312)
# plt.plot(inertia, metric_2, 'b')
# plt.xlabel('Particle Inertia')
# plt.ylabel('Metric 2')
# 
# plt.subplot(313)
# plt.plot(inertia, metric_3, 'b')
# plt.xlabel('Particle Inertia')
# plt.ylabel('Metric 3')
# 
# plt.suptitle('MOPSO Metric Performance')
# #plt.savefig('RESULTS/inertia/plot.png', bbox_inches='tight')
# plt.show()




####################### COGNITIVE AND SOCIAL TUNING ##############################

# cognitive = np.linspace(0.0, 2.3, 30)
# social = np.linspace(0.0, 2.3, 30)
#  
# x, y = np.meshgrid(cognitive, social)
# metric_1 = np.zeros((30, 30))
# metric_2 = np.zeros((30, 30))
# metric_3 = np.zeros((30, 30))
#  
#  
# for a in range(30):
#      
#     for b in range(30):
#          
#         algorithm_run = MOPSO.MOPSO(swarm_size=50,
#                   functions=Test_Functions.kursawe,
#                   par_bounds=bounds,
#                   maxiter=40,
#                   inertia=0.5,
#                   cognitive_parameter=cognitive[a], 
#                   social_parameter=social[b]
#                   )
#         
#         metric_1_to_be_averaged = []
#         metric_2_to_be_averaged = []
#         metric_3_to_be_averaged = []
#         
#         for i in range(8):
#             
#             print 'cognitive =', cognitive[a]
#             print 'social =', social[b]
#             print 'average =', i+1
#             
#              
#             pareto_front = algorithm_run.optimise()
#             pareto_objectives = get_pareto_objectives(pareto_front)
#             
#             metric_1_result = Metrics.metric1(analytic_objectives, pareto_objectives)
#             metric_2_result = Metrics.metric2(pareto_objectives, 0.5)
#             metric_3_result = Metrics.metric3(pareto_objectives)
#             
#             metric_1_to_be_averaged.append(metric_1_result)
#             metric_2_to_be_averaged.append(metric_2_result)
#             metric_3_to_be_averaged.append(metric_3_result)
#         
#         metric_1_average = sum(metric_1_to_be_averaged)/8
#         metric_2_average = sum(metric_2_to_be_averaged)/8
#         metric_3_average = sum(metric_3_to_be_averaged)/8
#         
#         metric_1[a][b] = metric_1_average
#         metric_2[a][b] = metric_2_average
#         metric_3[a][b] = metric_3_average
# 
# 
# plt.subplot(311)
# plt.title('Metric 1')
# plt.xlabel('Cognitive parameter')
# plt.ylabel('Social Parameter')
# plt.contourf(x, y, metric_1.T)
# plt.colorbar()
# 
# plt.subplot(312)
# plt.title('Metric 2')
# plt.xlabel('Cognitive parameter')
# plt.ylabel('Social Parameter')
# plt.contourf(x, y, metric_2.T)
# plt.colorbar()
# 
# plt.subplot(313)
# plt.title('Metric 3')
# plt.xlabel('Cognitive parameter')
# plt.ylabel('Social Parameter')
# plt.contourf(x, y, metric_3.T)
# plt.colorbar()
# 
# plt.suptitle('MOPSO Metric Performance')
# plt.show()

############################# BENCHMARK DATA ############################ 




measurements = np.arange(50,2050,50)

iterations = np.arange(1,41,1)

print len(measurements) 
print len(iterations)

metric_1_objective = []
metric_2_objective = []
metric_3_objective = []
 
metric_1_parameter = []
metric_2_parameter = []
metric_3_parameter = []
 
for i in iterations:
     
    algorithm_run = MOPSO.MOPSO(swarm_size=50,
                                functions=Test_Functions.kursawe,
                                par_bounds=bounds,
                                maxiter=i,
                                inertia=0.5,
                                cognitive_parameter=1.5, 
                                social_parameter=2.0
                                )
      
    metric_1_obj_to_be_averaged = []
    metric_2_obj_to_be_averaged = []
    metric_3_obj_to_be_averaged = []
     
    metric_1_par_to_be_averaged = []
    metric_2_par_to_be_averaged = []
    metric_3_par_to_be_averaged = []
      
    for j in range(5):
          
        pareto_front = algorithm_run.optimise()
        pareto_objectives = get_pareto_objectives(pareto_front)
        pareto_parameters = get_pareto_parameters(pareto_front)
        
          
        metric_1_obj_result = Metrics.metric1(analytic_objectives, pareto_objectives)
        metric_2_obj_result = Metrics.metric2(pareto_objectives, 0.5)
        metric_3_obj_result = Metrics.metric3(pareto_objectives)
         
        metric_1_obj_to_be_averaged.append(metric_1_obj_result)
        metric_2_obj_to_be_averaged.append(metric_2_obj_result)
        metric_3_obj_to_be_averaged.append(metric_3_obj_result)
        
         
        metric_1_par_result = Metrics.metric1(analytic_parameters, pareto_parameters)
        metric_2_par_result = Metrics.metric2(pareto_parameters, 0.5)
        metric_3_par_result = Metrics.metric3(pareto_parameters)
          
        metric_1_par_to_be_averaged.append(metric_1_par_result)
        metric_2_par_to_be_averaged.append(metric_2_par_result)
        metric_3_par_to_be_averaged.append(metric_3_par_result)
        
      
    metric_1_obj_average = sum(metric_1_obj_to_be_averaged)/5
    metric_2_obj_average = sum(metric_2_obj_to_be_averaged)/5
    metric_3_obj_average = sum(metric_3_obj_to_be_averaged)/5
     
    metric_1_par_average = sum(metric_1_par_to_be_averaged)/5
    metric_2_par_average = sum(metric_2_par_to_be_averaged)/5
    metric_3_par_average = sum(metric_3_par_to_be_averaged)/5
      
    metric_1_objective.append(metric_1_obj_average)
    metric_2_objective.append(metric_2_obj_average)
    metric_3_objective.append(metric_3_obj_average)
 
    metric_1_parameter.append(metric_1_par_average)
    metric_2_parameter.append(metric_2_par_average)
    metric_3_parameter.append(metric_3_par_average)
      
f = open('MOPSOConvergenceData.csv', 'w')
wr = csv.writer(f)

for i in range(len(measurements)):
    wr.writerow([measurements[i]]
              + [metric_1_parameter[i]]
              + [metric_2_parameter[i]]
              + [metric_3_parameter[i]]
              + [metric_1_objective[i]]
              + [metric_2_objective[i]]
              + [metric_3_objective[i]])
f.close()
    

