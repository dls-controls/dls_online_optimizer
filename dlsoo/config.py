

class Parameters(object):
    keepUpdating = True
    initial_settings = None
    initial_measurements = None
    interactor = None
    optimiser = None
    useMachine = False
    signConverter = []
    Striptool_On = None
    #Sign converter converts algo params to machine params. This is used in the plotting below.

    mr_to_ar_sign = []
    mp_addresses = []
    mr_addresses = []

    mp_min_var = []
    mp_max_var = []

    ap_min_var = []
    ap_max_var = []

    relative_settings = []

    optimiser_wrapper_address = None
    optimiser_wrapper = None

    store_address = None

    algo_settings_dict = None

    mp_labels = []
    mr_labels = []
    ap_labels = []
    ar_labels = []

    parameters = []
    results = []


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
    Machine parameter
    """

    def __init__(self):

        self.mp_obj = None
        self.list_iid = None
        self.mp_label = None


class MrRepresentation(object):
    """
    Machine result (objective)
    """

    def __init__(self):

        self.mr_obj = None
        self.list_iid = None
        self.mr_label = None
        self.ar_label = None
        self.mr_to_ar_sign = None
        self.max_min_text = None
        self.max_min_sign = None
