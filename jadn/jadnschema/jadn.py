"""
Load, validate, prettyprint, and dump JSON Abstract Encoding Notation (JADN) schemas
"""
from __future__ import print_function, unicode_literals

import copy
import json
import jsonschema
import numbers
import os
import re

from collections import defaultdict
from datetime import datetime
from io import BufferedIOBase, TextIOBase
from typing import Dict, List, Tuple, Union

from . import (
    jadn_defs,
    jadn_utils,
    utils
)
from .exceptions import (
    DuplicateError,
    FormatError,
    OptionError
)

# TODO: convert prints to ValidationError exception

jadn_schema = {
    "type": "object",
    "required": ["meta", "types"],
    "additionalProperties": False,
    "properties": {
        "meta": {
            "type": "object",
            "required": ["module"],
            "additionalProperties": False,
            "properties": {
                "module": {"type": "string"},
                "patch": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "imports": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "items": [
                            {"type": "string"},
                            {"type": "string"}
                        ]
                    }
                },
                "exports": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "types": {
            "type": "array",
            "items": {
                "type": "array",
                "minItems": 4,
                "maxItems": 5,
                "items": [
                    {"type": "string"},
                    {"type": "string"},
                    {"type": "array",
                        "items": {"type": "string"}
                    },
                    {"type": "string"},
                    {"type": "array",
                        "items": {
                            "type": "array",
                            "minItems": 3,
                            "maxItems": 5,
                            "items": [
                                {"type": "integer"},
                                {"type": "string"},
                                {"type": "string"},
                                {"type": "array",
                                 "items": {"type": "string"}
                                },
                                {"type": "string"}
                            ]
                        }
                    }
                ]
            }
        }
    }
}


def _check_typeopts(btype: str, topts: dict, tname: str) -> None:
    if jadn_defs.is_builtin(btype):
        vop = {topts.keys()} - {jadn_defs.TYPE_CONFIG.SUPPORTED_OPTIONS.get(btype, {}).keys()}
        if vop:
            OptionError(f"{tname} type {btype} invalid type option {', '.join(vop)}")
    else:
        TypeError(f"{tname} has invalid base type {btype}")


