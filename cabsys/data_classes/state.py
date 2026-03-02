import typing
from typing import List, Union

from cabsys.data_classes.install import CableSet, Install
from cabsys.quantity.log import Log
from cabsys.quantity import quantity_constants as dc
from cabsys.quantity.quantity_store import QuantityBase
from cabsys.quantity.quantity_store import QuantityStore, QFloat, QBool, QInt


class State(QuantityStore):

    _memorise: bool

    def __init__(self):
        super().__init__()
        self._memorise = False
        super().post_init()

    def get_memorise(self):
        return self._memorise

    def set_memorise(self, memorise: bool = False):
        self._memorise = memorise

    def clear_quantities(self):
        del_list = []
        for key in dir(self):
            if isinstance(getattr(self, key), QuantityBase):
                if getattr(self, key).source not in dc.ATTR_FIXED_INPUTS:
                    del_list.append(key)
        for key in del_list:
            delattr(self, key)


class CableState(State):
    """Calculation results linked to Cable"""

    def __init__(self):
        super().__init__()
        # self._memorise = False
        # super().post_init()

    # def get_memorise(self):
    #     return self._memorise

    # def set_memorise(self, memorise: bool = False):
    #     self._memorise = memorise


class PlacedCableState(State):
    """Calculation results linked to CableDetails"""

    cable_state: typing.Optional[CableState]

    def __init__(self):
        super().__init__()
        # self._memorise = False
        self.cable_state = CableState()
        # super().post_init()

    # def get_memorise(self):
    #     return self._memorise

    def set_memorise(self, memorise: bool = False):
        # self._memorise = memorise
        super(PlacedCableState, self).set_memorise(memorise)
        self.cable_state.set_memorise(memorise)

    def clear_quantities(self):
        super(PlacedCableState, self).clear_quantities()
        self.cable_state.clear_quantities()


class CableSetState(State):
    """Calculation results linked to CableSet"""

    placed_cable_states: List[PlacedCableState]

    def __init__(self, cable_set: CableSet):
        super().__init__()
        # self._memorise = False
        self.placed_cable_states = [PlacedCableState() for _i in range(len(cable_set.placed_cables))]
        # super().post_init()

    # def get_memorise(self):
    #     return self._memorise

    def set_memorise(self, memorise: bool = False):
        # self._memorise = memorise
        super(CableSetState, self).set_memorise(memorise)
        for placed_cable_state in self.placed_cable_states:
            placed_cable_state.set_memorise(memorise)

    def clear_quantities(self):
        super(CableSetState, self).clear_quantities()
        for placed_cable_state in self.placed_cable_states:
            placed_cable_state.clear_quantities()


class InstallState(State):
    """Calculation result linked to a Installation

    QuantityStore object that stores the results of calculations linked to an installation cross-section.
    """

    cancel: bool
    progress: str
    cable_set_states: List[CableSetState]

    def __init__(self, install: Install):
        super().__init__()
        # self._memorise = False
        self.cancel = False
        self.progress = ''
        self.cable_set_states = []
        for cable_set in install.cable_sets:
            cable_set_state = CableSetState(cable_set)
            self.cable_set_states.append(cable_set_state)
        super().post_init()

    # def get_memorise(self):
    #     return self._memorise

    def set_memorise(self, memorise: bool = False):
        # self._memorise = memorise
        super(InstallState, self).set_memorise(memorise)
        for cable_set_state in self.cable_set_states:
            cable_set_state.set_memorise(memorise)

    def clear_quantities(self):
        super(InstallState, self).clear_quantities()
        for cable_set_state in self.cable_set_states:
            cable_set_state.clear_quantities()


# ************************ Electra 87 States ************************************

class AdjacentCable(QuantityStore):
    """An adjacent cable in Electra 87"""

    cable_set_no: QInt
    cable_no: QInt
    layer_no: QInt
    image: QBool

    def __init__(self):
        super().__init__()
        # self._memorise = False
        self.cable_set_no = QInt(None, unit='', description='cable set number', source=None,
                                 options=None, symbol='cable_set_no of adjacent cable')
        self.cable_no = QInt(None, unit='', description='cable_set_number', source=None,
                             options=None, symbol='cable_number of adjacent cable')
        self.layer_no = QInt(None, unit='', description='layer number of adjacent cable', source=None,
                             options=None, symbol='layer_no')
        self.image = QBool(None, unit='', description='is adjacent cable image?', source=None,
                           options=None, symbol='image')
        # super().post_init()

    # def get_memorise(self):
    #     return self._memorise

    # def set_memorise(self, memorise: bool = False):
    #     # self._memorise = memorise
    #     super(AdjacentCable, self).set_memorise(memorise)

    # def clear_quantities(self):
    #     del_list = []
    #     for key in dir(self):
    #         if isinstance(getattr(self, key), QuantityBase):
    #             del_list.append(key)
    #     for key in del_list:
    #         delattr(self, key)


