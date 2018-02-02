'''
ANALYSIS TOOL for use of past optimisations in DLS OnlineOptimiser package (BASIC)

Created on 19 Jul 2017

@author: James Rogers
'''
from __future__ import division
import pkg_resources
import Tkinter
import ttk
import tkFileDialog
import tkMessageBox
import os
import imp
import pickle
import ast
import matplotlib
matplotlib.use("TkAgg")


store_address = None
algorithm_name = ""
algo_frame = None
optimiser_wrapper = None
interactor = None
results = []
parameters = []


class MainWindow(Tkinter.Frame):

    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent

        self.initUi()

    def initUi(self):
        """
        Generate DLS Post Optimisation Analysis GUI
        """

        self.parent.columnconfigure(0, weight=1)
        self.parent.columnconfigure(1, weight=4)
        self.parent.columnconfigure(2, weight=1)
        self.parent.columnconfigure(3, weight=1)

        self.parent.title("DLS Post Optimisation Analysis")

        Tkinter.Label(self.parent, text="Data directory:").grid(row=0, column=0, sticky=Tkinter.E)
        self.i_save_address = Tkinter.Entry(self.parent)
        self.i_save_address.grid(row=0, column=1, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_browse_save_address = Tkinter.Button(self.parent, text="Browse...", command=self.browse_save_location)
        self.btn_browse_save_address.grid(row=0, column=2, sticky=Tkinter.E+Tkinter.W)

        self.btn_algo_settings = Tkinter.Button(self.parent, text="Next...", bg="green", command=self.next_button)
        self.btn_algo_settings.grid(row=0, column=3, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="", justify=Tkinter.LEFT).grid(row=1, column=0, columnspan=4, sticky=Tkinter.W)

        ttk.Separator(self.parent, orient='horizontal').grid(row=2, column=0, columnspan=4, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)

        Tkinter.Label(self.parent, text="Please choose a directory in which optimisation data files have been saved.", justify=Tkinter.LEFT).grid(row=3, column=0, columnspan=4, sticky=Tkinter.W)

    def browse_save_location(self):
        """
        Find an optimisation file and detect what algorithm was used
        """

        global store_address
        global algorithm_name

        good_file = False

        #enter file into text box
        Tkinter.Label(self.parent, text=" ", justify=Tkinter.LEFT).grid(row=1, column=0, columnspan=4, sticky=Tkinter.W+Tkinter.S)
        store_directory = tkFileDialog.askdirectory()
        self.i_save_address.delete(0, 'end')
        self.i_save_address.insert(0, store_directory)
        store_address = store_directory

        #algo_details.txt should start with the optimiser file name. This is read and stored.
        if os.path.isfile('{0}/algo_details.txt'.format(store_address)):
            algo_details = open('{0}/algo_details.txt'.format(store_address), 'r')
            data = algo_details.read()
            for i in data:
                if i == ' ':
                    good_file = True
                    break
                algorithm_name += str(i)

        else:
            tkMessageBox.showerror("Directory Error", "The selected directory does not contain the correct files. Please try again")
            good_file = False

        #read out of the detected algorithm
        Tkinter.Label(self.parent, text="{0} algorithm data directory detected".format(algorithm_name), justify=Tkinter.LEFT).grid(row=1, column=0, columnspan=4, sticky=Tkinter.W+Tkinter.S)

        return good_file

    def load_algo_frame(self, file_address):
        """
        Import the appropriate algorithm file
        """
        module_name = os.path.splitext(os.path.basename(file_address))[0]
        optimiser_wrapper = imp.load_source(module_name, file_address)
        return optimiser_wrapper

    def next_button(self):
        """
        Load all parameters and results (objectives) as Pickle files from the store location. Then implement the import_algo_final_plot
        class in the algorithm file.
        """
        global algorithm_name
        global store_address
        global algo_frame
        global parameters
        global results
        global interactor
        global signConverter

        #load parameters
        for filename in os.listdir('{0}/PARAMETERS'.format(store_address)):
            parameter = pickle.load(open('{0}/PARAMETERS/{1}'.format(store_address, filename), 'r'))
            parameters.append(parameter)

        #load results (objectives)
        for filename in os.listdir('{0}/RESULTS'.format(store_address)):
            result = pickle.load(open('{0}/RESULTS/{1}'.format(store_address, filename), 'r'))
            results.append(result)

        #load signConverter (for max/min)
        signConverter_read = open('{0}/signConverter.txt'.format(store_address), 'r')
        signConverter_data = signConverter_read.read()
        signConverter = ast.literal_eval(signConverter_data)

        #load interactor
        interactor = pickle.load(open('{0}/interactor.txt'.format(store_address, filename), 'r'))

        ar_labels = [mrr.ar_label for mrr in results]

        #load the algorithm file
        optimiser_wrapper = self.load_algo_frame('{0}/dlsoo/{1}'.format(os.getcwd(), algorithm_name))

        #load and show the final plot from the optimisation
        final_plot_frame = optimiser_wrapper.import_algo_final_plot(final_plot_window, point_frame.generateUi, ar_labels, signConverter, post_analysis_store_address = store_address)
        final_plot_frame.initUi(initial_config_plot=False)
        final_plot_window.deiconify()

#------------------------------------------------------ SOLUTION SELECTION ---------------------------------------------------------#

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


if __name__ == '__main__':
    pkg_resources.require('matplotlib')
    pkg_resources.require('numpy')
    pkg_resources.require('scipy')
    #setup main window
    root = Tkinter.Tk()
    root.title("DLS Post Optimisation Analysis")
    the_main_window = MainWindow(root)

    #setup final plot window
    final_plot_window = Tkinter.Toplevel(root)
    final_plot_window.withdraw()

    #setup solution selection window
    point_window = Tkinter.Toplevel(root)
    point_frame = point_details(point_window)
    point_window.withdraw()

    root.mainloop()
