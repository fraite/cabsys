from typing import List
import xml.etree.ElementTree as ET

def log_line_str(line, heading_num=''):
    head_num = f'{heading_num: <3}'
    symbol = f'{line[1]:<30}'
    if isinstance(line[2], str):
        value = f'{line[2]:^42}'
    elif isinstance(line[2], bool):
        value = f'{str(line[2]):^42}'
    elif isinstance(line[2], int):
        value = f'{line[2]:^42}'
    elif isinstance(line[2], float):
        value = f'{line[2]:>42.5}'
    elif isinstance(line[2], tuple):
        value = '('
        for item in line[2]:
            value = value + str(item) + ','
        value = value[:-1] + ')'
        value = f'{value:^42}'
    else:
        raise Exception(f'trying to change log to text but value "{line[2]}" not expected type'
                        f' ("{type(line[2])}")')
    if line[0] != 'heading':
        units = f'{line[3]:<10}'
        source = f'{line[4]}'
    else:
        units = source = ''
    line_str = f'{head_num} {symbol}: {value}| {units}|  {source} \n'
    return line_str


def log_section_to_str(log_result, start_line=0, heading_num_pre=''):
    section_level = 1
    log_text = ''
    heading_num = 0
    for i in range(start_line, len(log_result)):
        line = log_result[i]
        if line[0] == 'heading':
            section_level = section_level + 1
        elif line[0] == 'body':
            if section_level == 1:
                heading_num = heading_num + 1
                log_text = log_text + log_line_str(line, str(heading_num))
        elif line[0] == 'result':
            section_level = section_level - 1
            if section_level == 1:
                heading_num = heading_num + 1
                log_text = log_text + log_line_str(line, str(heading_num) + '*')
            if section_level == 0:
                log_text = f'{heading_num_pre[:-1]}   {line[1]}\n\n' + log_text
                log_text = log_text + log_line_str(line, heading_num='')
            if section_level < 1:
                break
        else:
            raise Exception('line type in result not recognised')
    return log_text


