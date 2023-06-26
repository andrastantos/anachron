System considerations
=====================

High level specs
~~~~~~~~~~~~~~~~

For the processor:

* Internal data-path: 32-bit
* External data width: 8/16-bit
* Clock speed: ~10MHz (depends on DRAM speed)
* IPC: 0.3 sustained with graphics, 1 peak

Memory:

* Data width: 16-bit
* Size: 128kB to 16MB
* Number of banks: 2
* Technology: Page mode DRAM

Graphics:

* Resolution:
   * 320x240, 8 bits per pixel, 60Hz frame rate, 6.25MHz pixel clock rate
   * 640x240, 4 bits per pixel, 60Hz frame rate, 12.5MHz pixel clock rate
   * 640x480, 4 bits per pixel, 30Hz frame rate (interlaced), 12.5MHz pixel clock rate
* Number of colors: 5-bit per channel; 32768 total colors
* Sprites: 8 sprites
   * 32xN pixels, 1 bit/pixel (0: transparent)
   * 16xN pixels, 2 bits/pixel (0: transparent)
   * 8xN pixels, 4 bits/pixel (0: transparent)

Sound:

* 8 mono sampling sound channels
   * Independent panning control
   * Independent volume control
   * Re-sampling
   * Looping support
   * 8-bit/sample resolution
* Stereo output

Storage:

* 720k, 3.5" floppy drive (PC compatible)

Communication and networking:

* LAN through RS-485
* WAN through modem over RS-232

Human interface:

* Keyboard
* Mouse
* Joystick (switch-based)
* Joystick (analog)

Memory map
~~~~~~~~~~

=============  ===========  ===========
Start address  End address  Description
=============  ===========  ===========
0x000_0000     0x01f_ffff   EEPROM space 1 (and boot code from address 0)
0x020_0000     0x03f_ffff   EEPROM space 2
0x040_0000     0x05f_ffff   internal I/O space
0x060_0000     0x06f_ffff   ISA extension bus I/O address space
0x070_0000     0x07f_ffff   ISA extension bus memory address space
0x400_0000     0x3ff_ffff   CSR space: not decoded externally, but handled by the processor internally
0x800_0000     0x8ff_ffff   DRAM space (up to 16MByte)
=============  ===========  ===========

.. note::
    Address bits 29...26 select number of wait-states for every address. That is to say, each region has 16 aliases.
    DRAM and CSR space ignores the wait-state setting, but still alias the addresses 16 times.

Chipsets and Model lineup
~~~~~~~~~~~~~~~~~~~~~~~~~

All-in-one setup (A500 layout)
------------------------------

* custom CPU+DMA
* custom Graphics+sound
* custom Classic I/O 1 (mouse/joystick/serial/I2C)
* custom Classic I/O 2 (keyboard scan/centronics/RS-485)
* FDD

Expandable setup (A1000 layout)
-------------------------------

* custom CPU+DMA
* custom Graphics+sound
* custom Classic I/O 1 (mouse/joystick/serial/external keyboard)
* custom Classic I/O 2 (keyboard scan/centronics/RS-485)
* ISA-bus interface
* SCSI
* FDD

All-in-one setup (modern A500 layout)
-------------------------------------

* custom CPU+DMA
* custom Graphics+sound
* custom Nouveau I/O (keyboard/joystick/mouse over USB; SDCard; serial/sysconfig/I2C)
* custom Classic I/O (keyboard scan, unless done through USB)

Expandable setup (modern A1000 layout)
--------------------------------------

* custom CPU+DMA
* custom Graphics+sound
* custom Nouveau I/O 2 (keyboard/joystick/mouse over USB; SDCard; serial/sysconfig/I2C)
* ISA-bus interface (maybe custom interface chip, maybe custom Classic I/O)


Clocking
~~~~~~~~

We will stay with the very common NTSC clock rate of 28.63636MHz (double of what Amiga had). On top of that, we'll need 48MHz for USB (on Nouveau I/O of course)

* 28.63636MHz/2   -> Video clock (14.31818MHz)
* 28.63636MHz/3   -> system clock (~9.54MHz) <-- supports -10 DRAM
* 28.63636MHz/4   -> alternate system clock (~7.16MHz) <-- supports -12 DRAM
* 28.63636MHz/3.5 -> alternate system clock (~8.18MHz) <-- supports -12 DRAM, but needs a PLL, which wasn't really a thing back then, not at these frequencies at least.
* 28.63636MHz/3   -> Audio clock option l (37.28kHz Fs)
* 28.63636MHz/4   -> Audio clock option 2 (27.96kHz Fs)

