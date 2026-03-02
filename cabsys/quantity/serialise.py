"""Class that serialises python objects.

"""
import typing

from cabsys import LoadException
from cabsys.quantity.quantity_store import QuantityStore, QFloat, QStr, QInt, QBool


Q_CLASS = {'QBool': QBool,
           'QFloat': QFloat,
           'QStr': QStr,
           'QInt': QInt
           }


def dumps(o, name='') -> str:
    """Convert a Python object to a string.

    The given python object, o, is serialised to a string and returned. The object can then be loaded at a later point
    using loads function. The serialisation also encodes the data type of the object being encoded. The serialisation is
    limited to a subset of Python objects, so that the de-serialisation process is not intrinsically unsafe. The process
    is similar to JSON but preserves the objects data type and allows a wider range of objects to be serialised. The
    process is similar to pickling but is more limited on the objects that can be canned (serialised) so that
    de-serialisation is safer.

    The Python single item data types that are supported are: str, int, float, None, bool. The Python collections that
    are supported: dict, list, tuple. In addition the custom DataStore class, and some subclasses of DataStore are
    supported.

    Objects will not know their own name. For example in a dictionary d = {'a': 1, 'b': 2} the dict does not know that
    it is called 'd'. Where the name of the object is known this can be passed.

    :param o:      object being serialised
    :param name:   name of object
    :return:       serialisation representing object, including pre-existing serialisation
    """

    serial = '<?xml version="1.0" encoding="UTF-8"?>\n'
    default_o = type(o)()
    return dumps_object(o, name, serial, 0, default_o)


def dumps_object(o, name='', serial: str = '', level: int = 0, default_obj=None, stop_at_list=None) -> str:
    """Convert a Python object to a string.

    The given python object, o, is serialised to a string and returned. The object can then be loaded at a later point
    using loads function. The serialisation also encodes the data type of the object being encoded. The serialisation is
    limited to a subset of Python objects, so that the de-serialisation process is not intrinsically unsafe. The process
    is similar to JSON but preserves the objects data type and allows a wider range of objects to be serialised. The
    process is similar to pickling but is more limited on the objects that can be canned (serialised) so that
    de-serialisation is safer.

    The Python single item data types that are supported are: str, int, float, None, bool. The Python collections that
    are supported: dict, list, tuple. In addition the custom DataQuantity class, and some subclasses of DataQuantity are
    supported.

    Objects will not know their own name. For example in a dictionary {'a': 1, 'b': 2} the object 1 does not know that
    it is called 'a'. Where the name of the object is known this can be passed.

    If a default object is given, only differences between the object and the default object are recorded.

    If a stop_at DataQuantity class is specified, any objects that are encountered that are of the specified class will
    not be serialised and only the tag of the object will be serialised with the name of the object.

    :param o:           object being serialised
    :param name:        name of object
    :param serial:      pre-existing serialisation that is to be added to
    :param level:       element level
    :param default_obj: default object
    :param stop_at_list:     list of classes that do not get serialised
    :return:            serialisation representing object, including pre-existing serialisation
    """

    indent_str = '  ' * level
    if type(o) is str or type(o) is int or type(o) is float or o is None or type(o) is bool:
        return_serial = f'{serial}{indent_str}{dumps_item(o)}\n'
        return return_serial
    elif type(o) is dict:
        type_o = str(type(o)).split("'")[1]
        return_serial = f'{serial}{indent_str}<{type_o} name="{name}">\n'
        for key, value in o.items():
            is_default, default_value = is_default_dict(default_obj, key, value)
            if not is_default:
                return_serial = f'{return_serial}{indent_str}  <key>\n'
                return_serial = f'{return_serial}{indent_str}    {dumps_item(key)}\n'
                return_serial = f'{return_serial}{indent_str}  </key>\n'
                return_serial = f'{return_serial}{indent_str}  <value>\n'
                if isinstance(value, QuantityStore) and hasattr(value, 'name'):
                    value_name = value.name
                else:
                    value_name = ''
                return_serial = dumps_object(value, value_name, return_serial, level + 2, default_value, stop_at_list)
                return_serial = f'{return_serial}{indent_str}  </value>\n'
                # return_serial = dumps_object(value, None, return_serial, level + 1, default_value)
        return_serial = f'{return_serial}{indent_str}</{type_o}>\n'
        return return_serial
    elif type(o) is list or type(o) is tuple:
        type_o = str(type(o)).split("'")[1]
        return_serial = f'{serial}{indent_str}<{type_o} name="{name}">\n'
        for count in range(len(o)):
            item = o[count]
            is_default, default_item = is_default_list(default_obj, count, item)
            # default_item = default_obj[count]
            if not is_default:
                return_serial = f'{return_serial}{indent_str}  <item>\n'
                if isinstance(item, QuantityStore) and hasattr(item, 'name'):
                    item_name = item.name
                else:
                    item_name = ''
                return_serial = dumps_object(item, item_name, return_serial, level + 2, default_item, stop_at_list)
                return_serial = f'{return_serial}{indent_str}  </item>\n'
        return_serial = f'{return_serial}{indent_str}</{type_o}>\n'
        return return_serial
    elif (isinstance(o, QuantityStore) or isinstance(o, QBool) or isinstance(o, QStr) or isinstance(o, QInt) or
          isinstance(o, QFloat)):
        # get the name of the class, for example DataQuantity or Cable
        type_o = str(type(o)).split('.')[-1][:-2]
        return_serial = f'{serial}{indent_str}<{type_o} name="{name}">\n'
        is_object_in_stop_at_list = False
        if stop_at_list is not None:
            for stop_at in stop_at_list:
                if isinstance(o, stop_at):
                    is_object_in_stop_at_list = True
        if not is_object_in_stop_at_list:
            if default_obj is None:
                default_obj = type(o)()
            default_dict = vars(default_obj)
            if vars(o) != default_dict or True:
                return_serial = dumps_object(vars(o), '__dict__', return_serial, level + 1, default_dict, stop_at_list)
        return_serial = f'{return_serial}{indent_str}</{type_o}>\n'
        return return_serial
    else:
        raise LoadException(f'DataQuantity serialisation dump object type {type(o)} not supported')


