import base64
import json
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


def jadn_format(jadn, indent=1):
    if type(jadn) is not dict:
        try:
            jadn = json.load(jadn)
        except Exception as e:
            print(e)
            raise TypeError("JADN improperly formatted")

    idn = ' ' * (indent if type(indent) is int else 2)

    meta_opts = []
    if 'meta' in jadn:
        for key, val in jadn['meta'].items():
            if type(val) is list:
                obj = []

                for itm in val:
                    obj.append('{idn}[\"{val}\"]'.format(
                        idn=idn * 3,
                        val='\", \"'.join(itm) if type(itm) is list else itm
                    ))

                meta_opts.append('{idn}\"{key}\": [\n{val}\n{idn}]'.format(
                    idn=idn * 2,
                    key=key,
                    val=',\n'.join(obj)
                ))
            else:
                meta_opts.append('{idn}\"{key}\": \"{val}\"'.format(
                    idn=idn * 2,
                    key=key,
                    val=val
                ))

    meta = "{idn}\"meta\": {{\n{obj}\n{idn}}}".format(idn=idn, obj=',\n'.join(meta_opts))

    type_defs = []
    if 'types' in jadn:
        for itm in jadn['types']:
            # print(itm)
            header = []
            for h in itm[0: -1]:
                if type(h) is list:
                    header.append("[{obj}]".format(obj=', '.join(['\"{}\"'.format(i) for i in h])))
                else:
                    header.append('\"{}\"'.format(h))
            defs = []

            if type(itm[-1]) is list:
                for def_itm in itm[-1]:
                    defs.append('{itm}'.format(itm=json.dumps(def_itm) if type(def_itm) is list else def_itm))
            else:
                defs.append("\"{itm}\"".format(itm=itm[-1]))

            defs = ',\n'.join(defs)  # .replace('\'', '\"')

            if re.match(r'^\s*?\[', defs):
                defs = "[\n{defs}\n{idn}{idn}]".format(idn=idn, defs=re.sub(re.compile(r'^', re.MULTILINE), '{idn}'.format(idn=idn*3), defs))

            type_defs.append("\n{idn}{idn}[{header}{defs}]".format(
                idn=idn,
                header=', '.join(header),
                defs='' if defs == '' else ', {}'.format(defs)
            ))

    types = "[{obj}\n{idn}]".format(idn=idn, obj=','.join(type_defs))

    return "{{\n{meta},\n{idn}\"types\": {types}\n}}".format(idn=idn, meta=meta, types=types)


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


class Utils(object):
    @staticmethod
    def defaultEncode(itm):
        tmp = type(itm)()
        if hasattr(tmp, '__iter__') and type(tmp) not in defaultDecode_itr:
            for k in itm:
                ks = toUnicode(k)
                if type(itm) is dict:
                    tmp[ks] = Utils.defaultEncode(itm[k])

                elif type(itm) is list:
                    tmp.append(Utils.defaultEncode(itm[k]))

                else:
                    print('Not prepared type: {}-{}'.format(type(itm[k]), itm[k]))
        elif isinstance(itm, (int, float)):
            tmp = itm
        else:
            tmp = toUnicode(itm)

        return tmp

    @staticmethod
    def defaultDecode(itm):
        tmp = type(itm)()

        if hasattr(tmp, '__iter__') and type(tmp) not in defaultDecode_itr:
            for k in itm:
                if type(tmp) == dict:
                    tmp[Utils.defaultDecode(k)] = Utils.defaultDecode(itm[k])

                elif type(tmp) == list:
                    tmp.append(Utils.defaultDecode(k))

                else:
                    print('not prepared type: {}-{}'.format(type(tmp), tmp))
        elif isinstance(itm, (int, float)):
            tmp = itm
        else:
            tmp = toStr(itm)

        return tmp