An alternative would be to use an additional clock source for the system clock (which would allow for highest memory bandwidth and CPU perf.)
We could even add a third (audio) clock, or at least the option to use either clock for audio.

This is getting mad. I think the right answer is the following:

14.31818MHz clock source for video and audio (27.96kHz sampling rate); In actual implementation, probably twice of that so that VGA doesn't get terribly angry
6.6/8.3/10/12.5MHz clock source for system

These would be two different clocks, provided by three different crystals/oscillators. It's unclear whether a simple 74f04 based oscillator would work. The CMOS version (unbuffered mostly) should, but TTL is different enough that it might not. CMOS inverters of the day (CD4069) were *way* too slow to build inverters in these clock-ranges. Also, there would need to be a schmidt-trigger stage afterwards to create proper signal levels. So that would be two packages for this purpose. It would probably have been cheaper and certainly easier to use oscillators.

For USB, a third clock source of 48MHz is needed, but that is an XTAL connected to I/o Nouveau. clock source for USB

ISA bus notes
~~~~~~~~~~~~~

*VGA* cards used both memory and I/O, but really nothing beyond the first 1MB address range. They didn't use DMA. They might have used an interrupt
*Ethernet* cards used memory mapped ring buffers (I think) and I/O of course. Most were 16-bit, but no DMA and a few interrupts.
*Serial/parallel* cards used I/O and interrupt(s)
*IDE* interface used only a few I/O registers (16-bits) and (16-bit) DMA. It used a single interrupt line
*Sound* cards (at least Sound Blasters) used 16-bit I/O and (both 8- and 16-bot) DMA. They used interrupts as well.
*SCSI* cards are a bit tricky. Some Adaptec cards might even have been bus-masters. Others, such as the SYM20403 seems to have not even used DMAs. Many contained on-board BIOS, which of course is problematic.

DRAM interface
~~~~~~~~~~~~~~

There are up to 2 banks of DRAM, each divided into two 8-bit words. All DRAM pins are directly connected to the corresponding pins of the CPU and all other bus-masters.

While this would not have been the case (or possible really) in the old days, now a 3.3V level translator is necessary on the data lines. This is a single 74LVT245 device. Additional families to consider: AHCT (7ns), LVT (4.1ns), LVC (6ns)

Buffer stage
~~~~~~~~~~~~

Non-DRAM accesses go through a buffer stage to relieve the bus-masters from excessive loading. The exception is register access to other bus-masters: since the address and data-buses are already connected, only a single chip-select needs to be provided. This chip-select is decoded from the buffered addresses.

::
    nBCAS_0  <<= nCAS_0
    nBCAS_1  <<= nCAS_1
    nBWE     <<= nWE
    nBNREN   <<= nNREN

    BA12_1   <<= A11_0
    BA13_2   <<= A12_1
    BA14_3   <<= A13_2
    BA15_4   <<= A14_3

    BA16_5   <<= A15_4
    BA17_6   <<= A16_5
    BA18_7   <<= A17_6
    BA19_8   <<= A18_7

    BA20_9   <<= A19_8
    BA21_10  <<= A20_9
    BA22_11  <<= A21_10
    BDMA_TC  <<= DMA_TC

These buffers could be many things really, but most likely are going to be a pair of 74LS245 devices just to reduce part diversity.

.. note::
    nNREN does not have extensive loading on it, but it is still buffered to equalize delay between that and the address lines which it qualifies.

.. note::
    We are renaming buffered addresses: they are 16-bit addresses as they come out of the CPU, but we need byte-addresses on the buffered bus. We're also renaming the top three address bits to match what the actually do during non-DRAM accesses.

The data bus buffer is a bi-directional 74LS245 device. It is controlled by the following signals:

::
    ~nDACK    <<=   ~(nDACK_A & nDACK_B & nDACK_C & nDACK_D)
    DIR       <<=   nBWE ^ ~nDACK
    nOE       <<=   (nBNREN & nDACK) = ~(~nBNREN & ~nDACK)
    B0..B7    <<=>> D0..D7
    BD0..BD7  <<=>> A0..A7

.. note::
    The DMA controller generates addresses directly on the DRAM bus, but the data transfer is happening though the buffer and the requestor. Thus, during DMA operations, the buffer operates in the reverse direction compared to CPU cycles. Another consequence of this setup is that DMA can only happen to/from DRAM, not between I/O devices or memory-to-memory.

