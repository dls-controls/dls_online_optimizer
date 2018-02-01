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


def save_details_files(start_time, end_time, store_address):
    """
    saves details of optimisation in txt file using functions in the algorithm file and in dls_optimiser_util.py
    """
    f = file("{0}/algo_details.txt".format(store_address), "w")
    f.write(optimiser.save_details_file())

    f = file("{0}/inter_details.txt".format(store_address), "w")
    f.write(interactor.save_details_file())

    f = file("{0}/controller_details.txt".format(store_address), "w")
    f.write("Controller\n")
    f.write("==========\n\n")

    f.write("Start time: {0}-{1}-{2} {3}:{4}:{5}\n".format(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute, start_time.second))
    f.write("End time: {0}-{1}-{2} {3}:{4}:{5}\n".format(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute, end_time.second))



def run_optimisation(params):
    """
    initialises progress windows and calls on the the optimisation to begin susing function below
    """
    global final_plot_frame
    print "Lets go!"

    progress_frame.initUi()
    algorithm_settings_window.withdraw()

    params.initial_settings = interactor.get_mp()

    progress_window.deiconify()
    progress_window.grab_set()
    cothread.Spawn(optimiserThreadMethod)


def optimiserThreadMethod(params):
    global final_plot_frame
    
    params.initial_measurements = interactor.get_mr()
    
    #prepare folder in store_address to save fronts
    if not os.path.exists('{0}/FRONTS'.format(params.store_address)):
        os.makedirs('{0}/FRONTS'.format(params.store_address))
        
    ###NOW ACTUALLY CALL THE OPTIMISE FUNCTION WITHIN THE ALGORITHM FILE###   
    start_time = time.time()   #START
    params.optimiser.optimise()       #OPTIMISING...
    params.keepUpdating = False       
    end_time = time.time()     #STOP 

    #now save details for later reference by various code (results plotting, post_analysis etc..)
    interactor.set_mp(params.initial_settings)
    save_details_files(datetime.datetime.fromtimestamp(start_time),
            datetime.datetime.fromtimestamp(end_time),
            params.store_address)
    
    if not os.path.exists('{0}/PARAMETERS'.format(params.store_address)):
        os.makedirs('{0}/PARAMETERS'.format(params.store_address))
        
    if not os.path.exists('{0}/RESULTS'.format(params.store_address)):
        os.makedirs('{0}/RESULTS'.format(params.store_address))
    
    #save parameters and objectives as Pickle objects
    for i in range(len(params.parameters)):
        usefulFunctions.save_object(params.parameters[i], '{0}/PARAMETERS/parameter_{1}'.format(params.store_address, i))
    for i in range(len(params.results)):
        usefulFunctions.save_object(params.results[i], '{0}/RESULTS/result_{1}'.format(params.store_address, i))
    
    #save signconverter 
    signConverter_file = open("{0}/signConverter.txt".format(params.store_address), 'w')
    signConverter_file.write(str(params.signConverter))
    signConverter_file.close()
    
    #save the mapping method between algorithm parameters to machine parameters
    ap_to_mp_mapping_file = open("{0}/ap_to_mp_mapping_file.txt".format(params.store_address), 'w')
    ap_to_mp_mapping_file.write(interactor.string_ap_to_mp_store())
    ap_to_mp_mapping_file.close()

    #By this point, the algorithm has finished the optimisation, and restored the machine

    #close progress window
    progress_window.grab_release()
    progress_window.withdraw()
    
    #show the final plot windows
    ar_labels = [mrr.ar_label for mrr in results]
    final_plot_frame = optimiser_wrapper.import_algo_final_plot(final_plot_window,
            point_frame.generateUi, ar_labels, params.signConverter,
            initial_config=params.initial_measurements)
    final_plot_frame.initUi()
    final_plot_window.deiconify()



if __name__ == '__main__':

    parameters = config.Parameters()

    g = gui.Gui(OPTIMISERS, parameters)

    #start everything
    g.start()
