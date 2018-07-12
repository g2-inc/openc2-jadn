'''
Translate JSON Abstract Data Notation (JADN) files to other formats.

Creates text-based representations of a JADN syntax, including
  * Prettyprinted JADN
  * JADN Source (JAS)
  * Markdown tables
  * HTML tables, themed with CSS
  * Protobuf
  * Thrift

This script (jadn_translate) has no library dependencies other then jsonschema.
'''

from __future__ import print_function
import os

from libs.codec.jadn import jadn_load, jadn_dump, jadn_analyze
from libs.convert.w_jas import jas_dump
from libs.convert.w_base import base_dump


if __name__ == '__main__':
    cdir = os.path.dirname(os.path.realpath('__file__'))    # Current directory
    print(cdir)
    idir = os.path.join(cdir, 'schema')
    for fn in (f[0] for f in (os.path.splitext(i) for i in os.listdir(idir)) if f[1] == '.jadn'):
        print('**', fn)
        ifname = os.path.join(idir, fn)
        ofname = os.path.join(cdir, '..', '..', 'schema_out', fn)

        # Prettyprint JADN, and convert to other formats

        source = ifname + '.jadn'
        dest = ofname + '_gen'
        schema = jadn_load(source)
        sa = jadn_analyze(schema)

        version = ', ' + schema['meta']['version'] if 'version' in schema['meta'] else ''
        exports = ', '.join(schema['meta']['exports']) if 'exports' in schema['meta'] else ''
        sa.update({'module': schema['meta']['module'] + version, 'exports': exports})
        print('\n'.join(['  ' + k + ': ' + str(sa[k]) for k in ('module', 'exports', 'unreferenced', 'undefined', 'cycles')]))

        jadn_dump(schema, dest + '.jadn', source)
        jas_dump(schema, dest + '.jas', source)
        base_dump(schema, dest + '.md', source, form='markdown')
        base_dump(schema, dest + '.html', source, form='html')
