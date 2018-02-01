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
print 'Welcome to DLS-OnlineOptimiser'
print 'Loading...'
print 'Initialling setup windows...'

import pkg_resources
from audioop import avg
pkg_resources.require('cothread')
pkg_resources.require('matplotlib')
pkg_resources.require('numpy')
pkg_resources.require('scipy')

import Tkinter
import os
import time
import datetime
import pickle
import cothread

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.cm as cm

from dlsoo import config, gui, util, usefulFunctions


OPTIMISERS = {
    'Multi-Objective Particle Swarm Optimiser (MOPSO)': 'mopso',
    'Multi-Objective Simulated Annealing (MOSA)': 'mosa',
    'Multi-Objective Non-dominated Sorting Genetic Algorithm (NSGA-II)': 'nsga2',
    'Single-Objective Robust Conjugate Direction Search (RCDS)': 'rcds'
    }


if __name__ == '__main__':

    parameters = config.Parameters()

    g = gui.Gui(OPTIMISERS, parameters)

    #start everything
    g.start()
