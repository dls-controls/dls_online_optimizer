from __future__ import division

import time
import math
import pickle
import ca_abstraction_mapping

from cothread.catools import caget, caput
import cothread


def extract_column(matrix, colnum):
    col = []
    for i in matrix:
        col.append(i[colnum])
    return col


def mean(x):
    return sum(x)/len(x)


def extract_numbers(string1):
    #takes in a list and extracts the numbers with : ; around them to then stor in a list.
    collect = False
    collector = ''
    numbers = []
    for i in string1:
        if i == ':':
            collect = True
        elif i == ';':
            collect = False
            numbers.append(float(collector))
            collector = ''
        elif collect:
            collector += i
    return numbers


def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output)


def abstract_caget(pv, throw=False):
    """
    standard channel access 'get' function using cothread
    """
    print('caget {}'.format(pv))
    if pv in ca_abstraction_mapping.name_to_function_mapping:
        return ca_abstraction_mapping.name_to_function_mapping[pv]()
    else:
        return caget(pv, throw=True)


def abstract_caput(pv, value):
    """
    standard channel access 'set' function using cothread
    """
    caput(pv, value)


def set_params(param_vars, settings, set_command):
    """
    change the parameters using set_command. This will usually be abstract_caput
    """

    # Calculate the maximum delay time
    max_delay = 0
    for i in param_vars:
        if i.delay > max_delay:
            max_delay = i.delay

    # Set the parameters
    for i in range(len(param_vars)):
        set_command(param_vars[i].pv, settings[i])

    # Sleep for the appropriate amount of time
    cothread.Sleep(max_delay)


def measure_results(measurement_vars, get_command):
    """
    This part (redesigned by @James Rogers) measures the objectives and calculates the mean and standard deviation.
    Outliers are detected (2*sigma away from mean) and discarded. The mean and standard deviation are then returned.

    The get_command is usually abstract_caget (see above).
    """

    average = []
    counts = []
    dev = []
    err = []

    #for each objective
    for i in range(len(measurement_vars)):

        result = int(measurement_vars[i].min_counts) * [0.]
        std = int(measurement_vars[i].min_counts) * [0.]

        for j in range(int(measurement_vars[i].min_counts)):

            value = get_command(measurement_vars[i].pv)
            result[j] = value
            std[j] = value ** 2
            j += 1
            time.sleep(measurement_vars[i].delay)

        mean = sum(result) / measurement_vars[i].min_counts
        standard_deviation = (sum(std) / measurement_vars[i].min_counts) - mean ** 2
        standard_deviation = math.sqrt(standard_deviation)

        #detect and remove any outliers
        anomaly = False
        for j in result:
            if (abs(mean - j)) > 2 * standard_deviation:
                anomaly = True
                index = result.index(j)
                result.remove(j)
                del std[index]

        #recalculate mean if outliers are found
        if anomaly == True:
            mean = sum(result) / len(result)
            standard_deviation = (sum(std) / len(result)) - mean ** 2
            standard_deviation = math.sqrt(standard_deviation)

        stat_err = standard_deviation / math.sqrt(len(result))

        average.append(mean)
        counts.append(len(result))
        dev.append(standard_deviation)
        err.append(stat_err)

    results = []
    for i in range(len(average)):
        results.append(measurement(mean=average[i], counts=counts[i], dev=dev[i], err=err[i]))

    return results


def find_group_a_bounds(param_var_min, param_var_max, initial_values, set_relative):
    '''
    This part (not finished) is to find the boundaries required for the algorithm parameters
    such that the machine parameters never go out of their bounds. It currently works for setting
    when you have relative setting, but not yet for absolute setting. This is what I need to
    finish.

    Edit (@James Rogers): The absolute setting method (the part that wasn't finished) is not
                          necessary and the option has been removed from the GUI in main.py,
                          i.e. set_relative is always set as True in main.py if the parameter
                          ranges are defined using bounds (as opposed to changes).
    '''
    min = None
    max = None

    if set_relative:

        for p_min, p_max, init in zip(param_var_min, param_var_max, initial_values):
            amount_above = p_max - init
            amount_below = p_min - init

            if min != None:
                if amount_below > min:
                    min = amount_below
            else:
                min = amount_below

            if max != None:
                if amount_above < max:
                    max = amount_above
            else:
                max = amount_above


    else:

        for p_min, p_max in zip(param_var_min, param_var_max):
            if min != None:
                if p_min > min:
                    min = p_min
            else:
                min = p_min

            if max != None:
                if p_max < max:
                    max = p_max
            else:
                max = p_max


    print (min, max)
    return (min, max)


def save_details_file(object):
    """
    returns a file of useful information used in this file duration an optimisation
    """

    file_return = ""

    file_return += "DLS Machine Interactor Base\n"
    file_return += "===========================\n\n"

    file_return += "Parameter variables:\n"
    file_return += "-------------------\n"
    for i in object.param_vars:
        file_return += "PV name: {0}\n".format(i.pv)
        file_return += "Delay: {0} s\n\n".format(i.delay)

    file_return += "Measurement variables:\n"
    file_return += "---------------------\n"

    collated_measurement_vars = []
    if hasattr(object, "measurement_vars_noinj"):
        collated_measurement_vars = object.measurement_vars_noinj + object.measurement_vars_inj
    else:
        collated_measurement_vars = object.measurement_vars

    for i in collated_measurement_vars:
        file_return += "PV name: {0}\n".format(i.pv)
        file_return += "Minimum counts: {0}\n".format(i.min_counts)
        file_return += "Delay: {0} s\n\n".format(i.delay)

    return file_return

#-----------------------------------------PARAMETER AND OBJECTIVE PYTHON OBJECTS USED IN MAIN.PY------------------------------------#

#these classes are used in the 'add_pv' type functions in many classes in main.py

class measurement:

    def __init__(self, name=None, mean=None, dev=None, counts=None, err=None):
        self.name = name
        self.mean = mean
        self.dev = dev
        self.counts = counts
        self.err = err

    def __neg__(self):
        result = self
        result.mean = - result.mean

        return result

    def __pos__(self):
        return self

    def __add__(self, other):
        result = measurement()
        result.mean = self.mean + other.mean

        return result

    def __sub__(self, other):
        result = measurement()
        result.mean = self.mean - other.mean

        return result

    def __mul__(self, other):
        result = measurement()
        result.mean = self.mean * other.mean

        return result

    def __div__(self, other):
        result = measurement()
        result.mean = self.mean / other.mean

        return result

    def __iadd__(self, other):
        result = measurement.__add__(self, other)

        return result

    def __isub__(self, other):
        result = measurement.__sub__(self, other)

        return result

    def __imul__(self, other):
        result = measurement.__mul__(self, other)

        return result

    def __idiv__(self, other):
        result = measurement.__div__(self, other)

        return result

    def __lt__(self, other):
        result = False

        if self.mean < other.mean:
            result = True

        return result

    def __le__(self, other):
        result = False

        if self.mean <= other.mean:
            result = True

        return result

    def __eq__(self, other):
        result = False

        if self.mean == other.mean:
            result = True

        return result

    def __ne__(self, other):
        result = False

        if self.mean != other.mean:
            result = True

        return result

    def __ge__(self, other):
        result = False

        if self.mean >= other.mean:
            result = True

        return result

    def __gt__(self, other):
        result = False

        if self.mean > other.mean:
            result = True

        return result
