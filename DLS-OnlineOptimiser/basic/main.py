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

#----------------------------------------------------IMPORTS--------------------------------------------------------#


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

import sys
import csv
import Tkinter
import ttk
import tkFileDialog
import tkMessageBox
import os
import time
import datetime
import imp
import pickle
import cothread

import numpy
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.cm as cm

import dls_optimiser_util as util
import dls_optimiser_plot as plot

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output)


#---------------------------------------GLOBAL VARIABLES AND ALGORITHM SETUP SPACE-------------------------------------------------#

#The two classes below are for simulated interaction and machine interaction respectively.

class modified_interactor1(util.sim_machine_interactor_bulk_base):
    """
    This interactor is the for a simulation
    """
    def mr_to_ar(self, mrs):
        #converts a set of machine results to algorithm results
        ars = []

        mr_to_ar_sign = [mrr.mr_to_ar_sign for mrr in results]
        for mr, sign in zip(mrs, mr_to_ar_sign):
            if sign == '+':
                ars.append(mr)
            elif sign == '-':
                ars.append(-mr)

        return ars

class modified_interactor2(util.dls_machine_interactor_bulk_base):
    """
    This interactor is the for using the machine
    """
    def mr_to_ar(self, mrs):
        #converts a set of machine results to algorithm results
        ars = []

        mr_to_ar_sign = [mrr.mr_to_ar_sign for mrr in results]
        for mr, sign in zip(mrs, mr_to_ar_sign):
            if sign == '+':
                ars.append(mr)
            elif sign == '-':
                ars.append(-mr)

        return ars

#the next three classes provide objects for parameters and objectives once they have been defined.

class mp_group_representation:
    """
    Machine group of parameters
    """

    def __init__(self):

        self.mp_representations = []
        self.list_iid = None
        self.ap_label = None
        self.relative_setting = None
        self.ap_min = None
        self.ap_max = None


class mp_representation:
    """
    Machine parameter
    """

    def __init__(self):

        self.mp_obj = None
        self.list_iid = None
        self.mp_label = None


class mr_representation:
    """
    Machine result (objective)
    """

    def __init__(self):

        self.mr_obj = None
        self.list_iid = None
        self.mr_label = None
        self.ar_label = None
        self.mr_to_ar_sign = None
        self.max_min_text = None
        self.max_min_sign = None

#names and file names of all optimisers

optimiserNames = ('Multi-Objective Particle Swarm Optimiser (MOPSO)',
                  'Multi-Objective Simulated Annealing (MOSA)',
                  'Multi-Objective Non-dominated Sorting Genetic Algorithm (NSGA-II)',
                  'Single-Objective Robust Conjugate Direction Search (RCDS)')

optimiserFiles = {'Multi-Objective Particle Swarm Optimiser (MOPSO)': 'dlsoo_mopso.py',
                  'Multi-Objective Simulated Annealing (MOSA)': 'dlsoo_mosa.py',
                  'Multi-Objective Non-dominated Sorting Genetic Algorithm (NSGA-II)': 'dlsoo_nsga2.py',
                  'Single-Objective Robust Conjugate Direction Search (RCDS)': 'dlsoo_rcds.py'}

keepUpdating = True
initial_settings = None
interactor = None
optimiser = None
useMachine = False
signConverter = []
Striptool_On = None
#Sign converter converts algo params to machine params. This is used in the plotting below.

mr_to_ar_sign = []
mp_addresses = []
mr_addresses = []

mp_min_var = []
mp_max_var = []

ap_min_var = []
ap_max_var = []

relative_settings = []

optimiser_wrapper_address = None
optimiser_wrapper = None

store_address = None

algo_settings_dict = None

mp_labels = []
mr_labels = []
ap_labels = []
ar_labels = []


parameters = []
results = []

#--------------------------------------------------MACHINE OR SIMULATOR WINDOW--------------------------------------------#

class interactor_selector_frame(Tkinter.Frame):
    """
    This class generates the window that allows the choice between using the machine or the simulator
    """
    def __init__(self, parent):
        """
        generate GUI
        """
        Tkinter.Frame.__init__(self, parent)
        root.withdraw()
        self.parent = parent
        self.grid()
        self.iChoice = Tkinter.StringVar()
        self.iChoice.set('Simulator')
        self.question1 = Tkinter.Label(self, text='Which interactor are you intending to use?')
        self.question1.grid(row=0, column=0)
        self.optList = ttk.Combobox(self, textvariable=self.iChoice, values=('Machine', 'Simulator'))
        self.optList.grid(row=1,column=0)
        self.subBtn = Tkinter.Button(self, text='Continue', command=self.setInteractor)
        self.subBtn.grid(row=2, column=0)

    def setInteractor(self):
        """
        now set the interactor to the chosen option
        """
        global useMachine
        item = self.iChoice.get()
        if item == 'Machine':
            useMachine = True
            self.parent.withdraw()
            root.deiconify()
        elif item == 'Simulator':
            useMachine = False
            self.parent.withdraw()
            root.deiconify()

#-----------------------------------------------------MAIN WINDOW SETUP---------------------------------------------------#


