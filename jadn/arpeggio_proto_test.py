from __future__ import unicode_literals, print_function

import glob
import json
import os
import re

from arpeggio import EOF, Optional, OneOrMore, OrderedChoice, ParserPython, PTNodeVisitor, visit_parse_tree, RegExMatch, UnorderedGroup, ZeroOrMore

from libs.utils import toStr, Utils

lineSep = '\\r?\\n'


def ProtoRules():
    def endLine():
        return RegExMatch(r'({})?'.format(lineSep))

    def number():
        return RegExMatch(r'\d*\.\d*|\d+')

    def string():
        return RegExMatch(r'[\'\"].*?[\'\"]')

    def commentBlock():
        return RegExMatch(r'\/\*(.|{})*?\*\/'.format(lineSep)),

    def commentLine():
        return '//', RegExMatch(r'.*')

    def syntax():
        return RegExMatch(r'syntax\s?=\s?[\'\"].*[\'\"]\;?'), OneOrMore(endLine)

    def package():
        return RegExMatch(r'package\s?[\'\"]?.*[\'\"]?\;?'), OneOrMore(endLine)

    def pkgImports():
        return RegExMatch(r'import\s?[\'\"].*[\'\"]\;?'), OneOrMore(endLine)

    def headerComments():
        return (
            OrderedChoice(
                ZeroOrMore(commentBlock),
                ZeroOrMore(commentLine)
            )
        )

    def header():
        return UnorderedGroup(
            syntax,
            package,
            headerComments,
            ZeroOrMore(pkgImports)
        )

    def defHeader():
        return (
            RegExMatch(r'[\w\d]+'),  # name
            "{",
            Optional('//', RegExMatch(r'.*?(#|{})'.format(lineSep))),  # comment
            Optional(RegExMatch(r'#?jadn_opts:{.*}+')),  # jadn options
            OneOrMore(endLine)
        )

    def defField():
        return (
            RegExMatch(r'\w[\w\d\.]*?\s'),  # type
            RegExMatch(r'\w[\w\d]*?\s'),  # name
            '=',
            number,  # field number
            ';',
            Optional(
                '//',
                RegExMatch(r'.*?(#|{})'.format(lineSep)),  # comment
                Optional(RegExMatch(r'jadn_opts:{.*}+'))  # jadn options
            ),
            OneOrMore(endLine)
        )

    def messageDef():
        return (
            'message',
            defHeader,
            OneOrMore(defField),
            '}'
        )

    def enumField():
        return (
            RegExMatch(r'\w[\w\d]*?\s'),  # name
            '=',
            number,  # field number
            ';',
            Optional(
                '//',
                RegExMatch(r'.*?(#|{})'.format(lineSep)),  # comment
                Optional(RegExMatch(r'jadn_opts:{.*}+'))  # jadn options
            ),
            OneOrMore(endLine)
        )

    def enumDef():
        return (
            'enum',
            defHeader,
            OneOrMore(enumField),
            '}',
        )

    def repeatedDef():
        return (
            'repeated',
            defField
        )

    def oneofDef():
        return (
            'oneof',
            defHeader,
            OneOrMore(defField),
            '}'
        )

    def wrappedDef():
        return (
            'message',
            RegExMatch(r'[\w\d]+'),
            '{',
            OrderedChoice(
                Optional(oneofDef),
                Optional(repeatedDef)
            ),
            '}'
        )

    def typeDefs():
        return OneOrMore(
            UnorderedGroup(
                ZeroOrMore(messageDef),
                ZeroOrMore(wrappedDef),
                ZeroOrMore(enumDef),
            )
        )

    def customDef():
        return OrderedChoice(
            ZeroOrMore(commentBlock),
            ZeroOrMore(commentLine)
        )

    return (
        header,
        typeDefs,
        Optional(customDef),
        EOF
    )


