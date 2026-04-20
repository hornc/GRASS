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
?start: (line | COMMENT | _NL)+

line: [LABEL] command_sequence [COMMENT] _NL

command_sequence: command (";" command)*
command: VARIABLE "=" expression -> var
       | COMMAND[MODIFIER] [arglist] -> cmd
       | "IF" variable condition ifexpression "," command -> cond

arglist: argument ("," argument)*
argument: variable | INT | PIXNAME | STRING | LABEL

variable: VAR_STRING | DIAL | SLIDE | VARIABLE


expression: INT | EXPR
ifexpression: INT | IFEXPR
condition: "=" | "EQ" -> eq
         | "GT"       -> gt
         | "LT"       -> lt

EXPR: /[^\n]+/x
IFEXPR: /[^,]+/

COMMAND: /[A-Z]{2,}/
MODIFIER: "/" /[A-Z]/

LABEL: "%" /[A-Z]+/

PIXNAME: /[A-Z0-9]{3,}/
VARIABLE: /[$A-Z]{1,2}/
VAR_STRING: /$[A-Z]/
VAR_FIXED: /[VW]?[A-Z]/
VAR_FLOAT: /F[A-Z]/
DIAL: /D[0-9]/
SLIDE: /S[0-9]/
JOYSTICK: /[JK][XYX]/

COMMENT: "*" /.+/

%import common.WS_INLINE
%import common.SIGNED_INT -> INT
%import common.ESCAPED_STRING -> STRING
%import common.NEWLINE -> _NL
%ignore WS_INLINE
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
        return [[x*sx+mx, y*sy+my, z*sz+mz] for x, y, z in self.points]

    def from_file(self, fname):
        # load points from file
        self.name = fname.strip()
        with open(self.name, 'r') as f:
            for row in f:
                x, y, z = [int(v) for v in row.strip().split(',')]
                self.points.append([x, y, z])

    def save(self):
        print(f'Trying to save {self.name}...{self}')
        with open(self.name, 'w') as f:
            for row in self.points:
                f.write(', '.join([str(v) for v in row]) + '\n')

    def show(self):
        ax = plt.figure().add_subplot(projection='3d')
        x, y, z = zip(*self.get_points())
        ax.plot(x, z, y, label=self.name)
        ax.set(xlabel='X', ylabel='Z', zlabel='Y')
        ax.yaxis.set_inverted(True)
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
        label, cmds, _ = line.children
        for cmd in cmds.children:
            if cmd.data == 'var':
                var, expr = cmd.children
                print(f'  VAR: {var} = {expr.children}')
                v = self.evaluate(expr)
                self.set_var(var, v)
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
                    p = self.pictures.get(args[0])
                    if p:
                        p.show()
                        p.save()
                elif cmdname == 'SCALE':
                    print('SCALE:', args)
                    pix, scale = args
                    n = self.get_val(scale) or 1
                    p = self.pictures.get(pix)
                    p.scale = [n, n, n]
                elif cmdname == 'MOVE':
                    print('MOVE: ', args)
                    pix, x, y, z = args
                    p = self.pictures.get(pix)
                    p.move = [self.get_val(v) for v in [x, y, z]]
                else:
                    print(f'  Unimplmented CMD: {cmdname}')

    def evaluate(self, expr):
        print(f'EVAL: {expr} : {len(expr.children)} "{expr.children}"')
        if len(expr.children) == 1 and expr.children[0].type == 'INT':
            return int(expr.children[0])
        print(f'  EXPRESSION {expr} not yet evaluatable!')
        return None

    def get_val(self, value):
        if hasattr(value, 'data') and  value.data == 'variable':
            return self.variables.get(value)
        if value.type == 'INT':
            return int(value)

    def set_var(self, name, value):
        self.variables[name] = value
        return self.variables.get(name)


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
