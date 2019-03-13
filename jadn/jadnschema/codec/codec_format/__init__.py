"""
JADN Codec Validation Constants and Functions
"""

from .constants import (
    # Supported Operations - return value of check_format_function
    FMT_CHK,
    FMT_CVT,
    # Format Operations - return value of get_format_function
    FMT_NAME,
    FMT_CHECK,
    FMT_B2S,
    FMT_S2B,
    # Format Validation constants
    HOSTNAME_MAX_LENGTH,
    # Semantic validation function for type: String, Binary, Number
    FORMAT_CHECK_FUNCTIONS,
    FORMAT_CONVERT_BINARY_FUNCTIONS,
    FORMAT_CONVERT_MULTIPART_FUNCTIONS
)

from .convert import (
    s2b_hex,
    b2s_hex,
    s2b_base64url,
    b2s_base64url
)

from .general import (
    s_hostname,
    s_email,
    s_uri,
    check_format_function,
    get_format_function
)

from .network import (
    b_ip_addr,
    b_mac_addr,
    # Convert IP address string to binary
    s2b_ip_addr,
    s2b_ipv4_addr,
    s2b_ipv6_addr,
    # Convert IP address binary to string
    b2s_ip_addr,
    b2s_ipv4_addr,
    b2s_ipv6_addr,
    # Convert CIDR string to IP Net (v4 or v6)s2a_ip_net,
    s2a_ipv4_net,
    s2a_ipv6_net,
    # Convert IP Net (v4 or v6) to string in CIDR notation
    a2s_ip_net,
    a2s_ipv4_net,
    a2s_ipv6_net
)


__all__ = [
    # Constants
    # Supported Operations - return value of check_format_function
    'FMT_CHK',
    'FMT_CVT',
    # Format Operations - return value of get_format_function
    'FMT_NAME',
    'FMT_CHECK',
    'FMT_B2S',
    'FMT_S2B',
    # Format Validation constants
    'HOSTNAME_MAX_LENGTH',
    # Semantic validation function for type: String, Binary, Number
    'FORMAT_CHECK_FUNCTIONS',
    'FORMAT_CONVERT_BINARY_FUNCTIONS',
    'FORMAT_CONVERT_MULTIPART_FUNCTIONS',
    # Conversion
    's2b_hex',
    'b2s_hex',
    's2b_base64url',
    'b2s_base64url',
    # General
    's_hostname',
    's_email',
    's_uri',
    'check_format_function',
    'get_format_function',
    # Network
    'b_ip_addr',
    'b_mac_addr',
    # Convert IP address string to binary
    's2b_ip_addr',
    's2b_ipv4_addr',
    's2b_ipv6_addr',
    # Convert IP address binary to string
    'b2s_ip_addr',
    'b2s_ipv4_addr',
    'b2s_ipv6_addr',
    # Convert CIDR string to IP Net (v4 or v6)s2a_ip_net,
    's2a_ipv4_net',
    's2a_ipv6_net',
    # Convert IP Net (v4 or v6) to string in CIDR notation
    'a2s_ip_net',
    'a2s_ipv4_net',
    'a2s_ipv6_net'
]

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
