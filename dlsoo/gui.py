import csv
import datetime
import imp
import os
import pickle
import time
import Tkinter
import ttk
import tkFileDialog
import tkMessageBox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import cothread
from . import ca_abstraction_mapping, config, interactors, plot, tkutil, util


class InvalidEntry(Exception):
    def __init__(self, header, msg):
        self.header = header
        self.msg = msg

def save_details_files(start_time, end_time, store_address, optimiser,
        interactor):
    """
    saves details of optimisation in txt file using functions in the algorithm file and in dls_optimiser_util.py
    """
    with open(os.path.join(store_address, 'algo_details.txt'), 'w') as f:
        f.write(optimiser.save_details_file())
    with open(os.path.join(store_address, 'inter_details.txt'), 'w') as f:
        f.write(interactor.save_details_file())
    with open(os.path.join(store_address, 'controller_details.txt'), 'w') as f:
        f = file("{0}/controller_details.txt".format(store_address), "w")
        f.write("Controller\n")
        f.write("==========\n\n")
        f.write("Start time: {0}-{1}-{2} {3}:{4}:{5}\n".format(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute, start_time.second))
        f.write("End time: {0}-{1}-{2} {3}:{4}:{5}\n".format(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute, end_time.second))


def start(optimisers, parameters):
    root = Tkinter.Tk()
    root.title("DLS Online Optimiser")
    root.geometry('+100+100')
    # update the geometry so that we can query it later
    root.update()

    #threading method for Pause and Cancel methods to work
    def yielder():
        cothread.Yield()
        root.after(100, yielder)
    root.after(100, yielder)

    MainWindow(root, optimisers, parameters)
    if parameters.useMachine is None:
        selector = TargetSelector(root)
        selector.raise_to_top()
        root.wait_window(selector)
        parameters.useMachine = selector.machine_selected()

    root.title('DLS Online Optimiser - {}'.format('MACHINE' if parameters.useMachine else 'SIMULATOR'))
    root.mainloop()
    cothread.WaitForQuit()


class TargetSelector(tkutil.DialogBox):

    def __init__(self, parent):
        self.selected = Tkinter.IntVar()
        self.selected.set(1)
        tkutil.DialogBox.__init__(self, parent)
        # Very heavyweight way of keeping this window on top.
        # self.transient() should do this but doesn't seem to work.
        self.overrideredirect(True)
        self.title('Choose optimisation target')
        self.configure(background='lightblue')
        # Border since regular window decoraion is removed by
        # overrideredirect()
        self.config(borderwidth=2, relief=Tkinter.RIDGE)

    def machine_selected(self):
        return self.selected.get() == 2

    def create_body(self):
        s = ttk.Style()                     # Creating style element
        s.configure('Blue.TRadiobutton',    # First argument is the name of style. Needs to end with: .TRadiobutton
                    background='lightblue',         # Setting background to our specified color above
                    foreground='black')
        self.body = Tkinter.Frame(self)
        self.body.grid()
        question1 = Tkinter.Label(self.body, text='Which interactor are you intending to use?')
        question1.grid(row=0, column=0, columnspan=2)
        sim_button = ttk.Radiobutton(self.body, text='Simulator', variable=self.selected, value=1, style='Blue.TRadiobutton')
        sim_button.grid(row=1, column=0)
        machine_button = ttk.Radiobutton(self.body, text='Machine', variable=self.selected, value=2, style='Blue.TRadiobutton')
        machine_button.grid(row=1, column=1)
        continue_button = Tkinter.Button(self.body, text='Continue', command=self.cancel)
        continue_button.grid(row=2, column=0, columnspan=2)
        self.bind('<Return>', self.cancel)
        self.body.configure(background='lightblue')
        question1.configure(background='lightblue')
        self.body.pack()


