# jas_jadn.py
# Converts JAS Schema to JADN Schema
from __future__ import unicode_literals, print_function

import json
import re
import os

from datetime import datetime
from arpeggio import EOF, Optional, OneOrMore, ParserPython, PTNodeVisitor, visit_parse_tree, RegExMatch, OrderedChoice, UnorderedGroup, ZeroOrMore

from .... import (
    utils
)

lineSep = '\\r?\\n'

stype_map = {                   # Map JAS type names to JAS built-in types (Equivalent ASN.1 types in comments)
    'BINARY': 'Binary',           # OCTET STRING
    'BOOLEAN': 'Boolean',         # BOOLEAN
    'INTEGER': 'Integer',         # INTEGER
    'REAL': 'Number',             # REAL
    'NULL': 'Null',               # NULL
    'STRING': 'String',           # UTF8String
    'ARRAY': 'Array',             # SEQUENCE
    'ARRAY_OF': 'ArrayOf',        # SEQUENCE OF
    'CHOICE': 'Choice',           # CHOICE
    'ENUMERATED': 'Enumerated',   # ENUMERATED
    'MAP': 'Map',                 # SET
    'RECORD': 'Record'            # SEQUENCE
}


def JasRules():
    def endLine():
        return RegExMatch(r'({})?'.format(os.linesep))

    def commentLine():
        # match - any characters after comment line '--'
        return ZeroOrMore(RegExMatch(r'--.*')), endLine()
    
    def commentBlock():
        # match - any characters (line terminators included) enclosed with block quote signifier (/* and */)
        return RegExMatch(r'\/\*(.|{})*?\*\/'.format(lineSep))
    
    def headerComments():
        return ZeroOrMore(commentBlock)

    def header():
        return ZeroOrMore(headerComments)
    
    def repeatedItem():
        return OrderedChoice(
            RegExMatch(r'\S+'),     # item name
            RegExMatch(r'\[\d+\]'),  # array index
            RegExMatch(r'\S+'),     # item type
            ZeroOrMore(r'OPTIONAL'),
            ZeroOrMore(r','),
            ZeroOrMore(commentLine)
        )

    def repeatedDef():
        return (
            RegExMatch(r'\S+'),
            RegExMatch(r'::='),
            RegExMatch(r'(CHOICE|ARRAY|MAP)\S*'),
            RegExMatch(r'{'),
            Optional(commentLine),
            OneOrMore(repeatedItem),
            RegExMatch(r'}\s+')
        )
    
    def recordItem():
        return OrderedChoice(
            RegExMatch(r'[\w\-_]+'),     # item name
            RegExMatch(r'[\w\-_]+'),     # item type
            ZeroOrMore(r'OPTIONAL'),
            ZeroOrMore(r','),
            ZeroOrMore(commentLine)
        )

    def recordDef():
        return (
            RegExMatch(r'\S+'),
            RegExMatch(r'::='),
            RegExMatch(r'RECORD'),
            RegExMatch('{'),
            ZeroOrMore(commentLine),
            OneOrMore(recordItem),
            RegExMatch(r'}\s+')
        )

    def enumItem():
        return OrderedChoice(
            RegExMatch(r'[\w\-_\s]+'),    # item name
            RegExMatch(r'\(\d+\)'),      # enum value
            ZeroOrMore(r','),
            ZeroOrMore(commentLine)
        )

    def enumDef():
        return(
            RegExMatch(r'\S+'),
            RegExMatch(r'::='),
            RegExMatch(r'ENUMERATED\S*'),
            RegExMatch('{'),
            ZeroOrMore(commentLine),
            OneOrMore(enumItem),
            RegExMatch(r'}\s+')
        )

    def arrayOfDef():
        return (
            RegExMatch(r'\S+'),
            RegExMatch(r'::='),
            RegExMatch(r'ARRAY_OF'),
            RegExMatch(r'\(\S+\)'),                 # arrayOf type
            Optional(RegExMatch(r'\(.*\)')),        # size range
            Optional(commentLine)
        )

    def customDef():
        return (
            RegExMatch(r'\S+'),
            RegExMatch(r'::='),
            RegExMatch(r'(STRING|BINARY|INTEGER)'),
            Optional(RegExMatch(r'\(.*?\)')),
            Optional(commentLine)
        )

    def typeDefs():
        return OneOrMore(
            UnorderedGroup(
                ZeroOrMore(repeatedDef),
                ZeroOrMore(recordDef),
                ZeroOrMore(enumDef),
                ZeroOrMore(customDef),
                ZeroOrMore(arrayOfDef)
        ))
    
    return (
        header,
        typeDefs
    )