def is_default_dict(default_obj, key, value):
    if default_obj is None:
        is_default = False
        default_value = None
    else:
        try:
            default_value = default_obj[key]
            if default_value == value:
                is_default = True
            else:
                is_default = False
        except KeyError:
            is_default = False
            default_value = None
    return is_default, default_value


def is_default_list(default_obj, count, value):
    if default_obj is None:
        is_default = False
        default_value = None
    else:
        try:
            default_value = default_obj[count]
            if default_value == value:
                is_default = True
            else:
                is_default = False
        except IndexError:
            is_default = False
            default_value = None
    return is_default, default_value


def dumps_item(o):
    tag = str(type(o)).split("'")[1]
    item = str(o)
    item = item.replace('<', '&lt;')
    item = item.replace('&', '&amp;')
    item = item.replace('>', '&gt;')
    item = item.replace("'", '&apos;')
    item = item.replace('"', '&quot;')
    return f'<{tag}>{item}</{tag}>'


def loads_object_xml(serial: str, load_classes: typing.Optional[dict] = None):
    if serial.startswith('<?xml version="1.0" encoding="UTF-8"?>\n'):
        serial = serial[len('<?xml version="1.0" encoding="UTF-8"?>\n'):]
    else:
        raise LoadException('file read error: not an XML file')
    serial = serial.strip('')
    obj, name, serial = loads_obj(serial, load_classes=load_classes)
    return obj, name, serial