class MainWindow(Tkinter.Frame):

    def __init__(self, parent, optimisers, parameters):
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.optimisers = optimisers
        self.parameters = parameters

        self.initUi()

    def initUi(self):
        """
        Generate the GUI
        """
        self.parent.protocol('WM_DELETE_WINDOW', self.close)

        # The dialog showing calculation progress
        self.progress_window = Tkinter.Toplevel(self.parent)
        self.progress_frame = ShowProgress(self.progress_window,
                self.parameters)
        self.progress_window.withdraw()

        # The dialogs for showing the final results
        self.point_window = Tkinter.Toplevel(self.parent)
        self.point_frame = PointDetails(self.point_window, self.parameters)
        self.point_window.withdraw()

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
        self.Toutput_params = ttk.Treeview(self.parent, columns=("measurements", "delay", "maxmin", "inj"))
        self.Toutput_params.column("measurements", width=120)
        self.Toutput_params.heading("measurements", text="Measurements")
        self.Toutput_params.column("delay", width=120)
        self.Toutput_params.heading("delay", text="Delay /s")
        self.Toutput_params.column("maxmin", width=80)
        self.Toutput_params.heading("maxmin", text="Target")
        self.Toutput_params.column("inj", width=120)
        self.Toutput_params.heading("inj", text="Injection Settings")
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
        self.btn_output_params_add.grid(row=1, column=3, rowspan=1, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.lifetime_add = Tkinter.Button(self.parent, text="Add Lifetime", command=self.show_add_lifetime_window)
        self.lifetime_add.grid(row=2, column=3, rowspan=1, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_output_params_rmv = Tkinter.Button(self.parent, text="Remove", command=self.remove_obj)
        self.btn_output_params_rmv.grid(row=1, column=5, rowspan=2, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)

        ttk.Separator(self.parent, orient='horizontal').grid(row=3, column=0, columnspan=6, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)

        #SAVE DIRECTORY
        Tkinter.Label(self.parent, text="Save directory:").grid(row=4, column=0, sticky=Tkinter.E)
        self.i_save_address = Tkinter.Entry(self.parent)
        self.i_save_address.insert(0, self.parameters.save_location)
        self.i_save_address.grid(row=4, column=1, columnspan=4, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_browse_save_address = Tkinter.Button(self.parent, text="Browse...", command=self.browse_save_location)
        self.btn_browse_save_address.grid(row=4, column=5, sticky=Tkinter.E+Tkinter.W)

        ttk.Separator(self.parent, orient='horizontal').grid(row=5, column=0, columnspan=6, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)

        #ALGORITHM CHOICE
        self.optimiserChoice = Tkinter.StringVar()
        Tkinter.Label(self.parent, text="Algorithm:").grid(row=6, column=0, sticky=Tkinter.E)
        self.algo = ttk.Combobox(self.parent, textvariable=self.optimiserChoice,
                values=self.optimisers.keys(), state='readonly')
        self.algo.current(0)
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

        # The dialog for adding input parameters
        self.add_pv = AddPv(self, self.parameters)
        self.add_pv.hide()
        # The dialog for adding input group parameters
        self.add_bulk_pv = AddBulkPv(self, self.parameters)
        self.add_bulk_pv.hide()
        # The dialog for adding an objective
        self.add_obj_func = AddObjFunc(self, self.parameters.results)
        self.add_obj_func.hide()
        # The dialog for adding a lifetime proxy
        self.add_lifetime = AddLifetime(self)
        self.add_lifetime.hide()

    def close(self):
        self.parent.destroy()
        cothread.Quit()

    def run_optimisation(self):
        """
        initialises progress windows and calls on the the optimisation to begin susing function below
        """
        print "Let's go!"

        self.progress_frame.initUi()

        self.parameters.initial_settings = self.parameters.interactor.get_mp()

        self.progress_window.deiconify()
        self.progress_window.grab_set()
        cothread.Spawn(self.optimiserThreadMethod)

    def optimiserThreadMethod(self):
        global final_plot_frame

        self.parameters.initial_measurements = self.parameters.interactor.get_mr()

        #prepare folder in store_address to save fronts
        if not os.path.exists('{0}/FRONTS'.format(self.parameters.store_address)):
            os.makedirs('{0}/FRONTS'.format(self.parameters.store_address))

        ###NOW ACTUALLY CALL THE OPTIMISE FUNCTION WITHIN THE ALGORITHM FILE###
        start_time = time.time()   #START
        self.parameters.optimiser.optimise()       #OPTIMISING...
        self.parameters.keepUpdating = False
        end_time = time.time()     #STOP

        #now save details for later reference by various code (results plotting, post_analysis etc..)
        self.parameters.interactor.set_mp(self.parameters.initial_settings)
        save_details_files(datetime.datetime.fromtimestamp(start_time),
                datetime.datetime.fromtimestamp(end_time),
                self.parameters.store_address,
                self.parameters.optimiser,
                self.parameters.interactor)

        if not os.path.exists('{0}/PARAMETERS'.format(self.parameters.store_address)):
            os.makedirs('{0}/PARAMETERS'.format(self.parameters.store_address))

        if not os.path.exists('{0}/RESULTS'.format(self.parameters.store_address)):
            os.makedirs('{0}/RESULTS'.format(self.parameters.store_address))

        #save parameters and objectives as Pickle objects
        for i in range(len(self.parameters.parameters)):
            util.save_object(self.parameters.parameters[i],
                    '{0}/PARAMETERS/parameter_{1}'.format(self.parameters.store_address, i))
        for i in range(len(self.parameters.results)):
            util.save_object(self.parameters.results[i],
                    '{0}/RESULTS/result_{1}'.format(self.parameters.store_address, i))

        #save signconverter
        signConverter_file = open("{0}/signConverter.txt".format(self.parameters.store_address), 'w')
        signConverter_file.write(str(self.parameters.signConverter))
        signConverter_file.close()

        #save the mapping method between algorithm parameters to machine parameters
        ap_to_mp_mapping_file = open("{0}/ap_to_mp_mapping_file.txt".format(self.parameters.store_address), 'w')
        ap_to_mp_mapping_file.write(self.parameters.interactor.string_ap_to_mp_store())
        ap_to_mp_mapping_file.close()

        #By this point, the algorithm has finished the optimisation, and restored the machine

        #close progress window
        self.progress_window.grab_release()
        self.progress_window.withdraw()

        #show the final plot windows
        ar_labels = [mrr.ar_label for mrr in self.parameters.results]
        final_plot_window = Tkinter.Toplevel(self.parent)

        final_plot_frame = optimiser_wrapper.import_algo_final_plot(final_plot_window,
                self.point_frame.generateUi, ar_labels, self.parameters.signConverter,
                initial_config=self.parameters.initial_measurements)
        final_plot_frame.initUi()
        final_plot_window.deiconify()

    def validate_save_location(self, save_location):
        current_time_string = datetime.datetime.fromtimestamp(time.time()).strftime('%d.%m.%Y_%H.%M.%S')
        dirname = 'Optimisation@{}'.format(current_time_string)
        store_address = os.path.join(save_location, dirname)
        if not os.path.exists(store_address):
            try:
                os.makedirs(store_address)
            except OSError:
                return False
        self.i_save_address.delete(0, 'end')
        self.i_save_address.insert(0, save_location)
        self.parameters.store_address = store_address
        print 'Store address has been chosen to be ',self.parameters.store_address
        return True

    def browse_save_location(self):
        """
        Once a save location has been defined, this function creates a new folder in this location. All data will be save here.
        """
        save_location = tkFileDialog.askdirectory(initialdir=self.parameters.save_location)
        if save_location:
            self.validate_save_location(save_location)

    def show_add_pv_window(self):
        self.add_pv.restore()

    def show_add_bulk_pv_window(self):
        self.add_bulk_pv.restore()

    def show_add_obj_func_window(self):
        self.add_obj_func.restore()

    def show_add_lifetime_window(self):
        # The dialog for changing lifetime options
        self.add_lifetime.restore()

    #next two functions remove Parameters and Objectives from list (if required)
    def remove_pv(self):
        for sel in self.Tinput_params.selection():
            print('Removing parameter {}'.format(sel))
            for mpgrn, mpgr in enumerate(self.parameters.parameters):
                if mpgr.list_iid == sel:
                    self.Tinput_params.delete(sel)
                    del self.parameters.parameters[mpgrn]

    def remove_obj(self):
        for sel in self.Toutput_params.selection():
            print('Removing objective {}'.format(sel))
            for mrrn, mrr in enumerate(self.parameters.results):
                if mrr.list_iid == sel:
                    self.Toutput_params.delete(sel)
                    del self.parameters.results[mrrn]

    def validate_parameters(self):
        """
        Validate the parameters to be used.
        """
        if not self.validate_save_location(self.i_save_address.get()):
            tkutil.ErrorPopup(self.parent,
                              "No save directory",
                              "Please specify a save directory")
            return False
        if not self.parameters.parameters:
            tkutil.ErrorPopup(self.parent,
                              "No parameters set",
                              "No parameters set")
            return False
        if not self.parameters.results:
            tkutil.ErrorPopup(self.parent,
                              "No objectives set",
                              "No objectives set")

            return False
        # If not a simulation, check that all the configured PVs exist.
        if self.parameters.useMachine:
            param_pvs = []
            try:
                for p in self.parameters.parameters:
                    for mpg in p.mp_representations:
                        param_pvs.append(mpg.mp_obj.pv)
                        pv = mpg.mp_obj.pv
                        initial_value = util.abstract_caget(pv, throw=True)
                        print('Initial value for {}: {}'.format(pv, initial_value))
                for r in self.parameters.results:
                    pv = r.mr_obj.pv
                    initial_value = util.abstract_caget(pv, throw=True)
                    print('Initial value for {}: {}'.format(pv, initial_value))
            except Exception as e:
                tkutil.ErrorPopup(self.parent,
                                  "Initial PV check failed.",
                                  "Could not fetch initial values for PVs: {}".format(e))
                return False
        # All ok
        return True

    def next_button(self):
        """
        loads Optimiser file, withdraws all windows involved with the main window
        """
        if self.validate_parameters():
            optimiser_wrapper_address = self.optimisers[self.optimiserChoice.get()]
            self.parameters.Striptool_On = self.striptool_on.get()

            # The dialog for changing algorithm settings
            self.algorithm_settings_frame = AlgorithmSettings(
                self,
                self.parameters,
                self.progress_frame)

            self.algorithm_settings_frame.load_algo_frame(optimiser_wrapper_address)
            self.algorithm_settings_frame.set_up()
            self.algorithm_settings_frame.centre_in_parent()

    def load_config(self):
        """
        Loads a previously saved configuration
        """
        print "Loading configuration..."

        root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        config_dir = os.path.join(root_dir, 'config')
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir)
            except OSError as e:
                config_dir = None
        config_file = tkFileDialog.askopenfile(initialdir=config_dir)
        if config_file is not None:
            config = pickle.load(config_file)
            self.parameters.parameters += config['parameters']
            self.parameters.results += config['results']
            config_file.close()

            self.Tinput_params.delete(*self.Tinput_params.get_children())
            self.Toutput_params.delete(*self.Toutput_params.get_children())

            for mpgr in self.parameters.parameters:

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

            for mrr in self.parameters.results:

                iid = self.Toutput_params.insert('', 'end', text=mrr.mr_label, values=(mrr.mr_obj.min_counts, mrr.mr_obj.delay, mrr.max_min_text, mrr.inj_setting_text))
                mrr.list_iid = iid

            print [i.list_iid for i in self.parameters.parameters]

    def save_config(self):
        """
        Saves a configuration that has been define don screen
        """

        config_file = tkFileDialog.asksaveasfile()
        if config_file is not None:
            config = {'parameters' : self.parameters.parameters,
                      'results' : self.parameters.results}

            pickle.dump(config, config_file)
            config_file.close()


class PointDetails(Tkinter.Frame):
    """
    This class is for the window that is shown when clicking on a point in the final Pareto front. It requires reading saved files
    that are in Pickle format.
    """

    def __init__(self, parent, parameters):
        print "INIT: Solution window"
        Tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.parameters = parameters
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

        ''' First, unpickle the mp_to_ap mapping file '''

        mapping_file = open("{0}/ap_to_mp_mapping_file.txt".format(self.parameters.store_address))
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

        btn_reset = Tkinter.Button(self.parent, text="Reset", command=self.reset_initial_config)
        btn_reset.grid(row=3, column=1, sticky=Tkinter.W+Tkinter.E, pady=10)

        for i, ap in enumerate(aps):
            tree_ap.insert('', 'end', text=self.parameters.parameters[i].ap_label, values=(ap))

        for i, ar in enumerate(ars):
            tree_ar.insert('', 'end', text=self.parameters.results[i].ar_label, values=(self.parameters.signConverter[i]*ar))

        mp_labels = []
        for mpgr in self.parameters.parameters:
            for mpr in mpgr.mp_representations:
                mp_labels.append(mpr.mp_label)
        for i, mp in enumerate(mps):
            tree_mp.insert('', 'end', text=mp_labels[i], values=(mp))

        self.parent.deiconify()

    def set_state(self):
        """
        This allows the user to select a point and then to set the machine to this set of parameters
        """
        self.parameters.interactor.set_mp(self.mps)

    def reset_initial_config(self):
        """
        This allows the user to reconfigure the machine to the original settings
        """
        self.parameters.interactor.set_mp(self.parameters.initial_settings)

    def x_button(self):
        print "Exited"
        self.parent.withdraw()


class AlgorithmSettings(tkutil.DialogBox):
    """
    This class import_algo_frame class in the algorithm file. This is used to collect the algorithm settings, then the
    optimisation is started. Once this begins, all windows associated with the main window disappear.
    """

    def __init__(self, main_window, parameters, progress_frame):

        tkutil.DialogBox.__init__(self, main_window.parent)
        self.title("Algorithm settings")
        self.main_window = main_window
        self.parameters = parameters
        self.progress_frame = progress_frame

    def create_body(self):
        pass

    def set_up(self):
        """
        Generate GUI frame for algorithm settings
        """

        self.algo_frame.grid(row=0, column=0, columnspan=2, sticky=Tkinter.N+Tkinter.E+Tkinter.S+Tkinter.W, pady=10, padx=10)

        ttk.Separator(self, orient="horizontal").grid(row=1, pady=10, padx=10, sticky=Tkinter.E+Tkinter.W, columnspan=2)

        b0 = Tkinter.Button(self, text="Start...", bg="red", command=self.set_settings)
        b0.grid(row=2, column=1, sticky=Tkinter.E+Tkinter.W)

    def load_algo_frame(self, file_address):
        """
        Put import_algo_frame class in the GUI frame
        """
        module_name = 'dlsoo_{}'.format(file_address)
        module = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                '{}.py'.format(module_name))
        global optimiser_wrapper
        optimiser_wrapper = imp.load_source(module_name, module)
        self.algo_frame = optimiser_wrapper.import_algo_frame(self)

    def set_settings(self):
        """
        collect data from algorithm settings window and start optimisation
        """
        #get user defined algorithm settings
        self.parameters.reset()
        try:
            algo_settings = self.algo_frame.get_dict()
        #settings errors to ensure good data
        except ValueError as ve:
            tkutil.ErrorPopup(
                self, "Algorithm settings error",
                "{}.\n The optimisation procedure will not proceed.".format(ve))
        #show 'are you sure?' window
        else:

            #machine interactor?
            interactor = 'MACHINE' if self.parameters.useMachine else 'SIMULATOR'

            ready = tkutil.YesNoPopup.open(
                self,
                'READY?',
                'You are using the {}. '.format(interactor) +
                        'Are you sure you wish to start optimisation?')

            if ready:
                self.start(algo_settings)

    def start(self, algo_settings):
        mp_addresses = [[mpr.mp_obj for mpr in mpgr.mp_representations]
                for mpgr in self.parameters.parameters]          #gather machine parameters
        mr_addresses = []
        for mrr in self.parameters.results:
            mr_addresses.append(mrr.mr_obj)
            mrr.mr_obj.inj_setting = mrr.inj_setting
        mr_addresses = [mrr.mr_obj for mrr in self.parameters.results]                                                   #gather machine results (objectives)
        relative_settings = [mpgr.relative_setting for mpgr in
                self.parameters.parameters]                               #gather bounds for machine parameters
        ap_min_var = [mpgr.ap_min for mpgr in self.parameters.parameters]                                                #gather minimum bounds for parameter parameters
        ap_max_var = [mpgr.ap_max for mpgr in self.parameters.parameters]                                                #gather maximum bounds for parameter parameters

        #need a sign converter if any objectives are to be maximised (by default, algorithms minimise objectives)
        for mrr in self.parameters.results:
            if mrr.mr_to_ar_sign == '-':
                self.parameters.signConverter.append(-1)
            else:
                self.parameters.signConverter.append(1)

        #define the appropriate interactor depending on using machine or simulator
        interactor_class = (interactors.dls_machine_interactor_bulk_base_inj_control
                            if self.parameters.useMachine
                            else interactors.sim_machine_interactor_bulk_base)
        self.parameters.interactor = interactor_class(
            mp_addresses,
            mr_addresses,
            set_relative=relative_settings,
            results=self.parameters.results
        )
        self.parameters.interactor.beam_current_bounds = self.parameters.beam_current_bounds

        #save the interactor object to file (used in post_analysis file)
        util.save_object(self.parameters.interactor,
                '{0}/interactor.txt'.format(self.parameters.store_address))

        #find out initial settings
        initial_mp = self.parameters.interactor.get_mp()

        #initialise Optimiser class in the algorithm file using settings dictionary among other arguments
        self.parameters.optimiser = optimiser_wrapper.Optimiser(settings_dict=algo_settings,
                                                interactor=self.parameters.interactor,
                                                store_location=self.parameters.store_address,
                                                a_min_var=ap_min_var,
                                                a_max_var=ap_max_var,
                                                progress_handler=self.progress_frame.handle_progress) # Still need to add the individuals, and the progress handler

        #NOW RUN THE OPTIMISATION (using function below)
        self.destroy()
        self.main_window.run_optimisation()


class AddPv(tkutil.DialogBox):
    """
    This class is for adding a SINGLE PARAMETER.
    """

    def __init__(self, main_window, parameters):
        tkutil.DialogBox.__init__(self, main_window.parent, True)
        self.main_window = main_window
        self.parameters = parameters
        self.title('Add parameter PV')

    def create_body(self):
        self.frame = Tkinter.Frame(self)

        self.title("Add Parameter PV")
        self.setting_mode = Tkinter.IntVar()
        self.setting_mode.set(0)

        Tkinter.Label(self.frame, text="PV address:").grid(row=0, column=0, sticky=Tkinter.E)
        self.i0 = Tkinter.Entry(self.frame)
        self.i0.grid(row=0, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.frame, text="Lower bound/change:").grid(row=1, column=0, sticky=Tkinter.E)
        self.i1 = Tkinter.Entry(self.frame)
        self.i1.grid(row=1, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.frame, text="Upper bound/change:").grid(row=2, column=0, sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self.frame)
        self.i2.grid(row=2, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.frame, text="Delay /s:").grid(row=3, column=0, sticky=Tkinter.E)
        self.i3 = Tkinter.Entry(self.frame)
        self.i3.grid(row=3, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        self.r0 = Tkinter.Radiobutton(self.frame, text="Define PV bounds", variable=self.setting_mode, value=0)
        self.r0.grid(row=4, column=1, sticky=Tkinter.E+Tkinter.W)

        self.r1 = Tkinter.Radiobutton(self.frame, text="Define PV change", variable=self.setting_mode, value=1)
        self.r1.grid(row=4, column=2, sticky=Tkinter.E+Tkinter.W)

        self.b1 = Tkinter.Button(self.frame, text="Cancel", command=self.hide)
        self.b1.grid(row=5, column=1, sticky=Tkinter.E+Tkinter.W)
        self.b2 = Tkinter.Button(self.frame, text="OK", command=self.add_pv_to_list)
        self.b2.grid(row=5, column=2, sticky=Tkinter.E+Tkinter.W)

        self.frame.pack()

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
            iid = self.main_window.Tinput_params.insert('', 'end', text=details[0], values=(details[1], details[2], details[3]))

            #define parameter object
            mpgr = config.MpGroupRepresentation()
            mpr = config.MpRepresentation()
            mpr.mp_obj = config.DlsParamVar(details[0], float(details[3]))
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
            self.parameters.parameters.append(mpgr)

        self.hide()


class AddBulkPv(tkutil.DialogBox):
    """
    This class is for adding a GROUP PARAMETER.
    """

    def __init__(self, main_window, parameters):
        tkutil.DialogBox.__init__(self, main_window.parent, True)
        self.main_window = main_window
        self.parameters = parameters
        self.title("Add Bulk Parameter PVs")

    def create_body(self):
        """
        define the 'Add Bulk Parameter PVs' GUI
        """
        self.frame = Tkinter.Frame(self)

        self.setting_mode = Tkinter.IntVar()            #this is for which method of defining the parameter bounds is being used
        self.setting_mode.set(1)

        Tkinter.Label(self.frame, text="Group name:").grid(row=0, column=0, sticky=Tkinter.E, pady=(10, 0))
        self.group_name_entry = Tkinter.Entry(self.frame)
        self.group_name_entry.grid(row=0, column=1, columnspan=2, sticky=Tkinter.W+Tkinter.E, pady=(10, 0), padx=(0, 10))

        Tkinter.Label(self.frame, text="Group file (optional):").grid(row=1, column=0, sticky=Tkinter.E)
        self.i_file_address = Tkinter.Entry(self.frame)
        self.i_file_address.grid(row=1, column=1, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_browse_file_address = Tkinter.Button(self.frame, text="Add group file...", command=self.browse_save_location)
        self.btn_browse_file_address.grid(row=1, column=2, sticky=Tkinter.E+Tkinter.W)

        ttk.Separator(self.frame, orient='horizontal').grid(row=2, column=0, columnspan=3, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)
        Tkinter.Label(self.frame, text="PV names:").grid(row=3, column=0, sticky=Tkinter.E+Tkinter.W)
        Tkinter.Label(self.frame, text="Lower bounds:").grid(row=3, column=1, sticky=Tkinter.E+Tkinter.W)
        Tkinter.Label(self.frame, text="Upper bounds:").grid(row=3, column=2, sticky=Tkinter.E+Tkinter.W)

        self.pv_name_box = Tkinter.Text(self.frame, width=40)
        self.pv_name_box.grid(row=4, column=0, sticky=Tkinter.E + Tkinter.W)
        self.lower_bounds_box = Tkinter.Text(self.frame, width=40)
        self.lower_bounds_box.grid(row=4, column=1, sticky=Tkinter.E+Tkinter.W)
        self.upper_bounds_box = Tkinter.Text(self.frame, width=40)
        self.upper_bounds_box.grid(row=4, column=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.frame, text="Change:").grid(row=5, column=0, sticky=Tkinter.E)

        self.lower_bound_entry = Tkinter.Entry(self.frame)
        self.lower_bound_entry.grid(row=5, column=1, sticky=Tkinter.E+Tkinter.W)

        self.upper_bound_entry = Tkinter.Entry(self.frame)
        self.upper_bound_entry.grid(row=5, column=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.frame, text="Delay:").grid(row=6, column=0, sticky=Tkinter.E)
        self.delay_entry = Tkinter.Entry(self.frame)
        self.delay_entry.grid(row=6, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        self.r0 = Tkinter.Radiobutton(self.frame, text="Define PV Change", variable=self.setting_mode, value=0)
        self.r0.grid(row=7, column=1)

        self.r2 = Tkinter.Radiobutton(self.frame, text="Define PV Bounds", variable=self.setting_mode, value=1)
        self.r2.grid(row=7, column=0)

        self.b0 = Tkinter.Button(self.frame, text="Cancel", command=self.hide)
        self.b0.grid(row=8, column=1, sticky=Tkinter.E+Tkinter.W)

        self.b1 = Tkinter.Button(self.frame, text="Add", command=self.add_pvs)
        self.b1.grid(row=8, column=2, sticky=Tkinter.E+Tkinter.W)
        self.frame.pack()

    def browse_save_location(self):
        """
        This class is for reading a csv file with list of parameter PVs, which are then put into the column of parameter PVs in the 'Add Bulk Parameter PVs' window
        """
        pv_file = tkFileDialog.askopenfile()
        if pv_file is not None:
            self.i_file_address.delete(0, 'end')
            self.i_file_address.insert(0, pv_file.name)

            with open(pv_file.name, 'r') as f:
                all_pvs = [line.strip() for line in f.readlines()]
                self.pv_name_box.insert(Tkinter.END, '\n'.join(all_pvs))

    def _get_entry_value(self, entry, name, conversion):
        try:
            value = entry.get()
            setattr(self, name, conversion(value))
        except ValueError:
            raise InvalidEntry(
                'Format error for {}'.format(name),
                'Value for {} ("{}") could not be converted to a {}.'.format(
                    name, value, conversion
                )
            )

    def verify_entries(self):
        self.group_name = self.group_name_entry.get().strip()
        if not self.group_name:
            raise InvalidEntry('No group name', 'No group name specified')
        self.use_bounds = bool(self.setting_mode.get())
        all_pv_names = self.pv_name_box.get(0.0, Tkinter.END).strip()
        if not all_pv_names:
            raise InvalidEntry('No PV names', 'No PV names specified')
        self.pv_names = [line.strip() for line in all_pv_names.splitlines()]

        self._get_entry_value(self.lower_bound_entry, 'lower_bound', float)
        self._get_entry_value(self.upper_bound_entry, 'upper_bound', float)
        self._get_entry_value(self.delay_entry, 'delay', float)

        all_lower_bounds = self.lower_bounds_box.get(0.0, Tkinter.END).strip()
        if all_lower_bounds:
            self.lower_bounds = [float(line.strip()) for line in all_lower_bounds.splitlines()]
        else:
            self.lower_bounds = [self.lower_bound] * len(self.pv_names)
        all_upper_bounds = self.upper_bounds_box.get(0.0, Tkinter.END).strip()
        if all_upper_bounds:
            self.upper_bounds = [float(line.strip()) for line in all_upper_bounds.splitlines()]
        else:
            self.upper_bounds = [self.upper_bound] * len(self.pv_names)

        print(self.lower_bound_entry)

        if not self.use_bounds and self.lower_bound > 0:
            raise InvalidEntry(
                "Input Error",
                "The lower change must be less than or equal to zero"
            )

    def add_pvs(self):
        """
        Once the group PV has been defined, create a group parameter object
        """
        try:
            self.verify_entries()
        except InvalidEntry as e:
            tkMessageBox.showerror(e.header, e.msg)
            return

        mpgr = config.MpGroupRepresentation()
        for pv in self.pv_names:
            mpr = config.MpRepresentation()
            mpr.mp_obj = config.DlsParamVar(pv, self.delay)
            mpr.mp_label = pv
            mpgr.mp_representations.append(mpr)

        print "mpgr to be added: {0}".format([i.mp_label for i in mpgr.mp_representations])

        if self.use_bounds:
            mpgr.relative_setting = False
        else:
            # This means we are setting according to the change, not the bounds
            mpgr.relative_setting = True

        mpgr.ap_min = self.lower_bound
        mpgr.ap_max = self.upper_bound

        # Insert information of group parameter into main window
        parent_iid = self.main_window.Tinput_params.insert(
            '', 'end',
            text=self.group_name,
            values=(mpgr.ap_min, mpgr.ap_max, self.delay)
        )
        mpgr.list_iid = parent_iid

        for i, mpr in enumerate(mpgr.mp_representations):
            print "ADDING GROUP PARAMETER"
            iid = self.main_window.Tinput_params.insert(
                parent_iid,
                'end',
                text=self.pv_names[i],
                values=(self.lower_bounds[i],
                        self.upper_bounds[i],
                        self.delay)
            )
            mpr.list_iid = iid

        mpgr.ap_label = self.group_name
        self.parameters.parameters.append(mpgr)

        self.hide()


class StripPlot(Tkinter.Frame):
    """
    This class produces the Striptool plot, which is not used by default
    """

    def __init__(self, parent, progress_frame, interactor):

        Tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.progress_frame = progress_frame
        self.interactor = interactor
        self.initUi()

    def initUi(self):
        """
        define GUI
        """
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


class ShowProgress(Tkinter.Frame):
    """
    This class is for the progress window that appears during an optimisation. It includes a plot showing the calculated Pareto fronts
    as well as a percentage bar. The window has Pause and Cancel buttons that provide ease of use. The pause button will complete the
    measurement and then pause whilst the Cancel button will stop will complete the current measurement and then finish the optimisation.
    A striptool option can also be added but it is turned off by default (this can be changed in the main window GUI).
    """
    def __init__(self, parent, parameters):
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.parameters = parameters
        #variables for progress percentage
        self.progress = Tkinter.DoubleVar()
        self.progress.set(0.0)

    def initUi(self):
        """
        Define GUI
        """
        self.progress.set(0.0)
        self.parent.title("Optimising...")

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)

        self.pbar_progress = ttk.Progressbar(self.parent, length=400,
                variable=self.progress)
        self.pbar_progress.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

        #optional striptool feature (recommended to the user to be turned off (==0)
        if self.parameters.Striptool_On == 1:
            self.strip_plot = StripPlot(self.parent, self.pbar_progress)
            self.strip_plot.grid(row=2, column=0, columnspan=4)

        #cancel method
        self.btn_cancel = Tkinter.Button(self.parent, text="Cancel", command=self.cancelMethod)
        self.btn_cancel.grid(row=1, column=3, sticky=Tkinter.W+Tkinter.E)

        #pause method
        self.btn_pause = Tkinter.Button(self.parent, text="Pause", command=self.pause_algo)
        self.btn_pause.grid(row=1, column=2, sticky=Tkinter.E+Tkinter.W)

        # This part will display the latest plot
        ar_labels = [mrr.ar_label for mrr in self.parameters.results]
        #import_algo_prog_plot class from chosen algorithm
        self.progress_plot = optimiser_wrapper.import_algo_prog_plot(
                self.parent,
                ar_labels,
                self.parameters.signConverter
                )
        self.progress_plot.grid(row=3, column=0, columnspan=4)
        print "INIT: Progress window"

    def handle_progress(self, normalised_percentage, generation):
        """
        updates the percentage bar and plots using functions in the import_algo_prog_plot class in the chosen algorithm file
        """
        self.progress.set(normalised_percentage * 100)
        self.update()

        if self.parameters.Striptool_On == 1:
            self.strip_plot.update()

        self.progress_plot.update()

    def pause_algo(self):
        """
        This method pauses the algorithm
        """
        print "Pausing"
        self.parameters.optimiser.pause = not self.parameters.optimiser.pause

        if self.parameters.optimiser.pause:
            self.btn_pause.config(text="Unpause")
            self.parent.config(background="red")
        else:
            self.btn_pause.config(text="Pause")
            self.parent.config(background="#d9d9d9")

    def cancelMethod(self):
        """
        This method cancels the algorithm
        """
        self.parameters.optimiser.cancel = True


class PlotProgress(Tkinter.Frame):
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


class AddLifetime(tkutil.DialogBox):
    """
    This class is for adding LIFETIME PROXY as an objective
    """

    def __init__(self, main_window):
        tkutil.DialogBox.__init__(self, main_window.parent, True)
        self.main_window = main_window
        self.title('Add Lifetime PV')

    def create_body(self):
        """
        Generate 'Add Lifetime PV' GUI
        """
        self.frame = Tkinter.Frame(self)

        self.max_min_setting = Tkinter.IntVar()
        self.max_min_setting.set(1)                     #this setting is for choosing whether objective will maximised or minimised

        self.inj_setting = Tkinter.IntVar()
        self.inj_setting.set(0)                         #0 means don't inject, 1 means inject

        Tkinter.Label(self.frame, text="PV address:").grid(row=0, column=0, sticky=Tkinter.E)
        self.i0 = Tkinter.Entry(self.frame)
        self.i0.grid(row=0, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)
        self.i0.insert(0, 'lifetime_proxy')
        self.i0['state'] = 'disabled'                   #the PV address must be 'lifetime_proxy'

        Tkinter.Label(self.frame, text="Measurements:").grid(row=1, column=0, sticky=Tkinter.E)
        self.i1 = Tkinter.Entry(self.frame)
        self.i1.grid(row=1, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.frame, text="Delay /s:").grid(row=2, column=0, sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self.frame)
        self.i2.grid(row=2, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        self.r0 = Tkinter.Radiobutton(self.frame, text="Minimise", variable=self.max_min_setting, value=0)
        self.r0.grid(row = 3, column=0, sticky=Tkinter.W)
        self.r1 = Tkinter.Radiobutton(self.frame, text="Maximise", variable=self.max_min_setting, value=1)
        self.r1.grid(row = 3, column=1, sticky=Tkinter.W)

        self.r2 = Tkinter.Radiobutton(self.frame, text="Non-injection", variable = self.inj_setting, value=0)
        self.r2.grid(row=4, column=0, sticky=Tkinter.W)

        self.r3 = Tkinter.Radiobutton(self.frame, text="Injection", variable = self.inj_setting, value=1)
        self.r3.grid(row=4, column=1, sticky=Tkinter.W)

        ttk.Separator(self.frame, orient='horizontal').grid(row=5, column=0, columnspan=3, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)

        """ The user must also define the number of bunches as well as min/max beam current for the proxy equation to hold """

        Tkinter.Label(self.frame, text="Number of bunches:").grid(row=6, column=0, sticky=Tkinter.E)
        self.i4 = Tkinter.Entry(self.frame)
        self.i4.grid(row=6, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.frame, text="Min. Beam Current (mA):").grid(row=7, column=0, sticky=Tkinter.E)
        self.i5 = Tkinter.Entry(self.frame)
        self.i5.grid(row=7, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.frame, text="Max. Beam Current (mA)").grid(row=8, column=0, sticky=Tkinter.E)
        self.i6 = Tkinter.Entry(self.frame)
        self.i6.grid(row=8, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        self.b1 = Tkinter.Button(self.frame, text="Cancel", command=self.hide)
        self.b1.grid(row=9, column=1, sticky=Tkinter.E+Tkinter.W)
        self.b2 = Tkinter.Button(self.frame, text="OK", command=self.add_pv_to_list)
        self.b2.grid(row=9, column=2, sticky=Tkinter.E+Tkinter.W)

        self.frame.pack()

    def add_pv_to_list(self):
        """
        Once objective has been defined, create object for the objective
        """
        #create object
        mrr = config.MrRepresentation()

        #retrieve information from GUI
        mrr.mr_obj = config.DlsMeasurementVar(self.i0.get(), float(self.i1.get()), float(self.i2.get()))

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
        mrr.inj_setting =  self.inj_setting.get()
        if self.inj_setting.get() == 0:
            mrr.inj_setting_text = "Non-injection"
        elif self.inj_setting.get() == 1:
            mrr.inj_setting_text = "Injection"

        iid = self.main_window.Toutput_params.insert('', 'end', text=self.i0.get(), values=(self.i1.get(), self.i2.get(), mrr.max_min_text, mrr.inj_setting_text))
        mrr.list_iid = iid
        mrr.mr_label = self.i0.get()
        mrr.ar_label = "{0}{1}".format(mrr.max_min_sign, self.i0.get())

        self.main_window.parameters.results.append(mrr)

        #now retrieve and set beam dynamics using ca_abstraction_mapping.py
        number_of_bunches = float(self.i4.get())
        beam_current_min = float(self.i5.get())
        beam_current_max = float(self.i6.get())

        # Set variable for use in lifetime_proxy_function
        print('setting number of bunches to {}'.format(number_of_bunches))
        ca_abstraction_mapping.NUMBER_OF_BUNCHES = number_of_bunches
        self.main_window.parameters.beam_current_bounds = beam_current_min, beam_current_max

        self.hide()


class AddObjFunc(tkutil.DialogBox):
    """This class is for adding an objective."""

    def __init__(self, main_window, results):
        tkutil.DialogBox.__init__(self, main_window.parent, True)
        self.main_window = main_window
        self.results = results
        self.title('Add objective PV')

    def create_body(self):
        """Define 'Add Objective PV' GUI"""
        self.frame = Tkinter.Frame(self)

        self.max_min_setting = Tkinter.IntVar()
        self.max_min_setting.set(0)                 #this setting is for choosing whether objective will maximised or minimised

        self.inj_setting = Tkinter.IntVar()
        self.inj_setting.set(0)  # 0 means don't inject, 1 means inject

        Tkinter.Label(self.frame, text="PV address:").grid(row=0, column=0,
                                                            sticky=Tkinter.E)
        self.i0 = Tkinter.Entry(self.frame)
        self.i0.grid(row=0, column=1, columnspan=2,
                     sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self.frame, text="Measurements:").grid(row=1, column=0,
                                                            sticky=Tkinter.E)
        self.i1 = Tkinter.Entry(self.frame)
        self.i1.grid(row=1, column=1, columnspan=2,
                     sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self.frame, text="Delay /s:").grid(row=2, column=0,
                                                          sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self.frame)
        self.i2.grid(row=2, column=1, columnspan=2,
                     sticky=Tkinter.E + Tkinter.W)

        self.r0 = Tkinter.Radiobutton(self.frame, text="Minimise",
                                      variable=self.max_min_setting, value=0)
        self.r0.grid(row=3, column=0, sticky=Tkinter.W)
        self.r1 = Tkinter.Radiobutton(self.frame, text="Maximise",
                                      variable=self.max_min_setting, value=1)
        self.r1.grid(row=3, column=1, sticky=Tkinter.W)

        self.r2 = Tkinter.Radiobutton(self.frame, text="Non-injection",
                                      variable=self.inj_setting, value=0)
        self.r2.grid(row=4, column=0, sticky=Tkinter.W)

        self.r3 = Tkinter.Radiobutton(self.frame, text="Injection",
                                      variable=self.inj_setting, value=1)
        self.r3.grid(row=4, column=1, sticky=Tkinter.W)

        self.b1 = Tkinter.Button(self.frame, text="Cancel",
                                 command=self.hide)
        self.b1.grid(row=5, column=1, sticky=Tkinter.E + Tkinter.W)
        self.b2 = Tkinter.Button(self.frame, text="OK",
                                 command=self.add_pv_to_list)
        self.b2.grid(row=5, column=2, sticky=Tkinter.E + Tkinter.W)

        self.frame.pack()

    def add_pv_to_list(self):
        """
        Once objective has been defined, create object for the objective
        """
        #create object
        mrr = config.MrRepresentation()

        # retrieve information from GUI
        mrr.mr_obj = config.DlsMeasurementVar(self.i0.get(),
                                              float(self.i1.get()),
                                              float(self.i2.get()))

        # max/min settings
        if self.max_min_setting.get() == 0:
            mrr.max_min_text = "Minimise"
            mrr.max_min_sign = "+"
            mrr.mr_to_ar_sign = "+"
        elif self.max_min_setting.get() == 1:
            mrr.max_min_text = "Maximise"
            mrr.max_min_sign = "-"
            mrr.mr_to_ar_sign = "-"

        # injection/non-injection settings
        mrr.inj_setting = self.inj_setting.get()
        if self.inj_setting.get() == 0:
            mrr.inj_setting_text = "Non-injection"
        elif self.inj_setting.get() == 1:
            mrr.inj_setting_text = "Injection"

        iid = self.main_window.Toutput_params.insert('', 'end',
                                                    text=self.i0.get(),
                                                    values=(self.i1.get(),
                                                            self.i2.get(),
                                                            mrr.max_min_text,
                                                            mrr.inj_setting_text))
        mrr.list_iid = iid
        mrr.mr_label = self.i0.get()
        mrr.ar_label = "{0}{1}".format(mrr.max_min_sign, self.i0.get())

        self.main_window.parameters.results.append(mrr)
        self.hide()