Address decode and address latching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We need to identify the two address cycles (nBAC_1 and nBAC_2):

::

    nBCAS  <<= nBCAS_0 & nBCAS_1 = ~(~(nBCAS_0 & nBCAS_1))
    nBAC_1 <<= nBNREN | ~nBCAS = ~(~nBNREN & nBCAS)
    nBAC_2 <<= nBNREN | nBCAS  = ~(~nBNREN & ~nBCAS)

Next, we'll need to latch the high-order address bits, using the first address cycle.

::

    BLA12 <<= latch(BA12_1,  nBAC_1)
    BLA13 <<= latch(BA13_2,  nBAC_1)
    BLA14 <<= latch(BA14_3,  nBAC_1)
    BLA15 <<= latch(BA15_4,  nBAC_1)
    BLA16 <<= latch(BA16_5,  nBAC_1)
    BLA17 <<= latch(BA17_6,  nBAC_1)
    BLA18 <<= latch(BA18_7,  nBAC_1)
    BLA19 <<= latch(BA19_8,  nBAC_1)

    BLA20 <<= latch(BA20_9,  nBAC_1)
    BLA21 <<= latch(BA21_10, nBAC_1)
    BLA22 <<= latch(BA22_11, nBAC_1)

This can be done by an 74LS373 and three quarters of a 74LS75.

We can also rename the renaming signals to create the bottom address bits:

    BA0  <<= nBCAS_0
    BA1  <<= BA9_1
    BA2  <<= BA10_2
    BA3  <<= BA11_3
    BA4  <<= BA12_4
    BA5  <<= BA13_5
    BA6  <<= BA14_6
    BA7  <<= BA15_7
    BA8  <<= BA16_8
    BA17 <<= BA18_17

This is just wires, no magic here. But it does help with further explanations.

We can now decode 4 address regions, 2MB each:

::

    nBROM1_SEL   <<= ~((BLA22 == 0) & (BLA21 == 0)) | nBNREN
    nBROM2_SEL   <<= ~((BLA22 == 0) & (BLA21 == 1)) | nBNREN
    nBIO_SEL     <<= ~((BLA22 == 1) & (BLA21 == 0)) | nBNREN
    nBISA_SEL    <<= ~((BLA22 == 1) & (BLA21 == 1)) | nBNREN

This can be done by one half of a 74LS139.

.. note:: We can qualify the decode simply with nBNREN. This is important as it buys us about 100ns of decode time.

I/O region can be further decoded:

::
    nGPIO0_SEL       <<= ~((BLS14 == 0) & (BLA13 == 0) & (BLA12 == 0)) | nBAC_2
    nGPIO1_SEL       <<= ~((BLS14 == 0) & (BLA13 == 0) & (BLA12 == 1)) | nBAC_2
    nGFX_SND_SEL     <<= ~((BLS14 == 0) & (BLA13 == 1) & (BLA12 == 0)) | nBAC_2
    nFDD_SEL         <<= ~((BLS14 == 0) & (BLA13 == 1) & (BLA12 == 1)) | nBAC_2
    nSCSI_SEL        <<= ~((BLS14 == 1) & (BLA13 == 0) & (BLA12 == 0)) | nBAC_2
    nCENT_DATA_SEL   <<= ~((BLS14 == 1) & (BLA13 == 0) & (BLA12 == 1)) | nBAC_2
    nKBD_SCAN_SEL    <<= ~((BLS14 == 1) & (BLA13 == 1) & (BLA12 == 0)) | nBAC_2
    nRTC_SEL         <<= ~((BLS14 == 1) & (BLA13 == 1) & (BLA12 == 1)) | nBAC_2

This is a 74LS138. Each section is 4k large to prepare for later MMUs. There are several aliases, but that's unadvised to be used: those spaces
are going to be populated by more peripherals in future generations.

ISA bus
~~~~~~~

Spec: http://www.ee.nmt.edu/~rison/ee352_spr12/PC104timing.pdf and http://www.bitsavers.org/pdf/intel/_busSpec/Intel_ISA_Spec2.01_Sep89.pdf; pinout https://en.wikipedia.org/wiki/Industry_Standard_Architecture#/media/File:XT_Bus_pins.svg

On the ISA bus, we support only I/O (IOR/IOW) transactions and memory transactions in a windowed fashion:

