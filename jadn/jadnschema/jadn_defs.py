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

import json

from . import utils

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

META_ORDER = ('title', 'module', 'description', 'imports', 'exports', 'patch')

# TODO: Convert to use COLUMN_KEY instead of above key/index
COLUMN_KEYS = utils.FrozenDict(
    # Structures
    Structure=(
        'name',     # 0 - TNAME - Datatype name
        'type',     # 1 - TTYPE - Base type - built-in or defined
        'opts',     # 2 - TOPTS - Type options
        'desc',     # 3 - TDESC - Type description
        'fields'    # 4 - FIELDS - List of fields
    ),
    # Field Definitions
    Enum_Def=(
        'id',       # 0 - FTAG - Element ID
        'value',    # 1 - FNAME - Element name
        'desc'      # 2 - EDESC - Enumerated value description
    ),
    Gen_Def=(
        'id',       # 0 - FTAG - Element ID
        'name',     # 1 - FNAME - Element name
        'type',     # 2 - FTYPE - Datatype of field
        'opts',     # 3 - FOPTS - Field options
        'desc'      # 4 - FDESC - Field Description
    )
)

# JADN built-in datatypes
JADN_TYPES = utils.FrozenDict(
    PRIMITIVES=(
        'Binary',
        'Boolean',
        'Integer',
        'Number',
        'Null',
        'String'
    ),
    STRUCTURES=(
        'Array',
        'ArrayOf',      # Special case: instance is a structure but type definition has no fields
        'Choice',
        'Enumerated',
        'Map',
        'MapOf',        # (key type, value type)
        'Record'
    )
)


