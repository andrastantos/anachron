Pinouts
=======

According to https://en.wikipedia.org/wiki/Dual_in-line_package:

Common DIP package pin counts are: 24, 28, 32, and 40; less common are 36, 48, 52, and 64. So if we blow over 40 pins, the next step up is 48.

Classic I/O
-----------

========== =========== ===========
Pin Number Pin Name    Description
========== =========== ===========
1          D0          Data bus
2          D1          Data bus
3          D2          Data bus
4          D3          Data bus
5          D4          Data bus
6          D5          Data bus
7          D6          Data bus
8          D7          Data bus
9          A0          Register address bus (data/command port select)
10         nCS         Active low chip-select for register accesses
11         nWE         Active low register write-enable input
12         nRST        Active low reset input
13         nINT        Open collector, active low interrupt output
14         SYS_CLK     System clock input
15         PA_0_EN1_A  Port A bit 0; Quadrature encoder 1 input A
16         PA_1_EN1_B  Port A bit 1; Quadrature encoder 1 input B
17         PA_2_EN2_A  Port A bit 2; Quadrature encoder 2 input A
18         PA_3_EN2_B  Port A bit 3; Quadrature encoder 2 input B
19         PA_4_TMR1   Port A bit 4; Timer input/output 1
20         PA_5_TMR2   Port A bit 5; Timer input/output 2
21         PA_6_SDA    Port A bit 6; I2C data
22         PA_7_SCL    Port A bit 7; I2C clock
23         PB_0_EN2_A  Port B bit 0; Quadrature encoder 3 input A
24         PB_1_EN2_B  Port B bit 1; Quadrature encoder 3 input B
25         PB_2_EN3_A  Port B bit 2; Quadrature encoder 4 input A
26         PB_3_EN3_B  Port B bit 3; Quadrature encoder 4 input B
27         PB_4_TMR2   Port B bit 4; Timer input/output 3
28         PB_5_TMR3   Port B bit 5; Timer input/output 4
29         PB_6        Port B bit 6;
30         PB_7        Port B bit 7;
31         PC_0_TXD    Port C bit 0; serial RX
32         PC_1_RXD    Port C bit 1; serial TX
33         PC_2_RST    Port C bit 2; serial RST/TX_EN
34         PC_3_CTS    Port C bit 3; serial CST
35         PC_4_KB_C   Port C but 4; PS/2 keyboard port clock pin
36         PC_5_KB_D   Port C but 5; PS/2 keyboard port data pin
37         PC_6_MS_C   Port C but 6; PS/2 mouse port clock pin
38         PC_7_MS_D   Port C but 7; PS/2 mouse port data pin
39         VCC         Power input
40         GND         Ground input
========== =========== ===========

Nuvou I/O
---------

========== =========== ===========
Pin Number Pin Name    Description
========== =========== ===========
1          A0          Address bus
2          A1          Address bus
3          A2          Address bus
4          A3          Address bus
5          D0          Data bus
6          D1          Data bus
7          D2          Data bus
8          D3          Data bus
9          D4          Data bus
10         D5          Data bus
11         D6          Data bus
12         D7          Data bus
13         nDRQ        Active low DMA request
14         nDACK       Active low DMA response
15         nDMA_TC     DMA terminal count
16         nCS         Active low chip select
17         nWE         Active low write-enable
18         SYS_CLK     Clock input
19         nRST        Active low reset input
20         nINT        Active low interrupt output
21         D+          USB D+
22         D-          USB D-
23         SD_D0       SD card connector
24         SD_D1       SD card connector
25         SD_D2       SD card connector
26         SD_D3       SD card connector
27         SD_CMD      SD card connector
28         SD_CLK      SD card connector
29         XTAL_IN     48MHz crystal oscillator pins
30         XTAL_OUT    48MHz crystal oscillator pins
31         PA_0_TXD    Port A bit 0; serial RX
32         PA_1_RXD    Port A bit 1; serial TX
33         PA_2_RST    Port A bit 2; serial RST/TX_EN
34         PA_3_CTS    Port A bit 3; serial CST
35         PA_4_KB_C   Port A but 4; PS/2 keyboard port clock pin
36         PA_5_KB_D   Port A but 5; PS/2 keyboard port data pin
37         PA_6_SDA    Port A bit 6; I2C data
38         PA_7_SCL    Port A bit 7; I2C clock
39         VCC         Power input
40         GND         Ground input
========== =========== ===========