class JasVisitor(PTNodeVisitor):
    data = {}

    repeatedTypes = {
        'arrayOf': 'ArrayOf',
        'array': 'Array'
    }

    # in JAS, records are not indexed/enumerated, this variable keeps track of 
    # how many items are added per record and is modified in visit_recordItem and reset in visit_recordDef
    record_index = 1

    def visit_JasRules(self, node, children):
        return self.data

    def visit_commentLine(self, node, children):
        return re.sub(r'', '', node.value)
    
    def visit_commentBlock(self, node, children):
        com = re.compile(r'(^(/\*)?(\s+)?|(\s+)?(\*/)?$)', re.MULTILINE).sub('', node.value)
        com = re.split(r'{}'.format(lineSep), com)
        com = com[1:] if com[0] == '' else com
        com = com[:-1] if com[-1] == '' else com
        return com

    def visit_headerComments(self, node, children):
        hdr_list = ['module', 'patch', 'title', 'description', 'imports', 'exports', 'bounds', 'version']

        if 'meta' not in self.data:
            self.data['meta'] = {}
        for child in children[0]:
            line = child.split(': ')
            line[1] = re.sub(r'[\s]{2,}', '', str(line[1]))

            # Construct list of exports
            if line[0] == 'exports':
                line[1] = line[1].split(', ')    
                line[1][0] = re.sub(r'[\s]{2,}', '', str(line[1][0]))

            # Construct list of imports
            elif line[0] == 'imports':
                imports = []
                line[1] = re.sub(r'[\s]{2,}', '', str(line[1]))
                imports.append([line[1], line[2]])
                self.data['meta'][line[0]] = imports
                continue

            # Imports continued, since they do not reside on a single line
            elif line[0] not in hdr_list:
                self.data['meta']['imports'].append([line[0], line[1]])
                continue

            # Add line to header    
            try:
                self.data['meta'][line[0]] = json.loads(line[1])
            except Exception as e:
                self.data['meta'][line[0]] = line[1]
        
    def visit_repeatedItem(self, node, children):
        item = [int(children[1][1:-1]), children[0]]

        stype = re.sub(',', '', children[2])
        if stype in stype_map:
            item.append(stype_map[stype])
        else: 
            item.append(stype)

        opt = []
        if children[3] == 'OPTIONAL':
            opt.append("[0")
            match = re.search(r'\'max\':\s+(\d+)', children[-1])
            if match is not None:
                opt.append("]" + match.group(1))
                children[-1] = re.sub(r'\s*\%\{\S+\s*\d+\}', '', children[-1])
        item.append(opt)
        item.append(re.sub(r'--\s+', '', children[-1]))

        return item

    def visit_repeatedDef(self, node, children):
        # TODO: update how optional parameters and * translate
        compact = []
        if re.search(r'\.\w+', children[2]) is not None:
            children[2] = re.sub(r'\.ID', '', children[2])
            compact = ["="]

        try:
            comment = re.sub(r'--\s+', '', children[4])
            items = children[5:-1]
        except:
            comment = ""
            items = children[4:-1]

        return [
            children[0],
            stype_map[children[2]],
            compact,
            comment,
            items
        ]

    def visit_recordItem(self, node, children): 
        item = []
        item.append(int(self.record_index))
        self.record_index += 1
        item.append(children[0])
        if children[1] in stype_map:
            item.append(stype_map[children[1]])
        else:
            item.append(children[1])
        opt = []
        if children[2] == 'OPTIONAL':
            opt.append("[0")
            match = re.search(r'\'max\':\s+(\d+)', children[-1])
            if match is not None:
                opt.append("]" + match.group(1))
                children[-1] = re.sub(r'\s*\%\{\S+\s*\d+\}', '', children[-1])
        item.append(opt)
        item.append(re.sub(r'--\s+', '', children[-1]))

        return item

    def visit_recordDef(self, node, children):
        self.record_index = 1
        compact = []
        if re.search(r'\.\w+', children[2]) is not None:
            children[2] = re.sub(r'\.ID', '', children[2])
            compact = ["="]

        try:
            comment = re.sub(r'--\s+', '', children[4])
            items = children[5:-1]
        except:
            comment = ""
            items = children[4:-1]

        return [
            children[0],
            stype_map[children[2]],
            compact,
            comment,
            items
        ]
        
    def visit_enumItem(self, node, children):
        item = []
        item.append(int(re.search(r'\d+', children[1]).group(0)))
        item.append(re.sub(r'\s{2,}', '', children[0]))
        item.append(re.sub(r'--\s+', '', children[-1]))
        return item

    def visit_enumDef(self, node, children):
        compact = []
        if re.search(r'\.\w+', children[2]) is not None:
            children[2] = re.sub(r'\.ID', '', children[2])
            compact = ["="]

        comment = ""
        match = re.search('--', str(children[4]))
        if match is not None:
            comment = re.sub(r'--\s+', '', children[4])
            items = children[5:-1]
        else:
            items = children[4:-1]
        return [
            children[0],
            stype_map[children[2]],
            compact,
            comment,
            items
        ]

    def visit_arrayOfDef(self, node, children):
        # TODO: update how optional parameters translate
        arrayInfo = []        

        # check array type
        match = re.match(r'\((\w+)\)', children[3])
        if match is not None:
            arrayInfo.append('*' + match.group(1))
        
        # check array size
        match = re.search(r'(\d+)\.\.(\d+)', children[4])
        if match is not None:
            arrayInfo.append('[' + match.group(1))
            arrayInfo.append(']' + match.group(2))

        # check if comment exists
        try:
            comment = re.sub(r'--\s+', '', children[-1])
        except:
            comment = ""

        return [
            children[0],
            stype_map[children[2]],
            arrayInfo,
            comment
        ]

    def visit_customDef(self, node, children):
        # check if value constraints specified
        if children[2] == 'INTEGER':
            # match: [min]..[max]
            constraint = re.search(r'\s*(\d*)\.\.(\d*)', children[3])
            if constraint is not None:
                constraint = [constraint.group(1), constraint.group(2)]
                constraint[0] = '[' + constraint[0]
                constraint[1] = ']' + constraint[1]
            else:
                constraint = []
        else:
            # match: {constraint}
            constraint = re.search(r'CONSTRAINED\s*BY\s*\{(\S+)\}', children[3])
            if constraint is not None:
                constraint = ['@' + constraint.group(1)]
            else:
                constraint = []

        # check if comment exists
        try:
            comment = re.sub(r'--\s+', '', children[-1])
        except:
            comment = ""
      
        return [
            children[0],
            stype_map[children[2]],
            constraint,
            comment
        ]

    def visit_typeDefs(self, node, children):
        if 'types' not in self.data:
            self.data['types'] = []

        for child in children:
            if type(child) is list:
                self.data['types'].append(child)
            else:
                print('type child is not type list')


def jas_loads(jas):
    """
    Produce JADN schema from JAS schema
    :param jas: JAS schema to convert
    :return: JAS schema
    :rtype str
    """
    try:
        parser = ParserPython(JasRules)
        parse_tree = parser.parse(utils.toStr(jas))
        result = visit_parse_tree(parse_tree, JasVisitor())
        return utils.jadn_format(result, indent=2)

    except Exception as e:
        raise Exception(f"JAS parsing error has occurred: {e}")


def jas_load(jas, fname, source=""):
    with open(fname, "w") as f:
        if source:
            f.write(f"-- Generated from {source}, {datetime.ctime(datetime.now())}\n\n")
        f.write(jas_loads(jas))
