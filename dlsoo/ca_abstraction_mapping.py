from __future__ import division
import math

import pkg_resources
from audioop import avg
pkg_resources.require('cothread')

from cothread.catools import caget, caput, ca_nothing
from cothread.cadef import CAException
import cothread

number_of_bunches = None

def define_number_of_bunches(new_number_of_bunches):
    global number_of_bunches
    number_of_bunches  = new_number_of_bunches
    print 'NUMBER OF BUNCHES =', number_of_bunches


def bunch_length(I_beam):
    global number_of_bunches
    bunch_length_value = 11.85 + 9.55*((I_beam/number_of_bunches)**0.75)
    return bunch_length_value


def lifetime_proxy():

    PMT_count = caget('SR-DI-COUNT-01:MEAN')+0.001
    I_beam = caget('SR-DI-DCCT-01:SIGNAL')
    epsilon_y = caget('SR-DI-EMIT-01:VEMIT_MEAN')

    bunch_length_value = bunch_length(I_beam)
    #print 'PMT ',PMT_count
    #print 'I_beam', I_beam
    #print 'emittance', epsilon_y
    #print 'bunch_length', bunch_length_value

    objective = I_beam/(PMT_count*bunch_length_value*math.sqrt(epsilon_y))

    return objective


name_to_function_mapping = {"lifetime_proxy" : lifetime_proxy}




