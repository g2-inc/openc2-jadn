"""
Translate JADN to HTML or Markdown property tables
"""

from __future__ import unicode_literals
from ..codec.codec import is_builtin
from ..codec.jadn_defs import *
from ..codec.codec_utils import topts_s2d, fopts_s2d, cardinality
from datetime import datetime


def _fmt(s, f):
    f1 = {'n': '', 's': '', 'd': '', 'b': '**', 'h': '**_'}
    f2 = {'n': '', 's': '', 'd': '', 'b': '**', 'h': '_**'}
    ss = '\*' if s == '*' else s
    return f1[f] + ss + f2[f]

#--------- Markdown ouput -----------------


def doc_begin_m(title):
    text = '## Schema\n'
    return text


def doc_end_m():
    return ''


def sect_m(num, name):
    n = ''
    # n = '.'.join([str(n) for n in num]) + ' '
    # return '\n' + len(num)*'#' + ' ' + n + name + '\n'
    return ''


def meta_begin_m():
    return '| . | . |\n| ---: | :--- |\n'


def meta_item_m(h, val):
    if h == "exports":
        sval = ', '.join(val)
    elif h in ('imports', 'bounds'):
        sval = ' '.join(['**' + i[0] + '**:&nbsp;' + i[1] for i in val])
    else:
        sval = val
    return '| **' + h + ':** | ' + sval + ' |\n'


def meta_end_m():
    return ''


def type_begin_m(tname, ttype, topts, headers, cls):
    assert len(headers) == len(cls)
    ch = {'n': '---:', 'h': '---:', 's': ':---', 'd': ':---'}
    clh = [ch[c] if c in ch else '---' for c in cls]
    to = ' (' + ttype + topts + ')' if ttype else ''
    tc = '\n**_Type: ' + tname + to + '_**' if tname else ''
    return tc + '\n\n| ' + ' | '.join(headers) + ' |\n| ' + ' | '.join(clh) + ' |\n'


def type_item_m(row, cls):
    assert len(row) == len(cls)
    return '| ' + ' | '.join([_fmt(*r) for r in zip(row, cls)]) + ' |\n'


def type_end_m():
    return ''


# ---------- HTML output ------------------


def doc_begin_h(title):
    text = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
    text += '<link rel="stylesheet" type="text/css" href="theme.css">\n'
    text += '<title>' + title + '</title>\n</head>\n'
    text += '<body>\n<h2>Schema</h2>\n'
    return text


def doc_end_h():
    return '</body>\n'


def sect_h(num, name):
    hn = 'h' + str(len(num))
    n = ''
    # n = '.'.join([str(n) for n in num]) + ' '
    return '<' + hn + '>' + n + name + '</' + hn + '>\n'


def meta_begin_h():
    return '<table>\n'


def meta_item_h(h, val):
    if h == "exports":
        sval = ', '.join(val)
    elif h in ('imports', 'bounds'):
        sval = '<br>\n'.join(['<span class="b">' + i[0] + '</span>:&nbsp;' + i[1] for i in val])
    else:
        sval = val
    rc = [[h + ':', 'h'], [sval, 's']]
    return '<tr>' + ''.join(['<td class="' + c[1] + '">' + c[0] + '</td>' for c in rc]) + '</tr>\n'


def meta_imps_h(imports):
    return '<br>\n'.join([i[0] + ': ' + i[1] for i in imports])


def meta_end_h():
    return '</table>\n'


def type_begin_h(tname, ttype, topts, headers, cls):
    assert len(headers) == len(cls)
    to = ' (' + ttype + topts + ')' if ttype else ''
    tc = '<caption>' + tname + to + '</caption>' if tname else ''
    rc = zip(headers, cls)
    return '<table>' + tc + '<tr>' + ''.join(['<th class="' + c[1] + '">' + c[0] + '</th>' for c in rc]) + '</tr>\n'


def type_item_h(row, cls):
    assert len(row) == len(cls)
    rc = zip(row, cls)
    return '<tr>' + ''.join(['<td class="' + c[1] + '">' + c[0] + '</td>' for c in rc]) + '</tr>\n'


def type_end_h():
    return '</table>\n'


# ---------- JADN Source (JAS) output ------------------


def doc_begin_s(title):
    text = ''
    return text


def doc_end_s():
    return ''


def sect_s(num, name):
    return ''


def meta_begin_s():
    return ''


def meta_item_s(key, val):
    return ''


def meta_end_s():
    return ''


def type_begin_s(tname, ttype, topts, headers, cls):
    assert len(headers) == len(cls)
    return ''


def type_item_s(row, cls):
    assert len(row) == len(cls)
    return ''


