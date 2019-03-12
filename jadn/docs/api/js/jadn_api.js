const jadn_api = {
  "jadn" : {
    "title" : "JADN Base",
    "text" : [
      "Base JADN functions and objects"
    ],
    "body" : {
      "enum" : {
        "CommentLevels" : {
          "enum" : [
            {
              "name" : "ALL",
              "info" : {
                "info" : [
                  "Show all comment for conversion"
                ]
              }
            },
            {
              "name" : "NONE",
              "info" : {
                "info" : [
                  "Show no comment for conversion"
                ]
              }
            }
          ]
        }
      },
      "function" : {
        "jadn_analyze(...)" : {
          "return" : {
            "type" : "SET ME",
            "info" : [
              "SET ME"
            ]
          },
          "fun_desc" : [
            "SET ME"
          ]
        },
        "jadn_check(schema)" : {
          "return" : {
            "type" : "dict",
            "info" : [
              "JADN formatted dictionary"
            ]
          },
          "fun_desc" : [
            "Validate JADN structure against JSON schema",
            "Validate JADN structure against JADN schema",
            "Perform additional checks on type definitions"
          ]
        },
        "jadn_dump(schema, fname, source, strip)" : {
          "return" : {
            "type" : "void"
          },
          "fun_desc" : [
            "Convert a JADN schema to a JADN formatted string",
            "Write string to the given file"
          ]
        },
        "jadn_dumps(schema, level, indent, strip, nlevel)" : {
          "return" : {
            "type" : "str",
            "info" : [
              "JADN string"
            ]
          },
          "fun_desc" : [
            "Convert a JADN schema to a JADN formatted string"
          ]
        },
        "jadn_format(schema)" : {
          "return" : {
            "type" : "str",
            "info" : [
              "JADN formatted string"
            ]
          },
          "fun_desc" : [
            "Convert a JADN schema to a JADN formatted string"
          ]
        },
        "jadn_load(fname)" : {
          "return" : {
            "type" : "dict",
            "info" : [
              "JADN formatted dictionary"
            ]
          },
          "fun_desc" : [
            "Load and check a jadn schema from a JADN file"
          ]
        },
        "jadn_loads(jadn_str)" : {
          "return" : {
            "type" : "dict",
            "info" : [
              "JADN formatted dictionary"
            ]
          },
          "fun_desc" : [
            "Load and check a jadn schema from a JADN string"
          ]
        },
        "jadn_merge(base, imp, nsid)" : {
          "return" : {
            "type" : "dict",
            "info" : [
              "JADN formatted dictionary"
            ]
          },
          "fun_desc" : [
            "Merge an imported schema into a base schema"
          ]
        },
        "jadn_strip(schema)" : {
          "return" : {
            "type" : "dict",
            "info" : [
              "JADN formatted dictionary"
            ]
          },
          "fun_desc" : [
            "Strip comments from schema"
          ]
        }
      }
    }
  },
  "jadn.codec" : {
    "title" : "Validate messages against JADN schema, serialize and deserialize messages",
    "text" : [
      "codec.py - Message encoder and decoder",
      "codec_format.py - Validation routines usable with the \"format\" option",
      "codec_utils.py - Utility routines used with the Codec class",
      "jadn-defs.py - Constant definitions for the JADN file format",
      "jadn.py - Load, validate, and save JADN schemas"
    ],
    "body" : {
      "class" : [
        {
          "header" : "Codec",
          "title" : "Serialize (encode) and De-serialize (decode) values based on JADN syntax.",
          "constructor" : {
            "def" : "Codec(schema, verbose_rec, verbose_str)",
            "info" : [
              "SET ME"
            ]
          },
          "function" : [
            {
              "return" : {
                "type" : "SET ME",
                "info" : [
                  "SET ME"
                ]
              },
              "fun_desc" : {
                "def" : "decode(self, datatype, sval)",
                "info" : [
                  "Decode serialized value into API value"
                ]
              }
            },
            {
              "return" : {
                "type" : "SET ME",
                "info" : [
                  "SET ME"
                ]
              },
              "fun_desc" : {
                "def" : "encode(self, datatype, aval)",
                "info" : [
                  "Encode API value into serialized value"
                ]
              }
            },
            {
              "return" : {
                "type" : "SET ME",
                "info" : [
                  "SET ME"
                ]
              },
              "fun_desc" : {
                "def" : "set_mode(verbose_rec, verbose_str)",
                "info" : [
                  "Encode API value into serialized value"
                ]
              }
            }
          ]
        }
      ]
    }
  },
  "jadn.convert" : {
    "title" : "JADN conversion related functions",
    "text" : [
      "Conversion classes, enums, and functions"
    ],
    "body" : {
      "package" : {
        "jadn.convert.message" : {
          "title" : "JADN Message related classes, enums, and functions",
          "body" : {}
        },
        "jadn.convert.schema" : {
          "title" : "JADN Schema related classes, enums, and functions",
          "body" : {
            "function" : {
              "cddl_dump(jadn, fname, source, comm)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Produce CDDL schema from JADN schema and write to file provided",
                  "jadn - JADN Schema to convert",
                  "fname - Name of file to write",
                  "source - Name of the original JADN schema file",
                  "comm - Comment level as defined by jadn.CommentLevel"
                ]
              },
              "cddl_dumps(jadn, comm)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "CDDL string"
                  ]
                },
                "fun_desc" : [
                  "Produce CDDL schema from JADN schema",
                  "jadn - JADN Schema to convert",
                  "comm - Comment level as defined by jadn.CommentLevel"
                ]
              },
              "cddl_load(cddl, fname, source)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given CDDL to JADN and write output to the specified file",
                  "cddl - CDDL schema to convert",
                  "fname - Name of file to write",
                  ""
                ]
              },
              "cddl_loads(cddl)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "JADN schema"
                  ]
                },
                "fun_desc" : [
                  "Produce JADN schema from CDDL schema"
                ]
              },
              "html_dump(jadn, fname, source, styles)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given JADN to HTML and write output to the specified file",
                  "jadn - JADN formatted string, dictionary, file location",
                  "fname - File location to write output",
                  "source - Name of file being converted (optional)",
                  "styles - file location of styles to use for HTML/PDF conversion (optional)"
                ]
              },
              "html_dumps(jadn, styles)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "HTML string"
                  ]
                },
                "fun_desc" : [
                  "Convert the given JADN to HTML",
                  "jadn - JADN formatted string, dictionary, file location",
                  "styles - file location of styles to use for HTML/PDF conversion (optional)"
                ]
              },
              "json_dump(jadn, fname, source, comm)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given JADN to JSON Schema and write output to the specified file",
                  "jadn - JADN formatted string, dictionary, file location",
                  "fname - File location to write output",
                  "source - Name of file being converted (optional)",
                  "comm - Comment level as defined by jadn.CommentLevel"
                ]
              },
              "json_dumps(jadn, comm)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "JAS string"
                  ]
                },
                "fun_desc" : [
                  "Convert the given JADN to JSON Schema",
                  "jadn - JADN formatted string, dictionary, file location",
                  "comm - Comment level as defined by jadn.CommentLevel"
                ]
              },
              "json_load(jas, fname, source)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given JSON Schema to JADN and write output to the specified file"
                ]
              },
              "jas_loads(jas)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "JADN string"
                  ]
                },
                "fun_desc" : [
                  "Convert the given JAS to JADN"
                ]
              },
              "jas_dump(json, fname, source, comm)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given JADN to JAS and write output to the specified file",
                  "jadn - JADN formatted string, dictionary, file location",
                  "fname - File location to write output",
                  "source - Name of file being converted (optional)",
                  "comm - Comment level as defined by jadn.CommentLevel"
                ]
              },
              "jas_dumps(json, comm)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "JAS string"
                  ]
                },
                "fun_desc" : [
                  "Convert the given JADN to JAS",
                  "jadn - JADN formatted string, dictionary, file location",
                  "comm - Comment level as defined by jadn.CommentLevel"
                ]
              },
              "jas_load(jas, fname, source)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given JAS to JADN and write output to the specified file"
                ]
              },
              "md_dump(jadn, fname, source)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given JADN to MarkDown and write output to the specified file"
                ]
              },
              "md_dumps(jadn, styles)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "MarkDown string"
                  ]
                },
                "fun_desc" : [
                  "Convert the given JADN to MarkDown"
                ]
              },
              "proto_dump(proto, fname, source)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given JADN to ProtoBuf3 and write output to the specified file"
                ]
              },
              "proto_dumps(proto, comm)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "ProtoBuf3 string"
                  ]
                },
                "fun_desc" : [
                  "Convert the given JADN to ProtoBuf3"
                ]
              },
              "proto_load(proto, fname, source)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given ProtoBuf3 to JADN and write output to the specified file"
                ]
              },
              "proto_loads(proto)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "JADN string"
                  ]
                },
                "fun_desc" : [
                  "Convert the given ProtoBuf3 to JADN"
                ]
              },
              "relax_dump(relax, fname, source)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given JADN to Relax-NG and write output to the specified file"
                ]
              },
              "relax_dumps(relax, comm)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "Relax-NG string"
                  ]
                },
                "fun_desc" : [
                  "Convert the given JADN to Relax-NG"
                ]
              },
              "relax_load(relax, fname, source)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given Relax-NG to JADN and write output to the specified file"
                ]
              },
              "relax_loads(relax)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "JADN string"
                  ]
                },
                "fun_desc" : [
                  "Convert the given Relax-NG to JADN<"
                ]
              },
              "thrift_dump(thrift, fname, source)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given JADN to Thrift and write output to the specified file"
                ]
              },
              "thrift_dumps(thrift, comm)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "Thrift string"
                  ]
                },
                "fun_desc" : [
                  "Convert the given JADN to Thrift"
                ]
              },
              "thrift_load(thrift, fname, source)" : {
                "return" : {
                  "type" : "void"
                },
                "fun_desc" : [
                  "Convert the given Thrift to JADN and write output to the specified file"
                ]
              },
              "thrift_loads(thrift)" : {
                "return" : {
                  "type" : "str",
                  "info" : [
                    "JADN string"
                  ]
                },
                "fun_desc" : [
                  "Convert the given Thrift to JADN"
                ]
              }
            }
          }
        }
      }
    }
  }
}