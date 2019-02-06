"""
JADN Conversion Validation Functions
"""
from __future__ import unicode_literals

import base64
import binascii
import re


# Binary to String, String to Binary conversion functions
def s2b_hex(sval):      # Convert from hex string to binary
    """
    Convert from hex string to binary
    :param sval: hex string to convert to binary
    :return: binary value of the given hex string
    """
    try:
        return base64.b16decode(sval)
    except binascii.Error:
        raise TypeError


def b2s_hex(bval):
    """
    Convert from binary to hex string
    :param bval: binary value to convert to hex string
    :return: hex string of the binary value given
    """
    return base64.b16encode(bval).decode()


def s2b_base64url(sval):
    """
    Convert from base64url string to binary
    :param sval: base64url string to convert to binary
    :return: binary representation of the give base64url
    """
    v = str(sval + ('=' * (len(sval) % 4)))  # Pad b64 string out to a multiple of 4 characters
    if re.match(r'^[a-zA-z0-9\-_=]*={0,3}$', v):
        return base64.b64decode(v, altchars='-_')
    raise TypeError('base64decode: bad character')


def b2s_base64url(bval):
    """
    Convert from binary to base64url string
    :param bval: binary value to convert to a base64url string
    :return: base64url string of the binary value given
    """
    return base64.urlsafe_b64encode(bval).decode().rstrip('=')