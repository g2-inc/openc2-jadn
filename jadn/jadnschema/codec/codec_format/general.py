"""
JADN General Validation Functions
"""
from __future__ import unicode_literals

import re

from urllib.parse import urlparse

from . import (
    constants
)


# From https://stackoverflow.com/questions/2532053/validate-a-hostname-string
def s_hostname(sval: str) -> str:
    """
    Check if valid Hostname
    :param sval: Hostname to validate
    :return: given hostname
    :raises: TypeError, ValueError
    """
    if not isinstance(sval, str):
        raise TypeError(f"Hostname given is not expected {str}, given {type(sval)}")

    hostname = sval[:-1] if sval[-1] == "." else sval[:]  # Copy & strip exactly one dot from the right, if present
    if len(sval) > constants.HOSTNAME_MAX_LENGTH:
        raise ValueError(f'Hostname is not a valid length, exceeds {constants.HOSTNAME_MAX_LENGTH} characters')

    allowed = re.compile("(?!-)[A-Z0-9-]{1,63}(?<!-)$", re.IGNORECASE)
    if all(allowed.match(x) for x in hostname.split(".")):
        return sval
    raise ValueError(f"Hostname given is not valid")


# Use regex from https://stackoverflow.com/questions/201323/how-to-validate-an-email-address-using-a-regular-expression
#   A more comprehensive email address validator is available at http://isemail.info/about
def s_email(sval: str) -> str:
    """
    Check if valid E-Mail address
    :param sval: E-Mail address to validate
    :return: given e-mail
    :raises: TypeError, ValueError
    """
    if not isinstance(sval, str):
        raise TypeError(f"E-Mail given is not expected {str}, given {type(sval)}")
    rfc5322_re = (
        r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"
        r'"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@'
        r"(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])"
        r"|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]"
        r":(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])")
    if re.match(rfc5322_re, sval):
        return sval
    raise ValueError(f"E-Mail given is not valid")


def s_uri(sval: str) -> str:
    """
    Check if valid URI
    :param sval: URI to validate
    :return: uri given
    :raises TypeError, ValueError
    """
    if not isinstance(sval, str):
        raise TypeError(f"URI given is not expected {str}, given {type(sval)}")

    try:
        result = urlparse(sval)
        if all([result.scheme, result.netloc]):
            return sval
    except Exception:
        pass
    raise ValueError(f"URI given is not expected valid")


def _format_ok(val):  # No value constraints on this type
    return val


def _err(val):  # Unsupported format type
    raise NameError(f'Unsupported format type: {type(val)}')


def check_format_function(name, basetype, convert=None):
    ff = get_format_function(name, basetype, convert)
    return ff[constants.FMT_CHECK] != _err, ff[constants.FMT_B2S] != _err


def get_format_function(name, basetype, convert=None):
    err = (_err, _err)  # unsupported conversion

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
        return (name, _err if name else _format_ok) + cvt
