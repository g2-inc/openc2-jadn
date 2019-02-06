"""
JADN Validation Constants
"""
from __future__ import unicode_literals

from . import (
    convert,
    general,
    network
)


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
    'hostname':     [general.s_hostname, general._err, general._err],       # Domain-Name
    'email':        [general.s_email, general._err, general._err],          # Email-Addr
    'ip-addr':      [general._err, network.b_ip_addr, general._err],        # IP-Addr (IPv4 or IPv6)
    'mac-addr':     [general._err, network.b_mac_addr, general._err],       # MAC-Addr
    'uri':          [general.s_uri, general._err, general._err]             # URI
}

FORMAT_CONVERT_BINARY_FUNCTIONS = {  # TYPE: [BINARY, STRING]
    'b': (convert.b2s_base64url, convert.s2b_base64url),            # Base64url
    'x': (convert.b2s_hex, convert.s2b_hex),                        # Hex
    'ip-addr':  (network.b2s_ip_addr, network.s2b_ip_addr),         # IP (v4 or v6) Address, version autodetect
    'ipv4-addr': (network.b2s_ipv4_addr, network.s2b_ipv4_addr),    # IPv4 Address
    'ipv6-addr': (network.b2s_ipv6_addr, network.s2b_ipv6_addr),    # IPv6 Address
}

FORMAT_CONVERT_MULTIPART_FUNCTIONS = {  # TYPE: [LIST, STRING]
    'ip-net': (network.a2s_ip_net, network.s2a_ip_net),             # IP (v4 or v6) Net Address with CIDR prefix length
    'ipv4-net': (network.a2s_ipv4_net, network.s2a_ipv4_net),       # IPv4 Net Address with CIDR prefix length
    'ipv6-net': (network.a2s_ipv6_net, network.s2a_ipv6_net),       # IPv6 Net Address with CIDR prefix length
}
