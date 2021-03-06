'''
MULTI-OBJECTIVE SIMULATED ANEALING ALGORITHM
@authors: Greg Henderson
@algorithm variation designer: Gareth Bird
'''

from __future__ import division
import numpy
import math
import os
import random
from scipy import stats

import Tkinter
import ttk

from dlsoo import plot, tkutil, util
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

#define a global store address so that the program can store the fronts for plotting
#completed_generation is used to keep track of files that store the front infomration
store_address = None
completed_generation = 0


#The following is a list of functions useful to the Optimiser bolow
#used to deal with the case of progress handler for the Optimiser class
def nothing_function(data, x):
    '''
    Used as a substitute when there is no progress_handler given.
    '''
    pass


def is_dominated(x,y):
    '''
    Takes in two lists of numbers, x and y, to see if x dominates y.
    '''
    isLarger = False
    isLargerEqual = True
    for i in range(len(x)):
        if x[i] < y[i]:
            isLarger = True
        if x[i] > y[i]:
            isLargerEqual = False
    return (isLargerEqual and isLarger)


def probCalc(newObj, oldObj, temp):
    '''
    calculate the acceptance probability for a new set of parameters
    Takes in old Objectives and new Objectives with the tempertures to calculate P.
    '''
    exponent = 0
    for i in range(len(newObj)):
        exponent = exponent + (newObj[i] - oldObj[i])/temp[i]
    return min(1, numpy.exp(-exponent))


def addRanGuass(params, temp, upBound, downBound):
    '''
    adds gaussian onto the parameters ensuring that it is stil in bounds
    this version uses truncated gaussian so as to aviod long loops.
    '''
    newPoint = []
    for i in range(len(temp)):
        x = stats.truncnorm((downBound[i] - params[i])/temp[i],(upBound[i] - params[i])/temp[i], loc = params[i], scale=temp[i]).rvs(size=1)[0]
        #generate the truncated normal and then generage the random number to then etract it from the array.
        newPoint.append(x)
    return newPoint


