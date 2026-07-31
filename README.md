# GRASS
[![Tests](https://github.com/hornc/GRASS/actions/workflows/test.yml/badge.svg)](https://github.com/hornc/GRASS/actions/workflows/test.yml)

[Tom Defanti](https://en.wikipedia.org/wiki/Thomas_A._DeFanti)'s "real time computer language" "Grass" (1974)

* https://www.evl.uic.edu/dan/GRASS.html
* https://en.wikipedia.org/wiki/GRASS_(programming_language)

A BASIC style language used for 2D vector animation.

### Goals
* grammar parsing for the earlier versions of GRASS for the analog, real-time performance aspects (i.e. less ZGRASS, but figuring out the differences would be helpful)
* details of Vector General displays: hardware, timing, control, character font, terminology &c

### Resources / references
* T.A. DeFanti, ["The Digital Component of the Circle Graphics Habitat,"](https://www2.evl.uic.edu/documents/cgh-defanti.pdf) Proceedings of the National Computer Conference, 1976.
* https://dl.acm.org/doi/10.1145/965139.807366
* DeFanti, Thomas (November 1980). ["Language Control Structures for Easy Electronic Visualization"](https://archive.org/details/byte-magazine-1980-11-rescan/page/n91/mode/2up). BYTE.


`PROG1.MAC` program listing in T.A. DeFanti, D.J. Sandin, and R. Ainsworth, "Control Structures for Performance Graphics," SIGPLAN Notices, Vol. II, No. 6, 6/76 

`.MAC` = 'macro'

#### Vector General
This project includes a [Vector General assembler](VEC_GEN) to compile Vector General style op-codes to binary for the shared DMA expected by the displays.
This _might_ be a first step towards creating a display emulator.

I believe GRASS used compiled Vector General drawing instructions for its on-disk PICTURE objects. Discovering the format of these was the main purpose of the assembler.
_All_ of the original GRASS worked by forming Vector General instructions, so there is a path towards re-implementing every GRASS operation in terms of Vector General shared DMA, rather than just simulating it at a higher level, which is where I started with my Python code, and what ZGRASS did with its raster graphics implementation.

PDP-11/45  with [Vector General](https://en.wikipedia.org/wiki/Vector_General) 3DR display scope:
* https://archive.org/details/bitsavers_vectorGenephicsDisplaySystemReferenceManualJan72_6676862
* https://archive.org/details/designmanualforv00thor
* https://archive.org/details/usersmanualforve00thorpdf

___
c.horn 2026