def type_end_s():
    return ''


# ---------- JADN output ------------------


def doc_begin_d(title):
    text = ''
    return text


def doc_end_d():
    return ''


def sect_d(num, name):
    return ''


def meta_begin_d():
    return '{\n  "meta: {\n'


def meta_item_d(key, val):
    return '  "' + key + '": ' + val + '\n'


def meta_end_d():
    return '  }\n'


def type_begin_d(tname, ttype, topts, headers, cls):
    assert len(headers) == len(cls)
    return ''


def type_item_d(row, cls):
    assert len(row) == len(cls)
    return ''


def type_end_d():
    return ''


# ---------- CDDL output ------------------


def doc_begin_c(title):
    text = ''
    return text


def doc_end_c():
    return ''


def sect_c(num, name):
    return ''


def meta_begin_c():
    return ''


def meta_item_c(key, val):
    return ''


def meta_end_c():
    return ''


def type_begin_c(tname, ttype, topts, headers, cls):
    assert len(headers) == len(cls)
    return ''


def type_item_c(row, cls):
    assert len(row) == len(cls)
    return ''


def type_end_c():
    return ''


# ---------- Thrift output ------------------


def doc_begin_t(title):
    text = ''
    return text


def doc_end_t():
    return ''


def sect_t(num, name):
    return ''


def meta_begin_t():
    return ''


def meta_item_t(key, val):
    return ''


def meta_end_t():
    return ''


def type_begin_t(tname, ttype, topts, headers, cls):
    assert len(headers) == len(cls)
    return ''


def type_item_t(row, cls):
    assert len(row) == len(cls)
    return ''


def type_end_t():
    return ''


# ---------- JSON Schema output ------------------


def doc_begin_j(title):
    text = ''
    return text


def doc_end_j():
    return ''


def sect_j(num, name):
    return ''


def meta_begin_j():
    return ''


def meta_item_j(key, val):
    return ''


def meta_end_j():
    return ''


def type_begin_j(tname, ttype, topts, headers, cls):
    assert len(headers) == len(cls)
    return ''


def type_item_j(row, cls):
    assert len(row) == len(cls)
    return ''


def type_end_j():
    return ''


# ----------------------------------------------

"""
doc_begin - initial content
doc_end - closing content, if any
sect - section heading for human document formats, nothing for machine-readable schemas
meta_begin - begin meta content
meta_item - most meta items
meta_imps - special handling for imports meta item
meta_end - close meta content
type_begin - begin type definition
type_item - add field to type definition
type_end - close type definition
"""
# TODO: refactor into base and sub classes to support instance context

wtab = {
    'jas': (doc_begin_s, doc_end_s, sect_s, meta_begin_s, meta_item_s, meta_end_s, type_begin_s, type_item_s, type_end_s),
    'jadn': (doc_begin_d, doc_end_d, sect_d, meta_begin_d, meta_item_d, meta_end_d, type_begin_d, type_item_d, type_end_d),
    'cddl': (doc_begin_c, doc_end_c, sect_c, meta_begin_c, meta_item_c, meta_end_c, type_begin_c, type_item_c, type_end_c),
    'html': (doc_begin_h, doc_end_h, sect_h, meta_begin_h, meta_item_h, meta_end_h, type_begin_h, type_item_h, type_end_h),
    'thrift': (doc_begin_t, doc_end_t, sect_t, meta_begin_t, meta_item_t, meta_end_t, type_begin_t, type_item_t, type_end_t),
    'markdown': (doc_begin_m, doc_end_m, sect_m, meta_begin_m, meta_item_m, meta_end_m, type_begin_m, type_item_m, type_end_m),
    'jsonschema': (doc_begin_j, doc_end_j, sect_j, meta_begin_j, meta_item_j, meta_end_j, type_begin_j, type_item_j, type_end_j)
}

DEFAULT_FORMAT = 'html'


