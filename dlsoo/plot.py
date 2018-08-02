"""
Plotting package for use in main.py and algorithm files within BASIC directory

Created on 19 Jul 2017

@author: David Obee and James Rogers
"""


from __future__ import division

import operator

import matplotlib.cm as cm
import numpy
import matplotlib.pyplot as plt
import matplotlib.patches as pat

#------------------------------------------------------------ CORRECT PARETO PLOTTING FUNCTION ----------------------------------------------#

def virtual_pareto_points(x_pareto, y_pareto, signConverter):
    """
    The plotting needs to correctly show the correct dominated region. This is done by creating artificial points:

          ///////////
    y1 |  x-----o ///
       |        | ///
       |        | ///
    y2 |        x ///
       |
        ----------->
          x1    x2

    for points on pareto front (x1,y1) and (x2,y2), an artificial point is put at (x2,y1). This will change however
    if objectives are being minimised/maximised (this is why signconverter is used).
    """

    if signConverter == [1,1] or signConverter == [1,-1]:

        coords = zip(x_pareto,y_pareto)

        coords.sort(key=operator.itemgetter(0))

        new_coords = []

        for i in range(len(coords)-1):
            new_coords.append(coords[i])
            imaginary_point = (coords[i+1][0],coords[i][1])
            new_coords.append(imaginary_point)

        new_coords.append(coords[-1])
        new_x = [x[0] for x in new_coords]
        new_y = [y[1] for y in new_coords]

        return new_x, new_y

    if signConverter == [-1,-1] or signConverter == [-1,1]:

        coords = zip(x_pareto,y_pareto)
        coords.sort(key=operator.itemgetter(0))

        new_coords = []

        for i in range(len(coords)-1):
            new_coords.append(coords[i])
            imaginary_point = (coords[i][0],coords[i+1][1])
            new_coords.append(imaginary_point)

        new_coords.append(coords[-1])
        new_x = [x[0] for x in new_coords]
        new_y = [y[1] for y in new_coords]

        return new_x, new_y

#--------------------------------------------------------- PLOTTING CLASSES FOR PROGRESS AND FINAL RESULTS ------------------------------------------#


def plot_pareto_fronts(file_names, ax, axis_labels, signConverter):
    """
    This is used in the progress plot
    """

    global fs

    fs = []

    #execute all FRONTS files to obtain the pareto fronts.
    for file_name in file_names:
        execfile(file_name)

        fs.append(locals()['fronts'][0])

    x_vals = []
    y_vals = []

    colors = cm.jet(numpy.linspace(0, 1, len(fs)))

    for nf, f in enumerate(fs):

        for ni, i in enumerate(f):

            #take into account the change of sign for max/min
            x_vals.append(i[1][0]*signConverter[0])
            y_vals.append(i[1][1]*signConverter[1])


        px_vals = [x for (x, y) in sorted(zip(x_vals, y_vals))]
        py_vals = [y for (x, y) in sorted(zip(x_vals, y_vals))]

        #plot all solutions of Pareto front
        ax.plot(px_vals, py_vals, color=colors[nf], marker='D', linestyle='None',picker=5)

        #now join the solutions up using the virtual points
        new_x, new_y = virtual_pareto_points(px_vals,py_vals,signConverter)

        ax.plot(new_x, new_y, color=colors[nf], linestyle='--')

        x_vals = []
        y_vals = []

    ax.grid()
    ax.set_xlabel(axis_labels[0])
    ax.set_ylabel(axis_labels[1])