def loads_obj(serial: str, default_obj=None, default_obj_name: str = None, stop_at: dict = None,
              load_classes: typing.Optional[dict] = None):
    """Loads and object from a serial string

    The first object in the input serial is returned, with the name of the object if known. The remaining serial
    string is also returned. If the name of the object is not known, None is returned for the object name.

    Where a default object is given, the object will be the default object but updated by the input serial string. This
    allows for a more compact serial strings as only differences between the default object and the encoded object are
    needed. Where the default object is a quantity (such as QInt), the name of the new default object within the current
    default object is needed

    A dictionary of objects with the key of the dict defining the name of the objects can be passed as a stop_at
    argument. Where a class recognised by canning is encountered that has the same name as the objects in the stop_at
    dict, then the object returned will be the object in the dictionary. This allows the same cable to be used by
    a number of different installs or cable sets.

    :param serial: the input
    :param default_obj: base default object
    :param default_obj_name: name of default object
    :param stop_at: dictionary of sub-objects, with their names as the key
    :param load_classes: dictionary of classes that can be loaded
    :return: object, object name (if known), remaining input string
    """
    if load_classes is None:
        load_classes2 = {}
    else:
        load_classes2 = load_classes
    tag, attr_name, attr_value, serial = read_xml_tag(serial)
    if (tag in list(load_classes2.keys())) or (tag in list(Q_CLASS.keys())):
        # print(f'tag: {tag}, default object: {default_obj} default name: {default_obj_name}')
        if tag in list(load_classes2.keys()):
            if attr_name == 'name' and attr_value != '':
                name = attr_value
                obj = load_classes2[tag](name=name)
            else:
                name = None
                obj = load_classes2[tag]()
            default_obj2 = obj
        else:
            # obj = Q_CLASS[tag]() <- this would be empty and need default
            if default_obj_name is not None:
                default_obj2 = default_obj.get_quantity(default_obj_name)
                if default_obj2 is None:
                    raise LoadException(f'trying to load object but "{default_obj_name}" attribute not defined '
                                    f'in {type(default_obj)}')
                obj = default_obj2
            else:
                raise LoadException(f'trying to load object but "{tag}" has no name so can not create base object')
            name = None

        if stop_at is not None and name in list(stop_at.keys()):
            end_tag, _attr_name, _attr_value, serial = read_xml_tag(serial)
            if end_tag != '/' + tag:
                raise LoadException(f'file read error: DataQuantity not closed, tag "{end_tag}" got instead of "{tag}"')
            obj = stop_at[name]
            return obj, name, serial

        dict_obj, _name, serial = loads_obj(serial, default_obj2, None, stop_at, load_classes=load_classes2)
        # obj.__dict__.update(dict_obj) <---- can't use this as replaces nested dict objects.
        # print(f'obj={obj} dict_obj={dict_obj}')
        update_dict(obj.__dict__, dict_obj)

        end_tag, _attr_name, _attr_value, serial = read_xml_tag(serial)
        if end_tag != '/'+tag:
            raise LoadException(f'file read error: DataQuantity not closed, tag "{end_tag}" got')
        return obj, name, serial
    elif tag == 'dict':
        if attr_name == 'name' and attr_value != '':
            name = attr_value
        else:
            name = None
        obj = dict()
        tag, attr_name, attr_value, serial = read_xml_tag(serial)
        while tag != '/dict':
            if tag != 'key':
                raise LoadException(f'file read error: dict should have <key> but got "{tag}"')
            dict_key, _name, serial = loads_obj(serial, default_obj, None, stop_at)
            end_tag, attr_name, attr_value, serial = read_xml_tag(serial)
            if end_tag != '/' + tag:
                raise LoadException(f'file read error: {tag} should be closed by /{tag} but {end_tag} found')
            tag, attr_name, attr_value, serial = read_xml_tag(serial)
            if tag != 'value':
                raise LoadException(f'file read error: dict item "{dict_key}" should have <value>')
            dict_value, _name, serial = loads_obj(serial, default_obj, dict_key, stop_at, load_classes=load_classes2)
            end_tag, attr_name, attr_value, serial = read_xml_tag(serial)
            if end_tag != '/' + tag:
                raise LoadException(f'file read error: {tag} should be closed by /{tag} but {end_tag} found')
            obj[dict_key] = dict_value
            tag, attr_name, attr_value, serial = read_xml_tag(serial)
        return obj, name, serial
    elif tag == 'list' or tag == 'tuple':
        is_tuple = tag == 'tuple'
        if attr_name == 'name' and attr_value != '':
            name = attr_value
        else:
            name = None
        obj = list()
        tag, attr_name, attr_value, serial = read_xml_tag(serial)
        while tag != '/list' and tag != '/tuple':
            if tag != 'item':
                raise LoadException(f'file read error: list should have <item> but got "{tag}"')
            value, _name, serial = loads_obj(serial, default_obj, None, stop_at, load_classes=load_classes2)
            obj.append(value)
            end_tag, attr_name, attr_value, serial = read_xml_tag(serial)
            if end_tag != '/' + tag:
                raise LoadException(f'file read error: {tag} should be closed by /{tag} but {end_tag} found')
            tag, attr_name, attr_value, serial = read_xml_tag(serial)
        if is_tuple:
            obj = tuple(obj)
        return obj, name, serial
    elif tag == 'str' or tag == 'NoneType' or tag == 'int' or tag == 'float' or tag == 'bool':
        text, serial = read_text(serial)
        end_tag, attr_name, attr_value, serial = read_xml_tag(serial)
        if end_tag != '/'+tag:
            raise LoadException(f'file read error: {tag} should be closed by /{tag} but {end_tag} found')
        if tag == 'str':
            return_value = text
        elif tag == 'int':
            return_value = int(text)
        elif tag == 'float':
            return_value = float(text)
        elif tag == 'bool':
            return_value = True if text == 'True' else False
        elif tag == 'NoneType':
            return_value = None
        else:
            raise LoadException(f'file read error: do not recognise tag "{tag}"')
        return return_value, None, serial
    else:
        raise LoadException(f'file read error: do not recognise tag "{tag}"')


