# Constants for Transients

# kinds of transient
UNIT_STEP = [[0.0, 1.0, 1.0]]
NG_CYCLIC_TYPE = [[0.0, 1.0, 1.0],
                  [6*60*60, 0.6, 1.0]]
USER_DEFINED = [[0 * 3600.0, 0.0, 1.0], [1 * 3600.0, 0.0, 1.0], [2 * 3600.0, 0.0, 1.0], [3 * 3600.0, 0.0, 1.0],
                [4*3600.0, 0.0, 1.0], [5*3600.0, 0.0, 1.0], [6*3600.0, 0.0, 1.0], [7*3600.0, 0.0, 1.0],
                [8*3600.0, 0.0, 1.0], [9*3600.0, 0.0, 1.0], [10*3600.0, 0.0, 1.0], [11*3600.0, 0.0, 1.0],
                [12*3600.0, 0.0, 1.0], [13*3600.0, 0.0, 1.0], [14*3600.0, 0.0, 1.0], [15*3600.0, 0.0, 1.0],
                [16*3600.0, 0.0, 1.0], [17*3600.0, 0.0, 1.0], [18*3600.0, 0.0, 1.0], [19*3600.0, 0.0, 1.0],
                [20*3600.0, 0.0, 1.0], [21*3600.0, 0.0, 1.0], [22*3600.0, 0.0, 1.0], [23*3600.0, 0.0, 1.0]
                ]

CURVE_TYPES = {'unit step': (UNIT_STEP, False, 'step from 0 to 1 at time 0 s'),
               'NG cyclic': (NG_CYCLIC_TYPE, True, 'cyclic defined in NG TS 2.5'),
               'user defined': (USER_DEFINED, True, 'blank, to be filled by user')}

# need the keys as a list otherwise deep copy of current_curve fails when initialising curve type options
CURVE_TYPES_KEYS = list(CURVE_TYPES.keys())

PRELOAD_CONST_CURRENT = 'constant current'
PRELOAD_AVE_LOSS = 'average loss'
PRELOAD_OFF = 'cable set off'

PRELOAD_TYPES = [PRELOAD_CONST_CURRENT, PRELOAD_AVE_LOSS, PRELOAD_OFF]
