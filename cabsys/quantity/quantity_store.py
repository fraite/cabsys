"""Package that holds classes relating to storing data as quantity classes.

The following classes are defined:

    QuantityStore: holds a collection of data (generally quantities) as attributes

    * QuantityBase: base class that holds any type of data.
    * QFloat:       quantity class that holds float data
    * QStr:         quantity class that holds string data
    * QInt:         quantity class that holds int data
    * QBool:        quantity class that holds boolean data
"""
from __future__ import annotations


from typing import Any, Optional, List, Union
from cabsys.quantity.log import Log
from cabsys.quantity.exception import QuantityNoneError
import cabsys.quantity.quantity_constants as dc


class NoDefaultValue:
    pass


class QuantityBase:
    """Base class for a Quantity object.

    Stores an item of information with additional information such as the unit of measure.

    functions:
        * set_value(): set the value of the item, with the option to include extra information and log it
        * get_value(): get the value, with the option to log it and ask for a value if missing

    """
    value: Optional[any]
    unit: Optional[str]
    source: Optional[str]
    options: Optional[List]
    description: Optional[str]
    symbol: Optional[str]
    help_id: Optional[str]

    def __init__(self, value: Optional[any] = None, unit: Optional[str] = None, source: Optional[str] = None,
                 options: Optional[List] = None, description: Optional[str] = None, symbol: Optional[str] = None,
                 help_id: Optional[str] = None):
        """A quantity.

        Stores an object with additional information such as the unit of measure.

        :param value: the value of the quantity
        :param unit: the unit of measure
        :param source: where the value has come from, for example standard calculation
        :param options: values the item could hold, for example 'copper', 'aluminium'
        :param description: the description of the item, for example conductor material
        :param symbol: the symbol commonly used, for example I for current
        :param help_id: unique identifier, generally used to locate help documentation on the quantity
        """

        self.value = value
        self.unit = unit
        self.source = source
        self.options = options
        self.description = description
        self.symbol = symbol
        self.help_id = help_id

    def __eq__(self, other):
        if not isinstance(other, QuantityBase):
            return NotImplemented
        return self.value == other.value and self.unit == other.unit

    def __str__(self):
        return f'{self.value} {self.unit}'

    def __repr__(self):
        return f'{type(self)}({self.value!r}, unit={self.unit!r}, top={self.source!r}, options={self.options!r}, ' \
               f'description={self.description!r}, symbol={self.symbol!r})'

    def set_value(self, value: Optional[any], unit: Optional[str] = NoDefaultValue,
                  source: Optional[str] = NoDefaultValue,
                  options: Optional[List] = NoDefaultValue,
                  description: Optional[str] = NoDefaultValue,
                  symbol: Optional[str] = NoDefaultValue,
                  help_id: Optional[str] = NoDefaultValue,
                  log: Log = None) -> None:
        """Set the value of the quantity

        Sets the value of the quantity and optionally extra information

        :param value: the value of the quantity
        :param unit: the unit of measure
        :param source: where the value has come from, for example standard calculation
        :param options: values the item could hold, for example 'copper', 'aluminium'
        :param description: the description of the item, for example conductor material
        :param symbol: the symbol commonly used, for example I for current
        :param help_id: unique identifier, generally used to locate help documentation on the quantity
        :param log: if given an entry of the item will be added to the logger
        """
        self.value = value

        if unit is not NoDefaultValue:
            self.unit = unit
        if source is not NoDefaultValue:
            self.source = source
        if options is not NoDefaultValue:
            self.options = options
        if description is not NoDefaultValue:
            self.description = description
        if symbol is not NoDefaultValue:
            self.symbol = symbol
        if symbol is not NoDefaultValue:
            self.help_id = help_id

        if log is not None:
            log.add_line(self.symbol, self.value, self.unit, self.source)

    def get_value(self, unit: Optional[str] = NoDefaultValue, log: Log = None,
                  log_symbol: Optional[str] = NoDefaultValue) -> Optional[float]:
        """Get the value of the quantity

        Gets the value of the quantity and checks that the unit of measure is correct if unit is given. Optionally:
          * adds the item to the logger if a logger is given
          * asks the user for an input if the value is None

        Normally the log will use the symbol given in the quantity, but this can be overriden by supplying a symbol
        instead.

        :param unit: the unit of measure for the quantity
        :param log: if given an entry of the item will be added to the
        :param log_symbol: the symbol to use if the value is logged
        :return: the value of the quantity
        """
        if unit is not NoDefaultValue and unit is not None:
            if not unit == self.unit:
                raise Exception(f'getting {self.symbol!r}: unit of measure {unit} does not match {self.unit!r}')

        if log is not None and self.value is not None:
            if log_symbol is NoDefaultValue or log_symbol is None:
                log.add_line(self.symbol, self.value, self.unit, self.source)
            else:
                log.add_line(log_symbol, self.value, self.unit, self.source)

        return self.value

    def get_fixed_value(self, log: Log = None) -> Any:
        """Get a fixed value

        Returns a value only if the user has set the value. If the value has been set automatically by the computer the
        value will not be returned but None is returned instead. Where a value has been set by the user and a log is
        given an entry in the log will be made warning that there is a user input.

        Typical uses will be IEC parameters such as DC conductor resistance, where if not set by the user will return as
        None to allow an automatic IEC value to be used. Otherwise, the user value will be returned with a warning given
        in the log.

        :param log:               the calculation log
        :return:                  the parameter value if found, otherwise None
        """

        if self.source in dc.ATTR_FIXED_INPUTS:
            value = self.get_value(log=log)
            if log is not None:
                log.add_warning(f'{self.symbol} set by user input')
        else:
            value = None
        return value