class Optimiser(object):
    '''
    This is the Optimiser class which deals with the actual optimisation process.
    '''
    def __init__(self, settings_dict, interactor, store_location, a_min_var, a_max_var, individuals=None, progress_handler=None):
        self.interactor = interactor    #The interactor is what allows the program to evalute objectives.
        self.param = []                 #this keeps track of where in parameter space MOSA is.
        self.up = a_max_var             #upper bounds on parameters stored as a list.
        self.down = a_min_var           #This is the lower bounds on the parameters stored as a list.
        self.nOIterations = settings_dict['noIterations']   #This is the number of points MOSA can accept in one anneal.
        self.nOAneals = settings_dict['noAneals']           #This specifies the number of anneals that will be performed overall.
        self.failDropCount = settings_dict['failDropCount'] #This specifies how many failed attemps to find a new point occour before the input tempertures are reduced slightly.
        self.paramCount = len(interactor.param_var_groups)  #This allows the algorithm to keep track of the number of parameters
        self.objCount = len(interactor.measurement_vars)    #This lets the algorithm now the number of objectives
        self.passOutTempDrop = self.objCount*[settings_dict['passOutTempDrop']] #This is a list of temperture drops
        self.passInTempDrop = self.paramCount*[settings_dict['passInTempDrop']] #This is a list of temperture drops
        self.anealPlot = settings_dict['anealPlot']         #This tells the algorithm whne to plot the front
        self.progress_handler = progress_handler            #This is a callable function that lets the opimiser to communicate progress to the GUI.
        self.inTemp = []                                    #This keeps track of the input tempertures
        self.outTemp = []                                   #Keeps track of the output tempertures
        self.domFrontParam = []                             #keeps track of the points in parameter space that is the current algorithm front.
        self.domFrontObjectives = []                        #keeps track of the points of the front in objective space.
        self.domFrontErrors = []                            #keeps track of the error on each objective on the front in objective space.
        self.domFrontDevs = []                              #attribute to track standard deviation added rhs 17/07/18
        #dumpFlag is used to let the algorithm know to save the front every so often
        try:
            self.dumpFlag = settings_dict['dumpFlag']
        except:
            self.dumpFlag = True
        #try statement used as this might not be in settings_dict
        if progress_handler == None:
            self.progress_handler = nothing_function
        else:
            self.progress_handler = progress_handler
        self.objCallStop = settings_dict['objCallStop']     #lets the algorithm know the maximum number of measurements that can be made.
        self.store_location = store_location                #This is the location where the front data is stored.
        self.pause = False                                  #used to pause the algorithm
        self.cancel = False                                 #used to cancel the current run of the algorithm.
        if settings_dict['add_current_to_individuals'] == True:     #To keep track of wether the the algorithm should start from the current machine state or not.
            self.initParams = interactor.get_ap()                   #set the inital parameters accordingly.
        else:
            self.initParams = []
        #pause is used to allow the main GUI to pause the algorithm.

    def getObjectives(self):
        '''
        Allows the algorithm to obtain the objectives from what the current parameters are.
        '''
        #first we must set the machine to the desired parameter values
        self.interactor.set_ap(self.param)
        #now ask for a measurement
        measure = self.interactor.get_ar()
        #now extract the mean measurment values. The above function returns the measurment as a list of objects that are instances of the
        #the measurment class in dls_optimiser_util
        f = [i.mean for i in measure]
        unc = [i.err for i in measure]
        dev = [i.dev for i in measure] #rhs extracting deviation for plotting 17/07/18
        return (f, unc, dev)

    def setUnifRanPoints(self):
        '''
        sets the optimisers parameters to somewhere random in their range of allowed values.
        '''
        self.param = [random.uniform(self.down[i], self.up[i]) for i in range(self.paramCount)]

    def setIinitOutTemp(self):
        '''
        set the initial output temperture
        '''
        numTestPoints = min(2**len(self.up), 16)
        testResults = []
        #essentially preform a test and take some averages of the function values to set the temperture
        for i in range(numTestPoints):
            self.setUnifRanPoints()
            objectiveEval = self.getObjectives()
            testResults.append(objectiveEval[0])
        for i in range(self.objCount):
            newTemp = util.mean(util.extract_column(testResults, i))
            self.outTemp.append(newTemp)

    def setNewOutTemp(self, objMin):
        '''
        set the new ouput temperture. Used after every aneal
        '''
        zero = True
        while zero:
            self.outTemp = [abs(random.gauss(2*(objMin[i]),4*abs(objMin[i]))) for i in range(self.objCount)]
            #The new tempertures are based on a normal distrobution with mean and standard deviation based on min, max obj values from the previous aneal.
            if not (0 in self.outTemp):
                zero = False

    def setNewInTemp(self):
        '''
        set the input temperture after an aneal according to the range of allowed values.
        '''
        zero = True
        while zero:
            range1 = [(self.up[i] - self.down[i])/2 for i in range(self.paramCount)]
            self.inTemp = [abs(random.gauss(range1[i]/5, range1[i]/2)) for i in range(self.paramCount)]
            if not (0 in self.inTemp):
                zero = False

    def updateParetoFront(self, newObj):
        '''
        loop through the dominated front and see if the new solution can be added and remove
        any elements dominated by the new solution.
        '''
        notDom = True
        dominatedElements = []
        for i in range(len(self.domFrontObjectives)):
            if is_dominated(self.domFrontObjectives[i], newObj[0]):
                notDom = False
            elif is_dominated(newObj[0], self.domFrontObjectives[i]):
                dominatedElements.append(i)
        if notDom:
            self.domFrontObjectives.append(newObj[0])
            self.domFrontErrors.append(newObj[1])
            self.domFrontDevs.append(newObj[2]) #front deviation added rhs 17/07/18
            self.domFrontParam.append(self.param)
            #now to delete the elements use x to keep track of how many are deleted
            self.domFrontObjectives = [self.domFrontObjectives[i] for i in range(len(self.domFrontObjectives)) if not (i in dominatedElements)]
            self.domFrontParam = [self.domFrontParam[i] for i in range(len(self.domFrontParam)) if not (i in dominatedElements)]
            self.domFrontErrors = [self.domFrontErrors[i] for i in range(len(self.domFrontErrors)) if not (i in dominatedElements)]
            self.domFrontDevs = [self.domFrontDevs[i] for i in range(len(self.domFrontDevs)) if not (i in dominatedElements)] #added for standard deviation error rhs 17/07/18

    def dumpFront(self):
        '''
        at the end in order to plot the fronts we need to save a python file defining the fronts vairalbe which is then used to plot the data.
        '''
        f = file("{0}/FRONTS/fronts.{1}".format(self.store_location, completed_generation), "w")
        f.write('fronts = ((\n')
        #we need two ( so that this code is consistent with the DLS plot library.
        for i in range(len(self.domFrontObjectives)):
            f.write('({0}, {1}, {2}, {3}), \n'.format(tuple(self.domFrontParam[i][:]),tuple(self.domFrontObjectives[i][:]), tuple(self.domFrontErrors[i][:]), tuple(self.domFrontDevs[i][:]))) #added devs to front dump rhs 17/07/18
        f.write('),) \n')
        f.close()

        pass

    def save_details_file(self):
        '''
        when the optimsation is finished this is called in order to save the settings of the algorithm.
        '''
        file_return = ''

        file_return += 'dlsoo_mosa.py algorithm\n'
        file_return += '===================\n\n'
        file_return += 'Number of Aneals: {0}\n'.format(self.nOAneals)
        file_return += 'Number of iterations: {0}\n'.format(self.nOIterations)

        file_return += 'Parameter count: {0}\n'.format(self.paramCount)
        file_return += 'Objective count: {0}\n'.format(self.objCount)
        file_return += 'Output temperature drop: {0}\n'.format(self.passOutTempDrop)
        file_return += 'Minimum parameters: {0}\n'.format(self.down)
        file_return += 'Maximum parameters: {0}\n'.format(self.up)
        file_return += 'Fail drop count: {0}\n'.format(self.failDropCount)
        file_return += 'Maximum number of measurements: {0}\n'.format(self.objCallStop)

        return file_return

    def optimise(self):
        '''
        This method runs the actual optimisation process.
        '''
        global store_address
        #Store address keeps track of where we store the output of dumpFront
        global completed_generation
        #completed_generation keeps track of how many fronts have been saved.
        store_address = self.store_location
        currentParams = []
        currentObj = ()
        #Two lists above for storing old values whilst new parameters are tested.
        objCall = 0
        #this variable is used to keep track of the number of times we have evaluted the objectives.
        collectivePointCount = 0
        #this variable is used to keep track of progress
        if self.initParams == []:
            self.setUnifRanPoints()
        else:
            self.param = self.initParams
        currentParams = self.param
        currentObj = self.getObjectives()
        #initialise the pareto fronts
        self.domFrontParam.append(currentParams)
        self.domFrontObjectives.append(currentObj[0])
        self.domFrontErrors.append(currentObj[1])
        self.domFrontDevs.append(currentObj[2]) #rhs deviation error 17/07/18
        self.setIinitOutTemp()
        #set the initial input temperture
        self.inTemp = [(self.up[i] - self.down[i])/2 for i in range(self.paramCount)]
        performAneal = True
        aneal = 0
        maxPoints = self.nOAneals*self.nOIterations
        while performAneal:
            aneal += 1
            pointCount = 0
            failCount = 0
            minObjectives = currentObj[0]
            keepIterating = True
            x = 0
            #initialise the current minimum objectives. This variable will be used to keep track of the minimum objectives so as to help in calculating the new output temperture.
            while keepIterating:
                x = x + 1
                self.param = addRanGuass(currentParams, self.inTemp, self.up, self.down)
                #generate a new parameter set
                newObjectives = self.getObjectives()
                #and measure the objective values
                objCall = objCall + 1
                #print newObjectives
                #Keep track of how many measurments have been made.
                p = probCalc(newObjectives[0], currentObj[0], self.outTemp)
                #calculate the acceptance probability
                if random.uniform(0,1) <= p:
                    currentParams = self.param
                    currentObj = newObjectives
                    pointCount = pointCount + 1
                    collectivePointCount += 1
                    self.updateParetoFront(currentObj)
                    #update the minimum objective values
                    minObjectives = [min(currentObj[0][i], minObjectives[i]) for i in range(self.objCount)]
                    failCount = max(math.trunc(failCount/2), 0)
                    #drop the tempertures the tempertures
                    self.inTemp = [self.passInTempDrop[i]*self.inTemp[i] for i in range(self.paramCount)]
                    self.outTemp = [self.passOutTempDrop[i]*self.outTemp[i] for i in range(self.objCount)]
                    self.progress_handler(float(collectivePointCount)/float(maxPoints), collectivePointCount)
                    #update the progress
                else:
                    failCount = failCount + 1
                    #print 'Fail count: {0}'.format(failCount)
                    #reduce input temperture slightly
                    self.inTemp = [0.95**(max(self.failDropCount, failCount) - self.failDropCount)*self.inTemp[i] for i in range(self.paramCount)]
                #check to see if enough ponits have been checked and if so leave this loop
                if pointCount == self.nOIterations:
                    keepIterating = False
                if x == (self.nOIterations*10):
                    print 'failed to complete in 10*(number of iterations) check code'
                    print pointCount
                    keepIterating = False
                if objCall >= self.objCallStop:
                    keepIterating = False
                    performAneal = False
                elif self.cancel:
                    keepIterating = False
                    self.performAneal = False
                while self.pause:
                    #if it is in pause mode this will keep it paused
                    self.progress_handler(float(collectivePointCount)/float(maxPoints), collectivePointCount)
            maxPoints = maxPoints + pointCount - self.nOIterations
            #update, based on current information, the maximum number of points the algorithm will try.
            #set the new tempertures for a new anneal
            self.setNewInTemp()
            self.setNewOutTemp(minObjectives)
            #now set new starting point from the pareto front by method outlined in report
            objCollect = [[y[i] for y in self.domFrontObjectives] for i in range(self.objCount)]
            minParetoObj = [min(obj) for obj in objCollect]
            maxParetoObj = [max(obj) for obj in objCollect]
            ranPoint = [random.uniform(minParetoObj[i], maxParetoObj[i]) for i in range(self.objCount)]
            distances = [sum([(obj[i] - ranPoint[i])**2 for i in range(self.objCount)]) for obj in self.domFrontObjectives]
            newPoint = distances.index(min(distances))
            currentObj = (self.domFrontObjectives[newPoint], self.domFrontErrors[newPoint])
            currentParams = self.domFrontParam[newPoint]
            if aneal >= self.nOAneals:
                performAneal = False
            if (aneal % self.anealPlot) == 0 and self.dumpFlag:
                #update the front files and let the GUI know of the progress
                completed_generation += 1
                self.dumpFront()
                self.progress_handler(float(collectivePointCount)/float(maxPoints), collectivePointCount)
        if self.dumpFlag:
            self.dumpFront()

