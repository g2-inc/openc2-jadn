from __future__ import unicode_literals
import base64
import binascii
import ipaddress
import re

from urllib.parse import urlparse

# Supported Operations - return value of check_format_function
FMT_CHK = 0     # Format check function exists
FMT_CVT = 1     # Binary conversion functions exist

# Format Operations - return value of get_format_function
FMT_NAME = 0    # Name of format option
FMT_CHECK = 1   # Function to check if value is valid (String, Binary, or Integer/Number types)
FMT_B2S = 2     # Function to convert binary to string (encode / serialize Binary types)
FMT_S2B = 3     # Function to convert string to binary (decode / deserialize Binary types)


# From https://stackoverflow.com/questions/2532053/validate-a-hostname-string
def s_hostname(sval):
    if not isinstance(sval, type('')):
        raise TypeError
    hostname = sval[:]      # Copy since we're modifying input
    if hostname[-1] == ".":
        hostname = hostname[:-1]  # strip exactly one dot from the right, if present
    if len(sval) > 253:
        raise ValueError
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    if all(allowed.match(x) for x in hostname.split(".")):
        return sval
    raise ValueError


# Use regex from https://stackoverflow.com/questions/201323/how-to-validate-an-email-address-using-a-regular-expression
#   A more comprehensive email address validator is available at http://isemail.info/about
def s_email(sval):
    if not isinstance(sval, type('')):
        raise TypeError(f"E-Mail given is not expected {type('')}, given {type(sval)}")
    rfc5322_re = (
        r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"
        r'"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@'
        r"(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])"
        r"|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]"
        r":(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])")
    if re.match(rfc5322_re, sval):
        return sval
    raise ValueError(f"E-Mail given is not valid")


def b_ip_addr(bval):
    """
    Check if valid IP Address
    Length of IP addr must be 32 or 128 bits
    :param bval: MAC Address to validate
    :return: given MAC Address
    :raises TypeError, ValueError
    """
    if not isinstance(bval, bytes):
        raise TypeError(f"IP Address given is not expected {bytes}, given {type(bval)}")
    if len(bval) == 4 or len(bval) == 16:
        return bval
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
    if len(bval) == 6 or len(bval) == 8:
        return bval
    raise ValueError(f"Mac Address given is not valid")


def s_uri(sval):            # Check if valid URI
    """
    Check if valid URI
    :param sval: URI to validate
    :return: uri given
    :raises TypeError, ValueError
    """
    if not isinstance(sval, type('')):
        raise TypeError(f"URI given is not expected {type('')}, given {type(sval)}")

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
    raise NameError


# Semantic validation function for type: String, Binary, Number
FORMAT_CHECK_FUNCTIONS = {
    'hostname':     [s_hostname, _err, _err],       # Domain-Name
    'email':        [s_email, _err, _err],          # Email-Addr
    'ip-addr':      [_err, b_ip_addr, _err],        # IP-Addr (IPv4 or IPv6)
    'mac-addr':     [_err, b_mac_addr, _err],       # MAC-Addr
    'uri':          [s_uri, _err, _err]             # URI
}


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


# Convert IP address string to binary
def _value_check_s2b(val):
    """
    Validate the value given is the proper type
    :param val: value to validate the type
    :raises: TypeError - Invalid type given
    """
    if isinstance(type(val), type('')):
        raise TypeError(f"IP Address given is not expected {type('')}, given {type(val)}")


def s2b_ip_addr(sval):
    """
    Convert the given IP Address to a binary representation
    :param sval: string value of the IP Address to convert to binary
    :return: binary representation of the IP Address given
    """
    check = _value_check_s2b(sval)
    if check:
        raise check

    return s2b_ipv6_addr(sval) if ':' in sval else s2b_ipv4_addr(sval)


def s2b_ipv4_addr(sval):
    """
    Convert the given IPv4 Address to a binary representation
    :param sval: string value of the IPv4 Address to convert to binary
    :return: binary representation of the IPv4 Address given
    """
    try:
        check = _value_check_s2b(sval)
        return ipaddress.IPv4Address(sval).packed
    except Exception as e:
        raise e


