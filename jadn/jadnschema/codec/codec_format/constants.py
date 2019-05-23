"""
JADN Validation Constants
"""
from functools import partial

from . import (
    convert,
    general,
    validate,
    network
)


def testing(fun, fmt, val, *args, **kwargs):
    print(f"Format Function - {fun} {fmt}({val}) -> {args} - {kwargs}")
    raise TypeError("function not defined")


# Supported Operations - return value of check_format_function
FMT_CHK = 0     # Format check function exists
FMT_CVT = 1     # Binary conversion functions exist

# Format Operations - return value of get_format_function
FMT_NAME = 0    # Name of format option
FMT_CHECK = 1   # Function to check if value is valid (String, Binary, or Integer/Number types)
FMT_B2S = 2     # Function to convert binary to string (encode / serialize Binary types)
FMT_S2B = 3     # Function to convert string to binary (decode / deserialize Binary types)

# Format Validation constants
HOSTNAME_MAX_LENGTH = 255


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


# Semantic validation function for type: String, Binary, Number
FORMAT_CHECK_FUNCTIONS = {  # TYPE: [STRING, BINARY, ??]
    'email':        [validate.email, general.format_error, general.format_error],       # Email-Addr
    'hostname':     [validate.hostname, general.format_error, general.format_error],    # Domain-Name
    'ip-addr':      [validate.s_ip_addr, validate.b_ip_addr, general.format_error],     # IP-Addr (IPv4 or IPv6)
    'eui':          [validate.s_mac_addr, validate.b_mac_addr, general.format_error],   # MAC-Addr (EUI-48 or EUI-64)
    'uri':          [validate.uri, general.format_error, general.format_error],         # URI
    # Testing
    'x':            [general.format_error, validate.hex, general.format_error],         # Hex
    'ipv4-addr':    [validate.s_ip_addr, validate.b_ip_addr, general.format_error],     # IPv4
    'ipv6-addr':    [validate.s_ip_addr, validate.b_ip_addr, general.format_error],     # IPv6
}

FORMAT_CONVERT_BINARY_FUNCTIONS = {  # TYPE: [BINARY, STRING]
    'b':            (convert.b2s_base64url, convert.s2b_base64url),    # Base64url
    'ip-addr':      (network.b2s_ip_addr, network.s2b_ip_addr),        # IP (v4 or v6) Address, version autodetect
    'ipv4-addr':    (network.b2s_ipv4_addr, network.s2b_ipv4_addr),    # IPv4 Address
    'ipv6-addr':    (network.b2s_ipv6_addr, network.s2b_ipv6_addr),    # IPv6 Address
    'x':            (convert.b2s_hex, convert.s2b_hex),                # Hex
    # Testing
    'eui': (network.b2s_mac_addr, network.s2b_mac_addr),               # MAC-Addr (EUI-48 or EUI-64)
    'f16': (partial(testing, 'bin2str', 'f16'), partial(testing, 'str2bin', 'f16')),
    'f32': (partial(testing, 'bin2str', 'f32'), partial(testing, 'str2bin', 'f32')),
}

FORMAT_CONVERT_MULTIPART_FUNCTIONS = {  # TYPE: [LIST, STRING]
    'ip-net':   (network.a2s_ip_net, network.s2a_ip_net),       # IP (v4 or v6) Net Address with CIDR prefix length
    'ipv4-net': (network.a2s_ipv4_net, network.s2a_ipv4_net),   # IPv4 Net Address with CIDR prefix length
    'ipv6-net': (network.a2s_ipv6_net, network.s2a_ipv6_net),   # IPv6 Net Address with CIDR prefix length
}