def is_builtin(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin type
    :param vtype: Type
    :return: is builtin type
    """
    return vtype in JADN_TYPES.PRIMITIVES + JADN_TYPES.STRUCTURES


def is_primitive(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin primitive
    :param vtype: Type
    :return: is builtin primitive
    """
    return vtype in JADN_TYPES.PRIMITIVES


def is_structure(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin structure
    :param vtype: Type
    :return: is builtin structure
    """
    return vtype in JADN_TYPES.STRUCTURES


def is_compound(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin compound (has defined fields)
    :param vtype: Type
    :return: is builtin compound
    """
    return vtype in ('Array', 'Choice', 'Map', 'Record')


def column_index(col_type: str, col_name: str) -> int:
    """
    Get the index of hte column given the type and column name
    :param col_type: type of builtin - (Structure, Gen_Def, Enum_Def)
    :param col_name: name of column
    :return: index number of the column
    """
    if col_type not in COLUMN_KEYS:
        raise KeyError(f"{col_type} is not a valid column type")

    columns = COLUMN_KEYS[col_type]
    if col_name not in columns:
        raise KeyError(f"{col_name} is not a valid column for {col_type}")

    return columns.index(col_name)


# Option Tags/Keys
#   JADN Type Options (TOPTS) and Field Options (FOPTS) contain a list of strings, each of which is an option.
#   The first character of an option string is the type ID; the remaining characters are the value.
#   The option string is converted into a Name: Value pair before use.
#   The tables list the unicode codepoint of the ID and the corresponding Name.

# Type Config
TYPE_CONFIG = dict(
    OPTIONS={               # ID, value type, description
        0x3d: 'compact',    # '=', boolean, Enumerated type and Choice/Map/Record keys are ID not Name
        0x2e: 'cvt',        # '.', string, String conversion and validation function for Binary derived types
        0x40: 'format',     # '@', string, name of validation function, e.g., date-time, email, ipaddr, ...
        0x5b: 'min',        # '[', integer, minimum string length, integer value, array length, property count
        0x5d: 'max',        # ']', integer, maximum string length, integer value, array length, property count
        0x2a: 'rtype',      # '*', string, Enumerated value from referenced type or ArrayOf element type
        0x2b: 'ktype',      # '+', string, Key type for MapOf
        0x24: 'pattern',    # '$', string, regular expression that a string type must match
    },
    SUPPORTED_OPTIONS=dict(
        # Primitives
        Binary=('min', 'max', 'format', 'cvt'),
        Boolean=(),
        Integer=('min', 'max', 'format'),
        Number=('min', 'max', 'format'),
        Null=(),
        String=('min', 'max', 'pattern', 'format'),
        # Structures
        Array=('min', 'max', 'cvt'),
        ArrayOf=('min', 'max', 'rtype'),
        Choice=('compact',),
        Enumerated=('compact', 'rtype'),
        Map=('compact', 'min', 'max'),
        MapOf=('min', 'max', 'ktype', 'rtype'),
        Record=('min', 'max'),
    ),
    S2D=dict(  # Option Conversions - String -> Dict
        compact=lambda x: True,
        cvt=lambda x: x,
        format=lambda x: x,
        min=lambda x: utils.safe_cast(x, int, 1),
        max=lambda x: utils.safe_cast(x, int, 1),
        ktype=lambda x: x,
        pattern=lambda x: x,
        rtype=lambda x: x,
    )
)

TYPE_CONFIG['OPTIONS_INVERT'] = utils.FrozenDict(map(reversed, TYPE_CONFIG['OPTIONS'].items()))
TYPE_CONFIG['D2S'] = dict(
    compact=lambda x: chr(TYPE_CONFIG['OPTIONS_INVERT'].compact),
    cvt=lambda x: f"{chr(TYPE_CONFIG['OPTIONS_INVERT'].cvt)}{x}",
    format=lambda x: f"{chr(TYPE_CONFIG['OPTIONS_INVERT'].format)}{x}",
    min=lambda x: f"{chr(TYPE_CONFIG['OPTIONS_INVERT'].min)}{utils.safe_cast(x, int, 1)}",
    max=lambda x: f"{chr(TYPE_CONFIG['OPTIONS_INVERT'].max)}{utils.safe_cast(x, int, 1)}",
    ktype=lambda x: f"{chr(TYPE_CONFIG['OPTIONS_INVERT'].ktype)}{x}",
    rtype=lambda x: f"{chr(TYPE_CONFIG['OPTIONS_INVERT'].rtype)}{x}",
    pattern=lambda x: f"{chr(TYPE_CONFIG['OPTIONS_INVERT'].pattern)}{x}",
)
TYPE_CONFIG = utils.toFrozen(TYPE_CONFIG)

# Field Config
FIELD_CONFIG = dict(
    OPTIONS={               # ID, value type, description
        0x5b: 'min',        # '[', integer, minimum cardinality of field, default = 1, 0 = field is optional
        0x5d: 'max',        # ']', integer, maximum cardinality of field, default = 1, 0 = inherited max, not 1 = array
        0x25: 'enum',       # '%', boolean, enumeration derived from field type
        0x26: 'atfield',    # '&', string, name of a field that specifies the type of this field
        0x2a: 'rtype',      # '*', string, Enumerated value from referenced type
        0x2f: 'etype',      # '/', string, serializer-specific encoding type, e.g., u8, s16, hex, base64
        0x21: 'default',    # '!', string, default value for this field (coerced to field type)
    },
    SUPPORTED_OPTIONS=dict(
        # Primitives
        Binary=('min', 'max'),
        Boolean=('min', 'max'),
        Integer=('min', 'max'),
        Number=('min', 'max'),
        Null=(),
        String=('min', 'max', 'pattern', 'format'),
        # Structures
        Array=('min', 'max', 'etype', 'atfield'),
        ArrayOf=('min', 'max', 'rtype'),
        Choice=('min', 'max', 'etype'),
        Enumerated=('rtype',),
        Map=('min', 'max', 'etype'),
        Record=('min', 'max', 'etype', 'atfield'),
    ),
    S2D=dict(  # Option Conversions - String -> Dict
        atfield=lambda x: x,
        default=lambda x: x,
        enum=lambda x: True,
        etype=lambda x: x,
        min=lambda x: utils.safe_cast(x, int, 1),
        max=lambda x: utils.safe_cast(x, int, 1),
        rtype=lambda x: x,
    )
)
FIELD_CONFIG['OPTIONS_INVERT'] = utils.FrozenDict(map(reversed, FIELD_CONFIG['OPTIONS'].items()))
FIELD_CONFIG['D2S'] = dict(
    atfield=lambda x: f"{chr(FIELD_CONFIG['OPTIONS_INVERT'].atfield)}{x}",
    default=lambda x: f"{chr(FIELD_CONFIG['OPTIONS_INVERT'].default)}{x}",
    enum=lambda x: chr(FIELD_CONFIG['OPTIONS_INVERT'].enum),
    etype=lambda x: f"{chr(FIELD_CONFIG['OPTIONS_INVERT'].etype)}{x}",
    min=lambda x: f"{chr(FIELD_CONFIG['OPTIONS_INVERT'].min)}{utils.safe_cast(x, int, 1)}",
    max=lambda x: f"{chr(FIELD_CONFIG['OPTIONS_INVERT'].max)}{utils.safe_cast(x, int, 1)}",
    rtype=lambda x: f"{chr(FIELD_CONFIG['OPTIONS_INVERT'].rtype)}{x}"

)
FIELD_CONFIG = utils.toFrozen(FIELD_CONFIG)

OPTION_ID = {**TYPE_CONFIG['OPTIONS_INVERT']}
OPTION_ID.update(FIELD_CONFIG['OPTIONS_INVERT'])
OPTION_ID = utils.toFrozen(OPTION_ID)


FORMAT = utils.FrozenDict(
    CHECK=utils.FrozenDict({    # Semantic validation functions
        'email': 'String',      # email address, RFC 5322 Section 3.4.1
        'hostname': 'String',   # host name, RFC 1123 Section 2.1
        'ipv4-addr': 'Binary',  # IPv4 address as specified in RFC 791 Section 3.1
        'ipv6-addr': 'Binary',  # IPv6 address as specified in RFC 8200 Section 3
        'mac-addr': 'Binary',   # length must be 6 octets (EUI-48) or 8 octets (EUI-64)
        'ipv4-net': 'Array',    # Binary IPv4 address and Integer prefix length, RFC 4632 Section 3.1
        'ipv6-net': 'Array',    # Binary IPv6 address and Integer prefix length, RFC 4291 Section 2.3
        'uri': 'String',        # RFC 3986 Appendix A
    }),
    SERIALIZE=utils.FrozenDict(),
    CONVERT=utils.FrozenDict({  # Binary-String and Array-String conversion functions
        'b': 'Binary',          # Base64url - RFC 4648 Section 5 (default)
        'x': 'Binary',          # Hex - RFC 4648 Section 8
        'ipv4-addr': 'Binary',  # IPv4 "dotted-quad" text representation, RFC 2673 Section 3.2
        'ipv6-addr': 'Binary',  # IPv6 text representation, RFC 4291 Section 2.2
        'ipv4-net': 'Array',    # IPv4 Network Address CIDR string, RFC 4632 Section 3.1
        'ipv6-net': 'Array',    # IPv6 Network Address CIDR string, RFC 4291 Section 2.3
    })
)