class LayerState(State):
    """Calculation results linked to layer in Electra 87"""

    delta_theta_j: QFloat
    layer_radius: QFloat
    Wj: QFloat
    Tj: QFloat
    Qj: QFloat

    def __init__(self):
        super().__init__()
        # self._memorise = False
        self.delta_theta_j = QFloat(None, unit='°C', description='layer temperature', source=None,
                                    options=None, symbol='theta_j')
        self.layer_radius = QFloat(None, unit='m', description='layer radius', source=None,
                                   options=None, symbol='r_j')
        self.Wj = QFloat(None, unit='W/m', description='layer heat loss', source=None,
                         options=None, symbol='Wj')
        self.Tj = QFloat(None, unit='K.m/W', description='layer thermal resistance', source=None,
                         options=None, symbol='Tj')
        self.Qj = QFloat(None, unit='J/m.K', description='layer heat capacity', source=None,
                         options=None, symbol='Qj')
        # super().post_init()

    # def get_memorise(self):
    #     return self._memorise

    # def set_memorise(self, memorise: bool = False):
    #     super(LayerState, self).set_memorise(memorise)
    #     # self._memorise = memorise

    def clear_quantities(self):
        super(LayerState, self).clear_quantities()


class Elt087State(CableState):
    """Calculation results linked to Electra 87 Cable"""

    adjacent_cables: List[AdjacentCable]
    layers: List[LayerState]
    a_list: List[float]
    b_list: List[float]
    theta_list: List[float]
    start_theta_list: List[float]
    conductor_layer: QInt
    sheath_layer: QInt
    total_resistance: QFloat
    total_thermal_capacitance: QFloat

    def __init__(self):
        super().__init__()
        # self._memorise = False
        self.adjacent_cables = []
        self.layers = []
        self.a_list = []
        self.b_list = []
        self.theta_list = []
        self.start_theta_list = []
        self.conductor_layer = QInt(None, unit='', description='layer number of conductor', source=None,
                                    options=None, symbol='conductor_layer')
        self.sheath_layer = QInt(None, unit='', description='layer number of sheath', source=None,
                                 options=None, symbol='sheath_layer')
        self.total_resistance = QFloat(None, unit='K.m/W', description='total thermal resistance of cable', source=None,
                                       options=None, symbol='total_resistance')
        self.total_capacitance = QFloat(None, unit='J/m.K', description='total thermal capacitance of cable',
                                        source=None, options=None, symbol='total_capacitance')
        # super().post_init()

    # def get_memorise(self):
    #     return self._memorise

    def set_memorise(self, memorise: bool = False):
        super(Elt087State, self).set_memorise(memorise)
        # self._memorise = memorise
        for lay in self.layers:
            lay.set_memorise(memorise)

    def clear_quantities(self):
        super(Elt087State, self).clear_quantities()
        for lay in self.layers:
            lay.clear_quantities()


CABLE = 'cable'
PLACED_CABLE = 'placed_cable'
CABLE_SET = 'cable set'