def read_xml_tag(serial: str):
    """ Read an XML tag from a serial string

    Reads the first tag from a serial string and removes it from the serial string. The serial string should be in the
    format:

    '<tag attr_name="attr_value">*'

    The tag, attr_name, attr_value and remaining serial string will be returned

    :param serial: input serial string
    :return: tag, attr_name, attr_value, remaining serial string
    """
    serial = serial.strip()
    if serial.startswith('<'):
        serial = serial[1:]
    else:
        raise LoadException('xml tag does not start with "<"')
    tag, part, serial = serial.partition('>')
    if part == '':
        raise Exception('xml tag does not end with ">"')
    tag, space, attr = tag.partition(' ')
    attr_name, eq, attr_value = attr.partition('=')
    serial = serial.strip()
    return tag, attr_name, attr_value[1:-1], serial


def read_text(serial):
    """Read in text from a serial string

    Reads in text from a serial string, stopping when an XML tag is reached. Also returns the characters <&>'" back
    to their original values.

    :param serial: the input serial string
    :return: text, remaining serial string
    """
    text = serial.partition('<')[0]
    serial = serial[len(text):]

    text = text.replace('&lt;', '<')
    text = text.replace('&amp;', '&')
    text = text.replace('&gt;', '>')
    text = text.replace('&apos;', "'")
    text = text.replace('&quot;', '"')

    return text, serial


def update_dict(exist_dict: dict, new_dict: dict) -> None:
    """Update an existing dictionary with values from a new dictionary

    Updates values found in a new dictionary into an existing dictionary. The method takes account that the dictionary
    may also contain sub-dictionaries. Therefore:

    * if an item in the new dictionary does not exist in the old dictionary, the new item is added
    * if an item in the new dictionary already exists in the old dictionary, the value is updated
    * if an item in the new dictionary is a dict and does not exit in the old dictionary, the new dict is added
    * if an item in the new dictionary is a dict and exists in the old dictionary, the old dict is updated

    :param exist_dict: the existing dictionary to be updated
    :param new_dict:   the dictionary containing the new items
    :return: None
    """
    for key, value in new_dict.items():
        if isinstance(value, dict) and key in list(exist_dict.keys()):
            update_dict(exist_dict[key], new_dict[key])
        else:
            exist_dict[key] = value
