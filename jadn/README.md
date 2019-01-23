## JADN
JSON Abstract Data Notation (JADN) is a language-neutral, platform-neutral,
and format-neutral mechanism for serializing structured data.  See [docs](docs/jadn-overview.md) for
information about the JADN language.

### Python package
The JADN package ([libs](jadn)) contains two subpackages:

- Codec -- Validate messages against JADN schema, serialize and deserialize messages
  	- codec.py - Message encoder and decoder
 	- codec_format.py - Validation routines usable with the 'format' option
  	- codec_utils.py - Utility routines used with the Codec class
  	- jadn-defs.py - Constant definitions for the JADN file format
  	- jadn.py - Load, validate, and save JADN schemas
- Convert -- Translate a JADN schema to other formats.
	- Message
		- TBD
	- Schema
		- CDDL - convert to and from
		- HTML - convert to
		- JAS - convert to and from
		- MarkDown - convert too and from
		- Relax-NG - convert to and from
		- Thrift - convert to and from

### Scripts
The JADN package was created using the Test Driven Development process, where tests containing desired results
are developed first, then software is written to make the tests pass.  Test scripts serve to document both
example data (good and bad cases) and calling conventions for the software.
- test_codec.py - Unit tests for encoder and decoder functions
- test_openc2.py - Unit tests for OpenC2 commands
- jadn-translate.py - Convert JADN schemas to other formats supported in the "convert" package

### Scripts
The JADN package was created using the Test Driven Development process, where tests containing desired results
are developed first, then software is written to make the tests pass.  Test scripts serve to document both
example data (good and bad cases) and calling conventions for the software.

- test_codec.py - Unit tests for encoder and decoder functions
- test_openc2.py - Unit tests for OpenC2 commands
- jadn-translate.py - Convert JADN schemas to other formats supported in the "convert" package

### Schemas
The jadn-translate utility reads `.jadn` schemas from an input directory (*"schema"*) and writes
converted files to an output directory (*"schema_gen"*).

- openc2-wd\<*nn*>.jadn - Schema that defines the OpenC2 message format as defined in the OpenC2
Language Specification, currently a work-in-progress document.  This schema is included
in the language specification and is used to generate the property tables in that spec.
- jadn.jadn - Schema for the JADN language
- *others* - Schemas for other data types such as those defined in OpenC2 actuator profiles