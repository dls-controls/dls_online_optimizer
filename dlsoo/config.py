import os


class DlsParamVar:
    def __init__(self, pv, delay):
        self.pv = pv
        self.delay = delay
        self.initial_setting = None


class DlsMeasurementVar:
    def __init__(self, pv, min_counts, delay):
        self.pv = pv
        self.min_counts = min_counts
        self.delay = delay
        self.inj_setting = None


class Parameters(object):

    def __init__(self):
        self.keepUpdating = True
        self.initial_settings = None
        self.initial_measurements = None
        self.interactor = None
        self.optimiser = None
        self.useMachine = None
        self.Striptool_On = None

        self.mr_to_ar_sign = []
        self.mp_addresses = []
        self.mr_addresses = []

        self.mp_min_var = []
        self.mp_max_var = []

        self.ap_min_var = []
        self.ap_max_var = []

        self.relative_settings = []

        self.optimiser_wrapper_address = None
        self.optimiser_wrapper = None

        # Default to 'results' directory
        self.directory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.save_location = os.path.join(self.directory, 'results')
        if not os.path.exists(self.save_location):
            os.makedirs(self.save_location)

        self.store_address = None

        self.algo_settings_dict = None

        self.mp_labels = []
        self.mr_labels = []
        self.ap_labels = []
        self.ar_labels = []

        self.parameters = []
        self.results = []

        # for injection control
        self.beam_current_bounds = None
        self.reset()

    def reset(self):
        # Sign converter converts algo params to machine params.
        self.signConverter = []


class MpGroupRepresentation(object):
    """
    Machine group of parameters
    """

    def __init__(self):

        self.mp_representations = []
        self.list_iid = None
        self.ap_label = None
        self.relative_setting = None
        self.ap_min = None
        self.ap_max = None


class MpRepresentation(object):
    """
    Machine parameter - PV to be changed
    """

    def __init__(self):

        self.mp_obj = None  # DlsParamVar
        self.list_iid = None
        self.mp_label = None


class MrRepresentation(object):
    """
    Machine result (objective)
    """

    def __init__(self):

        self.mr_obj = None  # DlsMeasurementVar
        self.list_iid = None
        self.mr_label = None
        self.ar_label = None
        self.mr_to_ar_sign = None
        self.max_min_text = None
        self.max_min_sign = None
        self.inj_setting = None
        self.inj_setting_text = None
