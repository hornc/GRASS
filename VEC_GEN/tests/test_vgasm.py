from vgasm import vg_grammar, VGTransformer
from lark import Lark, Tree

parser = Lark(vg_grammar)
transformer = VGTransformer()


def test_single_statement():
    """
    Single statement returns a dict.
    """
    source = """
    LD, MCR                 ; LOAD MODE CONTROL
    """
    parse_tree = parser.parse(source)
    r = transformer.transform(parse_tree)
    print('Result:', r)
    assert isinstance(r, dict)
    assert r['word'] == 0x4005


def test_multiple_statements():
    """
    Multiple statements return a Tree, with lines as children
    """
    source = """
    LD, MCR                 ; LOAD MODE CONTROL
    MS1, MED, T             ; ENABLE DISPLAY INTERRUPT
    LD, IOR                 ; LOAD INTENSITY
    2047, T                 ; FULL SCALE BRIGHT
    """
    expected = [
            0x4005,
            0x8081,
            0x400C,
            0x7FF1,
    ]
    parse_tree = parser.parse(source)
    r = transformer.transform(parse_tree)
    assert isinstance(r, Tree)
    print('Result:', r)
    
    assert isinstance(r.children, list)
    assert [v['word'] for v in r.children] == expected

