import base64
import json
import os
import re
import sys

# Version Compatibility
encoding = sys.getdefaultencoding()
primitives = [
    bytes,
    str
]
defaultDecode_itr = [
    str,
    int,
    float
]

if sys.version_info.major >= 3:
    def toUnicode(s):
        return s.decode(encoding, 'backslashreplace') if hasattr(s, 'decode') else s

    def toStr(s):
        return toUnicode(s)

elif sys.version_info.major < 3:
    primitives.append(unicode)
    defaultDecode_itr.append(basestring)

    def toUnicode(s):
        return unicode(s)

    def toStr(s):
        return str(s)

_meta_order = ('title', 'module', 'description', 'imports', 'exports', 'patch')

_keys = {
    # Structures
    'structure': ('name', 'type', 'opts', 'desc', 'fields'),
    # Definitions
    'def': ('id', 'name', 'type', 'opts', 'desc'),
    'enum_def': ('id', 'value', 'desc'),
}


# Util Functions
def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default


def isBase64(sb):
    try:
        if type(sb) == str:
            # If there's any unicode here, an exception will be thrown and the function will return false
            sb_bytes = bytes(sb, 'ascii')
        elif type(sb) == bytes:
            sb_bytes = sb
        else:
            raise ValueError("Argument must be string or bytes")
        return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except Exception:
        return False


def jadn_format(jadn, indent=2):
    if not isinstance(jadn, dict):
        try:
            if os.path.isfile(jadn):
                with open(jadn, 'rb') as f:
                    jadn = json.load(f)
            else:
                jadn = json.loads(jadn)
        except Exception as e:
            print(e)
            raise TypeError("JADN improperly formatted")

    idn = ' ' * (indent if type(indent) is int else 2)

    meta_opts = []
    schema_meta = jadn.get("meta", {})
    for key in _meta_order:
        if key in schema_meta:
            val = schema_meta[key]
            if isinstance(val, list):
                obj = []

                for itm in val:
                    v = "[{}]".format(", ".join(f"\"{i}\"" for i in itm)) if isinstance(itm, list) else f"\"{itm}\""
                    obj.append(f"{idn * 3}{v}")

                v = ",\n".join(obj)
                meta_opts.append(f"{idn * 2}\"{key}\": [\n{v}\n{idn * 2}]")
            else:
                meta_opts.append(f"{idn * 2}\"{key}\": \"{val}\"")

    meta = ",\n".join(meta_opts)

    type_defs = []
    for itm in jadn.get("types", []):
        itm = dict(zip(_keys['structure'], itm))
        type_opts = ", ".join(f"\"{o}\"" for o in itm['opts'])
        header = f"\"{itm['name']}\", \"{itm['type']}\", [{type_opts}], \"{itm['desc']}\""
        fields = []

        i = 1
        for field in itm.get("fields", []):
            if itm['type'] == 'Enumerated':
                field = dict(zip(_keys['enum_def'], field))
                fields.append(f"[{safe_cast(field['id'], int, i)}, \"{field['value']}\", \"{field['desc']}\"]")
            else:
                field = dict(zip(_keys['def'], field))
                field_opts = ", ".join(f"\"{o}\"" for o in field['opts'])
                fields.append(f"[{safe_cast(field['id'], int, i)}, \"{field['name']}\", \"{field['type']}\", [{field_opts}], \"{field['desc']}\"]")

        if len(fields) >= 1:
            fields = f",\n{idn * 3}".join(fields)
            fields = f", [\n{idn * 3}{fields}\n{idn * 2}]"
        else:
            fields = ''

        type_defs.append(f"\n{idn * 2}[{header}{fields}]")

    types = ",".join(type_defs)
    return f"{{\n{idn}\"meta\": {{\n{meta}\n{idn}}},\n{idn}\"types\": [{types}\n{idn}]\n}}"


def default_encode(itm):
    tmp = type(itm)()
    if hasattr(tmp, '__iter__') and type(tmp) not in defaultDecode_itr:
        for k in itm:
            ks = toUnicode(k)
            if type(itm) is dict:
                tmp[ks] = default_encode(itm[k])
            elif type(itm) is list:
                tmp.append(default_encode(itm[k]))
            else:
                print('Not prepared type: {}-{}'.format(type(itm[k]), itm[k]))
    elif isinstance(itm, (int, float)):
        tmp = itm
    else:
        tmp = toUnicode(itm)
    return tmp


def default_decode(itm):
    tmp = type(itm)()
    if hasattr(tmp, '__iter__') and type(tmp) not in defaultDecode_itr:
        for k in itm:
            if type(tmp) == dict:
                tmp[default_encode(k)] = default_decode(itm[k])
            elif type(tmp) == list:
                tmp.append(default_decode(k))
            else:
                print('not prepared type: {}-{}'.format(type(tmp), tmp))
    elif isinstance(itm, (int, float)):
        tmp = itm
    else:
        tmp = toStr(itm)
    return tmp


# Util Classes
class FrozenDict(dict):
    def __init__(self, *args, **kwargs):
        self._hash = None
        super(FrozenDict, self).__init__(*args, **kwargs)

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self.items())))  # iteritems() on py2
        return self._hash

    def __getattr__(self, item):
        return self.get(item, None)

    def __getitem__(self, item):
        return self.get(item, None)

    def _immutable(self, *args, **kws):
        raise TypeError('cannot change object - object is immutable')

    __setitem__ = _immutable
    __delitem__ = _immutable
    pop = _immutable
    popitem = _immutable
    clear = _immutable
    update = _immutable
    setdefault = _immutable