def jadn_check(schema: Union[dict, str]) -> dict:
    """
    Validate JADN structure against JSON schema,
    Validate JADN structure against JADN schema, then
    Perform additional checks on type definitions
    :param schema: schema to check
    :return: validated schema
    """
    if isinstance(schema, str):
        try:
            schema = jadn_loads(schema)
        except Exception:
            schema = jadn_load(schema)

    val = jsonschema.Draft4Validator(jadn_schema).validate(schema)
    if val:
        # TODO: raise errors if invalid schema
        print(val)

    schema = utils.jadn_idx2key(schema, True)

    for type_def in schema.get("types", []):  # datatype definition: jadn_defs.COLUMN_KEYS.Structures
        base_type = jadn_utils.basetype(type_def["type"])
        type_opts = type_def.get("opts", {})

        _check_typeopts(base_type, type_opts, type_def["name"])
        if base_type in ("ArrayOf", "MapOf"):
            if 'vtype' in type_opts:
                pass  # check vtype options
            else:
                print(OptionError(f"{type_def['name']} - Missing value type"))

        if base_type == "MapOf":
            if 'ktype' in type_opts:
                pass  # check ktype options
            else:
                print(OptionError(f"{type_def['name']} - Missing key type"))

        fmt = type_opts.get("format", None)
        if fmt:
            fmts = jadn_defs.FORMAT.CHECK.copy()
            fmts.update(jadn_defs.FORMAT.SERIALIZE)
            if fmt not in fmts or base_type != fmts.get(fmt, None):
                print(ValueError(f"Unsupported value constraint \"{fmt}\" on {base_type}: {type_def['name']}"))

        if jadn_defs.is_builtin(base_type):
            topts = jadn_utils.topts_s2d(type_def["opts"])
            vop = {*topts.keys()}.difference({*jadn_defs.TYPE_CONFIG.SUPPORTED_OPTIONS[base_type]})

            if vop:
                print(TypeError(f"{type_def['name']} type {base_type} invalid type option{vop}"))

        else:  # TODO: handle if type_def[TNAME] doesn't exist
            topts = {}
            print(TypeError(f"Unknown Base Type: {base_type} ({type_def['name']})"))

        if base_type == "ArrayOf" and "rtype" not in topts:
            print(FormatError(f"Type: {type_def['name']} - Missing array element type"))



        cvt = topts.get("cvt")
        if cvt and (cvt not in jadn_defs.FORMAT.CONVERT or base_type != jadn_defs.FORMAT.CONVERT[cvt]):
            print(ValueError(f"Unsupported String conversion \"{cvt}\" on {base_type}: {type_def['name']}"))

        if jadn_defs.is_primitive(base_type) or base_type == "ArrayOf":
            if len(type_def) != 4:    # TODO: trace back to base type
                print(FormatError(f"{type_def['name']} - type {base_type} cannot have items"))

        elif jadn_defs.is_builtin(base_type):
            if len(type_def) == 5:
                tags = set()
                names = set()
                # TODO: check Choice min cardinality != 0
                # item definition: jadn_defs.COLUMN_KEYS.Gen_def or (enumerated): jadn_defs.COLUMN_KEYS.Enum_Def
                field_columns = jadn_defs.COLUMN_KEYS["Enum_Def" if base_type == "Enumerated" else "Gen_Def"]

                for k, field in enumerate(type_def["fields"]):
                    field = dict(zip(field_columns, field))
                    ordinal = base_type in ("Array", "Record")
                    tags.add(field["id"])
                    names.add(field["value" if base_type == "Enumerated" else "name"])

                    if ordinal and field["id"] != k + 1:
                        print(KeyError(f"Item tag: {type_def['name']} ({base_type}): {field['name']} -- {field['id']} should be {k + 1}"))

                    if len(field) != len(field_columns):
                        print(FormatError(f"Item: {type_def['name']} {base_type} {field['name']} - {len(field)} != {len(field_columns)}"))

                    if len(field) > 3 and jadn_defs.is_builtin(field["type"]):
                        # TODO: trace back to builtin types
                        fop = {*jadn_utils.fopts_s2d(field["opts"])}.difference({*jadn_defs.FIELD_CONFIG.SUPPORTED_OPTIONS.get(field["type"], ())})

                        if fop:
                            print(OptionError(f"{type_def['name']} : {field['name']} {field['type']} invalid field option {fop}"))
                    # TODO: check that wildcard name has Choice type, and that there is only one wildcard.

                if len(type_def["fields"]) != len(tags):
                    print(DuplicateError(f"Tag collision in {type_def['name']} - {len(type_def['fields'])} items, {len(tags)} unique tags"))

                # TODO: Check validity of error raising
                if len(type_def["fields"]) != len(names) and base_type not in ("Array", "ArrayOf"):
                    print(DuplicateError(f"Name collision in {type_def['name']} - {len(type_def['fields'])} items, {len(names)} unique names"))

            else:
                print(FormatError(f"Type: {type_def['name']} - missing items from compound type {base_type}"))

    return utils.jadn_key2idx(schema)


def jadn_strip(schema: dict) -> dict:
    """
    Strip comments from schema
    :param schema: schema to strip comments
    :return: comment stripped JADN schema
    """
    schema = utils.jadn_idx2key(schema)

    for type_def in schema.get("types", []):
        type_def["desc"] = ""
        for field in type_def.get("fields", []):
            field["desc"] = ""
    return utils.jadn_key2idx(schema)


