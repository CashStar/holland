"""
    holland.core.config.validation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Validation implementations for Configspec checks

    This module implementations individual validation for
    various datatype and checks that can be defined in a
    ``holland.core.config.Configspec``

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

import csv
import logging
try:
    from io import StringIO, BytesIO
except ImportError: #pragma: no cover
    from StringIO import StringIO
    BytesIO = StringIO
import shlex
import subprocess
from holland.core.config.util import unquote

class BaseValidator(object):
    """Validator interface

    Validators take some value and check that
    it conforms to some set of constraints. If a value
    is the string representation of the real value then
    validate() will convert the string as needed.  format()
    will do the opposite and serialize a value back into
    useful config string.
    """
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def normalize(cls, value):
        "Normalize a string value"
        if isinstance(value, basestring):
            return unquote(value)
        else:
            return value

    @classmethod
    def convert(cls, value):
        """Convert a value from its string representation to a python
        object.

        :returns: converted value
        """
        return value

    def validate(self, value):
        """Validate a value and return its conversion

        :raises: ValidationError on failure
        :returns: converted value
        """
        value = self.normalize(value)
        value = self.convert(value)
        return value

    @classmethod
    def format(cls, value):
        """Format a value as it should be written in a config file

        :returns: value formatted to a string
        """
        if value is None:
            return value
        return str(value)

class ValidationError(ValueError):
    """Raised when validation fails"""
    def __init__(self, message, value):
        ValueError.__init__(self, message)
        self.value = value
        self.message = message

    def __str__(self):
        return self.message

class BoolValidator(BaseValidator):
    """Validator for boolean values

    When converting a string this accepts the
    following boolean formats:
    True:  yes, on, true, 1
    False: no, off, false, 0
    """

    def convert(self, value):
        """Convert a string value to a python Boolean"""
        valid_bools = {
            'yes'  : True,
            'on'   : True,
            'true' : True,
            '1'    : True,
            'no'   : False,
            'off'  : False,
            'false': False,
            '0'    : False,
        }
        if isinstance(value, bool):
            return value
        return valid_bools[value.lower()]

    def format(self, value):
        """Format a python boolean as a string value"""
        return value and 'yes' or 'no'

class FloatValidator(BaseValidator):
    """Validate float strings"""

    def convert(self, value):
        """Convert a string to float

        :raises: ValidationError
        :returns: python float representation of value
        """
        try:
            return float(value)
        except ValueError:
            raise ValidationError("Invalid format for float %s" % value, value)

    def format(self, value):
        """Format a float to a string"""
        return "%.2f" % value

class IntValidator(BaseValidator):
    """Validate integer values"""

    def convert(self, value):
        if value is None:
            return value
        if isinstance(value, int):
            value = value
        else:
            try:
                value = int(value, self.kwargs.get('base', 10))
            except ValueError:
                raise ValidationError("Invalid format for integer %s" % value,
                                      value)

        if self.kwargs.get('min') is not None and \
                value < self.kwargs.get('min'):
            raise ValidationError("Integer value must be > %d" %
                                  self.kwargs['min'], value)

        if self.kwargs.get('max') and value > self.kwargs.get('max'):
            raise ValidationError("Integer value exceeds maximum %d" %
                                  self.kwargs['max'], value)

        return value

class StringValidator(BaseValidator):
    """Validate string values"""

class OptionValidator(BaseValidator):
    """Validate against a list of options

    This constrains a value to being one of a series of constants
    """
    def convert(self, value):
        """Ensure value is one of the available options"""
        if value in self.args:
            return value
        raise ValidationError("invalid option '%s' - choose from: %s" %
                              (value, ','.join(self.args)),
                              value)


class ListValidator(BaseValidator):
    """Validate a list

    This will validate a string is a proper comma-separate list. Each string
    in the list will be unquoted and a normal python list of the unquoted
    and unescaped values will be returned.
    """

    #@staticmethod
    def _utf8_encode(unicode_csv_data):
        """Shim to convert lines of text to utf8 byte strings to allow
        processing by the csv module

        :returns: iterable of utf8 bytestrings
        """
        for line in unicode_csv_data:
            yield line.encode('utf-8')
    _utf8_encode = staticmethod(_utf8_encode)

    def normalize(self, value):
        "Normalize a value"
        # skip BaseValidator's unquoting behavior
        return value

    def convert(self, value):
        """Convert a csv string to a python list"""
        if isinstance(value, list):
            return value
        data = self._utf8_encode(StringIO(value))
        reader = csv.reader(data, dialect='excel', delimiter=',',
                skipinitialspace=True)
        return [unquote(cell.decode('utf8')) for row in reader for cell in row
                 if unquote(cell.decode('utf8'))]

    def format(self, value):
        """Format a list to a csv string"""
        result = BytesIO()
        writer = csv.writer(result, dialect='excel')
        writer.writerow([cell.encode('utf8') for cell in value])
        return result.getvalue().decode('utf8').strip()

class TupleValidator(ListValidator):
    """Validate a tuple

    Identical to ``ListValidator`` but returns a tuple rather than
    a list.
    """
    def convert(self, value):
        """Convert a csv string to a python tuple"""
        value = super(TupleValidator, self).convert(value)
        return tuple(value)


class CmdlineValidator(BaseValidator):
    """Validate a commmand line"""

    def convert(self, value):
        """Convert a command line string to a list of command args"""
        return [arg.decode('utf8') for arg in shlex.split(value.encode('utf8'))]

    def format(self, value):
        """Convert a list of command args to a single command line string"""
        return subprocess.list2cmdline(value)


class LogLevelValidator(BaseValidator):
    """Validate a logging level

    This constraints a logging level to one of the standard levels supported
    by the python logging module:

    * debug
    * info
    * warning
    * error
    * fatal
    """

    levels = {
        'debug'         : logging.DEBUG,
        'info'          : logging.INFO,
        'warning'       : logging.WARNING,
        'error'         : logging.ERROR,
        'fatal'         : logging.FATAL,
        logging.DEBUG   : 'debug',
        logging.INFO    : 'info',
        logging.WARNING : 'warning',
        logging.ERROR   : 'error',
        logging.FATAL   : 'fatal',
    }

    def convert(self, value):
        """Convert a string log level to its integer equivalent"""
        if isinstance(value, int):
            return value
        try:
            return self.levels[value.lower()]
        except KeyError:
            raise ValidationError("Invalid log level '%s'" % value, value)

    def format(self, value):
        """Format an integer log level to its string representation"""
        try:
            return self.levels[value].lower()
        except KeyError:
            raise ValidationError("Unknown logging level '%s'" % value, value)

#: default list of validators
default_validators = (
    ('boolean', BoolValidator),
    ('integer', IntValidator),
    ('float', FloatValidator),
    ('string', StringValidator),
    ('option', OptionValidator),
    ('list', ListValidator),
    ('force_list', ListValidator),
    ('tuple', TupleValidator),
    ('cmdline', CmdlineValidator),
    ('log_level', LogLevelValidator),
)
