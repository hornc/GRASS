#!/usr/bin/env python3
import os
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

line: [LABEL] command [";" command]* [COMMENT] _NL

LABEL: "%" /[A-Z]+/
command: VARIABLE "=" expression        -> var
         | COMMAND[MODIFIER] [arglist]  -> cmd

arglist: argument ("," argument)*

COMMAND: /[A-Z]{2,}/
MODIFIER: "/" /[A-Z]/
argument: VARIABLE | NUMBER | PIXNAME | STRING | expression

PIXNAME: /[A-Z0-9]{3,}/
VARIABLE: /[$A-Z]{1,2}/
expression: /.+/

comment: COMMENT

COMMENT: "*" /.+/

%import common.WS
%import common.NUMBER
%import common.ESCAPED_STRING -> STRING
%import common.NEWLINE -> _NL
%ignore WS
%ignore COMMENT
"""


class Picture:
    def __init__(self, name=None):
        self.name = name
        self.points = []
        self.scale = [1, 1, 1]  # x, y, z scale factors
        self.move = [0, 0, 0]

    def copy(self, copyname):
        # returns a transformed copy of self
        c = Picture(copyname)
        c.points = self.get_points()
        return c

    def get_point(self, n):
        k = 0
        if n == len(self.points):
            k = -1
        return self.points[n] + [k]

    def get_points(self):
        sx, sy, sz = self.scale
        mx, my, mz = self.move
        return [[x*sx, y*sy, z*sz] for x, y, z in self.points]

    def from_file(self, fname):
        # load points from file
        self.name = fname.strip()
        with open(self.name, 'r') as f:
            for row in f:
                x, y, z = [int(v) for v in row.strip().split(',')]
                self.points.append([x, y, z])

    def show(self):
        ax = plt.figure().add_subplot(projection='3d')
        x, y, z = zip(*self.get_points())
        ax.plot(x, z, y, label=self.name)
        ax.set(xlabel='X', ylabel='Z', zlabel='Y')
        ax.legend()
        plt.show()


class GrassEnv:
    def __init__(self, macro=None):
        self.main = macro
        self.pictures = {}
        self.variables = {}
        self.inputs = {}
        self.outputs = {}

    def run(self):
        for line in self.main.children:
            if line.data != 'comment':
                self.run_command(line)

    def run_command(self, line):
        label, cmd, next_cmd, _ = line.children
        if cmd.data == 'var':
            var, expr = cmd.children
            print(f'  VAR: {var} = {expr.children[0]}')
        elif cmd.data == 'cmd':
            cmdname, mod, args = cmd.children
            args = [a.children[0] for a in args.children]
            if cmdname.startswith('PROM'):
                print(args[0].strip('" '))
            elif cmdname.startswith('INP'):
                v = input('?')
            elif cmdname == 'COPY':
                src, dst = args
                print(f' COPY {src} to {dst}')
                orig = self.pictures.get(src)
                if orig:
                    self.pictures[dst] = orig.copy(dst)
            elif cmdname == 'GETDSK':
                # mod = /P means do not display yet, just load points
                if mod:
                    print(f'  GETDSK mod: {mod}')
                arg = args[0]
                print('GETDSK', mod, arg)
                p = Picture()
                p.from_file(arg)
                self.pictures[p.name] = p
                print('POINTS:', p.points)
                p.show()
            elif cmdname == 'PUTDSK':
                arg = args[0]
                p = self.pictures.get(arg)
                print(f'Trying to save {arg}...{p}')
                if p:
                    p.show()
            else:
                print(f'  Unimplmented CMD: {cmdname}')


def main():
    sourcefile = sys.argv[1]
    dirpath = os.path.dirname(sourcefile)
    with open(sourcefile, 'r') as f:
        source = f.read()
    if dirpath:
        os.chdir(dirpath)
    parser = Lark(grass_grammar)
    parse_tree = parser.parse(source)
    print(parse_tree.pretty())
    env = GrassEnv(parse_tree)
    env.run()


if __name__ == '__main__':
    main()