def s2b_ipv6_addr(sval):
    """
    Convert the given IPv6 Address to a binary representation
    :param sval: string value of the IPv6 Address to convert to binary
    :return: binary representation of the IPv6 Address given
    """
    try:
        check = _value_check_s2b(sval)
        return ipaddress.IPv6Address(sval).packed
    except Exception as e:
        raise e


# Convert IP address binary to string
def _value_check_b2s(val):
    """
    Validate the value given is the proper type
    :param val: value to validate the type
    :raises: TypeError - Invalid type given
    """
    if isinstance(type(val), type(b'')):
        raise TypeError(f"IP Address given is not expected {type(b'')}, given {type(val)}")


def b2s_ip_addr(bval):
    """
    Convert the given IP Address to a string representation
    :param bval: binary value of the IP Address to convert to string
    :return: string representation of the IP Address given
    """
    check = _value_check_b2s(bval)
    if check:
        raise check

    return b2s_ipv6_addr(bval) if len(bval) > 4 else b2s_ipv4_addr(bval)


def b2s_ipv4_addr(bval):
    """
    Convert the given IPv4 Address to a string representation
    :param bval: binary value of the IPv4 Address to convert to string
    :return: string representation of the IPv4 Address given
    """
    try:
        check = _value_check_b2s(bval)
        return str(ipaddress.IPv4Address(bval))
    except Exception as e:
        raise e


def b2s_ipv6_addr(bval):
    """
    Convert the given IPv6 Address to a string representation
    :param bval: binary value of the IPv6 Address to convert to string
    :return: string representation of the IPv6 Address given
    """
    try:
        check = _value_check_b2s(bval)
        return str(ipaddress.IPv6Address(bval))
    except Exception as e:
        raise e


# IP Net (address, prefix length tuple) conversions
# Convert CIDR string to IP Net (v4 or v6)
def _value_check_s2a(val):
    """
    Validate the value given is the proper type
    :param val: value to validate the type
    :raises: TypeError - Invalid type given
    """
    if isinstance(type(val), type('')):
        raise TypeError(f"CIDR Address given is not expected {type('')}, given {type(val)}")


def s2a_ip_net(sval, strict=False):
    """
    Convert the given CIDR Address to an IP and Prefix
    :param sval: binary value of the CIDR Address to convert an IP and Prefix
    :param strict: boot - enforce validation of network with host bits set
    :return: list - ip, prefix
    """
    check = _value_check_b2s(sval)
    if check:
        raise check

    return s2a_ipv6_net(sval, strict) if ':' in sval else s2a_ipv4_net(sval, strict)


def s2a_ipv4_net(sval, strict=False):
    """
    Convert the given CIDRv4 Address to an IP and Prefix
    :param sval: binary value of the CIDRv4 Address to convert an IP and Prefix
    :param strict: boot - enforce validation of network with host bits set
    :return: list - ipv4, prefix
    """
    try:
        check = _value_check_s2a(sval)
        addr = tuple(sval.split('/', 1))
        v = ipaddress.IPv4Network(addr, strict)
        return [b2s_base64url(s2b_ipv4_addr(addr[0])), v.prefixlen]
    except Exception as e:
        raise e


def s2a_ipv6_net(sval, strict=False):
    """
    Convert the given CIDRv6 Address to an IP and Prefix
    :param sval: binary value of the CIDRv6 Address to convert an IP and Prefix
    :param strict: boot - enforce validation of network with host bits set
    :return: list - ipv6, prefix
    """
    try:
        check = _value_check_s2a(sval)
        addr = tuple(sval.split('/', 1))
        v = ipaddress.IPv6Network(addr, strict)
        return [b2s_base64url(s2b_ipv6_addr(addr[0])), v.prefixlen]
    except Exception as e:
        raise e


# Convert IP Net (v4 or v6) to string in CIDR notation
def _value_check_a2s(val):
    """
    Validate the value given is the proper type
    :param val: value to validate the type
    :raises: Value - Invalid size list given
    :raises: TypeError - Invalid type given
    """
    if len(val) != 2:
        raise ValueError(f'List of size 2 expected, give size {len(val)}')
    elif isinstance(type(val[0]), type('')):
        raise TypeError(f"IP Address given is not expected {type('')}, given {type(val[0])}")


def a2s_ip_net(aval):
    """
    Convert the given IP Address and Prefix to CIDR representation
    :param aval: list of IP and Prefix
    :return: string representation of the CIDR Address
    """
    check = _value_check_a2s(aval)
    if check:
        raise check

    return a2s_ipv6_net(aval) if len(aval[0]) > 4 else a2s_ipv4_net(aval)