# TODO: Cleanup code
def jadn_simplify(schema: dict) -> dict:          # Remove schema optimizations
    """
    Given an input schema, return a simplified schema with any optimized definitions removed.

    1) Replace all derived enumerations with explicit Enumerated type definitions
    2) Replace all multiple-value fields with explicit ArrayOf type definitions
    3) Replace all MapOf types with listed keys with explicit Map type definitions
    """

    def get_optx(opts, oname):
        n = [i for i, x in enumerate(opts) if x[0] == OPTION_ID[oname]]
        return n[0] if n else None

    def del_opt(opts, oname):
        n = [i for i, x in enumerate(opts) if x[0] == OPTION_ID[oname]]
        if n:
            del opts[n[0]]

    def get_function(fname, typeref):
        m = re.match(fname + "\((\w+)\)$", typeref) if typeref else None
        return m.group(1) if m else None

    def update_eref(refs, opts, optname):
        n = get_optx(opts, optname)
        if n is not None:
            x = get_function("Enum", opts[n][1:])
            if x:
                refs[x].append([opts, n])

    Sys = "$"                                   # Character reserved for tool-generated TypeNames
    sc = copy.deepcopy(schema)                  # Don't modify original schema
    tdefs = sc["types"]
    typex = {t[TypeName]: n for n, t in enumerate(tdefs)}   # Build type index
    new_types = []

    enum_defs = {}                              # Map of base type to Enumerated type definition
    enum_refs = defaultdict(list)               # Map of base type to list of references
    for tdef in tdefs:                          # Build list of derived enumerations
        if tdef[BaseType] in ["Enumerated", "ArrayOf", "MapOf"]:
            opts = tdef[TypeOptions]
            n = get_optx(opts, "enum")
            if n is not None:
                enum_defs[opts[n][1:]] = tdef[TypeName]
            update_eref(enum_refs, opts, "ktype")
            update_eref(enum_refs, opts, "vtype")
    for tname, refs in enum_refs.items():       #
        if tname in enum_defs:                  # Replace derived enumeration with Enumerated type
            typename = enum_defs[tname]
            tx = typex[typename]
        else:                                   # Referenced - create new Enumerated type
            typename = tname + Sys + "Enum"
            tx = len(tdefs)
            tdefs.append([])
            typex.update({typename: tx})
        rdef = tdefs[typex[tname]]              # Referenced type definition
        newfields = [[f[FieldID], f[FieldName], f[FieldDesc]] for f in rdef[Fields]]
        idopt = [OPTION_ID["id"]] if get_optx(rdef[TypeOptions], "id") is not None else []
        tdefs[tx] = [typename, "Enumerated", idopt, rdef[TypeDesc], newfields]
        for opts, n in refs:                        # Replace all references with Enumerated type
            opts[n] = opts[n][0] + typename

    for n, tdef in enumerate(sc["types"]):
        to = topts_s2d(tdef[TypeOptions])
        if tdef[BaseType] == "MapOf" and tdefs[typex[to["ktype"]]][BaseType] == "Enumerated":  # Replace MapOf(Enumerated, ..) with Map
            newfields = [[f[FieldID], f[FieldName], to["vtype"], [], f[EnumDesc]] for f in tdefs[typex[to["ktype"]]][Fields]]
            sc["types"][n] = [tdef[TypeName], "Map", [], tdef[TypeDesc], newfields]
        elif is_compound(tdef[BaseType]):
            for fdef in tdef[Fields]:
                fo = fopts_s2d(fdef[FieldOptions])
                if "maxc" in fo and fo["maxc"] != 1:                # Expand field multiplicity
                    newname = tdef[TypeName] + Sys + fdef[FieldName]
                    minc = fo["minc"] if "minc" in fo else 1
                    newopts = {"vtype": fdef[FieldType], "minv": max(minc, 1)}      # Don't allow empty ArrayOf
                    newopts.update({"maxv": fo["maxc"]} if fo["maxc"] > 1 else {})  # Omit unspecified upper bound
                    new_types.append([newname, "ArrayOf", opts_d2s(newopts), fdef[FieldDesc]])

                    fdef[FieldType] = newname       # Point existing field to new ArrayOf
                    f = fdef[FieldOptions]
                    del_opt(f, "maxc")
                    if minc != 0:
                        del_opt(f, "minc")
    sc["types"].append(new_types)
    return sc


