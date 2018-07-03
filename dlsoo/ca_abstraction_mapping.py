from __future__ import division
import math

from cothread.catools import caget


# Set before use in gui.py
NUMBER_OF_BUNCHES = None


def bunch_length(I_beam):
    print('Number of bunches: {}'.format(NUMBER_OF_BUNCHES))
    bunch_length_value = 11.85 + 9.55*((I_beam/NUMBER_OF_BUNCHES)**0.75)
    return bunch_length_value


def lifetime_proxy():

    PMT_count = caget('SR-DI-COUNT-01:MEAN')+0.001
    I_beam = caget('SR-DI-DCCT-01:SIGNAL')
    epsilon_y = caget('SR-DI-EMIT-01:VEMIT_MEAN')

    bunch_length_value = bunch_length(I_beam)

    objective = I_beam/(PMT_count*bunch_length_value*math.sqrt(epsilon_y))

    return objective


name_to_function_mapping = {"lifetime_proxy" : lifetime_proxy}