class UseState:
    """Decorator that gets and stores attributes from a State object.

    A state object is linked to another object and stores information about the state that object is in. For example
    the conductor temperature of a cable. This decorator is used for a function that performs a calculation to obtain
    the state of the object, for example calculating the conductor resistance of a cable. By decorating the function,
    the state function will be checked to see if the value has been set by the user and if so will return the fixed
    value without getting the function to calculating it. If the value is calculated, the state function will be updated
    with the new value calculated and the top of the calculation noted.
    """

    def __init__(self, state_attr_name: Union[str, tuple], level: str = None, memorise: bool = None):
        """Decorator that gets and stores attributes to and from a State object.

        The result of the function that is being decorated is stored in the state object specified in the function
        argument. This allows the user to see intermediate results. Additionally, the option to memorise the result is
        available, in which case if the function is called again and the result already exists in the state object
        the pre-calculated result is given.

        The option to memorise the result can be set by the memorise parameter. If the memorise parameter is not given
        or set to None, the memorise attribute of the state object is used. This is normally set by the program to be
        the same as the Install.Config.memorise attribute.

        The result as a default is stored in the state object given, which matches the object given in the function. It
        is possible to store the result in a subclass of the state object by defining the subclass in the level
        parameter.

        :param state_attr_name: name of attribute in State object (generally the symbol name in ascii characters)
        :param level: the class level the attribute is stored in
        :param memorise: should the function be memorised
        """

        self.state_name = state_attr_name
        self.level = level
        self.memorise = memorise

    def __call__(self, fn):

        def wrapped_fn(*args, **kargs):

            # get state object and logger if they exist
            state = None
            log = None
            for arg in args:
                if isinstance(arg, State):
                    state = arg
                if isinstance(arg, Log):
                    log = arg
            if state is None:
                try:
                    state = kargs['state']
                except KeyError:
                    pass
            if log is None:
                try:
                    log = kargs['log']
                except KeyError:
                    pass

            # get cable number if x_sec is being used
            if state is None:
                active_state = None
            elif self.level == CABLE or self.level == PLACED_CABLE:
                # TODO: args may be: cable_set_no=0, cable_no=0 and this needs decoding
                if isinstance(state, InstallState):
                    if isinstance(args[0], Install):
                        cable_set_no = args[1]
                        cable_no = args[2]
                    elif isinstance(args[1], Install):
                        cable_set_no = args[2]
                        cable_no = args[3]
                    else:
                        raise Exception('InstallState being used but could not find Install object in args')
                    if self.level == CABLE:
                        active_state = state.cable_set_states[cable_set_no].placed_cable_states[cable_no].cable_state
                    else:
                        active_state = state.cable_set_states[cable_set_no].placed_cable_states[cable_no]
                # get cable number if cable sets are being used
                elif isinstance(state, CableSetState):
                    if isinstance(args[0], CableSet):
                        cable_no = args[1]
                    elif isinstance(args[1], CableSet):
                        cable_no = args[2]
                    else:
                        raise Exception('CableSetState being used but could not find CableSet object in args')
                    if self.level == CABLE:
                        active_state = state.placed_cable_states[cable_no].cable_state
                    else:
                        active_state = state.placed_cable_states[cable_no]
                elif isinstance(state, PlacedCableState):
                    if self.level == PLACED_CABLE:
                        active_state = state.cable_state
                    else:
                        active_state = state
                elif isinstance(state, CableState):
                    if self.level == PLACED_CABLE:
                        raise Exception('trying to use state decorator, '
                                        'requested state is PlacedCable but state given is CableState')
                    active_state = state
                else:
                    raise Exception(f'trying to use state decorator but do not recognise "{type(state)}" state')
            elif self.level == CABLE_SET:
                if isinstance(state, InstallState):
                    if isinstance(args[0], Install):
                        cable_set_no = args[1]
                    elif isinstance(args[1], Install):
                        cable_set_no = args[2]
                    else:
                        raise Exception('XsecState being used but could not find XSec object in args')
                    active_state = state.cable_set_states[cable_set_no]
                # get cable number if cable sets are being used
                elif isinstance(state, CableSetState):
                    if isinstance(args[0], CableSet):
                        pass
                    else:
                        raise Exception('CableSetState being used but could not find CableSet object in args')
                    active_state = state
                elif isinstance(state, CableState):
                    raise Exception('trying to use state decorator for cable set but cable state given')
                else:
                    raise Exception(f'trying to use state decorator but do not recognise "{type(state)}" state')
            elif self.level is None:
                active_state = state
            else:
                raise Exception(f'trying UseState decorator but level "{self.level}" not recognised')

            if active_state is not None:
                if self.memorise is None:
                    memorise = active_state.get_memorise()
                else:
                    memorise = self.memorise

                if isinstance(self.state_name, tuple):
                    if ((active_state.get_source(self.state_name[0]) in dc.ATTR_FIXED_INPUTS or
                         (memorise and active_state.get_quantity(self.state_name[0]) is not None))):
                        value_list=[]
                        for state_num, state_name in enumerate(self.state_name):
                            try:
                                value = active_state.get_quantity(state_name, log=log)
                            except KeyError:
                                raise Exception(f'Trying to add {self.state_name} but value or unit not specified')
                            value_list.append(value)
                        return tuple(value_list)
                else:
                    if ((active_state.get_source(self.state_name) in dc.ATTR_FIXED_INPUTS or
                         (memorise and active_state.get_quantity(self.state_name) is not None))):
                        try:
                            value = active_state.get_quantity(self.state_name, log=log)
                        except KeyError:
                            raise Exception(f'Trying to add {self.state_name} but value or unit not specified')
                        return value

            fn_result: Union[QuantityBase,tuple] = fn(*args, **kargs)

            if active_state is not None:
                if isinstance(self.state_name, tuple):
                    for state_num, state_name in enumerate(self.state_name):
                        active_state.set_quantity(state_name, fn_result[state_num].value, fn_result[state_num].unit,
                                                  source=fn_result[state_num].source,
                                                  description=fn_result[state_num].description)
                        active_state.__annotations__[state_name] = type(fn_result[state_num].value)
                else:
                    active_state.set_quantity(self.state_name, fn_result.value, fn_result.unit, source=fn_result.source,
                                              description=fn_result.description)
                    active_state.__annotations__[self.state_name] = type(fn_result.value)

            return fn_result
        return wrapped_fn
