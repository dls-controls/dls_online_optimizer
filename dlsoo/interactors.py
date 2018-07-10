"""
IMPORTANT KEY:
ARs: Algorithm results (objectives)
APs: Algorithm parameters
MRs: Machine results (objectives)
MPs: Machine parameters

Older interactors that are no longer used have been removed, but are
stored in Git history if they are needed for reference.

"""
from . import model, util
import cothread
from cothread.catools import caput
import pickle
import tkMessageBox


#  MAIN INTERACTOR FOR BASIC (SIMULATION)
# Many of the functions within this class are used in main.py and the 
# algorithm files. The most important to understand is get_mr.

class sim_machine_interactor_bulk_base:

    def __init__(self,
                 param_var_groups=None,
                 measurement_vars=None,
                 set_relative=None,
                 results=None):

        self.param_var_groups = param_var_groups
        self.measurement_vars = measurement_vars
        self.results = results

        self.param_vars = []
        for group in self.param_var_groups:
            for param in group:
                self.param_vars.append(param)

        if set_relative == None:
            self.set_relative = []

            for i in self.param_var_groups:
                self.set_relative.append(False)

        # If we need to do relative setting, we need the initial values
        if set_relative != None:
            self.initial_values = self.get_mp()
            self.set_relative = set_relative


        ''' We create a dictionary to store the input ap keys, with the output mp values '''
        self.ap_to_mp_store = {}


    def save_details_file(self):
        return util.save_details_file(self)

    def get_pv(self, pv):
        return model.caget(pv)

    def set_pv(self, pv, value):
        model.caput(pv, value)

    def ap_to_mp(self, aps):

        mps = []

        mpsindex = 0
        for ngroup, group in enumerate(self.param_var_groups):

            for nparam, param in enumerate(group):

                if self.set_relative[ngroup] == True:
                    mps.append(self.initial_values[mpsindex] + aps[ngroup])

                else:
                    mps.append(aps[ngroup])

                mpsindex += 1

        ''' Store this mapping in the ap_to_mp_store dictionary '''
        self.ap_to_mp_store[tuple(aps)] = tuple(mps)
        #print self.ap_to_mp_store

        return mps

    def mp_to_ap(self, mps):

        aps = []

        mpsindex = 0
        for ngroup, group in enumerate(self.param_var_groups):
            print mpsindex
            if self.set_relative[ngroup]:
                aps.append(mps[mpsindex] - self.initial_values[mpsindex])
            elif not self.set_relative[ngroup]:
                aps.append(mps[mpsindex])

            for nparam, param in enumerate(group):
                mpsindex += 1


        print "mps: {0}".format(mps)
        print "aps: {0}".format(aps)
        print "initial values: {0}".format(self.initial_values)

        return aps

    def mr_to_ar(self, mrs):
        #converts a set of machine results to algorithm results
        ars = []

        mr_to_ar_sign = [mrr.mr_to_ar_sign for mrr in self.results]
        for mr, sign in zip(mrs, mr_to_ar_sign):
            if sign == '+':
                ars.append(mr)
            elif sign == '-':
                ars.append(-mr)

        return ars

    def set_mp(self, mps):
        util.set_params(self.param_vars, mps, model.caput)

    def get_mp(self):
        mps = []
        for param in self.param_vars:
            mps.append(model.caget(param.pv))

        return mps

    def get_mr(self):
        mrs = util.measure_results(self.measurement_vars, model.caget)
        return mrs

    def set_ap(self, aps):
        mps = self.ap_to_mp(aps)
        self.set_mp(mps)

    def get_ap(self):
        mps = self.get_mp()
        aps = self.mp_to_ap(mps)
        return aps

    def get_ar(self):
        mrs = self.get_mr()
        ars = self.mr_to_ar(mrs)
        return ars

    def find_a_bounds(self, param_var_min, param_var_max):

        min_bounds = []
        max_bounds = []

        mpsindex = 0
        for ngroup, group in enumerate(self.param_var_groups):

            if self.set_relative[ngroup]:
                min = None
                max = None

                for param in group:
                    amount_above = param_var_max[mpsindex] - self.initial_values[mpsindex]
                    amount_below = param_var_min[mpsindex] - self.initial_values[mpsindex]

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

                    mpsindex += 1

            else:
                min = None
                max = None

                for param in group:
                    if min != None:
                        if param_var_min[mpsindex] > min:
                            min = param_var_min[mpsindex]
                    else:
                        min = param_var_min[mpsindex]

                    if max != None:
                        if param_var_max[mpsindex] < max:
                            max = param_var_max[mpsindex]
                    else:
                        max = param_var_max[mpsindex]

                    mpsindex += 1


            min_bounds.append(min)
            max_bounds.append(max)

        print (min_bounds, max_bounds)
        return (min_bounds, max_bounds)

    def string_ap_to_mp_store(self):
        print self.ap_to_mp_store
        return pickle.dumps(self.ap_to_mp_store)

######################################################### END OF USEFUL CLASSES/FUNCTIONS ##########################################

# the remaining classes/functions are not used in injection that often and are not important in understanding how the file works.

