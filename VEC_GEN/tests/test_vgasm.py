from vgasm import vg_grammar, VGTransformer
from lark import Lark, Tree

import pytest

parser = Lark(vg_grammar)
transformer = VGTransformer()


# Test case helper:
def case(id_, *args, **kwargs):
    return pytest.param(*args, id=id_, **kwargs)


def hex_list(vals):
    #return [f'{v:016b}' for v in vals]  # binary output
    return [f'{v:04X}' for v in vals]   # hex out


def test_single_statement():
    """
    Single statement returns a dict.
    """
    source = """
    LD, MCR                 ; LOAD MODE CONTROL
    """
    parse_tree = parser.parse(source)
    r = transformer.transform(parse_tree)
    assert isinstance(r, dict)
    assert r['word'] == 0x4005


# TODO: this is now covered in the LD param tests below...
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


ld_cases = [
    case('0. Empty source',
        """
        """,
        []
    ),
    case('1. Load Mode Control Register (MCR), set interrupts',
        """
        LD, MCR                 ; LOAD MODE CONTROL
        MS1, MED, T             ; ENABLE DISPLAY INTERRUPT
        """,
        [0x4005, 0x8081]
    ),
    case('2. Load Intensity',
        """
        LD, IOR                 ; LOAD INTENSITY
        2047, T                 ; FULL SCALE BRIGHT
        """,
        [0x400C, 0x7FF1]
    ),
    case('3. Load Register, with interrupt (P-bit set via *)',
        """
        *LD, PSR                 ; LOAD PICTURE SCALE
        1023, T                 ; HALF SCALE
        """,
        [0xC011, 0x3FF1]
    ),
    case('4. Load register, labelled, multi-list, negative values, #1',
        """
        TRANS1:*LD, CSR                 ; LOAD BEGINNING WITH SCALE
                1023                    ; CSR: HALF SCALE
               -511                     ; DXR: -1/4 OFFSET LEFT
               -511, T                  ; DYR: -1/4 OFFSET DOWN
        """,
        [0xC013, 0x3FF0, 0x8000, 0x8001]
    ),
    case('5. Load register, labelled, multi-list, negative values, #2',
        """
        ZIGZAG: LD, XR                  ; LOAD STARTING WITH X-COORD
               -2048                    ; LOAD X COORDINATE WITH HALF FS
                0, T                    ; LOAD Y COORDINATE WITH ZERO
        """,
        [0x4008, 0xC000, 0x0001]
    ),
    case('6. Another simple LD',
        """
        LD, AIR                 ; LOAD INCREMENT REGISTER
        255, T                  ; WITH 255
        """,
        [0x400B, 0x07F1]
    ),
    case('7. Multi-list LD',
        """
        TRANS2:*LD, CSR                 ; LOAD BEGINNING WITH COORD SCALE
                1008                    ; LOAD CSR
                1023                    ; LOAD DXR
                1023, T                 ; LOAD DYR
        """,
        [0xC013, 0x1FF0, 0x3FF0, 0x3FF1]
    ),
]


@pytest.mark.parametrize("source,expected_words", ld_cases)
def test_LD_instruction(source, expected_words):
    parse_tree = parser.parse(source)
    r = transformer.transform(parse_tree)
    assert hex_list([v['word'] for v in r.children]) == hex_list(expected_words)