class QFloat(QuantityBase):
    """A Float Quantity.

    Stores a float object with additional information such as the unit of measure.

    functions:
        * set_value(): set the value of the item, with the option to include extra information and log it
        * get_value(): get the value, with the option to log it and ask for a value if missing

    """
    value: Optional[float]
    # TODO: implement validation, in particular depth to be negative value

    def __init__(self, value: Optional[float] = None, unit: Optional[str] = None, source: Optional[str] = None,
                 options: Optional[List] = None, description: Optional[str] = None, symbol: Optional[str] = None,
                 help_id: Optional[str] = None):
        """A Float quantity.

        Stores a float object with additional information such as the unit of measure.

        :param value: the value of the quantity
        :param unit: the unit of measure
        :param source: where the value has come from, for example standard calculation
        :param options: values the item could hold, for example 'copper', 'aluminium'
        :param description: the description of the item, for example conductor material
        :param symbol: the symbol commonly used, for example I for current
        :param help_id: unique identifier, generally used to locate help documentation on the quantity
        """
        checked_value = self._check_value(value)
        super().__init__(checked_value, unit, source, options, description, symbol, help_id)

    def __eq__(self, other):
        return super().__eq__(other)

    def set_value(self, value: Optional[float], unit: Optional[str] = NoDefaultValue,
                  source: Optional[str] = NoDefaultValue, options: Optional[List] = NoDefaultValue,
                  description: Optional[str] = NoDefaultValue, symbol: Optional[str] = NoDefaultValue,
                  help_id: Optional[str] = NoDefaultValue,
                  log: Log = None) -> None:
        """Set the value of the quantity

        Sets the value of the quantity and optionally extra information

        :param value: the value of the quantity
        :param unit: the unit of measure
        :param source: where the value has come from, for example standard calculation
        :param options: values the item could hold, for example 'copper', 'aluminium'
        :param description: the description of the item, for example conductor material
        :param symbol: the symbol commonly used, for example I for current
        :param help_id: unique identifier, generally used to locate help documentation on the quantity
        :param log: if given an entry of the item will be added to the logger
        """
        checked_value = self._check_value(value)
        super().set_value(checked_value, unit, source, options, description, symbol, help_id, log)

    @staticmethod
    def _check_value(value):
        if value is None:
            float_value = None
        else:
            try:
                float_value = float(value)
            except ValueError:
                raise Exception(f'setting float quantity but could not convert {type(value)} to float: {value!r}')
        return float_value

    def get_value(self, unit: str = NoDefaultValue, log: Log = None, ask_if_missing=NoDefaultValue,
                  ask_item_name: str = '', default=NoDefaultValue, log_symbol: str = NoDefaultValue) -> Optional[float]:
        """Get the value of the quantity

        Gets the value of the quantity and checks the unit of measure if unit is given. Optionally:
          * adds the item to the logger if a logger is given
          * asks the user for an input if the value is None

        If the value of the quantity is None the function will behave as follows:

        ask_if_missing == None, ask_item_name == '':    return None
        ask_if_missing == None, ask_item_name != '':    raise Exception
        ask_if_missing != None                     :    ask for item

        :param unit: unit of measure for quantity
        :param log: if given an entry of the item will be added to the
        :param ask_if_missing: if given the user will be asked for missing values
        :param ask_item_name: the name the user is given for the missing item
        :param default: default value if value is None
        :param log_symbol: symbol to display if logger being used
        :return: the value of the quantity
        """
        if ask_if_missing is not NoDefaultValue:
            if self.value is None:
                print(f'missing {ask_item_name}')
                value = input()
                try:
                    self.value = float(value)
                except ValueError:
                    print(f'{value} not a float number')
        elif self.value is None and default == NoDefaultValue:
            raise QuantityNoneError(f'trying to get {self.symbol} ({self.description}) but value is None')

        return_value = super().get_value(unit, log, log_symbol)

        return return_value

    def get_value2(self, unit: Optional[str] = None, log: Log = None,
                   default: Optional[float] = None, log_symbol: str = None) -> float:
        """Get the value of the quantity

        Gets the value of the quantity and checks the unit of measure if unit is given. Optionally adds the item to the
        logger if a logger is given.

        If the value of the quantity is None the function will return the default value if given, else raise an
        Exception

        :param unit: unit of measure for quantity
        :param log: if given an entry of the item will be added to the logger
        :param default: default value if value is None
        :param log_symbol: symbol to display if logger being used
        :return: the value of the quantity
        """

        return_value = super().get_value(unit, log, log_symbol)

        if return_value is None:
            if default is None:
                raise QuantityNoneError(f'trying to get {self.symbol} ({self.description}) but value is None')
            else:
                return default

        return return_value