First, we need to decode the IO and MEM read/write signals::

    ISA_nIOR     <<= ((BLA20 == 0) & (nBWE == 1)) | nBAC_2 | nBISA_SEL
    ISA_nIOW     <<= ((BLA20 == 0) & (nBWE == 0)) | nBAC_2 | nBISA_SEL
    ISA_nMEMR    <<= ((BLA20 == 1) & (nBWE == 1)) | nBAC_2 | nBISA_SEL
    ISA_nMEMR    <<= ((BLA20 == 1) & (nBWE == 0)) | nBAC_2 | nBISA_SEL

This can be done by a single 74LS138, or the second half of a 74LS139, plus an OR gate, if we have some left.

The ISA address and data bits are going as follows::

    ISA_A0 <<= BA0
    ISA_A1 <<= BA1
    ISA_A2 <<= BA2
    ISA_A3 <<= BA3
    ISA_A4 <<= BA4
    ISA_A5 <<= BA5
    ISA_A6 <<= BA6
    ISA_A7 <<= BA7
    ISA_A8 <<= BA8
    ISA_A9 <<= BA9
    ISA_A10 <<= BA10
    ISA_A11 <<= BA11
    ISA_A12 <<= BLA12
    ISA_A13 <<= BLA13
    ISA_A14 <<= BLA14
    ISA_A15 <<= BLA15
    ISA_A16 <<= BLA16
    ISA_A17 <<= BLA17
    ISA_A18 <<= BLA18
    ISA_A19 <<= BLA19

    ISA_D0-7 <<=>> D0-7

These most likely could be wires as long as we don't intend to support a huge number of ISA slots.

.. note:: For modern environments, a level-shifter/buffer (74LVT245) is needed to buffer the data-lines. Potentially the same instance that is used for DRAM data buffering could be used.

The rest of the ISA signals::

    ISA_AEN       <<= ~nDACK # active high address enable for DMA cycles
    nWAIT         <<= open_collector(ISA_IO_CH_RDY)
    ISA_ALE       <<= ~nBISA_SEL
    ISA_TC        <<= BDMA_TC
    ISA_nDACK1    <<= nDACK_B
    ISA_nDACK2    <<= nDACK_C
    ISA_nDACK3    <<= nDACK_D
    nDRQ_B        <<= ISA_DRQ1 - note: level-shifter is needed
    nDRQ_C        <<= ISA_DRQ2 - note: level-shifter is needed
    nDRQ_D        <<= ISA_DRQ3 - note: level-shifter is needed
    ISA_RST       <<= ~nRST - note: bi-directional level-shifter (FET-based) is needed

There are 2 inverters needed here. We also need an open-collector driver for nWAIT.

This leaves with interrupt signals. These need to go ... somewhere. I'm starting to think that a simple I/O controller chip would do the job. It would be an overkill, but would support both the address page generation above and the interrupt routing.

    ISA_IRQ2      =>>
    ISA_IRQ3      =>>
    ISA_IRQ4      =>>
    ISA_IRQ5      =>>
    ISA_IRQ6      =>>
    ISA_IRQ7      =>>

.. note:: level shifters are needed on modern systems.

DMA
---

There is a little problem in the number of DMA channels: in a system, where we have:
- graphics
- FDD
- SCSI
We've already used up 3 DMA channels, so only one is available for the ISA bus. That's much, not enough to get a decent sound-card working. Then again, in a PC there weren't a whole lot of DMA channels available either, after adding a floppy and an MFM or similar controller (both used up DMA channels).

Internal keyboard
~~~~~~~~~~~~~~~~~

The idea is that row-select is done by a shift-register. It could be a pair of 74LS164, which is an 8-bit parallel output register. Very old device...
For row read we use a 74LS374 as the input buffer. So that's three extra small devices, allowing for 16x8 matrices... plenty.

Centronics
~~~~~~~~~~

Centronics is a PITA, to be honest. It has 4 ctrl outputs, 5 ctrl inputs and 8 data lines. If we want to be something like IEEE1284, we want the data pins to be bi-directional.

http://www.efplus.com/techref/io/parallel/1284/ecpmode.htm
http://www.efplus.com/techref/io/parallel/1284/eppmode.htm
http://www.efplus.com/techref/io/parallel/1284/bytemode.htm

I decided that bi-directional printer port is not interesting. I'll simply use a 74LS374 as the data-buffer. If needed, an extra GPIO cold be used for direction control and a reverse-connected 74LS374 for input data capture.

Total chip-count tally
~~~~~~~~~~~~~~~~~~~~~~

