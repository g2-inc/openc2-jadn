"""
JADN Network Related Validation Functions
"""
import ipaddress

from . import convert


# Convert Mac Address
def b2s_mac_addr(bval):
    """
    Convert binary MAC Address to string format
    :param bval: binary value of the MAC Address to convert
    :return: string representation of the MAC Address
    """
    if not isinstance(bval, (bytes, bytearray)):
        raise TypeError(f"MAC Address given is not expected {bytes}/{bytearray}, given {type(bval)}")
    # str - ':'.join(f"{b:02x}" for b in bval)
    return convert.b2s_base64url(bval)


def s2b_mac_addr(sval):
    """
    Convert string MAC Address to binary format
    :param sval: string value of the MAC Address to convert
    :return: binary representation of the MAC Address
    """
    if not isinstance(sval, str):
        raise TypeError(f"MAC Address given is not expected {str}, given {type(sval)}")
    # bytes - bytes.fromhex(re.sub(r"[:-]", "", sval))
    return convert.s2b_base64url(sval)


# Convert IP address
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


# Convert IP address
def _value_check_b2s(val):
    """
    Validate the value given is the proper type
    :param val: value to validate the type
    :raises: TypeError - Invalid type given
    """
    if isinstance(type(val), bytes):
        raise TypeError(f"IP Address given is not expected {bytes}, given {type(val)}")


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
        return [convert.b2s_base64url(s2b_ipv4_addr(addr[0])), v.prefixlen]
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
        return [convert.b2s_base64url(s2b_ipv6_addr(addr[0])), v.prefixlen]
    except Exception as e:
        raise e


# Convert IP Net (v4 or v6) CIDR notation
def _value_check_a2s(val):
    """
    Validate the value given is the proper type
    :param val: value to validate the type
    :raises: Value - Invalid size list given
    :raises: TypeError - Invalid type given
    """
    # print(val)
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
    return f'{b2s_ipv4_addr(convert.s2b_base64url(aval[0]))}/{aval[1]}'  # Convert Binary default string to type-specific string


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
    return f'{b2s_ipv6_addr(convert.s2b_base64url(aval[0]))}/{aval[1]}'  # Convert Binary default string to type-specific string