class QStr(QuantityBase):
    """A string Quantity.

    Stores a string object with additional information such as the unit of measure.

    functions:
        * set_value(): set the value of the item, with the option to include extra information and log it
        * get_value(): get the value, with the option to log it and ask for a value if missing

    """
    value: Optional[str]

    def __init__(self, value: Optional[str] = None, unit: Optional[str] = None, source: Optional[str] = None,
                 options: Optional[List] = None, description: Optional[str] = None, symbol: Optional[str] = None,
                 help_id: Optional[str] = None):
        """A string quantity.

        Stores a string object with additional information such as the unit of measure.

        :param value: value of the quantity
        :param unit: unit of measure for the quantity
        :param source: where the value has come from, for example standard calculation
        :param options: values the item could hold, for example 'copper', 'aluminium'
        :param description: the description of the quantity, for example conductor material
        :param symbol: the symbol commonly used, for example I for current
        :param help_id: unique identifier, generally used to locate help documentation on the quantity
        """
        checked_value = self._check_value(value)
        super().__init__(checked_value, unit, source, options, description, symbol, help_id)

    def __eq__(self, other):
        return super().__eq__(other)

    def set_value(self, value: Optional[str], unit: Optional[str] = NoDefaultValue,
                  source: Optional[str] = NoDefaultValue, options: Optional[List] = NoDefaultValue,
                  description: Optional[str] = NoDefaultValue, symbol: Optional[str] = NoDefaultValue,
                  help_id: Optional[str] = NoDefaultValue,
                  log: Log = None) -> None:
        """Set the value of the quantity

        Sets the value of the quantity and optionally extra information

        :param value: the value of the quantity
        :param unit: the unit of measure
        :param source: where the value has come from, for example standard calculation
        :param options: values the item could hold, for example 'copper', 'aluminium'
        :param description: the description of the item, for example conductor material
        :param symbol: the symbol commonly used, for example I for current
        :param help_id: unique identifier, generally used to locate help documentation on the quantity
        :param log: if given an entry of the item will be added to the logger
        """
        checked_value = self._check_value(value)
        super().set_value(checked_value, unit, source, options, description, symbol, help_id, log)

    @staticmethod
    def _check_value(value):
        if value is None:
            str_value = None
        else:
            try:
                str_value = str(value)
            except ValueError:
                raise Exception(f'setting string quantity but could not convert {type(value)} to string: {value!r}')
        return str_value

    def get_value(self, unit: str = NoDefaultValue, log: Log = None, ask_if_missing=NoDefaultValue,
                  ask_item_name: str = '') -> Optional[str]:
        """Get the value of the quantity

        Gets the value of the quantity and checks the unit of measure if unit is given. Optionally:
          * adds the item to the logger if a logger is given
          * asks the user for an input if the value is None

        :param unit: unit of measure for quantity
        :param log: if given an entry of the item will be added to the
        :param ask_if_missing: if given the user will be asked for missing values
        :param ask_item_name: the name the user is given for the missing item
        :return: the value of the quantity
        """
        if ask_if_missing is not NoDefaultValue:
            if self.value is None:
                print(f'missing {ask_item_name}')
                value = input()
                try:
                    self.value = str(value)
                except ValueError:
                    print(f'{value} not a string number')

        return_value = super().get_value(unit, log)

        return return_value


