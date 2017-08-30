'''
Fast testing classes
This library contains the classes that can be used to test any algorithm without the GUI and runs fast. Note this uses the kursawe test.
@authors: Greg Henderson
'''
from __future__ import division
import kur_model
import dlsoo_mosa
import numpy
import random

def fon(x):
    rootn = len(x)**0.5
    f1 = 1 - numpy.exp(-sum([(i - 1/rootn)**2 for i in x]))
    f2 = 1 - numpy.exp(-sum([(i + 1/rootn)**2 for i in x]))
    return (f1, f2)

class measure:
    '''
    This is used as a basic measure class simular to the class used in the optimiser_util but simpler.
    '''
    def __init__(self, f):
        self.mean = f
        self.err = 0


class interactorFast:
    '''
    Simple interactor for kursawe made to be compatible with current get and set methods of interactors defined in dls_optimiser_util
    '''
    def __init__(self, pv, nParam):
        self.params = [1]*nParam
        self.param_var_groups = self.params
        self.measurement_vars = [1,1]
        self.pv = pv

    def set_ap(self, x):
        self.params = x

    def get_ap(self):
        return self.params

    def get_ar(self, addNoise = True):
        if addNoise:
            f = [0]*2
            for test in range(10):
                if self.pv == 'kur':
                    f1 = kur_model.kur(self.params)
                elif self.pv == 'fon':
                    f1 = fon(self.params)

                f1 = [random.gauss(i, abs(i)/40) for i in f1]
                f = [f[i] + f1[i] for i in range(2)]
            f = [i/10 for i in f]
        else:
            if self.pv == 'kur':
                f = kur_model.kur(self.params)
            elif self.pv == 'fon':
                f = fon(self.params)
        result = []
        for i in f:
            result.append(measure(i))

        return result