class main_window(Tkinter.Frame):

    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent

        self.initUi()

    def initUi(self):
        """
        Generate the GUI
        """
        
        self.parent.title("DLS Machine Optimiser")

        self.striptool_on = Tkinter.IntVar()
        self.striptool_on.set(0)

        self.parent.columnconfigure(0, weight=1)
        self.parent.columnconfigure(1, weight=1)
        self.parent.columnconfigure(2, weight=1)
        self.parent.columnconfigure(3, weight=1)
        self.parent.columnconfigure(4, weight=1)
        self.parent.columnconfigure(5, weight=1)
        
        #PARAMETER COLUMNS
        self.Tinput_params = ttk.Treeview(self.parent, columns=("lb", "ub", "delay"))
        self.Tinput_params.column("lb", width=120)
        self.Tinput_params.heading("lb", text="Lower bound")
        self.Tinput_params.column("ub", width=120)
        self.Tinput_params.heading("ub", text="Upper bound")
        self.Tinput_params.column("delay", width=80)
        self.Tinput_params.heading("delay", text="Delay /s")
        self.Tinput_params.grid(row=0, column=0, columnspan=3)

        #OBJECTIVE COLUMNS
        self.Toutput_params = ttk.Treeview(self.parent, columns=("counts", "delay", "maxmin"))
        self.Toutput_params.column("counts", width=120)
        self.Toutput_params.heading("counts", text="Min. Counts")
        self.Toutput_params.column("delay", width=120)
        self.Toutput_params.heading("delay", text="Delay /s")
        self.Toutput_params.column("maxmin", width=80)
        self.Toutput_params.heading("maxmin", text="Target")
        self.Toutput_params.grid(row=0, column=3, columnspan=3)
        
        #ADD PARAMETER BUTTONS
        self.btn_input_params_add = Tkinter.Button(self.parent, text="Add single", command=self.show_add_pv_window)
        self.btn_input_params_add.grid(row=1, column=0, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_input_params_addbulk = Tkinter.Button(self.parent, text="Add group", command=self.show_add_bulk_pv_window)
        self.btn_input_params_addbulk.grid(row=2, column=0, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_input_params_rmv = Tkinter.Button(self.parent, text="Remove", command=self.remove_pv)
        self.btn_input_params_rmv.grid(row=1, column=2, rowspan=2, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        
        #ADD OBJECTIVE BUTTONS
        self.btn_output_params_add = Tkinter.Button(self.parent, text="Add", command=self.show_add_obj_func_window)
        self.btn_output_params_add.grid(row=1, column=3, rowspan=2, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_output_params_rmv = Tkinter.Button(self.parent, text="Remove", command=self.remove_obj)
        self.btn_output_params_rmv.grid(row=1, column=5, rowspan=2, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)

        ttk.Separator(self.parent, orient='horizontal').grid(row=3, column=0, columnspan=6, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)

        #SAVE DIRECTORY
        Tkinter.Label(self.parent, text="Save directory:").grid(row=4, column=0, sticky=Tkinter.E)
        self.i_save_address = Tkinter.Entry(self.parent)
        self.i_save_address.grid(row=4, column=1, columnspan=4, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_browse_save_address = Tkinter.Button(self.parent, text="Browse...", command=self.browse_save_location)
        self.btn_browse_save_address.grid(row=4, column=5, sticky=Tkinter.E+Tkinter.W)

        ttk.Separator(self.parent, orient='horizontal').grid(row=5, column=0, columnspan=6, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)
        
        #ALGORITHM CHOICE
        self.optimiserChoice = Tkinter.StringVar()
        Tkinter.Label(self.parent, text="Algorithm:").grid(row=6, column=0, sticky=Tkinter.E)
        self.algo = ttk.Combobox(self.parent, textvariable=self.optimiserChoice, values=optimiserNames)
        self.algo.grid(row=6, column=1, columnspan=4, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)

        ttk.Separator(self.parent, orient='horizontal').grid(row=7, column=0, columnspan=6, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)

        #NEXT BUTTON
        self.btn_algo_settings = Tkinter.Button(self.parent, text="Next...", bg="red", command=self.next_button)
        self.btn_algo_settings.grid(row=8, column=5, sticky=Tkinter.E+Tkinter.W)

        #STRIPTOOL OPTION
        self.r0 = Tkinter.Radiobutton(self.parent, text="Striptool Off (Recommended)", variable=self.striptool_on, value=0)
        self.r0.grid(row=8, column=4, sticky=Tkinter.E+Tkinter.W)
        self.r1 = Tkinter.Radiobutton(self.parent, text="Striptool On", variable=self.striptool_on, value=1)
        self.r1.grid(row=8, column=3, sticky=Tkinter.E+Tkinter.W)
        
        #CONFIGURATION BUTTONS
        self.btn_load_config = Tkinter.Button(self.parent, text="Load configuration", command=self.load_config)
        self.btn_load_config.grid(row=8, column=0, sticky=Tkinter.E+Tkinter.W)
        self.btn_save_config = Tkinter.Button(self.parent, text="Save configuration", command=self.save_config)
        self.btn_save_config.grid(row=8, column=1, sticky=Tkinter.E+Tkinter.W)

    def browse_save_location(self):
        """
        Once a save location has been defined, this function creates a new folder in this location. All data will be save here.
        """
        global store_address
        current_time_string = datetime.datetime.fromtimestamp(time.time()).strftime('%d.%m.%Y_%H.%M.%S')
        store_directory = tkFileDialog.askdirectory()
        self.i_save_address.delete(0, 'end')
        self.i_save_address.insert(0, store_directory)
        store_address = '{0}/Optimisation@{1}'.format(store_directory, current_time_string)
        if not os.path.exists(store_address):                                               #make save directory
            os.makedirs(store_address)
        print 'Store address has been chosen to be ',store_address

    #next three functions make associated windows appear on screen
    def show_add_pv_window(self):
        add_pv_window.deiconify()
        
    def show_add_bulk_pv_window(self):
        add_bulk_pv_window.deiconify()
        
    def show_add_obj_func_window(self):
        add_obj_func_window.deiconify()


    #next two functions remove Parameters and objectives from list (if required)
    def remove_pv(self):
        iid = self.Tinput_params.selection()[0]
        print "REMOVE PV"

        for mpgrn, mpgr in enumerate(parameters):
            print mpgr.list_iid
            if mpgr.list_iid == iid:
                self.Tinput_params.delete(iid)
                del parameters[mpgrn]

    def remove_obj(self):
        print "REMOVE OBJ"
        iid = self.Toutput_params.selection()[0]

        for mrrn, mrr in enumerate(results):

            if mrr.list_iid == iid:
                self.Toutput_params.delete(iid)
                del results[mrrn]

    

    def next_button(self):
        """
        loads optimiser file, makes all windows involved with the main window withdraw
        """
        global optimiser_wrapper_address
        global Striptool_On
        
        optimiser_wrapper_address = optimiserFiles[self.optimiserChoice.get()]
        Striptool_On = self.striptool_on.get()
        
        add_obj_func_window.withdraw()
        add_pv_window.withdraw()
        add_bulk_pv_window.withdraw()
        self.parent.withdraw()
        algorithm_settings_frame.load_algo_frame(optimiser_wrapper_address)
        algorithm_settings_frame.initUi()
        algorithm_settings_window.deiconify()


    def load_config(self):
        """
        Loads a previously saved configuration
        """
        global parameters
        global results
        print "Configuration loaded"
        
        config_file = tkFileDialog.askopenfile()
        config = pickle.load(config_file)
        parameters += config['parameters']
        results += config['results']
        config_file.close()

        self.Tinput_params.delete(*self.Tinput_params.get_children())
        self.Toutput_params.delete(*self.Toutput_params.get_children())

        for mpgr in parameters:

            if len(mpgr.mp_representations) == 1:
                mpr = mpgr.mp_representations[0]
                iid = self.Tinput_params.insert('', 'end', text=mpr.mp_label, values=(mpgr.ap_min, mpgr.ap_max, mpr.mp_obj.delay))
                print "Single iid: {0}".format(iid)
                mpgr.list_iid = iid
                mpr.list_iid = iid

            else:
                parent_iid = self.Tinput_params.insert('', 'end', text=mpgr.ap_label, values=(mpgr.ap_min, mpgr.ap_max, mpgr.mp_representations[0].mp_obj.delay))
                mpgr.list_iid = parent_iid
                print "Bulk parent iid: {0}".format(parent_iid)
                for mpr in mpgr.mp_representations:
                    iid = self.Tinput_params.insert(parent_iid, 'end', text=mpr.mp_label, values=("", "", mpr.mp_obj.delay))
                    print "Bulk individual iid: {0}, belonging to parent iid: {1}".format(iid, parent_iid)
                    mpr.list_iid = iid

        for mrr in results:

            iid = self.Toutput_params.insert('', 'end', text=mrr.mr_label, values=(mrr.mr_obj.min_counts, mrr.mr_obj.delay, mrr.max_min_text))
            mrr.list_iid = iid

        print [i.list_iid for i in parameters]
        
        

    def save_config(self):
        """
        Saves a configuration that has been define don screen
        """
        global parameters
        global results
        
        config_file = tkFileDialog.asksaveasfile()     
        config = {'parameters' : parameters,
                  'results' : results}

        pickle.dump(config, config_file)
        config_file.close()


class add_pv(Tkinter.Frame):
    """
    This class is for adding a SINGLE PARAMETER.
    """

    def __init__(self, parent):
        print "INIT: Single Parameter window"
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.parent.protocol('WM_DELETE_WINDOW', self.x_button)

        self.initUi()

    def initUi(self):
        """
        Define the 'add parameter PV' GUI
        """
        
        self.parent.title("Add Parameter PV")
        self.setting_mode = Tkinter.IntVar()
        self.setting_mode.set(0)

        Tkinter.Label(self.parent, text="PV address:").grid(row=0, column=0, sticky=Tkinter.E)
        self.i0 = Tkinter.Entry(self.parent)
        self.i0.grid(row=0, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Lower bound/change:").grid(row=1, column=0, sticky=Tkinter.E)
        self.i1 = Tkinter.Entry(self.parent)
        self.i1.grid(row=1, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Upper bound/change:").grid(row=2, column=0, sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self.parent)
        self.i2.grid(row=2, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Delay /s:").grid(row=3, column=0, sticky=Tkinter.E)
        self.i3 = Tkinter.Entry(self.parent)
        self.i3.grid(row=3, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        self.r0 = Tkinter.Radiobutton(self.parent, text="Define PV bounds", variable=self.setting_mode, value=0)
        self.r0.grid(row=4, column=1, sticky=Tkinter.E+Tkinter.W)

        self.r1 = Tkinter.Radiobutton(self.parent, text="Define PV change", variable=self.setting_mode, value=1)
        self.r1.grid(row=4, column=2, sticky=Tkinter.E+Tkinter.W)

        self.b1 = Tkinter.Button(self.parent, text="Cancel", command=add_pv_window.withdraw)
        self.b1.grid(row=5, column=1, sticky=Tkinter.E+Tkinter.W)
        self.b2 = Tkinter.Button(self.parent, text="OK", command=self.add_pv_to_list)
        self.b2.grid(row=5, column=2, sticky=Tkinter.E+Tkinter.W)

    def add_pv_to_list(self):
        """
        Once defined, collect PV address + other options and create parameter object
        """
        
        details = (self.i0.get(), self.i1.get(), self.i2.get(), self.i3.get(), self.setting_mode.get())
        good_data = True

        #various errors for bad data
        try:
            float(details[1])
        except:
            good_data = False
            tkMessageBox.showerror("Input Error", "The lower bound/change cannot be converted to a float")
            
        if float(details[1])>0 and details[4]==1:
            good_data = False
            tkMessageBox.showerror("Input Error", "The lower change must be less than or equal to zero")

        try:
            float(details[2])
        except:
            good_data = False
            tkMessageBox.showerror("Input Error", "The upper bound/change cannot be converted to a float")

        try:
            float(details[3])
        except:
            good_data = False
            tkMessageBox.showerror("Input Error", "The delay cannot be converted to a float")
        
        #now that we have good data, make parameter object
        if good_data:

            #print parameter info on main window
            iid = the_main_window.Tinput_params.insert('', 'end', text=details[0], values=(details[1], details[2], details[3]))
            
            #define parameter object
            mpgr = mp_group_representation()
            mpr = mp_representation()
            mpr.mp_obj = util.dls_param_var(details[0], float(details[3]))
            mpr.list_iid = iid
            mpr.mp_label = details[0]

            mpgr.mp_representations.append(mpr)
            mpgr.list_iid = iid
            mpgr.ap_label = details[0]

            if details[4] == 0:
                mpgr.relative_setting = False
                mpgr.ap_min = float(details[1])
                mpgr.ap_max = float(details[2])

            elif details[4] == 1:
                mpgr.relative_setting = True
                mpgr.ap_min = float(details[1])
                mpgr.ap_max = float(details[2])

            #parameter is stored as a group even though its a single parameter
            parameters.append(mpgr)

            add_pv_window.withdraw()



    def x_button(self):
        print "Exited"
        self.parent.withdraw()


class add_bulk_pv(Tkinter.Frame):
    """
    This class is for adding a GROUP PARAMETER.
    """
    
    def __init__(self, parent):
        
        Tkinter.Frame.__init__(self, parent)
        
        self.parent = parent
        self.parent.protocol('WM_DELETE_WINDOW', self.x_button)
        
        self.initUi()
    
    def initUi(self):
        """
        define the 'Add Bulk Parameter PVs' GUI
        """
        
        self.parent.title("Add Bulk Parameter PVs")
        self.setting_mode = Tkinter.IntVar()            #this is for which method of defining the parameter bounds is being used
        self.setting_mode.set(1)
        
        
        Tkinter.Label(self.parent, text="Group name:").grid(row=0, column=0, sticky=Tkinter.E, pady=(10, 0))
        self.i6 = Tkinter.Entry(self.parent)
        self.i6.grid(row=0, column=1, columnspan=2, sticky=Tkinter.W+Tkinter.E, pady=(10, 0), padx=(0, 10))
        
        Tkinter.Label(self.parent, text="Group file (optional):").grid(row=1, column=0, sticky=Tkinter.E)
        self.i_file_address = Tkinter.Entry(self.parent)
        self.i_file_address.grid(row=1, column=1, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_browse_file_address = Tkinter.Button(self.parent, text="Add group file...", command=self.browse_save_location)
        self.btn_browse_file_address.grid(row=1, column=2, sticky=Tkinter.E+Tkinter.W)
        
        ttk.Separator(self.parent, orient='horizontal').grid(row=2, column=0, columnspan=3, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)
        
        Tkinter.Label(self.parent, text="PV addresses:").grid(row=3, column=0, sticky=Tkinter.E+Tkinter.W)
        Tkinter.Label(self.parent, text="Lower bounds:").grid(row=3, column=1, sticky=Tkinter.E+Tkinter.W)
        Tkinter.Label(self.parent, text="Upper bounds:").grid(row=3, column=2, sticky=Tkinter.E+Tkinter.W)
        
        self.i0 = Tkinter.Text(self.parent, width=40)
        self.i0.grid(row=4, column=0, sticky=Tkinter.E+Tkinter.W)
        self.i1 = Tkinter.Text(self.parent, width=40)
        self.i1.grid(row=4, column=1, sticky=Tkinter.E+Tkinter.W)
        self.i2 = Tkinter.Text(self.parent, width=40)
        self.i2.grid(row=4, column=2, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self.parent, text="Change:").grid(row=5, column=0, sticky=Tkinter.E)
        
        self.i4 = Tkinter.Entry(self.parent)
        self.i4.grid(row=5, column=1, sticky=Tkinter.E+Tkinter.W)
        
        self.i5 = Tkinter.Entry(self.parent)
        self.i5.grid(row=5, column=2, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self.parent, text="Delay:").grid(row=6, column=0, sticky=Tkinter.E)
        self.i3 = Tkinter.Entry(self.parent)
        self.i3.grid(row=6, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)
        
        self.r0 = Tkinter.Radiobutton(self.parent, text="Define PV Change", variable=self.setting_mode, value=0)
        self.r0.grid(row=7, column=1)
        
        self.r2 = Tkinter.Radiobutton(self.parent, text="Define PV Bounds", variable=self.setting_mode, value=1)
        self.r2.grid(row=7, column=0)
        
        self.b0 = Tkinter.Button(self.parent, text="Cancel", command=self.parent.withdraw)
        self.b0.grid(row=8, column=1, sticky=Tkinter.E+Tkinter.W)
        
        self.b1 = Tkinter.Button(self.parent, text="Add", command=self.add_pvs)
        self.b1.grid(row=8, column=2, sticky=Tkinter.E+Tkinter.W)
        
        
        
    def browse_save_location(self):
        """
        This class is for reading a csv file with list of parameter PVs, which are then put into the column of parameter PVs in the 'Add Bulk Parameter PVs' window
        """
        
        store_directory = tkFileDialog.askopenfile()
        self.i_file_address.delete(0, 'end')
        self.i_file_address.insert(0, store_directory.name)
        groupPV_address = store_directory
        
        print groupPV_address
        
        group_file = open(groupPV_address.name, 'r')
        wr = csv.reader(group_file)
        
        addresses = []
        
        for row in wr:
            addresses.append(row[0:1][0])
        
        for i in addresses:
            
            if i == addresses[-1]:
                self.i0.insert(Tkinter.END, i)
                return
            
            self.i0.insert(Tkinter.END, '{0}\n'.format(i))

        
        
    def add_pvs(self):
        """
        Once the group PV has been defined, create a group parameter object 
        """
        
        #collect data from GUI
        details = (self.i0.get(0.0, Tkinter.END), self.i1.get(0.0, Tkinter.END), self.i2.get(0.0, Tkinter.END), self.i4.get(), self.i5.get(), self.i3.get(), self.setting_mode.get())
        processed_details = [[], [], [], None, None, None, None] # This will contain PVs, lb, ub, lc, uc, delay, and setting_mode
        
        for address in details[0].splitlines():
            processed_details[0].append(str(address))
        
        for lower,  upper in zip(details[1].splitlines(), details[2].splitlines()):
            processed_details[1].append(lower)
            processed_details[2].append(upper)
        
        processed_details[3] = details[3]
        processed_details[4] = details[4]
        
        processed_details[5] = details[5]
        processed_details[6] = details[6]
        
        # Check that the data is all of the correct format
        good_data = True
        for i in range(len(processed_details[1])):
            try:
                if processed_details[6] in [0, 1] and processed_details[6] == 1:
                    processed_details[1][i] = float(processed_details[1][i])
            except:
                tkMessageBox.showerror("Format error with lower bound", "The lower bound value for PV #{0}: \"{1}\", could not be converted to a float. Please check the values you have entered.".format(i+1, processed_details[1][i]))
                good_data = False
        
        for i in range(len(processed_details[2])):
            try:
                if processed_details[6] in [0, 1] and processed_details[6] == 1:
                    processed_details[2][i] = float(processed_details[2][i])
            except:
                tkMessageBox.showerror("Format error with upper bound", "The upper bound value for PV #{0}: \"{1}\", could not be converted to a float. Please check the values you have entered.".format(i+1, processed_details[2][i]))
                good_data = False
        
        try:
            if processed_details[6] == 0:
                processed_details[3] = float(processed_details[3])
        except:
            tkMessageBox.showerror("Format error with lower change", "The lower change value: \"{0}\", could not be converted to a float. Please check the value you have entered.".format(processed_details[3]))
            good_data = False
            
        if float(processed_details[6])==0 and float(processed_details[3])>0:
            good_data = False
            tkMessageBox.showerror("Input Error", "The lower change must be less than or equal to zero")
        
        try:
            if processed_details[6] == 0:
                processed_details[4] = float(processed_details[4])
        except:
            tkMessageBox.showerror("Format error with upper change", "The upper change value: \"{0}\", could not be converted to a float. Please check the value you have entered.".format(processed_details[4]))
            good_data = False
        
        try:
            processed_details[5] = float(processed_details[5])
        except:
            tkMessageBox.showerror("Format error with delay", "The delay value: \"{0}\", could not be converted to a float. Please check the value you have entered.".format(processed_details[5]))
            good_data = False
        
        #now that we have good data, create object 
        if good_data:
            
            mpgr = mp_group_representation()
            for pv in processed_details[0]:
                mpr = mp_representation()
                mpr.mp_obj = util.dls_param_var(pv, processed_details[5])
                mpr.mp_label = pv
                mpgr.mp_representations.append(mpr)
                
            print "processed_details[0]: {0}".format(processed_details[0])
            print "mpgr to be added: {0}".format([i.mp_label for i in mpgr.mp_representations])
            
            #need to calculate bounds and hence need to use the machine interactor to measure PVs
            temp_interactor = modified_interactor2(param_var_groups=[[i.mp_obj for i in mpgr.mp_representations]])
            initial_mps = temp_interactor.get_mp()
            
            if processed_details[6] == 1:
                # This means we are setting according to the bounds
                
                # Calculate relative from bounds
                a_min, a_max = util.find_group_a_bounds(processed_details[1], processed_details[2], initial_mps, True)
                
                mpgr.relative_setting = True
                mpgr.ap_min = a_min
                mpgr.ap_max = a_max

            
            elif processed_details[6] == 0:
                # This means we are setting according to the change, not the bounds
                
                # Calculate relative from change
                mpgr.relative_setting = True
                mpgr.ap_min = processed_details[3]
                mpgr.ap_max = processed_details[4]
                
                processed_details[1] = ["" for i in processed_details[0]]
                processed_details[2] = ["" for i in processed_details[0]]
            
            #insert information of group parameter into main window
            parent_iid = the_main_window.Tinput_params.insert('', 'end', text=self.i6.get(), values=(mpgr.ap_min, mpgr.ap_max, processed_details[5]))
            mpgr.list_iid = parent_iid
            
            for i, mpr in enumerate(mpgr.mp_representations):
                print "ADDING GROUP PARAMETER"
                iid = the_main_window.Tinput_params.insert(parent_iid, 'end', text=processed_details[0][i], values=(processed_details[1][i], processed_details[2][i], processed_details[5]))
                mpr.list_iid = iid
            
            mpgr.ap_label = self.i6.get()
            parameters.append(mpgr)
                       
            add_bulk_pv_window.withdraw()
            
        
    def x_button(self):
        print "Exited"
        self.parent.withdraw()


class add_obj_func(Tkinter.Frame):
    """
    This class is for adding a OBJECTIVES.
    """

    def __init__(self, parent):
        print "INIT: Objective window"
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.parent.protocol('WM_DELETE_WINDOW', self.x_button)

        self.initUi()

    def initUi(self):
        """
        Define 'Add Objective PV' GUI
        """
        
        self.parent.title("Add Objective PV")
        self.max_min_setting = Tkinter.IntVar()
        self.max_min_setting.set(0)                 #this setting is for choosing whether objective will maximised or minimised

        Tkinter.Label(self.parent, text="PV address:").grid(row=0, column=0, sticky=Tkinter.E)
        self.i0 = Tkinter.Entry(self.parent)
        self.i0.grid(row=0, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Min. count:").grid(row=1, column=0, sticky=Tkinter.E)
        self.i1 = Tkinter.Entry(self.parent)
        self.i1.grid(row=1, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Delay /s:").grid(row=2, column=0, sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self.parent)
        self.i2.grid(row=2, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        self.r0 = Tkinter.Radiobutton(self.parent, text="Minimise", variable=self.max_min_setting, value=0)
        self.r0.grid(row = 3, column=0, sticky=Tkinter.W)
        self.r1 = Tkinter.Radiobutton(self.parent, text="Maximise", variable=self.max_min_setting, value=1)
        self.r1.grid(row = 3, column=1, sticky=Tkinter.W)

        self.b1 = Tkinter.Button(self.parent, text="Cancel", command=add_obj_func_window.withdraw)
        self.b1.grid(row=4, column=1, sticky=Tkinter.E+Tkinter.W)
        self.b2 = Tkinter.Button(self.parent, text="OK", command=self.add_pv_to_list)
        self.b2.grid(row=4, column=2, sticky=Tkinter.E+Tkinter.W)


    def add_pv_to_list(self):
        """
        Once objective has been defined, create object for the objective
        """
        
        global results
        
        #create object
        mrr = mr_representation()
        
        #retrieve information from GUI
        mrr.mr_obj = util.dls_measurement_var(self.i0.get(), float(self.i1.get()), float(self.i2.get()))

        #max/min settings
        if self.max_min_setting.get() == 0:
            mrr.max_min_text = "Minimise"
            mrr.max_min_sign = "+"
            mrr.mr_to_ar_sign = "+"
        elif self.max_min_setting.get() == 1:
            mrr.max_min_text = "Maximise"
            mrr.max_min_sign = "-"
            mrr.mr_to_ar_sign = "-"

        #injection/non-injection settings
        iid = the_main_window.Toutput_params.insert('', 'end', text=self.i0.get(), values=(self.i1.get(), self.i2.get(), mrr.max_min_text))
        mrr.list_iid = iid
        mrr.mr_label = self.i0.get()
        mrr.ar_label = self.i0.get()

        results.append(mrr)
        add_obj_func_window.withdraw()


    def x_button(self):
        print "Exited"
        self.parent.withdraw()

#-------------------------------------------------------PROGRESS WINDOW------------------------------------------------------------------#

class show_progress(Tkinter.Frame):
    """
    This class is for the progress window that appears during an optimisation. It includes a plot showing the calculated Pareto fronts
    as well as a percentage bar. The window has Pause and Cancel buttons that provide ease of use. The pause button will complete the
    measurement and then pause whilst the Cancel button will stop will complete the current measurement and then finish the optimisation.
    A striptool option can also be added but it is turned off by default (this can be changed in the main window GUI).
    """
    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent


    def initUi(self):
        """
        Define GUI
        """
        global signConverter
        global Striptool_On

        self.parent.title("Optimising...")

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)

        self.pbar_progress = ttk.Progressbar(self.parent, length=400, variable=progress)
        self.pbar_progress.grid(row=0, column=0, columnspan=4, padx=10, pady=10)
        
        #optional striptool feature (recommended to the user to be turned off (==0)
        if Striptool_On == 1:
            self.strip_plot = strip_plot(self.parent)
            self.strip_plot.grid(row=2, column=0, columnspan=4)

        #cancel method
        self.btn_cancel = Tkinter.Button(self.parent, text="Cancel", command=self.cancelMethod)
        self.btn_cancel.grid(row=1, column=3, sticky=Tkinter.W+Tkinter.E)

        #pause method
        self.btn_pause = Tkinter.Button(self.parent, text="Pause", command=self.pause_algo)
        self.btn_pause.grid(row=1, column=2, sticky=Tkinter.E+Tkinter.W)

        # This part will display the latest plot
        ar_labels = [mrr.ar_label for mrr in results]
        #import_algo_prog_plot class from chosen algorithm
        self.progress_plot = optimiser_wrapper.import_algo_prog_plot(self.parent, ar_labels, signConverter)
        self.progress_plot.grid(row=3, column=0, columnspan=4)
        print "INIT: Progress window"

    def handle_progress(self, normalised_percentage, generation):
        """
        updates the percentage bar and plots using functions in the import_algo_prog_plot class in the chosen algorithm file
        """
        global Striptool_On

        progress.set(normalised_percentage * 100)
        progress_frame.update()

        if Striptool_On == 1:
            self.strip_plot.update()

        self.progress_plot.update()


    def pause_algo(self):
        """
        This method pauses the algorithm
        """
        print "Pausing"
        global optimiser
        optimiser.pause = not optimiser.pause

        if optimiser.pause:
            self.btn_pause.config(text="Unpause")
            self.parent.config(background="red")
        else:
            self.btn_pause.config(text="Pause")
            self.parent.config(background="#d9d9d9")

    def cancelMethod(self):
        """
        This method cancels the algorithm
        """
        optimiser.cancel = True


class plot_progress(Tkinter.Frame):
    """
    This class produces the actual plot that is put in the show_progress window
    """

    def __init__(self, parent):

        Tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.initUi()

    def initUi(self):
        """
        define GUI
        """
        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.a = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)


class strip_plot(Tkinter.Frame):
    """
    This class produces the Striptool plot, which is not used by default
    """

    def __init__(self, parent):

        Tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.initUi()

    def initUi(self):
        """
        define GUI
        """
        
        global interactor
        self.interactor = interactor
        self.data_sets = []
        self.time_sets = []
        self.initTime = time.time()

        self.fig = Figure(figsize=(5, 1), dpi=100)
        self.a = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)

    def update(self):
        """
        updates the Striptool for one objective measurement
        """

        mps = self.interactor.get_mp()
        mrs = []
        for i in self.interactor.measurement_vars:
            mrs.append(self.interactor.get_pv(i.pv))

        new_data = mrs + mps
        self.data_sets.append(new_data)
        self.time_sets.append(time.time() - self.initTime)

        plot.plot_strip_tool(self.a, self.data_sets, self.time_sets)
        self.canvas.show()

#----------------------------------------------------------SELECT SOLUTION FROM FINAL RESULTS--------------------------------------------#

class point_details(Tkinter.Frame):
    """
    This class is for the window that is shown when clicking on a point in the final Pareto front. It requires reading saved files
    that are in Pickle format.
    """
 
    def __init__(self, parent):
        print "INIT: Solution window"
        Tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.protocol('WM_DELETE_WINDOW', self.x_button)
        self.initUi()
 
    def initUi(self):
        """
        generates GUI frame
        """
        self.parent.title("Point")


    def generateUi(self, ars, aps):
        """
        generates table that goes into GUI
        """
        
        global signConverter

        ''' First, unpickle the mp_to_ap mapping file '''

        mapping_file = open("{0}/ap_to_mp_mapping_file.txt".format(store_address))
        mp_to_ap_mapping = pickle.load(mapping_file)
        mapping_file.close()

        ''' Now get the mp values '''

        mps = mp_to_ap_mapping[aps]
        self.mps = mps

        ''' Now make UI '''

        Tkinter.Label(self.parent, text="Machine").grid(row=0, column=1, sticky=Tkinter.W+Tkinter.E+Tkinter.N+Tkinter.S)
        Tkinter.Label(self.parent, text="Algorithm").grid(row=0, column=2, sticky=Tkinter.W+Tkinter.E+Tkinter.N+Tkinter.S)
        Tkinter.Label(self.parent, text="Parameters").grid(row=1, column=0, sticky=Tkinter.W+Tkinter.E+Tkinter.N+Tkinter.S)
        Tkinter.Label(self.parent, text="Results").grid(row=2, column=0, sticky=Tkinter.W+Tkinter.E+Tkinter.N+Tkinter.S)

        tree_mp = ttk.Treeview(self.parent, columns=("value"))
        tree_mp.column("value", width=200)
        tree_mp.heading("value", text="Value")
        tree_mp.grid(row=1, column=1)

        tree_mr = ttk.Treeview(self.parent, columns=("value"))
        tree_mr.column("value", width=200)
        tree_mr.heading("value", text="Value")
        tree_mr.grid(row=2, column=1)

        tree_ap = ttk.Treeview(self.parent, columns=("value"))
        tree_ap.column("value", width=200)
        tree_ap.heading("value", text="Value")
        tree_ap.grid(row=1, column=2)

        tree_ar = ttk.Treeview(self.parent, columns=("value"))
        tree_ar.column("value", width=200)
        tree_ar.heading("value", text="Value")
        tree_ar.grid(row=2, column=2)

        btn_set = Tkinter.Button(self.parent, text="Set", command=self.set_state)
        btn_set.grid(row=3, column=2, sticky=Tkinter.W+Tkinter.E, pady=10)

        for i, ap in enumerate(aps):
            tree_ap.insert('', 'end', text=parameters[i].ap_label, values=(ap))

        for i, ar in enumerate(ars):
            tree_ar.insert('', 'end', text=results[i].ar_label, values=(signConverter[i]*ar))

        mp_labels = []
        for mpgr in parameters:
            for mpr in mpgr.mp_representations:
                mp_labels.append(mpr.mp_label)
        for i, mp in enumerate(mps):
            tree_mp.insert('', 'end', text=mp_labels[i], values=(mp))

        self.parent.deiconify()
        

    def set_state(self):
        """
        This allows the user to select a point and then to set the machine to this set of parameters
        """
        interactor.set_mp(self.mps)

    def x_button(self):
        print "Exited"
        self.parent.withdraw()



class algorithm_settings(Tkinter.Frame):
    """
    This class import_algo_frame class in the algorithm file. This is used to collect the algorithm settings, then the 
    optimisation is started. Once this begins, all windows associated with the main window disappear.
    """

    def __init__(self, parent):

        Tkinter.Frame.__init__(self, parent)

        self.parent = parent

    def initUi(self):
        """
        Generate GUI frame for algorithm settings
        """

        self.parent.title("Algorithm settings")

        self.algo_frame.grid(row=0, column=0, columnspan=2, sticky=Tkinter.N+Tkinter.E+Tkinter.S+Tkinter.W, pady=10, padx=10)

        ttk.Separator(self.parent, orient="horizontal").grid(row=1, pady=10, padx=10, sticky=Tkinter.E+Tkinter.W, columnspan=2)

        b0 = Tkinter.Button(self.parent, text="Start...", bg="red", command=self.set_settings)
        b0.grid(row=2, column=1, sticky=Tkinter.E+Tkinter.W)


    def load_algo_frame(self, file_address):
        """
        Put import_algo_frame class in the GUI frame
        """
        global optimiser_wrapper
        optimiser_wrapper = imp.load_source(os.path.splitext(os.path.split(file_address)[1])[0], file_address)
        self.algo_frame = optimiser_wrapper.import_algo_frame(self.parent)

    def set_settings(self):
        """
        collect data from algorithm settings window and start optimisation
        """
        global algo_settings_dict
        global optimiser
        global optimiser_wrapper
        global interactor
        global parameters
        global results
        global signConverter
        global store_address
        
        #get user defined algorithm settings
        algo_settings_dict = self.algo_frame.get_dict()

        #settings errors to ensure good data
        if algo_settings_dict == "error":
            tkMessageBox.showerror("Algorithm settings error", "There was an error in one or more of the settings given. The optimisation procedure will not proceed.")
        
        #show 'are you sure?' window
        else:
            interactorIdentity = ''
            
            #machine interactor?
            if useMachine:
                interactorIdentity = 'MACHINE'
                
            #simulator interactor?
            else:
                interactorIdentity = 'SIMULATOR'
                
            userContinue = tkMessageBox.askyesno(title='READY?', message='You are using the ' + interactorIdentity + '. ' + 'Are you sure you wish to start optimisation?', icon=tkMessageBox.WARNING)
            
            #if all is good; prepare for start of optimisation
            if userContinue:
                mp_addresses = [[mpr.mp_obj for mpr in mpgr.mp_representations] for mpgr in parameters]          #gather machine parameters
                mr_addresses = [mrr.mr_obj for mrr in results]                                                   #gather machine results (objectives) 
                relative_settings = [mpgr.relative_setting for mpgr in parameters]                               #gather bounds for machine parameters
                ap_min_var = [mpgr.ap_min for mpgr in parameters]                                                #gather minimum bounds for parameter parameters
                ap_max_var = [mpgr.ap_max for mpgr in parameters]                                                #gather maximum bounds for parameter parameters
                
                #need a sign converter if any objectives are to be maximised (by default, algorithms minimise objectives)
                for mrr in results:
                    if mrr.mr_to_ar_sign == '-':
                        signConverter.append(-1)
                    else:
                        signConverter.append(1)
                        
                #define the appropriate interactor depending on using machine or simulator
                if useMachine:
                    interactor = modified_interactor2(mp_addresses, mr_addresses, set_relative=relative_settings)
                else:
                    interactor = modified_interactor1(mp_addresses, mr_addresses, set_relative=relative_settings)
                
                #save the interactor object to file (used in post_analysis file)
                save_object(interactor, '{0}/interactor.txt'.format(store_address))
                
                #find out initial settings
                initial_mp = interactor.get_mp()
                
                #initialise optimiser class in the algorithm file using settings dictionary among other arguments
                optimiser = optimiser_wrapper.optimiser(settings_dict=algo_settings_dict,
                                                        interactor=interactor,
                                                        store_location=store_address,
                                                        a_min_var=ap_min_var,
                                                        a_max_var=ap_max_var,
                                                        progress_handler=progress_frame.handle_progress) # Still need to add the individuals, and the progress handler

                #withdraw all windows associated with the main window
                self.parent.withdraw()
                #NOW RUN THE OPTIMISATION (using function below)
                run_optimisation()
 
 
### I'm almost certain this function is never used but i wont' get rid of it just incase...###
def main_window_lock_unlock(new_state):
    the_main_window.btn_algo_settings.config(state=new_state)
    the_main_window.btn_browse_address.config(state=new_state)
    the_main_window.btn_input_params_add.config(state=new_state)
    the_main_window.btn_input_params_rmv.config(state=new_state)
    the_main_window.btn_output_params_add.config(state=new_state)
    the_main_window.btn_output_params_rmv.config(state=new_state)
    the_main_window.btn_run.config(state=new_state)



def save_details_files(start_time, end_time):
    """
    saves details of optimisation in txt file using functions in the algorithm file and in dls_optimiser_util.py
    """
    global my_solver
    global the_interactor
    global store_address

    f = file("{0}/algo_details.txt".format(store_address), "w")
    f.write(optimiser.save_details_file())

    f = file("{0}/inter_details.txt".format(store_address), "w")
    f.write(interactor.save_details_file())

    f = file("{0}/controller_details.txt".format(store_address), "w")
    f.write("Controller\n")
    f.write("==========\n\n")

    f.write("Start time: {0}-{1}-{2} {3}:{4}:{5}\n".format(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute, start_time.second))
    f.write("End time: {0}-{1}-{2} {3}:{4}:{5}\n".format(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute, end_time.second))



def run_optimisation():
    """
    initialises progress windows and calls on the the optimisation to begin susing function below
    """
    global final_plot_frame
    global initial_settings
    print "Lets go!"

    progress_frame.initUi()
    algorithm_settings_window.withdraw()

    initial_settings = interactor.get_mp()

    progress_window.deiconify()
    progress_window.grab_set()
    cothread.Spawn(optimiserThreadMethod)


def optimiserThreadMethod():
    global signConverter
    global final_plot_frame
    global optimiser
    global parameters
    global results
    global store_address
    global keepUpdating
    
    #prepare folder in store_address to save fronts
    if not os.path.exists('{0}/FRONTS'.format(store_address)):
        os.makedirs('{0}/FRONTS'.format(store_address))
        
    ###NOW ACTUALLY CALL THE OPTIMISE FUNCTION WITHIN THE ALGORITHM FILE###   
    start_time = time.time()   #START
    optimiser.optimise()       #OPTIMISING...
    keepUpdating = False       
    end_time = time.time()     #STOP 

    #now save details for later reference by various code (results plotting, post_analysis etc..)
    interactor.set_mp(initial_settings)
    save_details_files(datetime.datetime.fromtimestamp(start_time), datetime.datetime.fromtimestamp(end_time))
    
    if not os.path.exists('{0}/PARAMETERS'.format(store_address)):
        os.makedirs('{0}/PARAMETERS'.format(store_address))
        
    if not os.path.exists('{0}/RESULTS'.format(store_address)):
        os.makedirs('{0}/RESULTS'.format(store_address))
    
    #save parameters and objectives as Pickle objects
    for i in range(len(parameters)):
        save_object(parameters[i], '{0}/PARAMETERS/parameter_{1}'.format(store_address, i))
    for i in range(len(results)):
        save_object(results[i], '{0}/RESULTS/result_{1}'.format(store_address, i))
    
    #save signconverter 
    signConverter_file = open("{0}/signConverter.txt".format(store_address), 'w')
    signConverter_file.write(str(signConverter))
    signConverter_file.close()
    
    #save the mapping method between algorithm parameters to machine parameters
    ap_to_mp_mapping_file = open("{0}/ap_to_mp_mapping_file.txt".format(store_address), 'w')
    ap_to_mp_mapping_file.write(interactor.string_ap_to_mp_store())
    ap_to_mp_mapping_file.close()

    #By this point, the algorithm has finished the optimisation, and restored the machine

    #close progress window
    progress_window.grab_release()
    progress_window.withdraw()
    
    #show the final plot windows
    ar_labels = [mrr.ar_label for mrr in results]
    final_plot_frame = optimiser_wrapper.import_algo_final_plot(final_plot_window, point_frame.generateUi, ar_labels, signConverter)
    final_plot_frame.initUi()
    final_plot_window.deiconify()



#define root window
root = Tkinter.Tk()
root.title("DLS Online Optimiser")
rootInit = Tkinter.Toplevel(root)
rootInit.title('DLS Interactor Selector')
initter = interactor_selector_frame(rootInit)

#threading method for Pause and Cancel methods to work
def yielder():
    cothread.Yield()
    root.after(100, yielder)
root.after(100, yielder)

#variables for progress percentage 
progress = Tkinter.DoubleVar()
progress.set(0.00)

# The main setup window
the_main_window = main_window(root)

# The dialog for adding input parameters
add_pv_window = Tkinter.Toplevel(root)
add_pv_frame = add_pv(add_pv_window)
add_pv_window.withdraw()

# The dialog for adding input group parameters
add_bulk_pv_window = Tkinter.Toplevel(root)
add_bulk_pv_frame = add_bulk_pv(add_bulk_pv_window)
add_bulk_pv_window.withdraw()

# The dialog for adding objective functions
add_obj_func_window = Tkinter.Toplevel(root)
add_obj_func_frame = add_obj_func(add_obj_func_window)
add_obj_func_window.withdraw()

# The dialog for changing algorithm settings
algorithm_settings_window = Tkinter.Toplevel(root)
algorithm_settings_frame = algorithm_settings(algorithm_settings_window)
algorithm_settings_window.withdraw()

# The dialog showing calculation progress
progress_window = Tkinter.Toplevel(root)
progress_frame = show_progress(progress_window)
progress_window.withdraw()

# The dialogs for showing the final results
point_window = Tkinter.Toplevel(root)
point_frame = point_details(point_window)
point_window.withdraw()

# dialog for final plot
final_plot_window = Tkinter.Toplevel(root)
final_plot_window.withdraw()

#cothread sanity check
def ticker():
    while True:
        cothread.Sleep(5)


#start everything
root.mainloop()
cothread.WaitForQuit()