class QInt(QuantityBase):
    """An integer Quantity.

    Stores an integer object with additional information such as the unit of measure.

    functions:
        * set_value(): set the value of the quantity, with the option to include extra information and log it
        * get_value(): get the value, with the option to log it and ask for a value if missing

    """
    value: Optional[int]

    def __init__(self, value: Optional[int] = None, unit: Optional[str] = None, source: Optional[str] = None,
                 options: Optional[List] = None, description: Optional[str] = None, symbol: Optional[str] = None,
                 help_id: Optional[str] = None):
        """An integer quantity.

        Stores an integer object with additional information such as the unit of measure.

        :param value: value of the quantity
        :param unit: unit of measure for the quantity
        :param source: where the value has come from, for example standard calculation
        :param options: values the item could hold, for example 'copper', 'aluminium'
        :param description: the description of the quantity, for example conductor material
        :param symbol: the symbol commonly used, for example I for current
        :param help_id: unique identifier, generally used to locate help documentation on the quantity
        """
        checked_value = self._check_value(value)
        super().__init__(checked_value, unit, source, options, description, symbol, help_id)

    def __eq__(self, other):
        return super().__eq__(other)

    def set_value(self, value: Optional[int], unit: Optional[str] = NoDefaultValue,
                  source: Optional[str] = NoDefaultValue, options: Optional[List] = NoDefaultValue,
                  description: Optional[str] = NoDefaultValue, symbol: Optional[str] = NoDefaultValue,
                  help_id: Optional[str] = NoDefaultValue,
                  log: Log = None) -> None:
        """Set the value of the quantity

        Sets the value of the quantity and optionally extra information

        :param value: the value of the quantity
        :param unit: the unit of measure
        :param source: where the value has come from, for example standard calculation
        :param options: values the item could hold, for example 'copper', 'aluminium'
        :param description: the description of the item, for example conductor material
        :param symbol: the symbol commonly used, for example I for current
        :param help_id: unique identifier, generally used to locate help documentation on the quantity
        :param log: if given an entry of the item will be added to the logger
        """
        checked_value = self._check_value(value)
        super().set_value(checked_value, unit, source, options, description, symbol, help_id, log)

    @staticmethod
    def _check_value(value):
        if value is None:
            str_value = None
        else:
            try:
                str_value = int(value)
            except ValueError:
                raise Exception(f'setting integer quantity but could not convert {type(value)} to integer: {value!r}')
        return str_value

    def get_value(self, unit: str = NoDefaultValue, log: Log = None, ask_if_missing=NoDefaultValue,
                  ask_item_name: str = '') -> Optional[int]:
        """Get the value of the quantity

        Gets the value of the quantity and checks the unit of measure if unit is given. Optionally:
          * adds the item to the logger if a logger is given
          * asks the user for an input if the value is None

        :param unit: unit of measure for quantity
        :param log: if given an entry of the item will be added to the
        :param ask_if_missing: if given the user will be asked for missing values
        :param ask_item_name: the name the user is given for the missing item
        :return: the value of the quantity
        """
        if ask_if_missing is not NoDefaultValue:
            if self.value is None:
                print(f'missing {ask_item_name}')
                value = input()
                try:
                    self.value = int(value)
                except ValueError:
                    print(f'{value} not an integer number')

        return_value = super().get_value(unit, log)

        return return_value


