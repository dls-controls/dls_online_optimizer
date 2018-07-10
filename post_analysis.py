'''
ANALYSIS TOOL for use of past optimisations in DLS OnlineOptimiser package (BASIC)

Created on 19 Jul 2017

@author: James Rogers
'''
from __future__ import division
import pkg_resources
pkg_resources.require('matplotlib')
pkg_resources.require('numpy')
pkg_resources.require('scipy')
pkg_resources.require('cothread')
import matplotlib
matplotlib.use("TkAgg")
import Tkinter
import ttk
import tkFileDialog
import tkMessageBox
import os
import imp
import pickle
import ast
from dlsoo import config, gui


class MainWindow(Tkinter.Frame):

    def __init__(self, parent, parameters):
        Tkinter.Frame.__init__(self, parent)
        self.parameters = parameters
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
        good_file = False

        # enter file into text box
        Tkinter.Label(self.parent, text=" ", justify=Tkinter.LEFT).grid(row=1, column=0, columnspan=4, sticky=Tkinter.W+Tkinter.S)
        store_directory = tkFileDialog.askdirectory()
        self.i_save_address.delete(0, 'end')
        self.i_save_address.insert(0, store_directory)
        self.parameters.store_address = store_directory

        # algo_details.txt should start with the Optimiser file name.
        # This is read and stored.
        try:
            with open(os.path.join(store_directory, 'algo_details.txt'), 'r') as f:
                first_line = f.readlines()[0]
                self.parameters.algorithm_name = first_line.split()[0]
            good_file = True
        except IOError:
            tkMessageBox.showerror("Directory Error", "The selected directory does not contain the correct files. Please try again")
            good_file = False

        # read out of the detected algorithm
        Tkinter.Label(self.parent,
                      text="{0} algorithm data directory detected".format(self.parameters.algorithm_name),
                      justify=Tkinter.LEFT).grid(row=1, column=0, columnspan=4, sticky=Tkinter.W+Tkinter.S)
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
        store_address = self.parameters.store_address
        global algo_frame

        # load parameters
        for filename in os.listdir('{0}/PARAMETERS'.format(store_address)):
            parameter = pickle.load(open('{0}/PARAMETERS/{1}'.format(store_address, filename), 'r'))
            self.parameters.parameters.append(parameter)

        # load results (objectives)
        for filename in os.listdir('{0}/RESULTS'.format(store_address)):
            result = pickle.load(open('{0}/RESULTS/{1}'.format(store_address, filename), 'r'))
            self.parameters.results.append(result)

        # load signConverter (for max/min)
        signConverter_read = open('{0}/signConverter.txt'.format(store_address), 'r')
        signConverter_data = signConverter_read.read()
        self.parameters.signConverter = ast.literal_eval(signConverter_data)

        # load interactor
        self.parameters.interactor = pickle.load(open('{0}/interactor.txt'.format(store_address, filename), 'r'))

        ar_labels = [mrr.ar_label for mrr in self.parameters.results]

        #load the algorithm file
        optimiser_wrapper = self.load_algo_frame('{0}/dlsoo/{1}'.format(os.getcwd(), self.parameters.algorithm_name))

        #load and show the final plot from the optimisation
        final_plot_frame = optimiser_wrapper.import_algo_final_plot(final_plot_window, point_frame.generateUi, ar_labels, self.parameters.signConverter, post_analysis_store_address = store_address)
        final_plot_frame.initUi(initial_config_plot=False)
        final_plot_window.deiconify()


if __name__ == '__main__':

    parameters = config.Parameters()
    #setup main window
    root = Tkinter.Tk()
    root.title("DLS Post Optimisation Analysis")
    the_main_window = MainWindow(root, parameters)

    #setup final plot window
    final_plot_window = Tkinter.Toplevel(root)
    final_plot_window.withdraw()

    #setup solution selection window
    point_window = Tkinter.Toplevel(root)
    point_frame = gui.PointDetails(point_window, parameters)
    point_window.withdraw()

    root.mainloop()
