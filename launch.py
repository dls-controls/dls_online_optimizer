'''
DLS-OnlineOptimiser: A flexible online optimisation package for use on the Diamond machine.
Version 2  2017-07-04
@authors: David Obee, James Rogers, Greg Henderson and Gareth Bird

IMPORTANT KEY:
        ARs: Algorithm results (objectives)
        APs: Algorithm parameters
        MRs: Machine results (objectives)
        MPs: Machine parameters

'''
from __future__ import division
import pkg_resources
pkg_resources.require('cothread')
pkg_resources.require('matplotlib')
pkg_resources.require('numpy')
pkg_resources.require('scipy')

import matplotlib
matplotlib.use("TkAgg")

from dlsoo import config, gui


OPTIMISERS = {
    'Multi-Objective Particle Swarm Optimiser (MOPSO)': 'mopso',
    'Multi-Objective Simulated Annealing (MOSA)': 'mosa',
    'Multi-Objective Non-dominated Sorting Genetic Algorithm (NSGA-II)': 'nsga2',
    'Single-Objective Robust Conjugate Direction Search (RCDS)': 'rcds'
    }


if __name__ == '__main__':
    print 'Welcome to DLS-OnlineOptimiser'
    print 'Loading...'
    print 'Initialling setup windows...'

    parameters = config.Parameters()

    g = gui.Gui(OPTIMISERS, parameters)

    g.start()
