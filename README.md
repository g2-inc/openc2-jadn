#JSON Abstract Encoding Notation

# JAEN
JSON Abstract Encoding Notation (JAEN, pronounced "Jane") is a JSON document format for defining abstract schemas.
Unlike concrete schema languages such as XSD and JSON Schema, JAEN defines the structure of datatypes independently
of the serialization used to communicate and store data objects.  An encoder/decoder (codec) validates the structure
of data objects against the JAEN schema and serializes/deserializes objects using a specified message format.
## JAS
JAEN Abstract Syntax (or perhaps JAen Source -- JAS) is a source format used to create JAEN files.  Although a JAEN
schema is a human-readable JSON document and can be edited directly, JAS is simpler to read and write, eliminating
the boilerplate (quotes, braces, brackets) inherent to JSON.  A converter utility translates a schema bidirectionally
between JAS and JAEN formats.
### JAEN Python package
The JAEN package contains two subpackages:
- Codec -- Validate messages against JAEN schema, serialize and deserialize messages
  - codec.py - Message encoder and decoder.
  - codec_uitils.py - Utility routines used with the Codec class.
  - jaen.py - Jaen module used to load, validate, and save JAEN schemas.
- Convert -- Translate between JAEN, JAS, and property table files.
  - jas.ebnf - EBNF grammar for JAS files
  - jas_parse.py - JAS parser generated from EBNF by the Grako grammar compiler
  - tr_jas.py - load and save JAS files
  - tr_tables.py - generate property tables (xlsx workbook format) from JAEN schema
### Scripts
The JAEN package was created using the Test Driven Development process, where tests containing desired results
are developed first, then software is written to make the tests pass.  Test scripts serve to document both
example data (good and bad cases) and calling conventions for the software.
- test_codec.py - unittest file for encoder and decoder functions
- test_openc2.py - unittest file for OpenC2 commands
- jaen-convert.py - convert JAEN specifications between formats
   - openc2 - Schema that defines the OpenC2 message format
   - cybox - Target data model based on CybOX 2.1 (legacy)
   - observables - Target data model based on STIX Cyber Observables (under development)