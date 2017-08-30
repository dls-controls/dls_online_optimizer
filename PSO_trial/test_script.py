'''
Created on 10 Jul 2017

@author: qvi61384i
'''

import itertools
import operator

pareto_front = [[1,4],[2,3],[3,2],[4,1]]
swarm = [[1,4],[2,3],[0.5,3.5],[3,2],[4,1]]
def pareto_test(a,b):
    if all(a_i > b_i for (a_i,b_i) in zip(a,b)):
        return True #only condition for solution to be on front
    else:
        return False

def find_pareto_front(current_swarm):
    global pareto_front
    proposed_front = current_swarm + pareto_front
    print 'proposed_front is ',proposed_front
    for i in proposed_front:
        print 'front is now', proposed_front
        for j in proposed_front:
            print 'is', j, 'less than', i
            if pareto_test(j,i):
                print 'remove', j
                proposed_front.remove(j)
    proposed_front = sorted(proposed_front, key=operator.attrgetter('fit_best_i'))
    proposed_front = list(set(proposed_front))
    pareto_front = list(proposed_front)

find_pareto_front(swarm)
print pareto_front