class Log:
    """Stores calculation result output

    Stores the results of the calculations in a structured format that is useful for reviewing calculations.
    Additionally, any warning (such as non-IEC methods being used) are also stored.

    The level of detail that is stored is selectable by using the required_log_level attribute. The higher the
    required_log_level the more detailed the stored results. The required log_level ranges from 0 for only
    top level results to 100 for full details.

    Each section has a section_log_level. If this is greater (more detailed) than the log_level the entire calculation
    in that section will not be recorded, even if the line or subsection has a lower (more important) number. Suggested
    log levels are:
    10: minimal,
    30: default,
    70: detailed,
    90: verbose.
    """

    # Results and warnings are stored in self.result and self.warnings lists. The format is:
    # [type, text, value, source]
    # type is either 'heading', 'body', or 'result'
    # text is typically the variable name, value is variable value, and source is the source of the value
    def __init__(self, required_log_level: int = 30, max_log_count: int = 50000):
        """Stores calculation result output

        The level of detail that is stored is selectable by setting required_log_level. The higher the
        required_log_level the more detailed the stored results. The required log_level ranges from 0 for only
        top level results to 100 for full details.

        To ensure that the log does not run out of memory a maximum log count sets the maximum number of rows in the
        log. Attempts to log lines after the limit has been set will result in an Exception being generated.

        If required_log_level is set to None or zero then the logger does nothing.

        :param required_log_level: level of detail for logging
        :param max_log_count: the maximum number of rows in the log

        """
        self.result = []
        self.warning = []
        self.warning.append(('heading', 'Warnings', ''))
        self.required_log_level: int = required_log_level
        self.current_log_level: List[int] = [0]
        self.current_heading = []
        self.max_log_count = max_log_count

    def start_log_level(self, section_log_level: int = None):
        # set debug level for section. Note debug level can only get more detailed.
        if section_log_level is None:
            self.current_log_level.append(self.current_log_level[-1])
        elif section_log_level >= self.current_log_level[-1]:
            self.current_log_level.append(section_log_level)
        else:
            self.current_log_level.append(self.current_log_level[-1])

    def end_log_level(self):
        # end debug level for section
        del self.current_log_level[-1]

    def start_section(self, text: str, source: str, section_log_level: int = None):
        """Start a log section

        Starts a new log section, generally indicating the start of a section or subsection of calculations if the
        current log level is higher than the section log level.

        The section_log_level attribute indicates which level of detail that the section is considered to be. Sections
        with a section_log_level of 0 indicate that they are always included if log data is stored, while a
        section_log_level of 100 indicates the section will be included for the most detailed results. Where no
        section_debug_level is specified, the section_log_level of the parent sections is used. Note the
        section_log_level can not be less (lower value) than the parent section and if this is specified the parent
        section value is used instead.

        If the required_log_level is set to None or zero then nothing happens as a result of this call.

        :param text: title of section, generally the calculated IEC symbol
        :param source: reference to the calculation
        :param section_log_level: the level that the section belongs to, where 0 to 100

        """

        if self.required_log_level == 0 or self.required_log_level is None:
            return

        # set debug level for section. Note debug level can only get more detailed.
        if len(self.result) > 900000:
            raise Exception(f'too many log entries ({len(self.result)}), reduce install.config.log_level')
        elif section_log_level is None:
            self.current_log_level.append(self.current_log_level[-1])
        elif section_log_level >= self.current_log_level[-1]:
            self.current_log_level.append(section_log_level)
        else:
            self.current_log_level.append(self.current_log_level[-1])

        # start section if debug_level is sufficiently detailed
        if self.required_log_level >= self.current_log_level[-1]:
            self.result.append(('heading', text, source))
            self.current_heading.append(text)
        self.warning.append(('heading', text, source))

    def add_line(self, text, value, unit, source=''):
        """Add a line to the log section

        A new line is added to the log if the required_log_level is greater than the current_log_value. The
        current_log_value is set at the start of the log section (set by start_section function).

        The line contains the text (normally a symbol), the value of the symbol, the unit of the symbol, optionally
        the source of the value (for example the IEC clause).

        If the required_log_level is set to None or zero then nothing happens as a result of this call.

        :param text: title of the value, generally the IEC symbol
        :param value: value of the text
        :param unit: unit of the value (for example 'm')
        :param source: reference to the value

        """
        if self.required_log_level == 0 or self.required_log_level is None:
            return

        if text is None:
            raise Exception('attempting add entry to log but text (probably symbol) missing')
        if not (isinstance(value, float) or isinstance(value, int) or isinstance(value, str)
                or isinstance(value, tuple)):
            raise Exception(f'trying to add line to the logger but {text} is type {type(value)}')
        if self.required_log_level >= self.current_log_level[-1] and len(self.result) < 900000:
            self.result.append(('body', text, value, unit, source))

    def add_warning(self, warning_text=''):
        if self.required_log_level == 0 or self.required_log_level is None:
            return

        if self.required_log_level >= self.current_log_level[-1]:
            self.result.append(('body', 'warning', '-', '-', warning_text))
            self.warning.append(('body', 'warning', warning_text))

    def end_section(self, text, value, unit, source):
        """End a log section

        Ends a log section, generally indicating the end of a section or subsection of calculations if the
        current log level is higher than the section log level. The text argument has to be the same title as given when
        the section was started otherwise an exception is raised. The source argument will overwrite the source value
        given at when the section was started.

        The value and unit of the heading is given when ending the section, since it is not known when the section
        starts.

        :param text: title of section, generally the IEC symbol
        :param value: the value of the final value calculated in the section
        :param unit: the unit of the final value calculated
        :param source: reference to the calculation

        """
        if self.required_log_level == 0 or self.required_log_level is None:
            return

        if value is None:
            value = "None"
        if not (isinstance(value, float) or isinstance(value, int) or isinstance(value, str)
                or isinstance(value, tuple)):
            raise Exception(f'trying to end a section in the logger but {text} is type {type(value)}')
        if self.required_log_level >= self.current_log_level[-1]:
            self.result.append(('result', text, value, unit, source))
            if text != self.current_heading[-1]:
                raise Exception(f'logging trying to end section but heading "{self.current_heading[-1]}"'
                                f'at start is not the same as "{text}"')
            self.current_heading.pop()
        if self.warning[-1][0] == 'heading':
            self.warning = self.warning[:-1]
        else:
            self.warning.append(('result', text, source))

        # end debug level for section
        del self.current_log_level[-1]

    def close_section(self, text='', value=None, unit='', source=''):
        """Closes a log section

        Closes a log section, generally indicating the end of a section or subsection of calculations, where no result
        has been found. This is typically if an exception has been generated.

        :param text: text, normally error message
        :param value: value of the final value calculated in the section
        :param unit: unit of the final value calculated
        :param source: reference to the calculation

        """

        if self.required_log_level == 0 or self.required_log_level is None:
            return

        if value is None:
            value = "None"

        if not (isinstance(value, float) or isinstance(value, int) or isinstance(value, str)
                or isinstance(value, tuple)):
            raise Exception(f'trying to end a section in the logger but'
                            f' {self.current_heading[-1]} is type {type(value)}')
        # if self.required_log_level >= self.current_log_level[-1]:
        self.result.append(('result', self.current_heading[-1], 'Exception generated', '', source))
        self.warning.append(('body', 'Exception generated', text))
        self.result.append(('body', f'! {text} !', value, unit, source))
        self.current_heading.pop()

        # if self.warning[-1][0] == 'heading':
        #     self.warning = self.warning[:-1]
        # else:
        #     self.warning.append(('result', self.current_heading[-1], source))

        # end debug level for section
        # del self.current_log_level[-1]

    def close_sections(self, text, value='', unit='', source=''):
        """Close all sections in the log

        Closes a log ensuring all sections are closed (no hanging headings). This is typically if an exception has been
        generated.

        :param text: text, normally error message
        :param value: value of the final value calculated in the section
        :param unit: unit of the final value calculated
        :param source: reference to the calculation
        :return:
        """

        if len(self.current_heading) > 0:
            self.close_section(text, value, unit, source)
        while len(self.current_heading) > 0:
            self.close_section()
            # self.current_heading.pop()

    def text(self):
        """Convert the log to a text string

        :return: log in a string format"""

        log_text = '             Cabsys log\n\n'
        # create first section of the log output
        log_text = log_text + log_section_to_str(self.result)

        head_num = [1]
        for i in range(len(self.result)):
            line = self.result[i]
            if line[0] == 'body':
                head_num[-1] = head_num[-1] + 1
            elif line[0] == 'heading':
                head_num_str = ''
                for head_num_part in head_num:
                    head_num_str = head_num_str + str(head_num_part) + '.'
                log_text = log_text + '\n'
                log_text = log_text + log_section_to_str(self.result, i + 1, head_num_str)
                head_num.append(1)
            elif line[0] == 'result':
                head_num.pop()
                head_num[-1] = head_num[-1] + 1

        return log_text

    def text_xml(self):
        """Convert the log to a text string

        :return: log in a string format"""

        root = ET.Element('result')

        xml_tree = [root]
        for i in range(len(self.result)):
            line = self.result[i]
            line_1 = line[1].replace(" ", "_").replace(",", "_").replace("(", '_').replace(")", '_')
            line_1 = line_1.replace("'", 'dash').replace('^', "raise").replace("/", '_').replace('%', 'percent_')
            line_1 = line_1.replace("=", '_')
            if line[0] == 'heading':
                new_head = ET.SubElement(xml_tree[-1], f'{line_1}')
                xml_tree.append(new_head)
            elif line[0] == 'result':
                xml_head = xml_tree.pop()
                if isinstance(line[2], (str, int, float)):
                    value = f'{line[2]}'
                elif isinstance(line[2], bool):
                    value = f'{str(line[2])}'
                elif isinstance(line[2], tuple):
                    value = '('
                    for item in line[2]:
                        value = value + str(item) + ','
                    value = value[:-1] + ')'
                else:
                    raise Exception(f'trying to change log to text but value "{line[2]}" not expected type'
                                    f' ("{type(line[2])}")')
                xml_head.set('value', value)
                xml_head.set('unit', line[3])
                xml_head.set('source', line[4])
            elif line[0] == 'body':
                symbol = f'{line_1}'
                if isinstance(line[2], (str, int, float)):
                    value = f'{line[2]}'
                elif isinstance(line[2], bool):
                    value = f'{str(line[2])}'
                elif isinstance(line[2], tuple):
                    value = '('
                    for item in line[2]:
                        value = value + str(item) + ','
                    value = value[:-1] + ')'
                    # value = f'{value:^42}'
                else:
                    raise Exception(f'trying to change log to text but value "{line[2]}" not expected type'
                                    f' ("{type(line[2])}")')
                body_element = ET.SubElement(xml_tree[-1], symbol)
                # ET.SubElement(body_element, 'value').text = f'{value}'
                # if line[3] != '':
                #     ET.SubElement(body_element, 'unit').text = f'{line[3]}'
                # if line[4] != '':
                #     ET.SubElement(body_element, 'source').text =f'{line[4]}'
                body_element.set('value', value)
                body_element.set('unit', line[3])
                body_element.set('source', line[4])
            else:
                raise Exception(f'first element is "{line[0]}", but should be heading, body or result')

        ET.indent(root, '  ')
        log_text = ET.tostring(root, encoding='unicode')
        return log_text