Combined graphics/sound
-----------------------

========== ============= ========== ===========
Pin Number Pin Name      IO std.    Description
========== ============= ========== ===========
1          A8_0          3.3V out   Multiplexed address bus
2          A9_1          3.3V out   Multiplexed address bus
3          A10_2         3.3V out   Multiplexed address bus
4          A11_3         3.3V out   Multiplexed address bus
5          A12_4         3.3V out   Multiplexed address bus
6          A13_5         3.3V out   Multiplexed address bus
7          A14_6         3.3V out   Multiplexed address bus
8          A15_7         3.3V out   Multiplexed address bus
9          A17_16        3.3V out   Multiplexed address bus
10         A19_18        3.3V out   Multiplexed address bus
11         A20_21        3.3V out   Multiplexed address bus
12         D0            3.3V io    Data bus
13         D1            3.3V io    Data bus
14         D2            3.3V io    Data bus
15         D3            3.3V io    Data bus
16         D4            3.3V io    Data bus
17         D5            3.3V io    Data bus
18         D6            3.3V io    Data bus
19         D7            3.3V io    Data bus
20         nRAS_A        3.3V out   Active low row-select, bank A
21         nRAS_B        3.3V out   Active low row-select, bank B
22         nCAS_0        3.3V out   Active low column select, byte 0
23         nCAS_1        3.3V out   Active low column select, byte 1
24         nWE           3.3V out   Active low write-enable
25         SYS_CLK       3.3V out   Clock output
26         nRST          3.3V in    Active low reset input
27         nINT          3.3V out   Active low interrupt output
28         nBREQ         3.3V out   Active low bus-request output
29         nBGRANT       3.3V in    Active low bus-grant input
30         nREG_CS       3.3V in    Active low chip-select for register accesses
31         R             ANALOG     Analog 'red' channel output
32         G             ANALOG     Analog 'green' channel output
33         B             ANALOG     Analog 'blue' channel output
34         HSYNC         3.3V out   Horizontal video sync output with programmable polarity
35         VSYNC         3.3V out   Vertical video sync output with programmable polarity
36         AUD_L_OUT     ANALOG     Audio output left channel
37         AUD_R_OUT/IN  ANALOG     Audio output right channel; audio input
38         CLK_IN        3.3V in    28.63636MHz crystal oscillator pins
39         VCC           3.3V PWR   Power input
40         GND           GND        Ground input
========== ============= ========== ===========


Bus extender
------------

========== =========== ===========
Pin Number Pin Name    Description
========== =========== ===========
1          A8_0        Multiplexed address bus
2          A9_1        Multiplexed address bus
3          A10_2       Multiplexed address bus
4          A11_3       Multiplexed address bus
5          A12_4       Multiplexed address bus
6          A13_5       Multiplexed address bus
7          A14_6       Multiplexed address bus
8          A15_7       Multiplexed address bus
9          A17_16      Multiplexed address bus
10         A19_18      Multiplexed address bus, nRAS_C for bank C
11         A20_21      Multiplexed address bus, nRAS_D for bank D
12         D0          Data bus
13         D1          Data bus
14         D2          Data bus
15         D3          Data bus
16         D4          Data bus
17         D5          Data bus
18         D6          Data bus
19         D7          Data bus
20         nRAS_A      Active low row-select, bank A
21         nRAS_B      Active low row-select, bank B
22         nCAS_0      Active low column select, byte 0
23         nCAS_1      Active low column select, byte 1
24         nWE         Active low write-enable
25         SYS_CLK     Clock input
26         nRST        Active low reset input
27         nINT        Active low interrupt output
28         nBREQ_IN    Active low bus-request daisy-chain input
29         nBREQ_OUT   Active low bus-request daisy-chain output
30         nBGRANT     Active low bus-grant input
31         nWAIT       Active low wait-state output
32         nREG_CS     Active low chip-select for register accesses
33         nDRQ_A      DMA channel A request input
34         nDACK_A     DMA channel A acknowledge output
35         nDRQ_B      DMA channel B request input
36         nDACK_B     DMA channel B acknowledge output
37         nDRQ_C      DMA channel C request input
38         nDACK_C     DMA channel C acknowledge output
39         DMA_TC      DMA terminal count output
41         IRQ_A       Interrupt signal A
42         IRQ_B       Interrupt signal B
43         IRQ_C       Interrupt signal C
44         IRQ_D       Interrupt signal D
45         IRQ_E       Interrupt signal E
46
47         VCC         Power input
48         GND         Ground input
========== =========== ===========


