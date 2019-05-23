"""
Abstract Object Encoder/Decoder

Object schema is specified in JSON Abstract Data Notation (JADN) format.

Codec currently supports three JSON concrete message formats (verbose,
concise, and minified) but can be extended to support XML or binary formats.

Copyright 2016 David Kemp
Licensed under the Apache License, Version 2.0
http://www.apache.org/licenses/LICENSE-2.0
"""

from .constants import *

from .codec_format import get_format_function

from .codec_serialize import (
    enctab,
    encode,
    decode
)

from ..jadn_defs import (
    JADN_TYPES,
    # Type Indexes
    TypeName,
    BaseType,
    TypeOptions,
    Fields,
    # Field Indexes
    FieldName,
    FieldType,
    FieldOptions,
    FieldID
)

from ..jadn_utils import (
    topts_s2d,
    fopts_s2d
)

__version__ = '0.2'

# TODO: add DEFAULT
# TODO: use CHOICE with both explicit (attribute) and implicit (wildcard field) type


class Codec:
    """
    Serialize (encode) and De-serialize (decode) values based on JADN syntax.

    verbose_rec - True: Record types encoded as JSON objects
                 False: Record types encoded as JSON arrays
    verbose_str - True: Identifiers encoded as JSON strings
                 False: Identifiers encoded as JSON integers (tags)

    Encoding modes: rec,   str     Record Encoding
    --------------  -----  -----  -----------
        'Verbose'  = True,  True    Dict, Name
        'M2M'      = False, False   List, Tag
    unused concise = False, True    List, Name
         unused    = True,  False   Dict, Tag
    """

    def __init__(self, schema, verbose_rec=False, verbose_str=False):
        self.schema = schema
        assert set(enctab) == set(JADN_TYPES.PRIMITIVES + JADN_TYPES.STRUCTURES)
        self.max_array = 100        # Conservative default upper bounds that can be overridden
        self.max_string = 255       # Codec defaults (these) -> Schema defaults (bounds) -> Datatype options (max)
        self.max_binary = 1000

        self.arrays = None          # Array types generated when cardinality > 1.
        self.symtab = None          # Symbol table - pre-computed values for all datatypes
        self.types = None           # Index of defined types
        self.set_mode(verbose_rec, verbose_str)     # Create symbol table based on encoding mode

    def decode(self, datatype, sval):       # Decode serialized value into API value
        try:
            ts = self.symtab[datatype]
        except KeyError:
            raise ValueError(f"datatype \"{datatype}\" is not defined")
        return ts[S_CODEC][C_DEC](ts, sval, self)     # Dispatch to type-specific decoder

    def encode(self, datatype, aval):       # Encode API value into serialized value
        try:
            ts = self.symtab[datatype]
        except KeyError:
            raise ValueError(f"datatype \"{datatype}\" is not defined")
        return ts[S_CODEC][C_ENC](ts, aval, self)     # Dispatch to type-specific encoder

    def set_mode(self, verbose_rec=False, verbose_str=False):
        def _add_dtype(fs, newfs):          # Create datatype needed by a field
            dname = f"${len(self.arrays)}"
            self.arrays.update({dname: newfs})
            fs[S_FDEF] = fs[S_FDEF][:]      # Make a copy to modify
            fs[S_FDEF][FieldType] = dname       # Redirect field to dynamically generated type
            return dname

        def symf(fld):                      # Build symbol table field entries
            fs = [
                fld,                        # S_FDEF: JADN field definition
                fopts_s2d(fld[FieldOptions]),      # S_FOPT: Field options (dict)
                []                          # S_FNAMES: Possible field names returned from Choice type  TODO: not used
            ]
            opts = fs[S_FOPT]
            if fld[FieldType] == 'Enumerated' and 'vtype' in opts:      # Generate Enumerated from a referenced type
                rt = self.types[opts['vtype']]
                items = [[j[FieldID], j[FieldName], ''] for j in rt[Fields]]
                aa = ['', 'Enumerated', rt[TypeOptions], '', items]       # Dynamic type definition
                aas = sym(aa)
                aa[TypeName] = _add_dtype(fs, aas)                     # Add to list of dynamically generated types
            if 'maxc' in opts and opts['maxc'] != 1:                  # Create ArrayOf for fields with cardinality > 1
                amin = opts['minc'] if 'minc' in opts and opts['minc'] > 1 else 1      # Array cannot be empty
                amax = opts['maxc'] if opts['maxc'] > 0 else self.max_array           # Inherit max length if 0
                aa = ['', 'ArrayOf', [], '']                        # Dynamic JADN type definition
                aas = [                             # Symtab entry for dynamic type
                    aa,                             # 0: S_TDEF:  JADN type definition
                    enctab['ArrayOf'],              # 1: S_CODEC: Decoder, Encoder, Encoded type
                    list,                           # 2: S_STYPE: Encoded string type (str or tag)
                    get_format_function('', ''),    # 3: S_FORMAT: Functions that check value constraints
                    {'vtype': fs[S_FDEF][FieldType], 'minv': amin, 'maxv': amax}  # 4: S_TOPT:  Type Options (dict)
                ]
                aa[TypeName] = _add_dtype(fs, aas)                     # Add to list of dynamically generated types
            return fs

        def sym(t):                 # Build symbol table based on encoding modes
            symval = [
                t,                                  # 0: S_TDEF:  JADN type definition
                enctab[t[BaseType]],                # 1: S_CODEC: Decoder, Encoder, Encoded type
                type('') if verbose_str else int,   # 2: S_STYPE: Encoded string type (str or tag)
                [],                                 # 3: S_FORMAT: Functions that check value constraints
                topts_s2d(t[TypeOptions]),          # 4: S_TOPT:  Type Options (dict)
                verbose_str,                        # 5: S_VSTR:  Verbose String Identifiers
                {},                                 # 6: S_DMAP: Encoded field key or enum value to API
                {},                                 # 7: S_EMAP: API field key or enum value to Encoded
                {}                                  # 8: S_FLD: Symbol table field entry
            ]
            if t[BaseType] == 'Record':
                rtype = dict if verbose_rec else list
                symval[S_CODEC] = [decode.maprec, encode.maprec, rtype]
            fx = FieldName if verbose_str else FieldID
            if t[BaseType] in ['Enumerated', 'Choice', 'Map', 'Record']:
                fx, fa = (FieldID, FieldID) if 'id' in symval[S_TOPT] else (fx, FieldName)
                symval[S_DMAP] = {f[fx]: f[fa] for f in t[Fields]}
                symval[S_EMAP] = {f[fa]: f[fx] for f in t[Fields]}
                if t[BaseType] in ['Choice', 'Map', 'Record']:
                    symval[S_FLD] = {f[fx]: symf(f) for f in t[Fields]}
            elif t[BaseType] == 'Array':
                symval[S_FLD] = {f[FieldID]: symf(f) for f in t[Fields]}
            elif t[BaseType] == 'ArrayOf':
                opts = symval[S_TOPT]
                amin = opts['minv'] if 'minv' in opts else 1
                amax = opts['maxv'] if 'maxv' in opts and opts['maxv'] > 0 else self.max_array
                opts.update({'minv': amin, 'maxv': amax})
            fchk = symval[S_TOPT]['format'] if 'format' in symval[S_TOPT] else ''
            # fcvt = symval[S_TOPT]['sopt'] if 'sopt' in symval[S_TOPT] else ''
            symval[S_FORMAT] = get_format_function(fchk, t[BaseType], fchk)
            return symval
        # TODO: Add string and binary min and max

        self.arrays = {}
        self.types = {t[TypeName]: t for t in self.schema['types']}        # pre-index types to allow symtab forward refs
        self.symtab = {t[TypeName]: sym(t) for t in self.schema['types']}
        self.symtab.update(self.arrays)                                 # Add generated arrays to symbol table
        self.symtab.update({t: [['', t], enctab[t], enctab[t][C_ETYPE], get_format_function('', t), []] for t in JADN_TYPES.PRIMITIVES})
