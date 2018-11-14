"""
Translate JSON Abstract Data Notation (JADN) files to other formats.

Creates text-based representations of a JADN syntax, including
  * Prettyprinted JADN
  * JADN Source (JAS)
  * Markdown tables
  * Protobuf
  * Thrift

This script (jadn-translate) has no library dependencies other then jsonschema.

The jadn-convert script parses text representations into JADN, and creates representations that require
addtional libraries such as xlsxwriter.
"""

from __future__ import print_function
import os

from libs.codec import jadn_load,  jadn_analyze
from libs.convert import base_dump, html_dump


if __name__ == "__main__":
    idir = 'schema'
    for fn in (f[0] for f in (os.path.splitext(i) for i in os.listdir(idir)) if f[1] == '.jadn'):
        print('**', fn)
        ifname = os.path.join(idir, fn)
        ofname = os.path.join("schema_gen_test", fn)

        # Prettyprint JADN, and convert to other formats

        source = ifname + ".jadn"
        dest = ofname + "_gen"
        schema = jadn_load(source)
        jadn_analyze(schema)
        # base_dump(schema, dest + "_orig.html", source, form='html')
        html_dump(schema, dest + "_new.html", source)
