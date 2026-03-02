
import typing
import math
from typing import List

from cabsys.quantity.log import Log
from cabsys.quantity.quantity_store import QuantityStore, QFloat, QStr, QBool


class TransientCurrentPoint(QuantityStore):
    """Time, current point in transient current curve"""

    time: QFloat
    current: QFloat
    name: typing.Optional[str]

    def __init__(self, **kwargs):
        super().__init__()
        self.name = None
        self.time = QFloat(unit='s', description='time', source=None, options=None, symbol='t_tp')
        self.current = QFloat(unit='A', description='current', source=None, options=None, symbol='I_tp')
        super().post_init(**kwargs)


class CurrentCurve(QuantityStore):
    """Transient current curve"""

    auto_comment: QStr
    emergency: QBool
    cyclic: QBool
    cycle_time: QFloat
    normalise_curve: QBool
    points: List[TransientCurrentPoint]
    name: typing.Optional[str]

    def __init__(self, **kwargs):
        super().__init__()
        self.name = None
        self.auto_comment = QStr(None, unit='', description='comment on current curve',
                                 source=None, options=None, symbol='curve comment')
        self.emergency = QBool(None, unit='', description='use emergency conductor temperature',
                               source=None, options=[True, False], symbol='emergency')
        self.cyclic = QBool(None, unit='', description='is the current curve cyclic',
                            source=None, options=[True, False], symbol='cyclic')
        self.cycle_time = QFloat(None, unit='s', description='length of cycle',
                                 source=None, options=None, symbol='t_cycle')
        self.normalise_curve = QBool(None, unit='', description='scale current curve to peak of 1.0', source=None,
                                     options=[True, False], symbol='normalise_curve')
        self.points = []
        super().post_init(**kwargs)

    # @LogSection('I_curve_min')
    def calc_min(self, end_time: float = None, log: Log = None) -> QFloat:
        """Calculate minimum current in a curve (absolute value).

        Calculates the minimum current in the curve, taking account of normalisation and desired current if required.

        :param end_time: finish time for curve
        :param log: logger used to store results
        :return: maximum current (A)
        """

        min_current = self.points[0].current.value
        if log is not None:
            log.start_section('min_current', f'current curve {self.name}')
        for point in self.points:
            if end_time is None or end_time > point.time.get_value(unit='s', log=log):
                min_current = min(min_current, point.current.get_value(unit='A', log=log))
        if log is not None:
            log.end_section('min_current', min_current, 'A', f'current curve name = {self.name}')

        return QFloat(min_current, 'A', 'CurrentCurve', description='minimum current in curve',
                      symbol='I_curve_min')

    # @LogSection('I_curve_max')
    def calc_max(self, end_time: float = None, log: Log = None) -> QFloat:
        """Calculate maximum current in a curve (absolute value).

        Calculates the maximum current in a curve without taking account of the scaling factor, that is without taking
        account of normalisation and desired current.

        :param end_time: finish time for curve
        :param log: logger used to store results
        :return: maximum current (A)
        """

        max_current = self.points[0].current.value
        if log is not None:
            log.start_section('max_current', f'current curve {self.name}')
        for point in self.points:
            if end_time is None or end_time > point.time.get_value(unit='s', log=log):
                max_current = max(max_current, point.current.get_value(unit='A', log=log))
        if log is not None:
            log.end_section('max_current', max_current, 'A', f'current curve name = {self.name}')

        return QFloat(max_current, 'A', 'CurrentCurve', description='maximum current in curve',
                      symbol='I_curve_max')

    def calc_ave(self, end_time: float = None, log: Log = None) -> QFloat:
        """Calculate maximum current in a curve (absolute value).

        Calculates the rms average current in a curve without taking account of the scaling factor, that is without
        taking account of normalisation and desired current.

        :param end_time: finish time for curve
        :param log: logger used to store results
        :return: maximum current (A)
        """

        if self.cyclic.value:
            end_time = self.cycle_time.value
        elif end_time is None:
            raise Exception(f'calculating ave current for current curve {self.name} but no end time given')

        sum_current = 0
        prev_time = 0.0
        point_time = 0.0
        if self.points[0].time.get_value(unit='s', log=log) == 0.0:
            prev_current = self.points[0].time.value
        else:
            raise Exception(f'calculating ave current for current curve {self.name} but no time 0 current given')
        if log is not None:
            log.start_section('rms_current', f'current curve {self.name}')
        for point in self.points:
            point_time = point.time.get_value(unit='s', log=log)
            if end_time > point_time:
                sum_current = sum_current + prev_current**2 * (point_time - prev_time)
                prev_time = point_time
                prev_current = point.current.get_value(unit='A', log=log)
            else:
                sum_current = sum_current + prev_current**2 * (end_time - prev_time)
                # prev_current = point.current.get_value(unit='A', log=log)
                break
        if end_time > point_time:
            sum_current = sum_current + (self.points[-1].current.get_value(unit='A', log=log) ** 2 *
                                         (end_time - prev_time))
        ave_current = math.sqrt(sum_current / end_time)
        if log is not None:
            log.end_section('rms_current', ave_current, 'A', f'current curve name = {self.name}')
        return QFloat(ave_current, 'A', 'CurrentCurve', description='rms of current in curve',
                      symbol='I_curve_rms')

    # @LogSection('I_time', section_log_level=30)
    def calc_current_time(self, time: float = None, log: Log = None) -> QFloat:
        """Calculate current at time t.

        Calculates the current at time t from a current curve.

        :param time: time
        :param log: logger used to store results
        :return: maximum current (A)
        """

        if self.cyclic.value:
            time = time % self.cycle_time.value

        if self.normalise_curve.value:
            m_unit = ''
        else:
            m_unit = 'A'

        if log is not None:
            log.start_section('current (current curve)', f'current curve {self.name} at time {time}')
        current_abs = self.points[0].current.value
        for point in self.points:
            # TODO: write unit tests for this function
            if point.time.get_value(unit='s') > time:
                break
            current_abs = point.current.value
        if log is not None:
            log.end_section('current (current curve)', current_abs, m_unit, f'current curve name = {self.name}')
        return QFloat(current_abs, m_unit, 'cigre support', description=f'current in curve at time {time}',
                      symbol='I_time (current curve)')

    # @LogSection('next_t', section_log_level=30)
    def calc_next_time(self, time: float = None, log: Log = None) -> QFloat:
        """Calculate the next time point.

        Calculates the next time point in a current curve given a time. If there is no next time point then None is
        returned

        :param time: time
        :param log: logger used to store results
        :return: next time point (s)
        """

        if self.cyclic.value:
            time = time % self.cycle_time.value

        next_time = self.cycle_time.value
        for point in self.points:
            if point.time.get_value(unit='s') > time:
                next_time = point.time.get_value(unit='s')
                break

        return QFloat(next_time, 's', 'cigre support', description=f'next time point after {time}',
                      symbol='I_time')


CURRENT_CURVE_CLASSES = {'CurrentCurve': CurrentCurve,
                         'TransientCurrentPoint': TransientCurrentPoint
                         }