def table_dumps(jadn, form=DEFAULT_FORMAT):
    """
    Translate JADN schema into other formats

    Column classes for presentation formats:
    n - number (right aligned)
    h - meta header (bold, right aligned)
    s - string (left aligned)
    b - bold (bold, left aligned)
    d - description (left aligned, extra width)
    """

    def _tbegin(to, td, head, cls):
        tor = set(to)
        id = ''
        h = head
        c = cls
        if 'compact' in to:
            tor -= {'compact', }
            id = '.ID'
            h = [head[0]] + head[2:]
            c = [cls[0]] + cls[2:]
        tos = ' ' + str([str(k) for k in tor]) if tor else ''
        return type_begin(td[TNAME], td[TTYPE] + id, tos, h, c)

    def _titem(to, fitems, cls):
        f = fitems
        c = cls
        if 'compact' in to:
            f = [fitems[0]] + fitems[2:]
            f[-1] = (fitems[1] + ' -- ' if fitems[1] else '') + f[-1]
            c = [cls[0]] + cls[2:]
        return type_item(f, c)

    doc_begin, doc_end, sect, meta_begin, meta_item, meta_end, type_begin, type_item, type_end = wtab[form]
    meta = jadn['meta']
    title = meta['module'] + (' v.' + meta['patch']) if 'patch' in meta else ''
    text = doc_begin(title)
    text += meta_begin()
    meta_list = ('title', 'module', 'patch', 'description', 'exports', 'imports', 'bounds')
    bn = ('max_msg', 'max_str', 'max_bin', 'max_fields')
    for h in meta_list + tuple(set(meta) - set(meta_list)):
        if h in meta:
            mh = zip(bn, meta[h]) if h == 'bounds' else meta[h]
            text += meta_item(h, mh)
    text += meta_end()

    for td in jadn['types']:
        to = topts_s2d(td[TOPTS])
        tor = set(to) - {'min', 'max'}
        tos = ' ' + str([str(k) for k in tor]) if tor else ''
        rng = ''
        if 'min' in to or 'max' in to:
            lo = to['min'] if 'min' in to else 0
            hi = to['max'] if 'max' in to else 0
            rng = ' [' + str(lo) + '..' + (str(hi) if hi else 'n') + ']'
        if td[TTYPE] in PRIMITIVE_TYPES or not is_builtin(td[TTYPE]):
            cls = ['s', 's', 'd']
            text += type_begin(td[TNAME], None, tos, ['Type Name', 'Base Type', 'Description'], cls)
            fmt = ' (' + to['format'] + ')' if 'format' in to else ''
            cvt = ''                # Binary-string conversion method:
            if 'cvt' in to:         # base64url (default), hex (.x), or type-specific (.s:)
                cvt = to['cvt']
                if cvt not in ('x'):
                    cvt = 's:' + cvt
                cvt = '.' + cvt
            text += type_item([td[TNAME], td[TTYPE] + cvt + rng + fmt, td[TDESC]], cls)
        elif td[TTYPE] == 'ArrayOf':            # In STRUCTURE_TYPES but with no field definitions
            cls = ['s', 's', 'd']
            rtype = '(' + to['rtype'] + ')'
            tor = set(to) - {'rtype', 'min', 'max'}
            tos = ' ' + str([str(k) for k in tor]) if tor else ''
            text += type_begin(td[TNAME], None, tos, ['Type Name', 'Base Type', 'Description'], cls)
            text += type_item([td[TNAME], td[TTYPE] + rtype + rng, td[TDESC]], cls)
        elif td[TTYPE] == 'Enumerated':
            if 'rtype' in to:
                rtype = '.*' + to['rtype']
                tor = set(to) - {'rtype'}
                tos = ' ' + str([str(k) for k in tor]) if tor else ''
                text += type_begin(td[TNAME], td[TTYPE] + rtype, tos, [], [])
            else:
                cls = ['n', 'b', 'd']
                text += _tbegin(to, td, ['ID', 'Name', 'Description'], cls)
                for fd in td[FIELDS]:
                    text += _titem(to, [str(fd[FTAG]), fd[FNAME], fd[EDESC]], cls)
        else:                                   # Array, Choice, Map, Record
            cls = ['n', 'b', 's', 'n', 'd']
            if td[TTYPE] == 'Array':
                cls2 = ['n', 's', 'n', 'd']      # Don't print ".ID" in type name but display fields as compact
                text += _tbegin(to, td, ['ID', 'Type', '#', 'Description'], cls2)
                to.update({'compact': True})
            else:
                text += _tbegin(to, td, ['ID', 'Name', 'Type', '#', 'Description'], cls)
            for fd in td[FIELDS]:
                fo = {'min': 1, 'max': 1}
                fo.update(fopts_s2d(fd[FOPTS]))
                rtype = '.*' if 'rtype' in fo else ''
                text += _titem(to, [str(fd[FTAG]), fd[FNAME], fd[FTYPE] + rtype, cardinality(fo['min'], fo['max']), fd[FDESC]], cls)
        text += type_end()

    text += doc_end()
    return text


def table_dump(jadn, fname, source='', form=DEFAULT_FORMAT):
    with open(fname, 'w') as f:
        if source:
            f.write('<!-- Generated from ' + source + ', ' + datetime.ctime(datetime.now()) + '-->\n')
        f.write(table_dumps(jadn, form))
