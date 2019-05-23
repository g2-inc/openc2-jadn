"""
JADN General Validation Functions
"""
from . import (
    constants
)


def format_ok(val):  # No value constraints on this type
    return val


def format_error(val):  # Unsupported format type
    raise ValueError(f'Unsupported format type: {type(val)}')


def check_format_function(name, basetype, convert=None):
    ff = get_format_function(name, basetype, convert)
    return ff[constants.FMT_CHECK] != format_error, ff[constants.FMT_B2S] != format_error


def get_format_function(name, basetype, convert=None):
    err = (format_error, format_error)  # unsupported conversion

    if basetype == 'Binary':
        convert = convert if convert else 'b'
        cvt = constants.FORMAT_CONVERT_BINARY_FUNCTIONS.get(convert, err)

    elif basetype == 'Array':
        cvt = constants.FORMAT_CONVERT_MULTIPART_FUNCTIONS.get(convert, err)

    else:
        cvt = err

    try:
        col = {'String': 0, 'Binary': 1, 'Number': 2}[basetype]
        return (name, constants.FORMAT_CHECK_FUNCTIONS[name][col]) + cvt
    except KeyError:
        return (name, format_error if name else format_ok) + cvt