class QBool(QuantityBase):
    """A Boolean Quantity.

    Stores a Boolean object with additional information such as the unit of measure.

    functions:
        * set_value(): set the value of the item, with the option to include extra information and log it
        * get_value(): get the value, with the option to log it and ask for a value if missing

    """
    value: Optional[bool]

    def __init__(self, value: Optional[bool] = None, unit: Optional[str] = None, source: Optional[str] = None,
                 options: Optional[List] = None, description: Optional[str] = None, symbol: Optional[str] = None,
                 help_id: Optional[str] = None):
        """A Boolean quantity.

        Stores a Boolean object with additional information such as the unit of measure.

        :param value: value of the quantity
        :param unit: unit of measure for the quantity
        :param source: where the value has come from, for example standard calculation
        :param options: values the item could hold, for example 'copper', 'aluminium'
        :param description: the description of the quantity, for example conductor material
        :param symbol: the symbol commonly used, for example I for current
        :param help_id: unique identifier, generally used to locate help documentation on the quantity
        """
        checked_value = self._check_value(value)
        super().__init__(checked_value, unit, source, options, description, symbol, help_id)

    def __eq__(self, other):
        return super().__eq__(other)

    def set_value(self, value: Optional[bool], unit: Optional[str] = NoDefaultValue,
                  source: Optional[str] = NoDefaultValue, options: Optional[List] = NoDefaultValue,
                  description: Optional[str] = NoDefaultValue, symbol: Optional[str] = NoDefaultValue,
                  help_id: Optional[str] = NoDefaultValue,
                  log: Log = None) -> None:
        """Set the value of the quantity

        Sets the value of the quantity and optionally extra information

        :param value: the value of the quantity
        :param unit: the unit of measure
        :param source: where the value has come from, for example standard calculation
        :param options: values the item could hold, for example 'copper', 'aluminium'
        :param description: the description of the item, for example conductor material
        :param symbol: the symbol commonly used, for example I for current
        :param help_id: unique identifier, generally used to locate help documentation on the quantity
        :param log: if given an entry of the item will be added to the logger
        """
        checked_value = self._check_value(value)
        super().set_value(checked_value, unit, source, options, description, symbol, help_id, log)

    @staticmethod
    def _check_value(value):
        if value is None:
            str_value = None
        else:
            try:
                str_value = bool(value)
            except ValueError:
                raise Exception(f'setting bool quantity but could not convert {type(value)} to bool: {value!r}')
        return str_value

    def get_value(self, unit: str = NoDefaultValue, log: Log = None, ask_if_missing=NoDefaultValue,
                  ask_item_name: str = '') -> Optional[bool]:
        """Get the value of the quantity

        Gets the value of the quantity if unit is given and checks the unit of measure. Optionally:
          * adds the item to the logger if a logger is given
          * asks the user for an input if the value is None

        :param unit: unit of measure for quantity
        :param log: if given an entry of the item will be added to the
        :param ask_if_missing: if given the user will be asked for missing values
        :param ask_item_name: the name the user is given for the missing item
        :return: the value of the quantity
        """
        if ask_if_missing is not NoDefaultValue:
            if self.value is None:
                print(f'missing {ask_item_name}')
                value = input()
                try:
                    self.value = bool(value)
                except ValueError:
                    print(f'{value} not a string number')

        return_value = super().get_value(unit, log)

        return return_value