74LS244 - address buffer
74LS244 - address buffer
74LS245 - data buffer
74LS20  - dual 4-input NAND gate: one to generate ~nDACK
74LS86  - XOR 1 gate used to generate data-buffer DIR, invert nBNREN, generate ISA_ALE and ISA_RST
74LS00  - quad NAND gate; 2 used to generate nBCAS and ~nBCAS, 2 used to generate nBAC_1 and nBAC_2
74LS373 - address latch
74LS75  - quad latch, three bit used for top BLA bits.
74LS139 - address decode; ISA control decode
74LS138 - I/O address decode
74LS07  - hex open-collector buffer; one used to buffer ISA_IO_CH_RDY; a pair used to implement an OR2 gate for ISA control decode
74LS164 - internal keyboard row-select
74LS164 - internal keyboard row-select
74LS374 - internal keyboard row-read
74LS374 - centronics data port

We're left with:

1 transparent latch
3 open-collector buffers
1 NAND4 gate

We can probably consolidate quite a few of this into a couple of PLAs, but I won't do it, I don't think as it's much harder to build at home.
This is a total of 17 jelly-bean chips.

An old-style system would be:

1     custom CPU
1     custom graphics/sound
2     custom GPIO chips
1     FDD ctrl
1     SCSI ctrl
2     EPROMs
16/32 DRAM chips
17    jelly-bean chips (3 less if no internal keyboard)
2     crystal oscillators
1     RTC/SRAM chip, right now the one from the original PC

A modern system would be like:

1     custom CPU
1     custom graphics/sound
1     custom GPIO chips
1     custom Nouveau I/O chip
2     EPROMs
16/32 DRAM chips
17    jelly-bean chips (3 less if no internal keyboard)
2     crystal oscillators
1     RTC/SRAM chip, I2C-based (PCF8583 is still active it seems) or Dallas DS12885 or similar (parallel-bus)


RTC
~~~

