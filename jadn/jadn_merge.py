"""
Merge a JSON Abstract Data Notation (JADN) module and its imported modules into a single file.
"""

from __future__ import print_function
import os

from libs.codec.jadn_defs import *
from libs.codec.jadn import jadn_load, jadn_dump, jadn_analyze, jadn_strip, jadn_merge


def merge(idir):
    def _merge_imports(info, files):
        base_schema = jadn_load(info['source'])
        for nsid, module in info['imports']:
            imp = [i for i in files.values() if i['module'] == module]
            patches = [i['patch'] for i in imp]
            print('  ', nsid, module, patches)
            if len(imp) > 1:
                raise ValueError('More than one matching import:', nsid, module, patches)
            elif len(imp) < 1:
                raise ValueError('Missing import:', nsid, module)
            else:
                imported_schema = jadn_load(imp[0]['source'])
                base_schema = jadn_merge(base_schema, imported_schema, nsid)
        joinchar = '.' if '+' in base_schema['meta']['patch'] else '+'
        base_schema['meta']['patch'] += joinchar + 'merged'
        del base_schema['meta']['imports']
        jadn_dump(base_schema, info['dest'])

    def _meta(schema, item):
        return schema['meta'][item] if item in schema['meta'] else ''

    cdir = os.path.dirname(os.path.realpath('__file__'))    # Current directory
    odir = os.path.normpath(os.path.join(cdir, '..', 'schema_out'))     # Put generated schemas outside of the repo
    print('Merging imported schemas from', os.path.realpath(idir), 'to', odir)
    files = {}
    for fn in (f[0] for f in (os.path.splitext(i) for i in os.listdir(idir)) if f[1] == '.jadn'):
        source = os.path.join(idir, fn) + '.jadn'
        dest = os.path.join(odir, fn) + '_merged.jadn'
        schema = jadn_load(source)
        id = _meta(schema, 'module') + '/' + _meta(schema, 'patch')
        if id in files:
            raise ValueError('Duplicate schema IDs:', id, source, files['id']['source'])
        else:
            files.update({id: {
                'source': source,
                'dest': dest,
                'id': id,
                'module': _meta(schema, 'module'),
                'patch': _meta(schema, 'patch'),
                'imports': _meta(schema, 'imports'),
                'exports': _meta(schema, 'exports'),
            }})

    for k, v in files.items():
        if v['imports']:
            print(k, 'imports', v['imports'])
            try:
                _merge_imports(v, files)
            except ValueError as e:
                print('  ##', v['source'], e.args)



if __name__ == '__main__':
    merge('schema')
