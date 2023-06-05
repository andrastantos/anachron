


Comparison
~~~~~~~~~~

A bit old, but a good idea for pricing of processors in the era:

http://www.bitsavers.org/components/edn/EDN-4th-annual-microprocessor-directory-Nov20-1977.pdf

8080: $10, 8085: $20
6502: $10
6800: $20
PIC1650/1655/1670: $20 (2500) $4 (100k)
Z80: $20

MIPS comparison
~~~~~~~~~~~~~~~

Source: https://en.wikipedia.org/wiki/Instructions_per_second

==============   ========   =========
Chip             Year       MIPS/MHz
==============   ========   =========
6502             1977       0.43
Z80              1976       0.145
Intel 8088       1979       0.075
MC68000          1979       0.175
Intel 80286      1982       0.107
MC68010          1984       0.193
MC68020          1984       0.303
Intel 80386      1985       0.134
ARM2             1986       0.5
MC68040          1987       0.36
Intel 80486      1989       0.3
==============   ========   =========

There seems to be a good micro-computer comparison table here: https://drolez.com/retro/

I'm currently standing at 0.23, slightly better then the competition, but not enormously.

The *main* reason for us not being faster is that the memory bus is busy. At least that's what it appears to be.
Now, that's not to say, it's doing useful work: we might be constantly fetching stuff that we'll discard.

Synthesis results
~~~~~~~~~~~~~~~~~

Now that the V1 design is more or less complete, here are some stats:

Using the OpenRoad toolchain and sky130hd PDK, the core area is 0.176mm^2.

============== =============    ========  ==========================================================================================
Core die area   Fmax             Node      Comparison (source: https://en.wikipedia.org/wiki/Transistor_count#Transistor_density)
============== =============    ========  ==========================================================================================
0.176mm^2       100MHz           130nm
0.148mm^2                        130nm     without multiplier and shifter
23mm^2          8.6MHz           1.5um     49mm^2 for 80286
41mm^2          6.5MHz           2um
93mm^2          4.3MHz           3um       60mm^2 for 80186; 33mm^2 for 8088
============== =============    ========  ==========================================================================================

According to http://www.bitsavers.org/components/rockwell/Trends_in_Microcomputer_Technology_1977.pdf people estimated 40,000mil^2 (62mm^2) dies to be economical in the early '80s. This is to say, that this processor would be rather cheap, if manufactured in 1.5 or 2u process nodes. 3u is not really feasible not just for die-size, but for speed reasons as well: 8-10MHz processors all only appeared in the 1.5u node. 3u node manufacturing tapped out at around 5MHz; too slow for our needs.

Timing-wise, the design seems to be closing at 100MHz (though I'm not quite sure about my constraints) at 130nm. If that's true, we are on target to hit about 8MHz in 1.5u. FPGA-based timing closure is all over the map, making me nervous about the accuracy of these results.

IO cells are apparently missing from the sky130 PDK. The gf180 PDF has them. Here's some data:

https://gf180mcu-pdk.readthedocs.io/en/latest/IPs/IO/gf180mcu_fd_io/features.html#cell-dimensions

Bond-pad guidelines are here:

https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_09_2.html

From these, I'm guessing that a basic I/O pad is 350x75um large. My expectation is that this includes the bond-pad and that these sizes
won't change all that much with technology. This is a rather standard size, including power pins as well.

So, a 40-pin package would need 750x350um I/O region on each side. The chip would be 1350um x 1350um, the total I/O area (with corners) is 1.4mm^2. The core area is 0.56mm^2.

Our little core in 130nm would be totally I/O limited, but in our target node, I/O is a rounding error: the chip is totally core-limited.

https://lnf-wiki.eecs.umich.edu/wiki/Wire_bonding confirms that ~60ux60u bond pads are OK (they claim 75x75, but oh, well).

RAMs
~~~~

I finally have found a RAM example for the sky130 SDK: it's a 32x1024bit RAM (single-ported, 6T cells).

https://github.com/ShonTaware/SRAM_SKY130#openram-configuration-for-skywater-sky130-pdks

It's size is 0.534mm^2, closes timing at about 80MHz. Back-scaling it to 1.5u, gives us a scaling factor of 133:1.

Taking all of this, gives us 71mm^2 for this 32kbit SRAM or 0.00217mm^2/bit.

What if we wanted to add a 1kByte ICache to the system? That would take 17.78mm^2, just for the SRAM array. In other words, we can expect our die-area to double even with a single 1kB of ICache. So, no ICache for sure!