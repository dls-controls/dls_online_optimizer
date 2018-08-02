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

    sy_ref = 12.2 # 8/5/2018 vertical beam size in um
    sy     = caget('SR-DI-EMIT-01:P1:SIGMAY_MEAN')
    I_beam = caget('SR-DI-DCCT-01:SIGNAL')
    PMT_count = caget('SR-DI-COUNT-01:MEAN')+0.001
    objective =  PMT_count /  PMT_ref(I_beam) * sy_ref / sy  # rescaled n. of losses (note it was sy / sy_ref, corrected after IPAC)
    print('LT_proxy_resc='+str(objective))

#    epsilon_y = caget('SR-DI-EMIT-01:VEMIT_MEAN')
#    bunch_length_value = bunch_length(I_beam)
#    objective = I_beam/(PMT_count*bunch_length_value*math.sqrt(epsilon_y))

    return objective

def PMT_ref(x):  # MA 17/4/2018
#
#   x is the beam current in Amps
#
# MA 10/04/2018
#    PMT_ref = -2.608e-6*x**4 + 0.000502*x**3 + 0.4294*x**2 + 18.55*x -258.2
#old    PMT_ref =  6.3521e-6*x**4 - 0.0046326*x**3 +2.1405*x**2 -25.915*x +307.87
#    PMT_ref = 1.3e-6*x**4 -0.0015*x**3 +0.68*x**2 +0.74*x +22
    PMT_ref = 2.1e-6*x**4 -0.0024*x**3 + 0.81*x**2 -0.88*x -0.55
    return PMT_ref


name_to_function_mapping = {"lifetime_proxy": lifetime_proxy}
