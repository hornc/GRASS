#!/usr/bin/env python3
import argparse
import sys
from lark import Lark

"""
Vector General display instruction mnemonic compiler 
"""


vg_grammar = r"""
    ?start: (line|_NL)+

    ?line: label statement _NL
         | label _NL
         | statement _NL

    label: CNAME ":"

    statement: arg+

    ?arg: CNAME
        | INT
        | SIGNED_INT
        | INDIRECT_CMD
        | ascii

    INDIRECT_CMD: "*" CNAME

    ascii: "'" CHAR_TOKEN "'"
        | "'" CHAR_TOKEN CHAR_TOKEN "'"
        | "\"" CHAR "\""
        | "\"" CHAR CHAR "\""
        | "'" "'"
        | "\"" "\""

    CHAR: /./
    CHAR_TOKEN: /[A-Z0-9]+/

    COMMENT: ";" /[^\n]*/

    %import common.WS_INLINE
    %import common (CNAME, INT, SIGNED_INT)
    %import common.NEWLINE -> _NL
    
    %ignore COMMENT
    %ignore WS_INLINE
    %ignore ","
"""


def main():
    sourcefile = sys.argv[1]
    with open(sourcefile, 'r') as f:
        source = f.read()
    parser = Lark(vg_grammar)
    parse_tree = parser.parse(source)
    print(parse_tree.pretty())


if __name__ == '__main__':
    main()
