"""
JADN Codec Validation Functions
"""
import re

from urllib.parse import urlparse
from typing import Union

from . import (
    constants
)

from ...exceptions import (
    FormatError
)


# From https://stackoverflow.com/questions/2532053/validate-a-hostname-string
def hostname(sval: str) -> str:
    """
    Check if valid Hostname
    :param sval: Hostname to validate
    :return: given hostname
    :raises: TypeError, ValueError
    """
    if not isinstance(sval, str):
        raise TypeError(f"Hostname given is not expected {str}, given {type(sval)}")

    hostname = sval[:-1] if sval.endswith(".") else sval[:]  # Copy & strip exactly one dot from the right, if present
    if len(sval) < 1:
        raise ValueError(f'Hostname is not a valid length, minimum 1 character')

    if len(sval) > constants.HOSTNAME_MAX_LENGTH:
        raise ValueError(f'Hostname is not a valid length, exceeds {constants.HOSTNAME_MAX_LENGTH} characters')

    allowed = re.compile("(?!-)[A-Z0-9-]{1,63}(?<!-)$", re.IGNORECASE)
    if all(allowed.match(x) for x in hostname.split(".")):
        return sval
    raise ValueError(f"Hostname given is not valid")


# Use regex from https://stackoverflow.com/questions/201323/how-to-validate-an-email-address-using-a-regular-expression
#   A more comprehensive email address validator is available at http://isemail.info/about
def email(sval: str) -> str:
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
        r":(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
    )
    if re.match(rfc5322_re, sval):
        return sval
    raise ValueError(f"E-Mail given is not valid")


def uri(sval: str) -> str:
    """
    Check if valid URI
    :param sval: URI to validate
    :return: uri given
    :raises TypeError, ValueError
    """
    if not isinstance(sval, str):
        raise TypeError(f"URI given is not expected {str}, given {type(sval)}")
    url_match = re.match(r"(https?:\/\/(www\.)?)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)", sval)

    try:
        result = urlparse(sval)
        if all([result.scheme, result.netloc, result.path]) or url_match:
            return sval
    except Exception:
        pass
    raise ValueError(f"URI given is not expected valid")


def hex(val: Union[bytes, bytearray, str]) -> Union[bytes, bytearray, str]:
    if isinstance(val, (bytes, bytearray)):
        return val
    elif isinstance(val, str):
        try:
            return bytes.fromhex(val)
        except Exception as e:
            raise FormatError(f'Hex string improperly formatted - {val}')
    raise TypeError(f"Hex given is not expected {bytes}/{bytearray}/{str}, given {type(val)}")


# Network
def b_ip_addr(bval):
    """
    Check if valid IP Address
    Length of IP addr must be 32 or 128 bits
    :param bval: IP Address to validate
    :return: given IP Address
    :raises: TypeError, ValueError
    """
    if not isinstance(bval, bytes):
        raise TypeError(f"IP Address given is not expected {bytes}, given {type(bval)}")
    if len(bval) in (4, 16):
        return bval
    raise ValueError(f"IP Address given is not valid")


def s_ip_addr(sval):
    """
    Check if valid IP Address
    Length of IP addr must be 32 or 128 bits
    :param sval: IP Address to validate
    :return: given IP Address
    :raises: TypeError, ValueError
    """
    if not isinstance(sval, str):
        raise TypeError(f"IP Address given is not expected {str}, given {type(sval)}")

    if len(sval) in (4, 16):
        return sval
    raise ValueError(f"IP Address given is not valid")


def b_mac_addr(bval):
    """
    Check if valid MAC Address
    Length of MAC addr must be 48 or 64 bits
    :param bval: MAC Address to validate
    :return: given MAC Address
    :raises TypeError, ValueError
    """
    if not isinstance(bval, bytes):
        raise TypeError(f"MAC Address given is not expected {bytes}, given {type(bval)}")
    if len(bval) in (6, 8):
        return bval
    raise ValueError(f"Mac Address given is not valid")


def s_mac_addr(sval):
    """
    Check if valid MAC Address
    Length of MAC addr must be 48 or 64 bits
    :param sval: MAC Address to validate
    :return: given MAC Address
    :raises TypeError, ValueError
    """
    if not isinstance(sval, str):
        raise TypeError(f"MAC Address given is not expected {str}, given {type(sval)}")

    sval = re.split(r"[-:]", sval)
    if len(sval) in (6, 8):
        return ':'.join(sval)
    raise ValueError(f"Mac Address given is not valid")