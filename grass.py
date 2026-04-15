#!/usr/bin/env python3
import sys
from lark import Lark


"""
GRASS programming language experimental parser
https://en.wikipedia.org/wiki/GRASS_(programming_language)

"""

grass_grammar = """
?start: (line | comment | _NL)+

line: [label] command [";" command]* [comment] _NL

label: "%" /[A-Z]+/
command: variable "=" expression
         | commandname[modifier] [argument ["," argument]*]

commandname: /[A-Z]+/
modifier: "/" /[A-Z]/
argument: /.+/

pixname: /[A-Z0-9]+/
variable: /[A-Z]{1,2}/ | "$" /[A-Z]/
expression: /.+/

comment: "*" /.+/

%import common.WS
%import common.NUMBER
%import common.ESCAPED_STRING -> STRING
%import common.NEWLINE -> _NL
%ignore WS
"""



def main():
    sourcefile = sys.argv[1]
    with open(sourcefile, 'r') as f:
        source = f.read()

    print(source)
    parser = Lark(grass_grammar)
    print(parser.parse(source).pretty())

if __name__ == '__main__':
    main()
