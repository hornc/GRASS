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


def test_control_display_instructions():
    source = """
        NOP
        *NOP  ; NOP with P-bit set
        SPC
        HLT
    """
    expected_words = [
        0x0000,
        0x8000,
        0x2000,
        0x3000,
    ]
    parse_tree = parser.parse(source)
    r = transformer.transform(parse_tree)
    assert isinstance(r, Tree)
    assert hex_list([v['word'] for v in r.children]) == hex_list(expected_words)


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
    case('4. Load register, labelled, set P-bit, multi-list, negative values #1',
        """
        TRANS1:*LD, CSR         ; LOAD BEGINNING WITH SCALE
                1023            ; CSR: HALF SCALE
               -512             ; DXR: -1/4 OFFSET LEFT
               -512, T          ; DYR: -1/4 OFFSET DOWN
        """,
        [0xC013, 0x3FF0, 0xE000, 0xE001]
    ),
    case('5. Load register, labelled, multi-list, negative values #2',
        """
        ZIGZAG: LD, XR          ; LOAD STARTING WITH X-COORD
               -1024            ; LOAD X COORDINATE WITH HALF FS
                0, T            ; LOAD Y COORDINATE WITH ZERO
        """,
        [0x4008, 0xC000, 0x0001]
    ),
    case('6. Another simple LD',
        """
        LD, AIR                 ; LOAD INCREMENT REGISTER
        127, T                  ; WITH 127
        """,
        [0x400B, 0x07F1]
    ),
    case('7. Multi-list LD',
        """
        TRANS2:*LD, CSR         ; LOAD BEGINNING WITH COORD SCALE
                511             ; LOAD CSR
                1023            ; LOAD DXR
                1023, T         ; LOAD DYR
        """,
        [0xC013, 0x1FF0, 0x3FF0, 0x3FF1]
    ),
]


@pytest.mark.parametrize("source,expected_words", ld_cases)
def test_LD_instruction(source, expected_words):
    parse_tree = parser.parse(source)
    r = transformer.transform(parse_tree)
    assert hex_list([v['word'] for v in r.children]) == hex_list(expected_words)


va_cases = [
    case('VA.1. Vector Absolute Display Write Instruction, single 12bit values per data list word',
        """
        BOX:    VA              ; VECTOR ABSOLUTE INSTRUCTION
               -2048, L, X      ; LOAD X COORDINATE
               -2048, M, Y      ; LOAD Y COORDINATE AND MOVE
                2047, D, X      ; LOAD X COORDINATE AND DRAW
                2047, D, Y      ; LOAD Y COORDINATE AND DRAW
               -2048, D, X      ; LOAD X COORDINATE AND DRAW
               -2048, DT, Y     ; LOAD Y COORDINATE, DRAW AND TERMINATE
        """,
        [0x1004, 0x8001, 0x800A, 0x7FF5, 0x7FF6, 0x8005, 0x800E]
    ),
]


@pytest.mark.parametrize("source,expected_words", va_cases)
def test_VA_instruction(source, expected_words):
    parse_tree = parser.parse(source)
    r = transformer.transform(parse_tree)
    assert hex_list([v['word'] for v in r.children]) == hex_list(expected_words)


inc_vec_cases = [
    case('Incremental Vectors 2D',
        """
        *DVYY                   ; 2D VECTOR INCREMENTAL, X AUTOINCREMENT
        +255, M, +255           ; MOVE Y
        +255, D, -255           ; INCREMENT X, DRAW Y
        +255, D, -255, T        ; INCREMENT X, DRAW Y AND TERMINATE
        """,
        [0x9009, 0x7E7E, 0x7F82, 0x7F83]
    ),
]


@pytest.mark.parametrize("source,expected_words", inc_vec_cases)
def test_inc_vec_instruction(source, expected_words):
    parse_tree = parser.parse(source)
    r = transformer.transform(parse_tree)
    assert hex_list([v['word'] for v in r.children]) == hex_list(expected_words)
