import sys
import traceback
from typing import Union

import cabsys.data_classes.current_curve

from cabsys.data_classes import current_curve_const as tc
from cabsys.quantity.quantity_store import QFloat, QStr, QBool, QInt
from cabsys.quantity.serialise import loads_object_xml
from cabsys.data_classes.current_curve import CurrentCurve, TransientCurrentPoint


class AutoCurrentCurve(CurrentCurve):
    """Transient current curve"""

    auto_kind: QStr
    auto_number_points: QInt

    def __init__(self, **kwargs):
        self._auto_design: bool = False
        self.auto_kind = QStr(None, unit='', description='kind of current curve',
                              source=None, options=tc.CURVE_TYPES_KEYS, symbol='curve kind')
        self.auto_number_points = QInt(None, unit='', description='number of points',
                                       source=None, options=None, symbol='n_points')
        super().__init__()
        self._auto_design_status = None
        super().post_init(**kwargs)

    def is_auto_design(self):
        return self._auto_design

    def set_auto_design(self, value: bool):
        self._auto_design = value

    def set_auto_design_status(self, status: str):
        self._auto_design_status = status

    def get_auto_design_status(self):
        return self._auto_design_status

    def auto_design(self) -> None:

        if current_curve_q_is_not_fixed(self.auto_kind) and self.is_auto_design():
            self.auto_kind.set_value(list(tc.CURVE_TYPES.keys())[0], unit='', source=CURRENT_CURVE_AUTO_DESIGN)

        if current_curve_q_is_not_fixed(self.auto_comment) and self.is_auto_design():
            self.auto_comment.set_value(tc.CURVE_TYPES[self.auto_kind.value][2],
                                        unit='', source=CURRENT_CURVE_AUTO_DESIGN)

        if current_curve_q_is_not_fixed(self.auto_number_points) and self.is_auto_design():
            self.auto_number_points.set_value(len(tc.CURVE_TYPES[self.auto_kind.value][0]),
                                              unit='', source=CURRENT_CURVE_AUTO_DESIGN)

        if len(self.points) != self.auto_number_points.value:
            new_current_curve = []
            if self.auto_number_points.value is None:
                auto_number_points = 0
            else:
                auto_number_points = self.auto_number_points.value
            for curve_point_no in range(auto_number_points):
                point = TransientCurrentPoint()
                if curve_point_no < len(self.points):
                    point = self.points[curve_point_no]
                elif not self.is_auto_design():
                    point.time.set_value(None, unit='s', source=None)
                    point.current.set_value(None, unit='A', source=None)
                elif (self.auto_kind.value in tc.CURVE_TYPES.keys() and
                      curve_point_no < len(tc.CURVE_TYPES[self.auto_kind.value][0])):
                    curve_point = tc.CURVE_TYPES[self.auto_kind.value][0][curve_point_no]
                    point.time.set_value(curve_point[0], unit='s', source=CURRENT_CURVE_AUTO_DESIGN)
                    point.current.set_value(curve_point[1], unit='A', source=CURRENT_CURVE_AUTO_DESIGN)
                else:
                    point.time.set_value(new_current_curve[-1].time.value, unit='s', source=CURRENT_CURVE_AUTO_DESIGN)
                    point.current.set_value(0.0, unit='A', source=CURRENT_CURVE_AUTO_DESIGN)

                new_current_curve.append(point)
            self.points = new_current_curve

        for i, point in enumerate(self.points):
            if current_curve_q_is_not_fixed(point.time) and self.is_auto_design():
                if i < len(tc.CURVE_TYPES[self.auto_kind.value][0]):
                    point.time.set_value(tc.CURVE_TYPES[self.auto_kind.value][0][i][0], unit='s',
                                         source=CURRENT_CURVE_AUTO_DESIGN)
                else:
                    point.time.set_value(self.points[i - 1].time.value, unit='s',
                                         source=CURRENT_CURVE_AUTO_DESIGN)
            if current_curve_q_is_not_fixed(point.current) and self.is_auto_design():
                if i < len(tc.CURVE_TYPES[self.auto_kind.value][0]):
                    point.current.set_value(tc.CURVE_TYPES[self.auto_kind.value][0][i][1], unit='A',
                                            source=CURRENT_CURVE_AUTO_DESIGN)
                else:
                    point.current.set_value(0.0, unit='A', source=CURRENT_CURVE_AUTO_DESIGN)

        if current_curve_q_is_not_fixed(self.cyclic) and self.is_auto_design():
            try:
                self.cyclic.set_value(tc.CURVE_TYPES[self.auto_kind.value][1],
                                      unit='', source=CURRENT_CURVE_AUTO_DESIGN)
            except KeyError:
                self.cyclic.set_value(False, unit='', source=CURRENT_CURVE_AUTO_DESIGN)

        if current_curve_q_is_not_fixed(self.emergency) and self.is_auto_design():
            self.emergency.set_value(False, unit='', source=CURRENT_CURVE_AUTO_DESIGN)

        if current_curve_q_is_not_fixed(self.cycle_time) and self.is_auto_design():
            if self.cyclic.value:
                self.cycle_time.set_value(24 * 60 * 60, unit='s', source=CURRENT_CURVE_AUTO_DESIGN)
            else:
                self.cycle_time.set_value(None, unit='s', source=CURRENT_CURVE_AUTO_DESIGN)

        if current_curve_q_is_not_fixed(self.normalise_curve) and self.is_auto_design():
            self.normalise_curve.set_value(True, unit='', source=CURRENT_CURVE_AUTO_DESIGN)

        return

    def auto_design_no_exceptions(self):
        try:
            self.auto_design()
        # except DesignCurveException:
        #     return sys.exc_info()
        except:
            print(traceback.format_exc())
            self.set_auto_design_status(f'{self.name}: unexpected error during auto_design cable')
            return sys.exc_info()[0]
        return None


CURRENT_CURVE_AUTO_DESIGN = 'current curve auto design'


def current_curve_q_is_not_fixed(quantity: Union[QInt, QBool, QStr, QFloat]) -> bool:
    return quantity.source == CURRENT_CURVE_AUTO_DESIGN or quantity.source is None


CURRENT_CURVE_CLASSES = {**cabsys.data_classes.current_curve.CURRENT_CURVE_CLASSES,
                         'AutoCurrentCurve':      AutoCurrentCurve,
                         'TransientCurrentPoint': TransientCurrentPoint
                         }


def loads_current_curve(serial: str):

    cc = loads_object_xml(serial, load_classes=CURRENT_CURVE_CLASSES)

    if cc[2] != '':
        raise Exception('DataQuantity serial stream load has remaining serial to decode')
    if not isinstance(cc[0], AutoCurrentCurve):
        raise Exception('file is not a current curve')
    return cc