class import_algo_frame(Tkinter.Frame):
    '''
    this class deals with the GUI for the algorithm. The main GUI will call this to get algorithm settings and so is called before optimise.
    '''
    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.initUi()

    def initUi(self):
        #this generates a number of widgets in the algorithm frame to input the settings with.
        self.add_current_to_individuals = Tkinter.BooleanVar(self)
        self.add_current_to_individuals.set(True)

        Tkinter.Label(self, text='Input temperature cooling ratio:').grid(row=2, column=0, sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self)
        self.i2.grid(row=2,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Output temperature cooling ratio:').grid(row=3, column=0, sticky=Tkinter.E)
        self.i3 = Tkinter.Entry(self)
        self.i3.grid(row=3,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Number of anneals:').grid(row=4, column=0, sticky=Tkinter.E)
        self.i4 = Tkinter.Entry(self)
        self.i4.grid(row=4,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Number of iterations:').grid(row=5, column=0, sticky=Tkinter.E)
        self.i5 = Tkinter.Entry(self)
        self.i5.grid(row=5,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Fail drop count').grid(row=6, column=0, sticky=Tkinter.E)
        self.i6 = Tkinter.Entry(self)
        self.i6.grid(row=6,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Maximum number of measurements').grid(row=7, column=0, sticky=Tkinter.E)
        self.i7 = Tkinter.Entry(self)
        self.i7.grid(row=7,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Number of anneals between plotting front:').grid(row=8, column=0, sticky=Tkinter.E)
        self.i8 = Tkinter.Entry(self)
        self.i8.grid(row=8, column=1, sticky=Tkinter.E + Tkinter.W)

        self.c0 = Tkinter.Checkbutton(self, text='Use current machine state', variable=self.add_current_to_individuals)
        self.c0.grid(row=9,column=0)

        Tkinter.Label(self, text="Recommendations:\nUse as scanning tool when good points not known and then implement GA when the front stops significantly improving\nDo not use if an objective function's best value approaches zero: Ideally the function's 'worst' value should be set to zero \nLength of cycle ~35 if ratios unchanged from default, else refer to doccumentation", justify=Tkinter.LEFT).grid(row=10, column=0, columnspan=2, sticky=Tkinter.W)

        self.i2.insert(0, '0.9')
        self.i3.insert(0, '0.87')
        self.i4.insert(0, '5')
        self.i5.insert(0, "35")
        self.i6.insert(0, "1")
        self.i7.insert(0, "500")
        self.i8.insert(0, '1')

    def get_dict(self):
        #extracts the inputted settings to put in settings dictionary
        setup = {}
        try:
            setup['passInTempDrop'] = float(self.i2.get())
        except:
            raise ValueError('Temperature drops input incorrectly')
        try:
            setup['passOutTempDrop'] = float(self.i3.get())
        except:
            raise ValueError('Temperature drops input incorrectly')
        try:
            setup['noAneals'] = int(self.i4.get())
        except:
            raise ValueError('Number of anneals must be an integer')
        try:
            setup['noIterations'] = int(self.i5.get())
        except:
            raise ValueError('Number of iterations must be an integer')
        try:
            setup['failDropCount'] = int(self.i6.get())
        except:
            raise ValueError('Fail drop count must be an integer')
        try:
            setup['objCallStop'] = int(self.i7.get())
        except:
            raise ValueError('Maximum number of measurements must be an integer')
        try:
            setup['anealPlot'] = int(self.i8.get())
        except:
            raise ValueError('The number of anneals before plotting must be an integer')

        if self.add_current_to_individuals.get() == 0:
            setup['add_current_to_individuals'] = False
        elif self.add_current_to_individuals.get() == 1:
            setup['add_current_to_individuals'] = True

        return setup


class import_algo_prog_plot(Tkinter.Frame):

    '''
    This deals with plotting the current front on the GUI.
    '''

    def __init__(self, parent, axis_labels, signConverter):

        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.signConverter = signConverter
        self.axis_labels = axis_labels

        self.initUi()

    def initUi(self):

        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.a = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)



    def update(self):
        global store_address
        global completed_generation
        self.a.clear()
        file_names = []
        for i in range(completed_generation):
            file_names.append("{0}/FRONTS/fronts.{1}".format(store_address, i+1))

        plot.plot_pareto_fronts(file_names, self.a, self.axis_labels, self.signConverter)

        #self.canvas = FigureCanvasTkAgg(self.fig, self.parent)
        self.canvas.show()

class import_algo_final_plot(Tkinter.Frame):

    '''
    This deals with giving the GUI the frame to plot the final front with.
    '''

    def __init__(self, parent, pick_handler, axis_labels, signConverter, initial_config=None, post_analysis_store_address = None):

        global store_address
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.signConverter = signConverter

        self.pick_handler = pick_handler
        self.axis_labels = axis_labels

        if initial_config is not None:
            self.initial_measurements = initial_config

        if post_analysis_store_address is not None:             #this class is also used for post_analysis
            store_address = post_analysis_store_address

        #self.initUi()

    def initUi(self, initial_config_plot=True):
        """
        Setup window GUI
        """
        global store_address

        self.parent.title("MOSA results")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        self.rowconfigure(0, weight=1)

        self.view_mode = Tkinter.StringVar()
        self.view_mode.set('No focus')

        if initial_config_plot is True:
            self.plot_frame = final_plot(self, self.axis_labels, self.signConverter, initial_config=self.initial_measurements)
        else:
            self.plot_frame = final_plot(self, self.axis_labels, self.signConverter)
        self.plot_frame.grid(row=0, column=0, pady=20, padx=20, rowspan=1, sticky=Tkinter.N+Tkinter.S+Tkinter.E+Tkinter.W)

        Tkinter.Label(self, text="View mode:").grid(row=0, column=1)

        self.cbx_view_mode = ttk.Combobox(self, textvariable=self.view_mode, values=('No focus', 'Best focus'))
        self.cbx_view_mode.bind("<<ComboboxSelected>>", lambda x: self.plot_frame.initUi())
        self.cbx_view_mode.grid(row=0, column=2)

        self.grid(sticky=Tkinter.N+Tkinter.S+Tkinter.E+Tkinter.W)
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)

    def on_pick(self, event):
        """
        This function gathers information from the saved files to allow the user to see the machine/algorithm parameters/results upon clicking
        on a solution on the Pareo front.
        """
        global store_address
        completed_generation = len(os.listdir('{0}/FRONTS'.format(store_address)))

        my_artist = event.artist
        x_data = my_artist.get_xdata()
        y_data = my_artist.get_ydata()
        ind = event.ind
        point = tuple(zip(self.signConverter[0]*x_data[ind], self.signConverter[1]*y_data[ind]))

        print "Point selected, point: {0}".format(point)

        ''' By this point we have the ars, but not the aps. We get these next. '''

        file_names = []
        for i in range(completed_generation):
            file_names.append("{0}/FRONTS/fronts.{1}".format(store_address, i+1))


        fs = []

        for file_name in file_names:
            execfile(file_name)

            fs.append(locals()['fronts'][0])

        aggregate_front_data = []
        for i in fs:
            for j in i:
                aggregate_front_data.append(j)
        aggregate_front_results = [i[1] for i in aggregate_front_data]
        point_number = aggregate_front_results.index(point[0])
        point_a_params = aggregate_front_data[point_number][0]

        print "ap: {0}".format(point_a_params)

        ''' By this point he have the aps, but not the mps. We don't find these in the algorithm. '''


        self.pick_handler(point[0], point_a_params)





class final_plot(Tkinter.Frame):

    '''
    This actually plots the final front for the algorithm at the end of running.
    '''

    def __init__(self, parent, axis_labels, signConverter, initial_config=None):

        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.signConverter = signConverter
        self.axis_labels = axis_labels

        if initial_config is not None:
            self.initial_measurements = initial_config
            self.initUi(initial_config_plot=True)
        else:
            self.initUi()

    def initUi(self, initial_config_plot=False):
        global store_address
        completed_generation = len(os.listdir('{0}/FRONTS'.format(store_address)))

        for widget in self.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(5, 5), dpi=100)
        a = fig.add_subplot(111)
        fig.subplots_adjust(left=0.15)

        file_names = []
        for i in range(completed_generation):                                            #gather fronts
            file_names.append("{0}/FRONTS/fronts.{1}".format(store_address, i+1))

        print 'file names', file_names

        if initial_config_plot is True:

            plot.plot_pareto_fronts_interactive(file_names,
                                                a,
                                                self.axis_labels,
                                                None,
                                                None,
                                                self.parent.view_mode.get(),
                                                self.signConverter,
                                                initial_measurements=self.initial_measurements)
        else:

            plot.plot_pareto_fronts_interactive(file_names,
                                                a,
                                                self.axis_labels,
                                                None,
                                                None,
                                                self.parent.view_mode.get(),
                                                self.signConverter)

        canvas = FigureCanvasTkAgg(fig, self)
        canvas.mpl_connect('pick_event', self.parent.on_pick)
        canvas.show()
        canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=True)