class QuantityStore(object):
    """Stores data as attributes and provides associated functions and storage functions.

    The attributes of the class are generally Quantity objects, which allows storing additional information such as
    the measurement unit and top of the value.

    The attributes of the Quantity can be changed in the normal python way, for example
        conductor.ks.value = 0.2222

    If the attribute is a quantity, not private and not 'name', the value can also be set using omitting the value, for
    example
        conductor.ks = 0.2222
    in which case the value will be changed, and the source will be set to user.

    * (to be implemented) save and load function.

    """

    def __init__(self):
        # super.__init__()
        self._source: str = ''

    def __eq__(self, other):
        if not isinstance(other, QuantityStore):
            return NotImplemented

        equals = True

        for attr in vars(self):
            if not attr.startswith('_'):
                if getattr(self, attr, None) != getattr(other, attr, None):
                    equals = False

        for attr in vars(other):
            if not attr.startswith('_'):
                if getattr(self, attr, None) != getattr(other, attr, None):
                    equals = False

        return equals

    def post_init(self, **kwargs):
        """Set attributes with a value after subclass has set up attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key) and isinstance(getattr(self, key), QuantityBase):
                raise Exception(f'trying to set {key} but this value is a Quantity class')
            setattr(self, key, value)

    def __setattr__(self, key, value):
        old_value = getattr(self, key, None)
        if (isinstance(old_value, QuantityBase) and not isinstance(value, QuantityBase) and
                key != 'name' and not key.startswith('_')):
            old_value.value = value
            old_value.source = dc.ATTR_USER_SET
        else:
            super().__setattr__(key, value)

    def get_value(self, attr_name: str) -> Union[float, int, str]:
        """Get the value of an attribute.

        Gets the value of an attribute. If the attribute is
          * a quantity, then the value attribute of the quantity is returned,
          * an int or float the int or float value is returned,
          * None then '<None>' is returned.

        Otherwise, a ValueError exception is raised.

        :param attr_name:      name of attribute
        :return:               value of attribute
        """

        attr = getattr(self, attr_name)
        if isinstance(attr, QFloat) or isinstance(attr, QInt) or isinstance(attr, QStr) or isinstance(attr, QBool):
            value = attr.value
            if value is None:
                value = '<None>'
        elif (attr is None or isinstance(attr, int) or isinstance(attr, float) or
              isinstance(attr, str)):
            value = attr
            if value is None:
                value = '<None>'
        else:
            raise ValueError(f'{attr_name} is a {type(attr)} and does not have a value')

        return value

    def get_unit(self, attr_name: str, default=None) -> Optional[str]:
        """Get 'unit' information on an attribute.

        Get the unit of measure (for example 'mm') for the attribute is given. If the attribute does not exist or the
        attribute is not a quantity then None is returned.

        :param attr_name:      name of attribute
        :param default:    return value if no options exists
        :return:               unit of attribute
        """

        attribute = self.get_quantity(attr_name, not_quantity_error=False)
        if isinstance(attribute, QuantityBase):
            return attribute.unit
        else:
            return default

    def get_description(self, attr_name: str, default=None) -> Any:
        """Get 'description' information on an attribute.

        Get the description of the attribute given. If the attribute does not exist or the
        attribute is not a quantity then None is returned.

        :param attr_name:  name of attribute
        :param default:    return value if no options exists
        :return:           description of attribute
        """

        attribute = self.get_quantity(attr_name, not_quantity_error=False)
        if isinstance(attribute, QuantityBase):
            return attribute.description
        else:
            return default

    def get_options(self, attr_name: str, default=None) -> Any:
        """Get 'options' information on an attribute.

        Get the options of the attribute given. If the attribute does not exist or the
        attribute is not a quantity then None is returned.

        :param attr_name:  name of attribute
        :param default:    return value if no options exists
        :return:           options for the attribute
        """

        attribute = self.get_quantity(attr_name, not_quantity_error=False)
        if isinstance(attribute, QuantityBase):
            return attribute.options
        else:
            return default

    def get_source(self, attr_name: str, default=None) -> Optional[str]:
        """Get 'source' information on an attribute.

        The attribute can be set by a number of different sources, manually or by different modules in the program. This
        function gets the source of the attribute. If there is no attribute or the attribute is not a quantity, the
        function returns the default.

        :param attr_name:      name of attribute
        :param default:        return value if no source exists
        :return:               source of attribute
        """

        if isinstance(self.get_quantity(attr_name, not_quantity_error=False), QuantityBase):
            source = self.get_quantity(attr_name).source
        else:
            source = default

        return source

    def set_source(self, attr_name: str, source: Optional[str]) -> None:
        """Set 'source' information on an attribute.

        Set the source for the attribute given. This could be manual or the name of the module that sets the attribute.

        :param attr_name:  name of attribute
        :param source:     source of attribute
        """

        if isinstance(self.get_quantity(attr_name), QuantityBase):
            self.get_quantity(attr_name).source = source
        else:
            raise Exception(f'try to set the top of "{attr_name}" but it is not a quantity')

    def get_symbol(self, attr_name: str) -> Any:
        """Get symbol from a quantity.

        Get the symbol from the quantity given. If there is no symbol the attr_name is returned instead

        :param attr_name:  name of attribute
        :return:           symbol of attribute
        """

        if isinstance(self.get_quantity(attr_name), QuantityBase):
            symbol = self.get_quantity(attr_name).symbol
        else:
            symbol = None
        if symbol is None:
            symbol = attr_name

        return symbol

    def get_help_id(self, attr_name: str) -> Any:
        """Get help_id from a quantity.

        Get the help_id from the quantity given. If there is no help_id None is returned instead

        :param attr_name:  name of attribute
        :return:           symbol of attribute
        """

        if isinstance(self.get_quantity(attr_name), QuantityBase):
            help_id = self.get_quantity(attr_name).help_id
        else:
            help_id = None

        return help_id

    def set_quantity(self, attr_name: str, attr_value: any, attr_unit: str = None, description: str = None,
                     source: str = None, symbol: str = None, help_id: str = None, log: Log = None) -> None:
        """Set the value of a quantity, and output to log if required.

        The value of a quantity, including additional information. If top is specified, the top
        information associated with the attribute will be updated. If no top information is given the top
        information associated with the attribute will be left unchanged. If a log is given then an entry will be added
        to the output log.

        :param attr_name:    name of attribute
        :param attr_value:   value of attribute
        :param attr_unit:    unit of measure for attribute
        :param description:  description of attribute
        :param source:       top of the attribute, for example IEC clause
        :param symbol:       symbol of the attribute
        :param help_id: unique identifier, generally used to locate help documentation on the quantity
        :param log:          calculation log attribute is to be added to
        :return:             None
        """

        value = getattr(self, attr_name, None)
        if value is None:
            if isinstance(attr_value, float):
                value = QFloat(attr_value, unit=attr_unit, source=source, description=description, symbol=symbol,
                               help_id=help_id)
            elif isinstance(attr_value, int):
                value = QInt(attr_value, unit=attr_unit, source=source, description=description, symbol=symbol,
                             help_id=help_id)
            elif isinstance(attr_value, bool):
                value = QBool(attr_value, unit=attr_unit, source=source, description=description, symbol=symbol,
                              help_id=help_id)
            elif isinstance(attr_value, str):
                value = QStr(attr_value, unit=attr_unit, source=source, description=description, symbol=symbol,
                             help_id=help_id)
            else:
                raise Exception(f'trying to set value but {type(attr_value)} not implemented')
            setattr(self, attr_name, value)

        if isinstance(value, QuantityBase):
            value.set_value(attr_value, unit=attr_unit, source=source, description=description, symbol=symbol,
                            help_id=help_id, log=log)
        else:
            raise Exception(f'trying to set a quantity but it is a {type(value)}')

    def get_quantity(self, attr_name: str, log: Log = None, not_quantity_error: bool = True) -> Optional[QuantityBase]:
        """Get a quantity, and optionally add to calculation log.

        The quantity value is returned. If the attribute does not exist None is returned.

        Source information associated with the attribute will be updated. If no top information is given None will be
        entered against the top information for the attribute. If a log is given then an entry will be added to
        the output log.

        :param attr_name:           name of attribute
        :param log:                 calculation log attribute is to be added to
        :param not_quantity_error:  raise exception if attribute is not a quantity
        :return:                    quantity assigned to the attribute name
        """

        attr_value = getattr(self, attr_name, None)

        if attr_value is None:
            return None

        if not isinstance(attr_value, QuantityBase) and not_quantity_error:
            raise Exception(f'trying to get quantity "{attr_name}" but it is of type "{type(attr_value)}"')

        if log is not None:
            source = self.get_source(attr_name)
            if source is 'No top':
                source = 'No top'
            try:
                symbol = self.get_symbol(attr_name)
            except KeyError:
                symbol = attr_name
            if isinstance(attr_value, QFloat):
                log.add_line(symbol, attr_value.value, attr_value.unit, source)
            else:
                log.add_line(symbol, attr_value.value, '-', source)

        return attr_value

    def get_q_float(self, attr_name: str, log: Log = None) -> Optional[QFloat]:
        """Get a QFloat, and optionally add to calculation log.

        The QFloat value is returned. If the attribute does not exist None is returned.

        Source information associated with the attribute will be updated. If no top information is given None will be
        entered against the top information for the attribute. If a log is given then an entry will be added to
        the output log.

        :param attr_name:           name of attribute
        :param log:                 calculation log attribute is to be added to
        :return:                    quantity assigned to the attribute name
        """

        attr_value = getattr(self, attr_name, None)

        if attr_value is None:
            return None

        if not isinstance(attr_value, QFloat):
            raise Exception(f'trying to get QFloat "{attr_name}" but it is of type "{type(attr_value)}"')

        if log is not None:
            source = self.get_source(attr_name)
            if source is 'No top':
                source = 'No top'
            try:
                symbol = self.get_symbol(attr_name)
            except KeyError:
                symbol = attr_name
            log.add_line(symbol, attr_value.value, attr_value.unit, source)

        return attr_value

    def add_quantity_store_list(self, list_name: str, list_value: List[QuantityStore]) -> List[QuantityStore]:
        """Add a list of QuantityStore objects to the State object.

        A list is added to the State object, that will hold QuantityStore objects (typically State objects)

        :param list_name:    name of list
        :param list_value:   the list
        :return:             None
        """

        value = getattr(self, list_name, None)
        if value is None:
            if isinstance(list_value, list):
                setattr(self, list_name, list_value)
            else:
                raise Exception(f'trying to add list for {list_name} but list not being given')
        elif isinstance(value, list):
            raise Exception(f'trying to add a list for {list_name} but list already exists')
        return list_value

    def add_quantity_store(self, quantity_store_name: str, quantity_store: QuantityStore) -> QuantityStore:
        """Add a QuantityStore object to the State object.

        A QuantityStore object is added to the State object. The QuantityStore object is normally a State object.

        :param quantity_store_name: name of QuantityStore object
        :param quantity_store:      object ot be added
        :return:                    None
        """

        value = getattr(self, quantity_store_name, None)
        if value is None:
            if isinstance(quantity_store, QuantityStore):
                setattr(self, quantity_store_name, quantity_store)
            else:
                raise Exception(f'trying to add QuantityStore {quantity_store_name} but QuantityStore not being given')
        else:
            raise Exception(f'trying to add QuantityStore for {quantity_store_name} but already exists')
        return quantity_store

    def get_quantity_store(self, quantity_store_name: str) -> QuantityStore:
        """Get a QuantityStore object from a State object.

        A QuantityStore object is retrieved to the State object. The QuantityStore object is normally a State object.

        :param quantity_store_name: name of QuantityStore object
        :return:                  requested QuantityStore object.
        """

        value = getattr(self, quantity_store_name, None)
        if value is None:
            raise Exception(f'trying to get QuantityStore {quantity_store_name} but QuantityStore does not exist')
        else:
            if not isinstance(value, QuantityStore):
                raise Exception(f'trying to get QuantityStore object {quantity_store_name} but is type {type(value)}')
        return value