def jadn_merge(base: dict, imp: dict, nsid: str) -> dict:
    """
    Merge an imported schema into a base schema
    :param base: base schema
    :param imp: schema to merge into base
    :param nsid:
    :return: merged schema
    """
    def update_opts(opts: list) -> list:
        return [(f"{x[0] + nsid}:{x[1:]}" if x[0] == "*" and x[1:] in imported_names else x) for x in opts]

    # Make a copy to avoid modifying base
    types = base["types"][:]
    imported_names = {t[jadn_defs.column_index("Structure", "name")] for t in imp["types"]}

    for type_def in imp["types"]:
        type_def = dict(zip(jadn_defs.COLUMN_KEYS.Structure, type_def))
        base_type = jadn_utils.basetype(type_def["type"])

        type_def["name"] = f"{nsid}:{type_def['name']}"
        type_def["opts"] = update_opts(type_def["opts"])

        if "fields" in type_def:
            fields = []
            for field in type_def["fields"]:
                if base_type != "Enumerated":
                    field = dict(zip(jadn_defs.COLUMN_KEYS["Gen_Def"], field))
                    field["type"] = f"{nsid}:{field['type']}" if field["type"] in imported_names else field["type"]
                    field["opts"] = update_opts(field["opts"])
                    fields.append(list(field.values()))
                else:
                    fields.append(field)

            type_def["fields"] = fields

        types.append(list(type_def.values()))
    return {"meta": base["meta"], "types": types}


def topo_sort(items: list) -> Tuple[List[str], List[str]]:
    """
    Topological sort with locality
    Sorts a list of (item: (dependencies)) pairs so that 1) all dependency items are listed before the parent item,
    and 2) dependencies are listed in the given order and as close to the parent as possible.
    Returns the sorted list of items and a list of root items.  A single root indicates a fully-connected hierarchy;
    multiple roots indicate disconnected items or hierarchies, and no roots indicate a dependency cycle.
    """
    def walk_tree(item: list):
        for i in deps.get(item, []):
            if i not in out:
                walk_tree(i)
                out.append(i)

    out = []
    deps = {i[0]: i[1] for i in items}
    roots = list({*deps.keys()}.difference({j for i in items for j in i[1]}))

    for item in roots:
        walk_tree(item)
        out.append(item)

    out = out if out else list(*deps.keys())     # if cycle detected, don't sort
    return out, roots


def build_jadn_deps(schema: dict) -> List[Tuple[str, List[str]]]:
    """
    Type dependency list
    :param schema: schema to gather dependencies
    :return: list of types and dependencies
    """
    def ns(name: str, nsids: list) -> str:
        """
        Return namespace if name has a known namespace, otherwise return full name
        """
        nsp = name.split(":")[0]
        return nsp if nsp in nsids else name

    schema = utils.jadn_idx2key(schema, True)
    imps = schema.get("meta", {}).get("imports", [])
    items = [(n[0], []) for n in imps]
    nsids = [n[0] for n in imps]

    for type_def in schema.get("types", []):
        base_type = jadn_utils.basetype(type_def["type"])
        deps = []

        if base_type == "ArrayOf":
            vtype = type_def["opts"].get("vtype", "")
            if not jadn_defs.is_builtin(vtype):
                deps.append(ns(vtype, nsids))

        elif "fields" in type_def and base_type != "Enumerated":
            for field in type_def["fields"]:
                if not jadn_defs.is_builtin(field["type"]):
                    deps.append(ns(field["type"], nsids))

        items.append((type_def["name"], deps))
    return items


