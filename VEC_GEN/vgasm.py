#!/usr/bin/env python3
import argparse
from lark import Lark, Token, Transformer

DESC = """
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
        | INTERRUPT
        | INT
        | SIGNED_INT
        | ascii

    INTERRUPT: "*"

    ascii: "'" CHAR_TOKEN "'"
        | "'" CHAR_TOKEN CHAR_TOKEN "'"
        | "\"" CHAR "\""
        | "\"" CHAR CHAR "\""
        | "'" "'"
        | "\"" "\""

    CHAR: /./
    CHAR_TOKEN: /[A-Z]{2}[0-9]?/

    COMMENT: ";" /[^\n]*/

    %import common.WS_INLINE
    %import common (CNAME, INT, SIGNED_INT)
    %import common.NEWLINE -> _NL

    %ignore COMMENT
    %ignore WS_INLINE
    %ignore ","
"""


BITS = 16
MASK = (1 << BITS) - 1


# VG72: 3.22, 3-17
REGISTERS = {
    'PIR': 0x4,
    'NMR': 0x4,
    'MCR': 0x5,
    'XR':  0x8,
    'YR':  0x9,
    'ZR':  0xA,
    'AIR': 0xB,
    'IOR': 0xC,
    'ISR': 0xD,
    'PSR': 0x11,
    'NMR': 0x12,
    'CSR': 0x13,
    'DXR': 0x14,
    'DYR': 0x15,
    'DZR': 0x16,
    'R11R': 0x17,
    'R12R': 0x18,
    'R13R': 0x19,
    'R21R': 0x1A,
    'R22R': 0x1B,
    'R23R': 0x1C,
    'R31R': 0x1D,
    'R32R': 0x1E,
    'R33R': 0x1F,
}


# VG72: 3.11, 3-7
INTERRUPTS = {k: v << 7 for k, v in {
    'MED': 1<<0,
    'MEC': 1<<1,
    'MEF': 1<<2,
    'MET': 1<<3,
    'MEK': 1<<4,
    'MES': 1<<5,
    'MDB': 1<<6,
    'MPH': 1<<7,
    'MS1': 1<<8,
    'MS2': 1<<9,
    'MS3': 1<<10,
    'MS4': 1<<11,
    # 'PB'  # 2 bits
    'MDR': 1<<14,
    'MDW': 1<<15,
}.items()}


# VG72: 3.29, 3-34
CHAR_SIZE = {
    'S0': 0x40,
    'S1': 0x50,
    'S2': 0x60,
    'S3': 0x70,
    'V' : 0x80,  # Vertical write-direction
}


# Vector Mode, 3-20
VM = {
    'DSH': 0x10,  # Dashed line
    'DOT': 0x20,  # Dotted line
    'PNT': 0x30,  # End-point
}


# VG72: 3.18 Control Display Instructions
#       3-14 to 3-35
LOOKUP = {
    '*'   : 0o100000,  # Interrupt P-bit
    'T'   : 0x1,       # Terminate
    # Control Display Instructions, 3-14
    'NOP' : 0x0,
    'SPC' : 0x2000,
    'HLT' : 0x3000,
    # Register Change Display Instructions, 3-15
    'LD'  : 0x4000,
    'OR'  : 0x5000,
    'AN'  : 0x6000,
    'AD'  : 0x7000,
    # Display Write Instructions, 3-19
    'VR'  : 0x1000,
    'VR IX': 0x1001,
    'VR IY': 0x1002,
    'VR IZ': 0x1003,
    'VA'  : 0x1004,
    'VA IX': 0x1005,
    'VA IY': 0x1006,
    'VA IZ': 0x1007,
    'DVXY': 0x1008,
    'DVYY': 0x1009,
    'DVXX': 0x100A,
    'DV3D': 0x100B,
    'CH'  : 0x100F,
    # OF: VA operation field, VG72: 3-25
    'L' : 0x0,  # Load register
    'D' : 0x4,  # Load, then draw vector
    'M' : 0x8,  # Load, then move beam (no draw)
    'DT': 0xC,  # Load, draw, terminate
    # CF: VA coordinate field
    'AI': 0x0,  # Autoincrement register (AIR)
    'X' : 0x1,  # X-coord reg (XR)
    'Y' : 0x2,  # Y-coord reg (YR)
    'Z' : 0x3,  # Z-coord reg (ZR)
} | REGISTERS | INTERRUPTS | VM | CHAR_SIZE


# VG72: TABLE A-1
ASCII = {
    'BS' : 0x08,
    'HT' : 0x09,
    'LF' : 0x0A,
    'VT' : 0x0B,
    'FF' : 0x0C,
    'NL' : 0x0D,
    'DC1': 0x11,
    'DC2': 0x12,
    'DC3': 0x13,
    'DC4': 0x14,
    'SP' : 0x20,
}


class VGTransformer(Transformer):
    def __init__(self, outfile, listfile=None):
        super().__init__()
        self.out = outfile
        self.list = listfile

    def ascii(self, children):
        # TODO: we want the statement to appear in the listing
        # combine the "x" 'DC4' statement into a single word
        print('ASCII:', children)
        word = 0
        for i, c in enumerate(children):
            if c.type == 'CHAR':
                v = ord(c)
            else:
                v = ASCII[str(c)]
            word |= v << (8*(1-i))
        return f'ASCII {word:04X}'

    def line(self, children):
        label = children[0]
        statement = children[1]
        # TODO: something more sensible:
        return statement.replace('\t\t', '\t' + label + '\t')

    def label(self, children):
        return f'{children[0]}:'

    def statement(self, children):
        word = 0
        text = []
        label = comment = ''
        debug = []
        for token in children:
            if token in LOOKUP:
                word |= LOOKUP[token]
            elif isinstance(token, Token) and token.type in ('INT', 'SIGNED_INT'):
                v = int(token)
                #v -= v < 0
                word |= (v << 4) & MASK
            else:
                debug.append(f'UNRECOGNISED TOKEN "{token}"')
            text.append(str(token))

            if isinstance(token, Token):
                print(f'TOKEN: {token} ({token.type})')
        statement = ', '.join(text)
        if debug:
            comment = '; !!! ' + '; '.join(debug)
        return '\t'.join([f'{word:04X}', f'{word:06o}', label, statement, comment])


def main():
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument('source', help='Vector General instrutions to compile')
    parser.add_argument('-l', help='listing file name (.LST)')
    parser.add_argument('-o', help='output file name (.BIN)')
    args = parser.parse_args()
    outfile = args.o
    listfile = args.l

    sourcefile = args.source
    with open(sourcefile, 'r') as f:
        source = f.read()
    parser = Lark(vg_grammar)
    parse_tree = parser.parse(source)
    transformer = VGTransformer(outfile, listfile)

    print('Parse Tree:')
    print(parse_tree.pretty())
    print('=' * 72)
    print(transformer.transform(parse_tree).pretty())


if __name__ == '__main__':
    main()
