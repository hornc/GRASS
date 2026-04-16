#!/usr/bin/env python3
import sys
import matplotlib.pyplot as plt
import numpy as np
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
argument: /[A-Z0-9]+/ | STRING | expression

pixname: /[A-Z0-9]+/
variable: /[$A-Z]{1,2}/
expression: /.+/

comment: "*" /.+/

%import common.WS
%import common.NUMBER
%import common.ESCAPED_STRING -> STRING
%import common.NEWLINE -> _NL
%ignore WS
"""


class Picture:
    def __init__(self):
        self.points = []

    def get_point(self, n):
        k = 0
        if n == len(self.points):
            k = -1
        return self.points[n] + [k]

    def from_file(self, fname):
        # load points from file
        self.name = fname.strip()
        with open(self.name, 'r') as f:
            for row in f:
                x, y, z = [int(v) for v in row.strip().split(',')]
                self.points.append([x, y, z])

    def show(self):
        ax = plt.figure().add_subplot(projection='3d')
        x, y, z = zip(*self.points)
        ax.plot(x, z, y, label=self.name)
        ax.set(xlabel='X', ylabel='Z', zlabel='Y')
        ax.legend()
        plt.show()


def run_command(t):
    label, cmd, a, b = t.children
    assert cmd.data == 'command'
    cmd_type = cmd.children[0]
    if cmd_type.data == 'variable':
        var, expr = cmd.children
        print(f'  VAR: {var.children[0]} = {expr.children[0]}')
    elif cmd_type.data == 'commandname':
        cmdname = cmd.children[0].children[0]
        arg = cmd.children[2].children[0]
        # print('DEBUG', cmd.children)
        if cmdname.startswith('PROM'):
            print(arg.strip('" '))
        elif cmdname.startswith('INP'):
            v = input('?')
        elif cmdname == 'GETDSK':
            mod = cmd.children[1]
            if mod:
                # /P means do not display yet, just load points
                mod = mod.children[0]
            arg = cmd.children[2].children[0]
            print('GETDSK', mod, arg)
            p = Picture()
            p.from_file(arg)
            print('POINTS:', p.points)
            p.show()
        else:
            print(f'  CMD: {cmdname}')


def main():
    sourcefile = sys.argv[1]
    with open(sourcefile, 'r') as f:
        source = f.read()

    parser = Lark(grass_grammar)
    parse_tree = parser.parse(source)
    print(parse_tree.pretty())

    for command in parse_tree.children:
        if command.data != 'comment':
            run_command(command)


if __name__ == '__main__':
    main()