def plot_pareto_fronts_interactive(file_names, ax, axis_labels, interactor, callback, view_mode, signConverter, initial_measurements=None):
    """
    This is used in the final results plot
    """
    global fs

    if initial_measurements is not None:
        initial_config = [i.mean for i in initial_measurements]

    fs = []

    #execute all FRONTS files to obtain the pareto fronts.
    for file_name in file_names:
        execfile(file_name)

        fs.append(locals()['fronts'][0])
    print "fs is: {}".format(fs)


    #different view modes for the final plot

    if view_mode == "No focus":

        colors = cm.jet(numpy.linspace(0, 1, len(fs)))

        for nf, f in enumerate(fs):
            x_vals = []
            y_vals = []
            std_Y = []
            std_X = []
            mean_errX = []
            mean_errY = []
            STD_bar_X = []
            STD_bar_Y = []
            mean_bar_X = []
            mean_bar_Y = []

            for ni, i in enumerate(f):

                #take into account the change of sign for max/min
                x_vals.append(i[1][0]*signConverter[0])
                y_vals.append(i[1][1]*signConverter[1])

                #add standard error of mean

                mean_errX.append(i[2][0])
                mean_errY.append(i[2][1])


                #diam_x = x_err * 2
                #diam_y = y_err * 2

        #standard_std_X = i[3][0]

                std_Y.append(i[3][1])
                std_X.append(i[3][0])

                if nf == len(fs) - 1:
                        #print "[X_val, Y_val]                          Standard Dev.                               error of mean"
                        #print "##########################################################"
                        #print ni
                        #print px_vals[ni], py_vals[ni], std_X[ni], std_Y[ni], x_err[ni], y_err[ni]

                        STD_bar_X.append(std_X[ni])
                        STD_bar_Y.append(std_Y[ni])
                        mean_bar_X.append(mean_errX[ni])
                        mean_bar_Y.append(mean_errY[ni])
                        #fig, (ax0, ax1) = plt.subplots(nrows =2, sharex = True)
                        #ax0.errorbar(x_vals, y_vals, yerr= std_Y, fmt='-o')
                        #plt.show()



                #if nf == len(fs) - 1:

                    #box = pat.Rectangle(xy=(x_vals[ni] - bar_errorX2[ni], y_vals[ni] - bar_errorY2[ni]), width=2*bar_errorX2[ni], height=2*bar_errorY2[ni], color = 'red') # changed for standard error of mean boxes rather than ellipses rhs 16/07/18

                    #box.set_facecolor('none')
                    #ax.add_artist(box)

                px_vals = [x for (x, y) in sorted(zip(x_vals, y_vals))]
                py_vals = [y for (x, y) in sorted(zip(x_vals, y_vals))]
            #print "the x values plotted:" , px_vals

            #Plot the FINAL front in bold
            if nf == len(fs) - 1:

                ax.errorbar(px_vals, py_vals, STD_bar_Y, STD_bar_X, color= 'blue',ecolor= 'crimson', marker='o', picker=5, linestyle='None')  #bars not ellipses added rhs 16/07/18

        #for i in range(len(bar_errorY2)):
        #box = pat.Rectangle(xy=(px_vals[i] - bar_errorX2[i], py_vals[i] - bar_errorY2[i]), width=2*bar_errorX2[i], height=2*bar_errorY2[i]) # changed for standard error of mean boxes rather than ellipses rhs 16/07/18
        #box.set_facecolor('none')
        #ax.add_artist(box)
            for i in range(len(STD_bar_Y)):
                box = pat.Rectangle(xy=(px_vals[i] - mean_bar_X[i], py_vals[i] - mean_bar_Y[i]), width=2*mean_bar_X[i], height=2*mean_bar_Y[i]) # changed for standard error of mean boxes rather than ellipses rhs 16/07/18
                box.set_facecolor('none')
                ax.add_artist(box)



                new_x, new_y = virtual_pareto_points(px_vals,py_vals,signConverter)

                ax.plot(new_x, new_y, color=colors[nf], linewidth=2)

            #Plot the past fronts normally
            else:
                ax.plot(px_vals, py_vals, color=colors[nf], marker='.', linestyle='None')

                new_x, new_y = virtual_pareto_points(px_vals,py_vals,signConverter)
                ax.plot(new_x, new_y, color=colors[nf], linestyle='--')


            x_vals = []
            y_vals = []

        if initial_measurements is not None:
            # now plot the initial config
            ax.plot(initial_config[0], initial_config[1], marker='o', markersize=10)
        ax.grid()

    #a different view mode using the same method but with different colours
    elif view_mode == "Best focus":

        ax.set_axis_bgcolor('black')
        greys = numpy.linspace(0.5, 0.9, len(fs) - 1)

        for nf, f in enumerate(fs):
            print "\n!\n"
            for ni, i in enumerate(f):

                x_vals.append(i[1][0]*signConverter[0])
                y_vals.append(i[1][1]*signConverter[1])

                x_err = i[2][0]
                y_err = i[2][1]

                if nf == len(fs) - 1:
                    ell = pat.Ellipse(xy=(i[1][0]*signConverter[0], i[1][1]*signConverter[1]), width=x_err, height=y_err)
                    ell.set_facecolor('none')
                    ell.set_edgecolor('white')
                    ax.add_artist(ell)


            px_vals = [x for (x, y) in sorted(zip(x_vals, y_vals))]
            py_vals = [y for (x, y) in sorted(zip(x_vals, y_vals))]


            if nf == len(fs) - 1:
                ax.plot(px_vals, py_vals, color='y', marker='D', linestyle='None', picker=5)

                new_x, new_y = virtual_pareto_points(px_vals,py_vals,signConverter)
                ax.plot(new_x, new_y, color='y', linewidth=2)
            else:
                ax.plot(px_vals, py_vals, color="{0}".format(greys[nf]), marker='.', linestyle='None')

                new_x, new_y = virtual_pareto_points(px_vals,py_vals,signConverter)
                ax.plot(new_x, new_y, color="{0}".format(greys[nf]), linestyle='--')

            x_vals = []
            y_vals = []

        if initial_measurements is not None:
            # now plot the initial config
            ax.plot(initial_config[0], initial_config[1], marker='o', markersize=10)
        ax.grid()

    ax.set_xlabel(axis_labels[0])
    ax.set_ylabel(axis_labels[1])





def plot_strip_tool(ax, data_sets, data_times):
    """
    This is the plotting for the Striptool, which is tunred off by default in the main GUI
    """

    data_set = [i[0] for i in data_sets]

    ax.plot(data_times, data_set)


