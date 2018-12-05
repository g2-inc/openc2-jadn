from __future__ import unicode_literals
import base64
import re
import socket
from socket import AF_INET, AF_INET6
import string

# Format Operations
FMT_NAME = 0    # Name of format option
FMT_CHECK = 1   # Function to check if value is valid (String, Binary, or Integer/Number types)
FMT_B2S = 2     # Function to convert binary to string (encode / serialize Binary types)
FMT_S2B = 3     # Function to convert string to binary (decode / deserialize Binary types)


def s2b_hex(sval):      # Convert from hex string to binary
    return base64.b16decode(sval)


def b2s_hex(bval):      # Convert from binary to hex string
    return base64.b16encode(bval).decode()


def s2b_base64url(sval):      # Convert from base64url string to binary
    v = sval + ((4 - len(sval) % 4) % 4)*'='          # Pad b64 string out to a multiple of 4 characters
    if set(v) - set(string.ascii_letters + string.digits + '-_='):  # Python 2 doesn't support Validate
        raise TypeError('base64decode: bad character')
    return base64.b64decode(str(v), altchars='-_')


def b2s_base64url(bval):      # Convert from binary to base64url string
    return base64.urlsafe_b64encode(bval).decode().rstrip('=')


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
        raise TypeError
    rfc5322_re = (
        r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"
        r'"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@'
        r"(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])"
        r"|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]"
        r":(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])")
    if re.match(rfc5322_re, sval):
        return sval
    raise ValueError


def b_ip_addr(bval):        # Length of IP addr must be 32 or 128 bits
    if not isinstance(bval, bytes):
        raise TypeError
    if len(bval) == 4 or len(bval) == 16:
        return bval
    raise ValueError


def b_ip_subnet(bval):      # CIDR IP Address Range = base address + network prefix length
    raise ValueError        # TODO: write it


def s2b_ip_addr(sval):      # Convert IP addr from string to binary
    try:
        return socket.inet_pton(AF_INET, sval)
    except AttributeError:
        return socket.inet_aton(sval)       # Python 2 doesn't support inet_pton on Windows
    except OSError:
        raise ValueError


def b2s_ip_addr(bval):      # Convert IP addr from binary to string
    try:
        return socket.inet_ntop(AF_INET, bval)
    except AttributeError:
        return socket.inet_ntoa(bval)       # Python 2 doesn't support inet_ntop on Windows
    except OSError:
        raise ValueError


def s2b_ip_subnet(sval):
    raise ValueError        # TODO: write it


def b2s_ip_subnet(bval):
    raise ValueError


def b_mac_addr(bval):       # Length of MAC addr must be 48 or 64 bits
    if not isinstance(bval, bytes):
        raise TypeError
    if len(bval) == 6 or len(bval) == 8:
        return bval
    raise ValueError


def s_uri(sval):            # Check if valid URI
    if not isinstance(sval, type('')):
        raise TypeError
    if True:    # TODO
        return sval
    raise ValueError


def _format_ok(val):      # No value constraints on this type
    return val


def get_format_function(name, basetype, convert=None):
    if basetype == 'Binary' and convert is None:
        convert = 'b64u'
    try:
        cvt = FORMAT_CONVERT_FUNCTIONS[convert]
    except KeyError:
        cvt = (None, None)
    try:
        col = {'String': 0, 'Binary': 1, 'Number': 2}[basetype]
        return (name, FORMAT_CHECK_FUNCTIONS[name][col]) + cvt
    except KeyError:
        return (convert if convert else '', _format_ok) + cvt


FORMAT_CHECK_FUNCTIONS = {
    'hostname':     [s_hostname, None, None],       # Domain-Name
    'email':        [s_email, None, None],          # Email-Addr
    'ip-addr':      [None, b_ip_addr, None],        # IP-Addr
    'ip-subnet':    [None, b_ip_subnet, None],      # IP-Subnet
    'mac-addr':     [None, b_mac_addr, None],       # MAC-Addr
    'uri':          [s_uri, None, None]             # URI
}

FORMAT_CONVERT_FUNCTIONS = {
    'b64u': (b2s_base64url, s2b_base64url),         # Base64url
    'x': (b2s_hex, s2b_hex),                        # Hex
    'ip-addr':  (b2s_ip_addr, s2b_ip_addr),         # IP Address
    'ip-subnet': (b2s_ip_subnet, s2b_ip_subnet)     # IP Subnet Address with CIDR prefix length
}

# May not need functions for:
#   Date-Time       - Integer - min and max value for plausible date range
#   Duration        - Integer - max value for plausible durations?
#   Identifier      - String - regex pattern
#   Port            - Integer - min 0, max 65535
#   Request-Id      - Binary - len 0 - 8 bytes
#   UUID            - Binary - len == 16 bytes + RFC 4122 checks?

# Semantic validation functions from JSON Schema Draft 6
#    date-time      - String, RFC 3339, section 5.6
#    email          - String, RFC 5322, section 3.4.1
#    hostname       - String, RFC 1034, section 3.1
#    ipv4           - String, dotted-quad
#    ipv6           - String, RFC 2373, section 2.2
#    uri            - RFC 3986
#    uri-reference  - RFC 3986, section 4.1
#    json-pointer   - RFC 6901
#    uri-template   - RFC 6570