How to make chips at home?
==========================

FPGAs, of course. Right now, it seems that Brew V1 synthesizes into ~800ALMs (LUTs) in a Cyclone V. Assuming a LUT is a LUT (not fair, depends on the number of inputs), any device with about 1000 to 2000 LUTs should fit the CPU. We also assume that the CPU is the biggest custom chip we would ever make, this same FPGA should fit all custom chips.

Looking at the landscape, the following devices seem to work well:

- Any of the MAX10 family, even the smallest one. However, these are *very* expensive, something around $30.
- ICE40LP1k from Lattice at $5.5
- T8Q144C3 from Efinix at $6.6
- LCMXO3L-4300E from Lattice at $7.7
- GoWin 1N FPGAs, probably the 4k or the 9k devices.

These are all 3.3V compatible parts, but only the latest lists LVTTL compatibility. However, LVTTL and LVCMOS33 is the same, it seems. Even the Mach3 chip can't take truly 5V inputs. So maybe that's another reason to require serial resistors on the DRAM data lines (and protection diodes). After all, those will be the only truly old parts in the real system. However, there seem to be 'modern' 3.3V FPM DRAMs (https://www.digikey.com/htmldatasheets/production/1700164/0/0/1/MSM51V17400F.pdf for instance).

All right, so we have 3.3V I/O and we're cool with that. We might have to build our own memory modules (after all SMD chips were not common back then). 30-pin sockets are not readily available anymore (eBay, others still carry it, but do we want to depend on them)? We can have the equivalent using single-row headers though, so no sweat.

These 3.3V memories are rather large, the above one is 16Mbit device in 4Mx4 config. So, qin a 16-bit (dual-bank) setup, that would create 8MByte of DRAM. That's 11 address lines: A0-A10. Righ now, we have only 9, but with the reduction of the data-bus to 8-bits, we can affort the extra address pin, at least on the CPU.

Universal Chips (UniC)
======================

An interesting idea is to make an FPGA-based chip, that can pretend to be anything.

Logic levels allow for a 3.3V I/O to be TTL compatible, provided we take care of the above-the-limit voltages:

https://en.wikipedia.org/wiki/7400-series_integrated_circuits#/media/File:Niveaux_logiques_CMOS-TTL-LVTTL.png

This can be done by a series 330 ohm resistor and a diode towards VCC. The resistor will limit the current to 5mA on the driver, if it hard-pulls to 5V. The resistor also (unfortunately) slows the transitions down, but hopefully not to the level where it's problematic: the RC constant with a 10pF load is 3.3ns, which is half the propagation delay of a single LS gate.

Power is more problematic: we don't know where the GND and VDD pins on the to-be-simulated package are. What we can do is to provide a pair of (Schottky) diodes towards the internal VDD and GND from each pin. These diodes would be on the 'outer' pin of the 330 ohm resistor and tied together on the top and bottom to provide my internal VDD and GND. This setup is tested in LTSpice and seems to work, albeit shifts the GND by maybe as much as 0.4V.

An LDO can then generate VCC from VDD. Due to the GND-shift, maybe it's better to generate a somewhat lower VCC, maybe 3.1V or so. That would split the difference in half.

There is a part (74S107 or something) that contains the right diode arrangement for 16 pins, though it might be a bit too large (TSSOP20 is the best it can do). There are quad-diode packages (2 pins worth) as well in the BV56 family.

We can add a tiny OLED display (https://www.ebay.com/itm/293291361583 for instance) to the top for fun displaying of the part number being emulated, maybe even small animations.

The PCB could be covered by a 3D printed snap-on plastic cover, pretending to be a DIP package.

Programming ideally would be done through USB, with a USB connector on one end of the package, but that might be a little too expensive, especially since that would need an FTDI chip of sorts as well.