OkiData M6242 apparently is a parallel-interface (4-bit??) CMOS RTC/Calendar that was used in some A600 expansion boards.
The Archimedes had a different (I2C) based solution: PCF8573/PCF8570, later PCF8583 (all detailed in the '97 I2C handbook from Philips http://www.bitsavers.org/components/philips/_dataBooks/1997_IC12_Philips_I2C_Peripherals.pdf)

The PCF8576/77 LCD drivers are mentioned in an '86 databook. Logic would say, they're newer than the 70/73.

The early MACs used a different RTC chip. There is a project to replace them with an ATTiny: https://www.quantulum.co.uk/blog/new-timepiece-for-a-classic-mac-part-1/ with protocol and everything, except for the part number... Suffice to say, it used 3 GPIOs and provided a 1sec pulse output.

The early PCs used a Motorola MC146818 part. This was a parallel-bus device with a multiplexed data/address interface (a'la 8085). Though even the datasheet shows how to interface to non-multiplexed devices (essentially use 'AS' pin as A0). https://www.nxp.com/docs/en/data-sheet/MC146818.pdf

A modern replacement for these Motorola chips can be had from ADI (Dallas): https://www.jameco.com/Jameco/Products/ProdDS/25101.pdf
Probably this one: https://www.analog.com/media/en/technical-documentation/data-sheets/DS12885-DS12C887A.pdf. There are different variants, with super-caps and what not.

Logic families
~~~~~~~~~~~~~~

The 74HC/74HCT/74HCU families were available by '85 from Philips. These had rise/fall times in the range of 15-22ns @5V and NAND2 propagation delays of 20-30ns

External connectors
~~~~~~~~~~~~~~~~~~~

Normal connectors of the time:
- Cartridge/expansion connector (for us it would be a single ISA8 connector)
- Centronics printer port
+ RS-232 serial port
- Audio/Video
- External disk drive connector
+ Keyboard/mouse/joystick connector
- SCSI (or other HDD) as of 1986 on the MAC plus, Atari ST at 1985.
- MIDI

GPIO usage
~~~~~~~~~~

For classic models, we have (up to) two I/O chips. These each have 24 GPIO pins.

15         PA_0_EN1_A  Joystick port 1
16         PA_1_EN1_B  Joystick port 1
17         PA_2_EN2_A  Joystick port 1
18         PA_3_EN2_B  Joystick port 1
19         PA_4_TMR1   Joystick port 1
20         PA_5_TMR2   Joystick port 1
21         PA_6_SDA    RS-232
22         PA_7_SCL    RS-232
23         PB_0_EN2_A  Joystick port 2
24         PB_1_EN2_B  Joystick port 2
25         PB_2_EN3_A  Joystick port 2
26         PB_3_EN3_B  Joystick port 2
27         PB_4_TMR2   Joystick port 2
28         PB_5_TMR3   Joystick port 2
29         PB_6        RS-232
30         PB_7        RS-232
31         PC_0_TXD    RS-232
32         PC_1_RXD    RS-232
33         PC_2_RST    RS-232
34         PC_3_CTS    RS-232
35         PC_4_KB_C   PS/2 keyboard port clock pin
36         PC_5_KB_D   PS/2 keyboard port data pin
37         PC_6_MS_C   PS/2 mouse port clock pin
38         PC_7_MS_D   PS/2 mouse port data pin

15         PA_0_EN1_A  ISA_IRQ2
16         PA_1_EN1_B  ISA_IRQ3
17         PA_2_EN2_A  ISA_IRQ4
18         PA_3_EN2_B  ISA_IRQ5
19         PA_4_TMR1   ISA_IRQ6
20         PA_5_TMR2   ISA_IRQ7
21         PA_6_SDA    Internal keyboard scan CLK
22         PA_7_SCL    Internal keyboard scan DATA
23         PB_0_EN2_A  Centronics control
24         PB_1_EN2_B  Centronics control
25         PB_2_EN3_A  Centronics control
26         PB_3_EN3_B  Centronics control
27         PB_4_TMR2   Centronics control
28         PB_5_TMR3   Centronics control
29         PB_6        Centronics control
30         PB_7        Centronics control
31         PC_0_TXD    RS-485 networking
32         PC_1_RXD    RS-485 networking
33         PC_2_RST    RS-485 networking
34         PC_3_CTS    RS-485 networking
35         PC_4_KB_C
36         PC_5_KB_D
37         PC_6_MS_C
38         PC_7_MS_D   Centronics control

SCSI
~~~~

The original controller would have been an AM5380, something that later was cloned by all manners of people. The zilog version (Z53c80) https://www.zilog.com/docs/serial/ps0108.pdf still seems to be in production. It's 'not recommended for new designs', but still available from Digikey and others.

The protocol is documented here: https://www.staff.uni-mainz.de/tacke/scsi/SCSI2-07.html

While rather narly, there's really nothing there that could not be implemented in an FPGA. So, it should be possible to re-create a SCSI controller, maybe even a pin-compatible one with the thingy in the Apple machines.

Another nicely formatted document is this: https://www.seagate.com/files/staticfiles/support/docs/manual/Interface%20manuals/100293068j.pdf

All in all, no custom chips for SCSI, just use what's available.

FDD
~~~

I'm going to use the FDC37C78 from Microchip. It's still available, though 'not recommended for new designs'. I don't care, it's such a niche, and I'm not in the mood of developing and debugging my own floppy controller.

Connector layout
~~~~~~~~~~~~~~~~

On the front:
- Joystick1       (DB9)
- Joystick2       (DB9)
- Mouse           (DIN-6 or something)
- Keyboard        (DIN-6 or something)

On the back:
- Audio out       (3.5mm jack)
- Video out       (DBhd15)
- Audio in (if)   (3.5mm jack)
- External Floppy (DB25)
- External SCSI   (DB25)
- Centronics      (DB25)
- RS-232          (DB9)
- RS-485          (2x phone jack or RJ45)

Networking
~~~~~~~~~~

We are base-lining a simple RS-485, shared bus based network. Or, a better idea: I2C over CAN!

So twisted pair propagation delay appears to be around 500ns for 100m. For I2C to be reliable in terms of arbitration, one would need to keep the round-trip latency below the bit-time. So, with 100m cable lengths, even 1Mbps is out of question, 400kbps is border-line, and 100kbps is doable.

To reach any reasonable distance, we need a protocol that doesn't depend on bit-level synchronization for arbitration. Symbol-level techniques must be used, combined with some slotted ALOHA mechanism, a'la Ethernet. The physical layer is almost irrelevant at that point, RS-485 is just fine, I guess.

ModBus is one such example, but that doesn't seem to be symmetrical, and is master-slave oriented.

I'm starting to think, that maybe I should just punt on networking and use the second serial port for MIDI. This is a home-computer after all, so RS-232 is probably sufficient.

Logic families
~~~~~~~~~~~~~~

According to http://www.bitsavers.org/components/national/_dataBooks/1983_National_74HC_Databook.pdf, the HC family was around in '83 and out-performed LS
for power, and on par for speed.

ALS was also around and was still twice as fast as either LS or HC.