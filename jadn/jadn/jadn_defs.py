"""
 JADN Definitions

A JSON Abstract Data Notation (JADN) file contains a list of datatype definitions.  Each type definition
has a specified format - a list of four or five columns depending on whether the type is primitive or
structure: (name, base type, type options, type description [, fields]).

For the enumerated type each field definition is a list of three items: (tag, name, description).

For other structure types (array, choice, map, record) each field definition is a list of five items:
(tag, name, type, field options, field description).
"""

from __future__ import unicode_literals

# JADN Datatype Definition columns
TNAME = 0       # Datatype name
TTYPE = 1       # Base type - built-in or defined
TOPTS = 2       # Type options
TDESC = 3       # Type description
FIELDS = 4      # List of fields

# JADN Field Definition columns
FTAG = 0        # Element ID
FNAME = 1       # Element name
EDESC = 2       # Enumerated value description
FTYPE = 2       # Datatype of field
FOPTS = 3       # Field options
FDESC = 4       # Field Description

# JADN built-in datatypes

PRIMITIVE_TYPES = (
    'Binary',
    'Boolean',
    'Integer',
    'Number',
    'Null',
    'String',
)

STRUCTURE_TYPES = (
    'Array',
    'ArrayOf',          # Special case: instance is a structure but type definition has no fields
    'Choice',
    'Enumerated',
    'Map',
    'Record',
)


def is_primitive(vtype):
    return vtype in PRIMITIVE_TYPES


def is_builtin(vtype):
    return vtype in PRIMITIVE_TYPES + STRUCTURE_TYPES


# Option Tags/Keys
#   JADN Type Options (TOPTS) and Field Options (FOPTS) contain a list of strings, each of which is an option.
#   The first character of an option string is the type ID; the remaining characters are the value.
#   The option string is converted into a Name: Value pair before use.
#   The tables list the unicode codepoint of the ID and the corresponding Name.

TYPE_OPTIONS = {        # ID, value type, description
    0x3d: 'compact',    # '=', boolean, Enumerated type and Choice/Map/Record keys are ID not Name
    0x2e: 'cvt',        # '.', string, String conversion and validation function for Binary derived types
    0x40: 'format',     # '@', string, name of validation function, e.g., date-time, email, ipaddr, ...
    0x5b: 'min',        # '[', integer, minimum string length, integer value, array length, property count
    0x5d: 'max',        # ']', integer, maximum string length, integer value, array length, property count
    0x2a: 'rtype',      # '*', string, Enumerated value from referenced type or ArrayOf element type
    0x24: 'pattern',    # '$', string, regular expression that a string type must match
}

FIELD_OPTIONS = {
    0x5b: 'min',        # '[', integer, minimum cardinality of field, default = 1, 0 = field is optional
    0x5d: 'max',        # ']', integer, maximum cardinality of field, default = 1, 0 = inherited max, not 1 = array
    0x26: 'atfield',    # '&', string, name of a field that specifies the type of this field
    0x2a: 'rtype',      # '*', string, Enumerated value from referenced type
    0x2f: 'etype',      # '/', string, serializer-specific encoding type, e.g., u8, s16, hex, base64
    0x21: 'default',    # '!', string, default value for this field (coerced to field type)
}

SUPPORTED_TYPE_OPTIONS = {
    'Binary': ['min', 'max', 'format', 'cvt'],
    'Boolean': [],
    'Integer': ['min', 'max', 'format'],
    'Number': ['min', 'max', 'format'],
    'Null': [],
    'String': ['min', 'max', 'pattern', 'format'],
    'Array': ['min', 'max', 'cvt'],
    'ArrayOf': ['min', 'max', 'rtype'],
    'Choice': ['compact'],
    'Enumerated': ['compact', 'rtype'],
    'Map': ['compact', 'min', 'max'],
    'Record': ['min', 'max'],
}

SUPPORTED_FIELD_OPTIONS = {
    'Binary': ['min', 'max'],
    'Boolean': ['min', 'max'],
    'Integer': ['min', 'max'],
    'Number': ['min', 'max'],
    'Null': [],
    'String': ['min', 'max', 'pattern', 'format'],
    'Array': ['min', 'max', 'etype', 'atfield'],
    'ArrayOf': ['min', 'max', 'rtype'],
    'Choice': ['min', 'max', 'etype'],
    'Enumerated': ['rtype'],
    'Map': ['min', 'max', 'etype'],
    'Record': ['min', 'max', 'etype', 'atfield'],
}

FORMAT_CHECK = {            # Semantic validation functions
    'email': 'String',      # email address, RFC 5322 Section 3.4.1
    'hostname': 'String',   # host name, RFC 1123 Section 2.1
    'ip-addr': 'Binary',    # length must be 4 octets (IPv4) or 16 octets (IPv6)
    'mac-addr': 'Binary',   # length must be 6 octets (EUI-48) or 8 octets (EUI-64)
    'uri': 'String',        # RFC 3986 Appendix A
}

FORMAT_CONVERT = {          # Binary-String and Array-String conversion functions
    'b': 'Binary',          # Base64url - RFC 4648 Section 5 (default)
    'x': 'Binary',          # Hex - RFC 4648 Section 8
    'ipv4-addr': 'Binary',  # IPv4 text representation - draft-main-ipaddr-text-rep-02 Section 3
    'ipv6-addr': 'Binary',  # IPv6 text representation - RFC 5952 Section 4
    'ipv4-net': 'Array',    # IPv4 Network Address CIDR string - RFC 4632 Section 3.1
    'ipv6-net': 'Array',    # IPv6 Network Address CIDR string - RFC 4291 Section 2.3
}
