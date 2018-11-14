"""
Translate JSON Abstract Data Notation (JADN) files to other formats.

Creates text-based representations of a JADN syntax, including
  * Prettyprinted JADN
  * JADN Source (JAS)
  * Markdown tables
  * HTML tables, themed with CSS
  * Protobuf
  * Thrift

This script (jadn_translate) has no library dependencies other then jsonschema.
"""

from __future__ import print_function
import os

from libs.codec.jadn import jadn_load, jadn_dump, jadn_analyze, jadn_strip
from libs.convert.w_jas import jas_dump
from libs.convert.w_table import table_dump


if __name__ == '__main__':
    cdir = os.path.dirname(os.path.realpath('__file__'))    # Current directory
    idir = 'schema'
    odir = os.path.normpath(os.path.join(cdir, '..', 'schema_out'))     # Put generated schemas outside of the repo
    print('Translating schemas from', os.path.realpath(idir), 'to', odir)
    for fn in (f[0] for f in (os.path.splitext(i) for i in os.listdir(idir)) if f[1] == '.jadn'):
        print('**', fn)
        source = os.path.join(idir, fn) + '.jadn'
        dest = os.path.join(odir, fn) + '_gen'

        # Prettyprint JADN, strip comments, and convert to other formats

        schema = jadn_load(source)
        sa = jadn_analyze(schema)

        patch = ', ' + schema['meta']['patch'] if 'patch' in schema['meta'] else ''
        exports = ', '.join(schema['meta']['exports']) if 'exports' in schema['meta'] else ''
        sa.update({'module': schema['meta']['module'] + patch, 'exports': exports})
        print('\n'.join(['  ' + k + ': ' + str(sa[k]) for k in ('module', 'exports', 'unreferenced', 'undefined', 'cycles')]))

        jadn_dump(jadn_strip(schema), dest + '_strip.jadn', strip=True)
        jadn_dump(schema, dest + '.jadn')
        jas_dump(schema, dest + '.jas')
        table_dump(schema, dest + '.md', source, form='markdown')
        table_dump(schema, dest + '.html', source, form='html')