def a2s_ipv4_net(aval):
    """
    Convert the given IPv4 Address and Prefix to CIDRv4 representation
    :param aval: list of IPv4 and Prefix
    :return: string representation of the CIDRv4 Address
    """
    check = _value_check_a2s(aval)
    if check:
        raise check

    if aval[1] < 0 or aval[1] > 32:  # Verify prefix length is valid
        raise ValueError(f'Prefix length not between 0 and 32: {aval[1]}')
    return f'{b2s_ipv4_addr(s2b_base64url(aval[0]))}/{aval[1]}'  # Convert Binary default string to type-specific string


def a2s_ipv6_net(aval):
    """
    Convert the given IPv6 Address and Prefix to CIDRv6 representation
    :param aval: list of IPv6 and Prefix
    :return: string representation of the CIDRv6 Address
    """
    check = _value_check_a2s(aval)
    if check:
        raise check

    if aval[1] < 0 or aval[1] > 128:  # Verify prefix length is valid
        raise ValueError(f'Prefix length not between 0 and 128: {aval[1]}')
    return f'{b2s_ipv6_addr(s2b_base64url(aval[0]))}/{aval[1]}'  # Convert Binary default string to type-specific string


FORMAT_CONVERT_BINARY_FUNCTIONS = {
    'b': (b2s_base64url, s2b_base64url),            # Base64url
    'x': (b2s_hex, s2b_hex),                        # Hex
    'ip-addr':  (b2s_ip_addr, s2b_ip_addr),         # IP (v4 or v6) Address, version autodetect
    'ipv4-addr': (b2s_ipv4_addr, s2b_ipv4_addr),    # IPv4 Address
    'ipv6-addr': (b2s_ipv6_addr, s2b_ipv6_addr),    # IPv6 Address
}

FORMAT_CONVERT_MULTIPART_FUNCTIONS = {
    'ip-net': (a2s_ip_net, s2a_ip_net),             # IP (v4 or v6) Net Address with CIDR prefix length
    'ipv4-net': (a2s_ipv4_net, s2a_ipv4_net),       # IPv4 Net Address with CIDR prefix length
    'ipv6-net': (a2s_ipv6_net, s2a_ipv6_net),       # IPv6 Net Address with CIDR prefix length
}


def check_format_function(name, basetype, convert=None):
    ff = get_format_function(name, basetype, convert)
    return ff[FMT_CHECK] != _err, ff[FMT_B2S] != _err


def get_format_function(name, basetype, convert=None):
    if basetype == 'Binary':
        convert = convert if convert else 'b'
        try:
            cvt = FORMAT_CONVERT_BINARY_FUNCTIONS[convert]
        except KeyError:
            cvt = (_err, _err)      # Binary conversion function not found
    elif basetype == 'Array':
        try:
            cvt = FORMAT_CONVERT_MULTIPART_FUNCTIONS[convert]
        except KeyError:
            cvt = (_err, _err)      # Multipart conversion function not found
    else:
        cvt = (_err, _err)          # Type does not support conversion
    try:
        col = {'String': 0, 'Binary': 1, 'Number': 2}[basetype]
        return (name, FORMAT_CHECK_FUNCTIONS[name][col]) + cvt
    except KeyError:
        return (name, _err if name else _format_ok) + cvt


# Don't need custom format functions, use built-in value constraints instead:
#   Date-Time       - Integer - min and max value for plausible date range
#   Duration        - Integer - min 0, max value for plausible durations
#   Identifier      - String - regex pattern
#   Port            - Integer - min 0, max 65535
#   Request-Id      - Binary - len 0 - 8 bytes

# Semantic validation functions from JSON Schema Draft 6
#    date-time      - String, RFC 3339, section 5.6
#    email          - String, RFC 5322, section 3.4.1
#    hostname       - String, RFC 1034, section 3.1
#    ipv4           - String, dotted-quad
#    ipv6           - String, RFC 2373, section 2.2
#    uri            - String, RFC 3986
#    uri-reference  - String, RFC 3986, section 4.1
#    json-pointer   - String, RFC 6901
#    uri-template   - String, RFC 6570