no_log: Log = Log(required_log_level=0)
"""no_log logger

Use this logger if no logger is required. This is useful as a default logger. The logger can be called normally but
not log anything.
"""


class LogSection:
    """Decorator that starts a new section in the logger

    A function that performs a calculation or looks up a value can be decorated so that a new section is started in
    the logger.
    """

    def __init__(self, log_attr_name: str, section_log_level: int = None):
        """Decorator that starts a new section in the logger

        The results of the function will be logged in a new section, if a logger is specified. The name of the new
        section is passed as the argument of the decorator and is normally the function symbol. This should use
        characters that can be displayed by tkinter.

        :param log_attr_name: name of new section in Log object
        :param section_log_level: section log level
        """
        self.log_attr_name = log_attr_name
        self.section_log_level = section_log_level

    def __call__(self, fn):

        def wrapped_fn(*args, **kargs):

            # get logger if if exists
            log = None
            for arg in args:
                if isinstance(arg, Log):
                    log = arg
            if log is None:
                try:
                    log = kargs['log']
                except KeyError:
                    pass

            if log is not None:
                log.start_section(self.log_attr_name, 'top', section_log_level=self.section_log_level)

            fn_result = fn(*args, **kargs)

            if log is not None:
                from cabsys.quantity.quantity_store import QuantityBase
                if isinstance(fn_result, QuantityBase):
                    log.end_section(self.log_attr_name, fn_result.value, fn_result.unit, fn_result.source)
                elif isinstance(fn_result, tuple):
                    value = ''
                    unit = ''
                    source = ''
                    for item in fn_result:
                        if isinstance(item, QuantityBase):
                            value = value + f'{item.value:.5f}, '
                            unit = unit + f'{item.unit}, '
                            source = item.source
                        else:
                            value = value + f'{item:.5f}, '
                    if value != '':
                        value = value[:-2]
                    if unit != '':
                        unit = unit[:-2]
                    log.end_section(self.log_attr_name, value, unit, source)
                else:
                    raise Exception(f'trying to log result of function but return type is {type(fn_result)}')

            return fn_result
        return wrapped_fn