class dls_machine_interactor_bulk_base_inj_control:

    def __init__(self, param_var_groups=None, measurement_vars=None,
                 set_relative=None, results=None):

        self.param_var_groups = param_var_groups
        self.measurement_vars = measurement_vars
        self.measurement_vars_noinj = [mv for mv in measurement_vars if not mv.inj_setting]
        self.measurement_vars_inj = [mv for mv in measurement_vars if mv.inj_setting]
        self.results = results
        self.beam_current_bounds = None, None

        self.param_vars = []
        for group in self.param_var_groups:
            for param in group:
                self.param_vars.append(param)

        if set_relative == None:
            self.set_relative = []

            for i in self.param_var_groups:
                self.set_relative.append(False)

        # If we need to do relative setting, we need the initial values
        if set_relative != None:
            self.initial_values = self.get_mp()
            self.set_relative = set_relative

        # We create a dictionary to store the input ap keys,
        # with the output mp values
        self.ap_to_mp_store = {}

    def save_details_file(self):
        return util.save_details_file(self)

    def get_pv(self, pv):
        return util.abstract_caget(pv)

    def set_pv(self, pv, value):
        caput(pv, value)

    def ap_to_mp(self, aps):

        mps = []

        mpsindex = 0
        for ngroup, group in enumerate(self.param_var_groups):

            for nparam, param in enumerate(group):

                if self.set_relative[ngroup] == True:
                    mps.append(self.initial_values[mpsindex] + aps[ngroup])

                else:
                    mps.append(aps[ngroup])

                mpsindex += 1

        ''' Store this mapping in the ap_to_mp_store dictionary '''
        self.ap_to_mp_store[tuple(aps)] = tuple(mps)

        return mps

    def mp_to_ap(self, mps):

        aps = []

        mpsindex = 0
        for ngroup, group in enumerate(self.param_var_groups):
            print mpsindex
            if self.set_relative[ngroup]:
                aps.append(mps[mpsindex] - self.initial_values[mpsindex])
            elif not self.set_relative[ngroup]:
                aps.append(mps[mpsindex])

            for nparam, param in enumerate(group):
                mpsindex += 1

        print "mps: {0}".format(mps)
        print "aps: {0}".format(aps)
        print "initial values: {0}".format(self.initial_values)

        return aps

    def mr_to_ar(self, mrs):
        #converts a set of machine results to algorithm results
        ars = []

        mr_to_ar_sign = [mrr.mr_to_ar_sign for mrr in self.results]
        for mr, sign in zip(mrs, mr_to_ar_sign):
            if sign == '+':
                ars.append(mr)
            elif sign == '-':
                ars.append(-mr)

        return ars

    def set_mp(self, mps):
        util.set_params(self.param_vars, mps, caput)

    def get_mp(self):
        mps = []
        for param in self.param_vars:
            mps.append(util.abstract_caget(param.pv))

        return mps

    # - MOST IMPORTANT FUNCTION IN CLASS FOR INJECTION CONTROL - #

    def get_mr(self):
        get_command = util.abstract_caget
        beam_current_max_warning = False

        # Only control injection if there are variables that require it.
        if self.measurement_vars_inj:
            # First measure the injection results
            # Begin injecting
            print "Start injection"
            caput('LI-TI-MTGEN-01:START', 1)
            cothread.Sleep(0.1)
            caput('LI-TI-MTGEN-01:START', 0)
            cothread.Sleep(4.0)

            if self.beam_current_bounds[0] is not None:
                beam_current = get_command('SR-DI-DCCT-01:SIGNAL')
                while beam_current < self.beam_current_bounds[0]:
                    print 'waiting for beam current to rise above ', \
                        self.beam_current_bounds[0]
                    cothread.Sleep(1)
                    beam_current = get_command('SR-DI-DCCT-01:SIGNAL')
                    print '...'

            mrs_inj = util.measure_results(self.measurement_vars_inj,
                                           util.abstract_caget)

            # Now for the non-injection measurements
            if self.beam_current_bounds[1] is not None:
                if get_command('SR-DI-DCCT-01:SIGNAL') > self.beam_current_bounds[1]:
                    beam_current_max_warning = True

            # Stop injection
            print "Stop injection"
            caput('LI-TI-MTGEN-01:STOP', 1)
            cothread.Sleep(0.1)
            caput('LI-TI-MTGEN-01:STOP', 0)
            cothread.Sleep(1)
        else:
            mrs_inj = []

        mrs_noinj = util.measure_results(self.measurement_vars_noinj,
                                         util.abstract_caget)

        # Now combine the results into a single list
        mrs = mrs_noinj + mrs_inj

        if beam_current_max_warning:
            msg = 'Beam current limit exceeded.\nDump the beam before pressing OK.'
            tkMessageBox.showwarning('DUMP THE BEAM', msg)

        return mrs

    # -----------------------------------------------------------------------

    def set_ap(self, aps):
        mps = self.ap_to_mp(aps)
        self.set_mp(mps)

    def get_ap(self):
        mps = self.get_mp()
        aps = self.mp_to_ap(mps)
        return aps

    def get_ar(self):
        mrs = self.get_mr()
        ars = self.mr_to_ar(mrs)
        return ars

    def find_a_bounds(self, param_var_min, param_var_max):

        min_bounds = []
        max_bounds = []

        mpsindex = 0
        for ngroup, group in enumerate(self.param_var_groups):

            if self.set_relative[ngroup]:
                min = None
                max = None

                for param in group:
                    amount_above = param_var_max[mpsindex] - \
                                   self.initial_values[mpsindex]
                    amount_below = param_var_min[mpsindex] - \
                                   self.initial_values[mpsindex]

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

                    mpsindex += 1

            else:
                min = None
                max = None

                for param in group:
                    if min != None:
                        if param_var_min[mpsindex] > min:
                            min = param_var_min[mpsindex]
                    else:
                        min = param_var_min[mpsindex]

                    if max != None:
                        if param_var_max[mpsindex] < max:
                            max = param_var_max[mpsindex]
                    else:
                        max = param_var_max[mpsindex]

                    mpsindex += 1

            min_bounds.append(min)
            max_bounds.append(max)

        print (min_bounds, max_bounds)
        return (min_bounds, max_bounds)

    def string_ap_to_mp_store(self):
        print self.ap_to_mp_store
        return pickle.dumps(self.ap_to_mp_store)
