"""
JADN Validation Constants
"""
from __future__ import unicode_literals

# from functools import partial

from . import (
    convert,
    general,
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

# Semantic validation function for type: String, Binary, Number
FORMAT_CHECK_FUNCTIONS = {  # TYPE: [STRING, BINARY, ??]
    'email':        [general.s_email, general.error, general.error],        # Email-Addr
    'hostname':     [general.s_hostname, general.error, general.error],     # Domain-Name
    'ip-addr':      [general.error, network.b_ip_addr, general.error],      # IP-Addr (IPv4 or IPv6)
    'eui':          [general.error, network.b_mac_addr, general.error],     # MAC-Addr (EUI-48 or EUI-64)
    'uri':          [general.s_uri, general.error, general.error],          # URI
    # Testing
    # 'ipv4-addr':    [general.error, partial(testing, 'chk', 'ipv4-addr'), general.error],
    # 'ipv6-addr':    [general.error, partial(testing, 'chk', 'ipv6-addr'), general.error],
}

FORMAT_CONVERT_BINARY_FUNCTIONS = {  # TYPE: [BINARY, STRING]
    'b':            (convert.b2s_base64url, convert.s2b_base64url),    # Base64url
    'x':            (convert.b2s_hex, convert.s2b_hex),                # Hex
    'ip-addr':      (network.b2s_ip_addr, network.s2b_ip_addr),        # IP (v4 or v6) Address, version autodetect
    'ipv4-addr':    (network.b2s_ipv4_addr, network.s2b_ipv4_addr),    # IPv4 Address
    'ipv6-addr':    (network.b2s_ipv6_addr, network.s2b_ipv6_addr),    # IPv6 Address
    # Testing
    # 'eui': (partial(testing, 'bin2str', 'eui'), partial(testing, 'str2bin', 'eui'))  # (network.b2s_mac_addr, network.s2b_mac_addr),
    # 'f16': (partial(testing, 'bin2str', 'f16'), partial(testing, 'str2bin', 'f16')),
    # 'f32': (partial(testing, 'bin2str', 'f32'), partial(testing, 'str2bin', 'f32')),
}

FORMAT_CONVERT_MULTIPART_FUNCTIONS = {  # TYPE: [LIST, STRING]
    'ip-net':   (network.a2s_ip_net, network.s2a_ip_net),       # IP (v4 or v6) Net Address with CIDR prefix length
    'ipv4-net': (network.a2s_ipv4_net, network.s2a_ipv4_net),   # IPv4 Net Address with CIDR prefix length
    'ipv6-net': (network.a2s_ipv6_net, network.s2a_ipv6_net),   # IPv6 Net Address with CIDR prefix length
}
