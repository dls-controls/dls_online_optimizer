'''
Created on 7 Aug 2017

@author: qvi61384
'''
from __future__ import division
import pkg_resources
pkg_resources.require('scipy')
pkg_resources.require('numpy')
from scipy import spatial

#front = [[1,5],[2,3],[3,0],[4,-2]]
front = [[1,1], [2,2]]

def Normalised_front(front):

    front_x = [i[0] for i in front]
    front_y = [i[1] for i in front]

    max_x = max(front_x)
    max_y = max(front_y)
    
    min_x = min(front_x)
    min_y = min(front_y)

    x_norm = [(i-min_x)/(max_x-min_x) for i in front_x]
    y_norm = [(i-min_y)/(max_y-min_y) for i in front_y]

    front_norm = zip(x_norm,y_norm)
    return front_norm


def density_estimator(front):
    
    if len(front) < 2:
        return []
    
#     swarm_size = len(front)
#     normalised_front = Normalised_front(front)
#     kd_tree = spatial.KDTree(normalised_front)
#     density = [len(kd_tree.query_ball_point(x=i, r=0.5))-1 for i in normalised_front]
    swarm_size = 3
    density = [2,3,1]
    density_sum = sum(density)
    inv_density = [density_sum-i for i in density]
    inv_density_size = sum(inv_density)
    roulette_wheel = [inv_density[0]/inv_density_size]
    for i in range(1,swarm_size):
        cumulative_prob = roulette_wheel[i-1] + inv_density[i]/inv_density_size
        roulette_wheel.append(cumulative_prob)
    print roulette_wheel

density_estimator(front)
    