def jadn_analyze(schema: dict) -> Dict[str, List[str]]:
    """
    Analyze the given schema for unreferenced and undefined types
    :param schema: schema to analyse
    :return: analysis results
    """
    items = build_jadn_deps(schema)
    # out, roots = topo_sort(items)
    exports = schema.get("meta", {}).get("exports", [])

    refs = {j for i in items for j in i[1]}.union({*exports})
    types = {i[0] for i in items}

    return dict(
        unreferenced=list(types.difference(refs)),
        undefined=list(refs.difference(types)),
        cycles=[]
    )


def jadn_loads(jadn_str: str) -> dict:
    """
    load a JADN schema from a string
    :param jadn_str: JADN schema to load
    :return: loaded schema
    """
    try:
        return jadn_check(json.loads(jadn_str))
    except Exception:
        raise ValueError("Schema improperly formatted")


def jadn_load(fname: Union[str, BufferedIOBase, TextIOBase]) -> dict:
    """
    Load a JADN schema from a file
    :param fname: JADN schema file to load
    :return: loaded schema
    """
    try:
        if isinstance(fname, str):
            if os.path.isfile(fname):
                with open(fname, "rb") as f:
                    return jadn_check(json.load(f))
            else:
                return jadn_check(json.loads(fname))
        elif isinstance(fname, (BufferedIOBase, TextIOBase)):
            return jadn_check(json.load(fname))
    except Exception:
        raise ValueError("Schema improperly formatted")

    raise TypeError("fname is not a valid type")


def jadn_dumps(schema: Union[complex, dict, float, int, str, tuple], indent: int = 2, strip: bool = False, _level: int = 0) -> str:
    """
    Properly format a JADN schema
    :param schema: Schema to format
    :param indent: spaces to indent
    :param strip: strip comments from schema
    :param _level: current indent level
    :return: Formatted JADN schema
    """
    schema = jadn_strip(schema) if strip and _level == 0 and isinstance(schema, dict) else schema
    _indent = indent - 1 if indent % 2 == 1 else indent
    _indent += (_level * 2)
    ind, ind_e = " " * _indent, " " * (_indent - 2)

    if isinstance(schema, dict):
        lines = f",\n".join(f"{ind}\"{k}\": {jadn_dumps(schema[k], indent, strip, _level+1)}" for k in schema)
        return f"{{\n{lines}\n{ind_e}}}"

    elif isinstance(schema, (list, tuple)):
        nested = schema and isinstance(schema[0], (list, tuple))
        lvl = _level+1 if nested and isinstance(schema[-1], (list, tuple)) else _level
        lines = [jadn_dumps(val, indent, strip, lvl) for val in schema]
        if nested:
            return f"[\n{ind}" + f",\n{ind}".join(lines) + f"\n{ind_e}]"
        return f"[{', '.join(lines)}]"

    elif isinstance(schema, (numbers.Number, str)):
        return json.dumps(schema)
    else:
        return "???"


def jadn_dump(schema: dict, fname: Union[str, BufferedIOBase, TextIOBase], source: str = "", strip: bool = False) -> None:
    """
    Write the JADN to a file
    :param schema: schema to write
    :param fname: file to write to
    :param source: name of source file
    :param strip: strip comments from schema
    """
    if isinstance(fname, str):
        with open(fname, "w") as f:
            if source:
                f.write(f"\"Generated from {source}, {datetime.ctime(datetime.now())}\"\n\n")
            f.write(f"{jadn_dumps(schema, strip=strip)}\n")

    elif isinstance(fname, (BufferedIOBase, TextIOBase)):
        if source:
            fname.write(f"\"Generated from {source}, {datetime.ctime(datetime.now())}\"\n\n")
        fname.write(f"{jadn_dumps(schema, strip=strip)}\n")
    else:
        raise TypeError("fname is not a valid type")
