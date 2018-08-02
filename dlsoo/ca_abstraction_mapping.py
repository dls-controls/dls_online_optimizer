from __future__ import division
import math
import numpy as np
from cothread.catools import caget


# Set before use in gui.py
NUMBER_OF_BUNCHES = None



def read_data():

    data = np.loadtxt("./lifetime_proxy_details")
    return data



def bunch_length(I_beam):
    print('Number of bunches: {}'.format(NUMBER_OF_BUNCHES))
    bunch_length_value = 11.85 + 9.55*((I_beam/NUMBER_OF_BUNCHES)**0.75)
    return bunch_length_value



def lifetime_proxy():
    data = read_data()

    vert_beam_size = data[0]
    sy     = caget('SR-DI-EMIT-01:P1:SIGMAY_MEAN')
    I_beam = caget('SR-DI-DCCT-01:SIGNAL')
    PMT_count = caget('SR-DI-COUNT-01:MEAN')+0.001
    objective =  PMT_count /  PMT_ref(I_beam) * vert_beam_size / sy  # rescaled n. of losses (note it was sy / sy_ref, corrected after IPAC)
    print('LT_proxy_resc='+str(objective))
    return objective

def PMT_ref(x):  # MA 17/4/2018

    #x is the beam current in Amps
    data = read_data()
    PMT_ref = data[6]*x**5 + data[5]*x**4 + data[4]*x**3 + data[3]*x**2 + data[2]*x + data[1]
    return PMT_ref


name_to_function_mapping = {"lifetime_proxy" : lifetime_proxy}