class ProtoVisitor(PTNodeVisitor):
    data = {}
    repeatedTypes = {
        'arrayOf': 'ArrayOf',
        'array': 'Array'
    }

    def load_jadnOpts(self, jadnString, defaultDict):
        jadnString = toStr(jadnString)
        defType = defaultDict['type'] if 'type' in defaultDict else 'String'
        optDict = {
            'type': 'String',
            'options': []
        }
        optDict.update(defaultDict)

        if re.match(r'^jadn_opts:', jadnString):
            optStr = re.sub(r'jadn_opts:(?P<opts>{.*?}+)', '\g<opts>', jadnString)

            try:
                optDict = json.loads(optStr)
                optDict['type'] = optDict['type'] if 'type' in optDict else defType
                optDict['options'] = Utils.opts_d2s(optDict['options']) if 'options' in optDict else []
            except Exception as e:
                print('Oops, cant load jadn')
                print(e)

        return optDict

    def visit_ProtoRules(self, node, children):
        return self.data

    def visit_number(self, node, children):
        try:
            return float(node.value) if '.' in node.value else int(node.value)
        except Exception as e:
            print(e)

        return node.value

    def visit_string(self, node, children):
        return node.value.strip('\'\"')

    def visit_commentBlock(self, node, children):
        com = re.compile(r'(^(/\*)?(\s+)?|(\s+)?(\*/)?$)', re.MULTILINE).sub('', node.value)
        com = re.split(r'{}'.format(lineSep), com)
        com = com[1:] if com[0] == '' else com
        com = com[:-1] if com[-1] == '' else com
        return com

    def visit_commentLine(self, node, children):
        return re.sub(r'^//\s*?', '', node.value)

    def visit_headerComments(self, node, children):
        if 'meta' not in self.data:
            self.data['meta'] = {}

        for child in children:
            if type(child) is list:
                for c in child:
                    if re.match(r'^\s?\*\s?meta:', c):
                        line = re.sub(r'(\s?\*\s?meta:\s+|{})'.format(lineSep), '', c).split(' - ')

                        try:
                            self.data['meta'][line[0]] = json.loads(' - '.join(line[1:]))
                        except Exception as e:
                            self.data['meta'][line[0]] = ' - '.join(line[1:])

    def visit_typeDefs(self, node, children):
        if 'types' not in self.data:
            self.data['types'] = []

        for child in children:
            if type(child) is list:
                self.data['types'].append(child)
            else:
                print('type child is not type list')
                print(child)

    def visit_defHeader(self, node, children):
        optDict = self.load_jadnOpts(children[-1], {
            'type': 'Record',
            'options': []
        })

        return [
            children[0],  # Type Name
            optDict['type'],  # Type
            optDict['options'],  # Options
            re.sub(r'\s?#\S?$', '', children[1]) if len(children) >= 2 else ''  # comment
        ]

    def visit_defField(self, node, children):
        optDict = self.load_jadnOpts(children[-1], {
            'type': 'String',
            'options': []
        })

        return [
            children[2],  # field number
            re.sub(r'(^\s+|\s+$)', '', children[1]),  # name
            self.repeatedTypes.get(optDict['type'], optDict['type']),  # type
            optDict['options'],  # options
            re.sub(r'\s?#\S?$', '', children[3]) if len(children) >= 4 else ''  # comment
        ]

    def visit_messageDef(self, node, children):
        msgFields = []

        for child in children[1:]:
            if type(child) is list:
                msgFields.append(child)
            else:
                print('Message child not type list')
                print(child)

        children[0].append(msgFields)
        return children[0]

    def visit_enumField(self, node, children):
        if len(children) >= 3 and re.match(r'^required starting enum number for protobuf3', children[-1]):
            return

        return [
            children[1],  # field number
            re.sub(r'(^\s+|\s+$)', '', children[0]),  # name
            re.sub(r'\s?(#|{})\S?$'.format(lineSep), '', children[2]) if len(children) >= 3 else ''  # comment
        ]

    def visit_enumDef(self, node, children):
        enumFields = []
        name = children[0][0]

        for child in children[1:]:
            if type(child) is list and not (child[0] == 0 and re.match(r'^Unknown_{}'.format(name), child[1])):
                enumFields.append(child)
            elif child[0] == 0 and re.match(r'^Unknown_{}'.format(name), child[1]):
                print('Enumerated field is placeholder')
                print(child)
            else:
                print('Enumerated field not type list')
                print(child)

        children[0].append(enumFields)
        return children[0]

    def visit_repeatedDef(self, node, children):
        if len(children) > 1:
            print('RepeatedDef Error')
            return
        else:
            children = children[0]

        return children[2:]

    def visit_oneofDef(self, node, children):
        oneofFields = []

        for child in children[1:]:
            if type(child) is list:
                oneofFields.append(child)
            else:
                print('OneOf child not type list')
                print(child)

        children[0].append(oneofFields)
        return children[0]

    def visit_wrappedDef(self, node, children):
        if children[0] == children[1][0]:
            return children[1]

        elif children[1][0] in self.repeatedTypes.values():
            repeated = [children[0]]
            repeated.extend(children[1])
            return repeated

        else:
            print('Invalid Wrapped Def')
            print(children[1])

    def visit_customDef(self, node, children):
        if 'types' not in self.data:
            self.data['types'] = []

        for child in children:
            if type(child) is list and 'JADN Custom Fields' in child[0]:
                try:
                    self.data['types'].append(json.loads(''.join(child[1:])))
                except Exception as e:
                    print(e)
            else:
                print('Custom Something..')
                print(child)


if __name__ == '__main__':
    # Install graphviz for python and to system before setting debugDraw
    debug = False
    debugDraw = (debug and False)
    schemaFile = 'openc2-wd06.proto'

    parser = ParserPython(ProtoRules, reduce_tree=True, debug=debug)
    schema = toStr(open(os.path.join('.', 'schema_gen_test', schemaFile), 'rb').read())
    parse_tree = parser.parse(schema)
    result = visit_parse_tree(parse_tree, ProtoVisitor())

    if debugDraw:
        from graphviz import render

        for dotFile in glob.glob('*.dot'):
            print('Rendering {}'.format(dotFile))
            render('dot', 'png', dotFile)

    jadn = Utils.jadnFormat(result, indent=2)
    # print(jadn)
    open(os.path.join('.', 'schema_gen_test', schemaFile + '.jadn'), 'w+').write(jadn)