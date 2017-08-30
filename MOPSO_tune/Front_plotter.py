'''
Created on 7 Aug 2017

@author: qvi61384
'''
import pkg_resources
pkg_resources.require('scipy')
pkg_resources.require('numpy')
pkg_resources.require('matplotlib')

import operator
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
import matplotlib.patches as pat


def virtual_pareto_points(x_pareto, y_pareto):


    coords = zip(x_pareto,y_pareto)
    coords.sort(key=operator.itemgetter(0))

    new_coords = []

    for i in range(len(coords)-1):
        new_coords.append(coords[i])
        imaginary_point = (coords[i+1][0],coords[i][1])
        new_coords.append(imaginary_point)

    new_coords.append(coords[-1])
    new_x = [x[0] for x in new_coords]
    new_y = [y[1] for y in new_coords]

    return new_x, new_y

def plot(store_location):

    file_name = "{0}/FRONTS/fronts.0".format(store_location)
    execfile(file_name)
    front = locals()['fronts'][0]

    x_vals = []
    y_vals = []
 
    for i in front: 
        x_vals.append(i[1][0])
        y_vals.append(i[1][1])
 
    px_vals = [x for (x, y) in sorted(zip(x_vals, y_vals))]
    py_vals = [y for (x, y) in sorted(zip(x_vals, y_vals))]
 
    plt.plot(px_vals, py_vals, color='b', marker='D', picker=5, linestyle='None')
 
    new_x, new_y = virtual_pareto_points(px_vals,py_vals)
    plt.plot(new_x, new_y, color='b', linestyle = '--')
 
 
    plt.xlabel('$f_1(x)$')
    plt.ylabel('$f_2(x)$')
    plt.title('Pareto Front of Kursawe Function')
    plt.grid()
 
 
    plt.savefig('{0}/plot.png'.format(store_location), bbox_inches='tight')      
    plt.show()
