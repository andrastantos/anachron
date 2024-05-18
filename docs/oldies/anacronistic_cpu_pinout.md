Introduction
=============

These are some *very* old notes, one of the first I've taken on Anachron.

There are some interesting, unreplicated notes here about graphics and sound.

Memory size considerations
--------------------------

I know this is a side-track, but I'm interested: can I make a functional 16-bit external bus CPU package with only 40 pins?

The idea here would be that instead of multiplexing the data and the address bus on top of each other (a'la intel), we would multiplex the address-bus in a fashion that it can be direct-connected to DRAM chips.

This would be something that could be built in the early '80-s, with an outlook towards a decade or so.

DRAM history from: http://doctord.dyndns.org/Courses/UNH/CS216/Ram-Timeline.pdf

    '70: 1kbit
    '73: 4kbit
    '76: 16kbit
    '78: 64kbit
    '82: 256kbit
    '86: 1Mbit
    '88: 4Mbit
    '91: 16Mbit
    '94: 64Mbit
    '98: 256Mbit

EPROM timeline (from https://en.wikipedia.org/wiki/EPROM):
    '75: 2704
    '75: 2708
    '77: 2716
    '79: 2732
    '81: 2764 (https://timeline.intel.com/1981/a-new-era-for-eprom)
    '82: 27128 (https://timeline.intel.com/1982/the-eprom-evolution-continues)
         27256
         27512
    '86: 27010 (https://timeline.intel.com/1986/one-megabit-eprom)


That would mean that we should think about supporting 32MBytes of addressable space. If all that is done using DRAMs, that would be 16 chips in '91 and 4 chips in '94.

If I look on Digikey today, there are only 4Mbit and 16MBit parts of FPM/EDO type. So 32MBytes of addressable space seems more than sufficient.

Now, on the low end, if our market introduction is early '80-s, we could assume wide availability of 64kbit chips with 256kbit on the near horizon. In that era, we probably are looking at system memory sizes of 128k and up.

EDO memory modules were already 32-bit wide, and usually built with 4x chips. The module pinout supported two banks with two sets or RAS/CAS signals. OE was grounded on these modules and WE was shared among both banks: https://www.pjrc.com/tech/mp3/simm/datasheet.html. Actually it's way more complicated with 4 CAS and 4 RAS lines because we also need byte-enables somehow.

So, conclusion is this: no FPM or EDO DRAM chip exists with more than 10 addr lines. These chips (the higher sizes at least) are still available from Digikey and others even though they are obsolete.

These 'modern' 16-bit parts support 2 CAS lines and a single RAS one, which is in line with the 72-pin EDO module pinout from above, however being only 16Mbit parts, they only go up to A9 in address lines.

The signals are as follows:
 - /RAS   - shared between 16-bits of data
 - /LCAS  - shared between chips driving the same byte, for a 16-bit wide system, we have 2 of them
 - /UCAS  - shared between chips driving the same byte, for a 16-bit wide system, we have 2 of them
 - /WE    - write-enable
 - A0-A10 - multiplexed address bus
 - D0-D15 - data-bus

The minimum chip size we would want to support is 64kbit DRAM (in 64kx1 configuration). Here's a datasheet: https://www.jameco.com/Jameco/Products/ProdDS/2290535SAM.pdf. Another one for the 4x part: https://www.jameco.com/Jameco/Products/ProdDS/2288023.pdf

The signals are as follows:
 - /RAS   - whatever, this is a 1x chip
 - /CAS   - whatever, this is a 1x chip
 - /WE    - write-enable
 - A0-A8  - multiplexed address bus
 - D      - data input
 - Q      - data output

What's interesting is that the 4x part has tri-stated DQ pins, but even the 1x part tri-states its Q line. So that really isn't all that different.

All right, so here's what we need to do:

Address line muxing:
 - A0  <<= A8   A0
 - A1  <<= A9   A1
 - A2  <<= A10  A2
 - A3  <<= A11  A3
 - A4  <<= A12  A4
 - A5  <<= A13  A5
 - A6  <<= A14  A6
 - A7  <<= A15  A7
 - ----------------
 - A8  <<= A16  A17
 - A9  <<= A19  A18
 - A10 <<= A21  A20
 - A22

This allows for 16MBytes of total address space and A0..A10 can be directly connected to anything from 64kbit to 16Mbit DRAM chips.

Control signals needed:

/RAS
/LCAS
/UCAS
/WE

Data pins needed:

D0...D15

Other pins needed:

CLK
/RST
/INT
/BREQ
/BGRANT

So, where are we?

--------
A0
A1
A2
A3
A4
--------
A5
A6
A7
A8
A9
--------
A10
A22
D0
D1
D2
--------
D3
D4
D5
D6
D7
--------
D8
D9
D10
D11
D12
--------
D13
D14
D15
/RAS
/LCAS
--------
/UCAS
/WE
CLK
/RST
/INT
--------
/BREQ
/BGRANT
/WAIT
VCC
GND
--------

This is EXACTLY 40 pins!!! So, this *could* be done, provided a single VCC/GND pair is sufficient (it probably was in those days) and that we're extremely frugal on control signals.

Now, the second problem: how to interface to SRAM/EPROM chips? Those have a non-multiplexed bus and the following control signals:

A0...An for address
D0...D7 for data
/WE (in case of SRAM)
/CE
/OE

What we would need is this:

1. On falling edge of /RAS, capture A0...A10 into a register
2. /LCAS and /UCAS are connected to /CE of the SRAM chips
3. /WE is /WE
4. Data is data
5. Address is the combination of the registered and direct-from-CPU address lines, as many as needed.

### Address decode:

This is a bit tricky and the result needs to be latched:
address decode can use A22 and A10 (which is A21 in the first cycle) to decode 4 regions, each being 4MByte each. A sub-decode
region 0: ROMs
region 1: I/O
region 2: DRAM
region 3: DRAM

Sub-region decoding could be done at the same time by capturing A0...A8 which is actually A8...A16 in the first cycle. This allows for the decoding of I/O regions, since 128kWord of I/O space is probably sufficient.

In the timeline we're looking at 4kByte EPROMs were widely available, so no smaller one should we think about. However, on the higher end 64kByte and 128kByte (maybe even higher) were available. Now, it's quite likely that any system would contain more than one EPROM of these sizes: it appears that ROM kernel sizes grew faster then EPROM prices came down. So, let's plan for up to 4 EPROM chips.

In the first address cycle, we have access to address lines A8...A16, which would allow for contiguous decoding of up to 256kBytes of ROM space. That I think should be acceptable. If more is needed, it can be done, but with holes in the addressing space.

So, really the only problem is that we only allow for scaling up to 8MBytes of DRAM without paging.

The 30-bit memory module (https://en.wikipedia.org/wiki/SIMM) has support up to 16MByte modules, but in reality, I don't think many of them were produced (especially because they would need A11 as a multiplexed line, which we don't support anyway). In practice those modules go up to 4MByte, two of which would get us to the maximum supported size of 8MByte. So it's not all bad.

So, there, we have it: a 40-pin, 16-bit (external) processor with trivial interfacing to DRAM, single-buffer (albeit 11-bits wide, so maybe 2 chips) for address de-multiplexing and 4-chip address decode (upper bits with a 74LS139, lower bits for I/O and ROM by 2x 74LS138 and a latch in front of all these to capture the right address bits).

## The internals

Let's look at the internals! Here are some relevant transistor counts:

'75:  6502    3510 transistors
'79: Z8000   17500 transistors 16 16-bit registers
'78: i8086   29000 transistors 13 16-bit registers
'79: 68000   40000 transistors 16 32-bit registers
'82: i80186  55000 transistors
'82: i80286 134000 transistors
'85: ARM1    25000 transistors
'86: ARM2    27000 transistors

The prevailing tech node was 2 or 3um.

Actually, there's a pretty good table here: https://en.wikipedia.org/wiki/Transistor_count

So, let's say I can afford around 50000 transistors in NMOS, which would translate to about 25000 gates.
That would be roughly (according to Digikey) an XC4028; XC4044 or an EPF6024. An Actel (Microchip) A54SX16 is also about the same size. These all clock in at around 1500 LUTs. Nothing gets even remotely close to them in size these days. Even the smallest Cyclone III has 5000 LEs. Which just goes to show how constrained these designs would need to be. Nevertheless, a straightforward 3-stage (or 5-stage) RISC pipeline should fit as the ARM1/2 cores show. The smallest MAX10 device is in this category as well (2000 LEs), but one can't use any of the on-chip RAMs or DSP blocks, cause that would be cheating.
The iCE40UL-1k XO2-2000, MachXO3L-2100, AGL030 all seem to be in the same league. The AGL030 is old enough apparently to be 5V tolerant too.


# Graphics

VIC II - 13000 transistors
Amiga Denise - 20000 transistors
Amiga AA+ - 100000 transistors

VGA pixel clock is 25.175MHz for 640x480. For 320x240, it would be half, 12.5875MHz. That's 40 or 80ns respectively.

If we want to support 8bpp mode in 320x240, and have a 16-bit bus, we would need 160ns access time to DRAM. We would also of course need at least 75kB of RAM.

That's not something that a 4164 can easily handle: it had access times of 190/220/260ns. Then again, within a page it could support 55/60/75ns access times and a precharge time of 40/45/60ns.

t_rcd = 45/60/75
t_cas = 55/60/75
t_cp  = 40/45/60
t_crp = 0
A 4-beat burst timing would be: t_rcd + (t_cas + t_cp) * 4 + t_crp

45+95*4=425, average 106.25ns
60+105*4=480, average 120ns
75+135*4=615, average 153.75ns

In other words, with 4-beat bursts we're just squeezing in the lowest speed-grade part, but we eat almost all cycles, not leaving anything for the CPU and audio.

A 41464 datasheet: https://downloads.reactivemicro.com/Electronics/DRAM/NEC%20D41464%2064k%20x%204bit%20DRAM%20Data%20Sheet.pdf
 shows it's somewhat faster:

t_rcd = 40/50/60
t_cas = 40/50/60
t_cp  = 30/40/50
t_crp = 0

So, this could reach 80ns average speed for a 4-beat burst, leaving about half of the bandwidth for the rest of the system. That might actually be acceptable.

The newest part (41C16000):

t_rcd = 37/45
t_cas = 13/15
t_cp  = 10
t_rp  = 35/40

Here, we need to add t_rp-tcp at the end of the cycle, so the average access is 38.5ns/43.75ns. These are screaming fast!

In other words, first models (based on 4164) would need to compromise to 320x240@4bpp. Once upgraded to at least 41464, 320x240@8bpp should be possible. This jives well with memory sizes too: if you only have 128k of RAM, you probably don't want to blow 75k of that just on a frame-buffer.

So, let's think of pinout!

We need to be able to drive the bus but also receive transactions. We probably want to be able to put the frame buffer wherever, so we want the whole address bus, and we certainly want all data being available:

--------
A0
A1
A2
A3
A4
--------
A5
A6
A7
A8
A9
--------
A10
A22
D0
D1
D2
--------
D3
D4
D5
D6
D7
--------
D8
D9
D10
D11
D12
--------
D13
D14
D15
/RAS
/LCAS
--------
/UCAS
/WE
CLK
/RST
/INT <-- output
--------
/BREQ
/BGRANT
/WAIT
VCC
GND
--------
R
G
B
HSYNC
VSYNC
--------

This is unfortunately 45 pins. Of course an FPGA implementation would have even more, given that it doesn't have built-in DACs.

No, to be fair, there were more than 40-pin packages in those days (the 68k was a 64pin DIP monster), but it would be nice to not going there.

48 and 50 pin packages also existed. So maybe that's where we will have to go.

Alternatively the DMA part and the video generation part could be in two different packages. That becomes an expensive proposition though... Still, let's consider it! The idea would be then that we have a generic DMA controller, one channel of which is used for video generation. This disallows sprites and all sort of other goodies though, unless we have several channels for it.

### DMA controller pinout

-------- 0
A0
A1
A2
A3
A4
-------- 5
A5
A6
A7
A8
A9
-------- 10
A10
A22
D0
D1
D2
-------- 15
D3
D4
D5
D6
D7
-------- 20
/DRQ
/DACK
/DCHRD (OC)
/RAS
/LCAS
-------- 25
/UCAS
/WE
CLK
/RST
/INT <-- output
-------- 30
/BREQ (OC)
/BGRANT
/WAIT (OC)
VCC
GND
-------- 35

-------- 40

The way this would work is this: DMA requestors are daisy-chained through their DRQ_IN/OUT signals. This establishes a hard-wired priority scheme between them. The furthest device from the controller has the highest priority.

The DMA controller, when it registers a DMA request, issues a special cycle (assert /DCHRD, after gaining control of the bus). This signal is decoded by all DMA requestors and the one who won arbitration puts it's requested channel ID on the data-bus (only the bottom 8-bits are used, so there could only be 256 DMA channels, but that's plenty).

Once the DMA controller has the channel info, it can create the appropriate bus-cycle in the name of the requestor and assert /DACK along with /CAS). This signal is read by all requestors along with /WAIT to determine the timing of the cycle. for DMA writes, requestors are responsible for driving the data-bus whenever /DACK is low. For read cycles, they are to latch the contents of the data-bus on the rising edge of /DACK or /WAIT, whichever happens first.

This is a rather convoluted and slow way of generating DMA cycles: there's a request cycle, a channel read cycle, potentially an address cycle and then the data cycle.

Multiple DMA controllers can collaborate in the following way: All controllers are connected 'in parallel', but they have a set of channels they implement. When /DRQ is asserted, all controllers request control of the bus (assert /BREQ, monitor /BGRANT) and issue the /DCHRD cycle. Based on the returned channel code, all but one of the DMA controllers determine that they are not the one to generate the bus-cycle, so they release /BREQ. The controller that got selected (i.e. the one with the requested channel) completes the transaction and releases /BREQ whenever it's ready.

This is actually not a horrible way of dealing with things. The only complexity is that video DMAs are special, especially with scan-line doubling. Sprite reads are also problematic if they get moved during a refresh cycle.

So, maybe a simple protocol could be established:

During the /DCHRD cycle, the following commands are returned along with the channel info:

D0 - CH0
D1 - CH1
D2 - CH2
D3 - CH3
D4 - CH4
D5 - CH6
D6 - CMD0
D7 - CMD1

CMD codes:
0 - advance
1 - mark (current address is saved off in mark-register)
2 - restore (current address is restored from mark-register)
3 - reset (current address is reset to DMA base-address)

Now we only allow for 64 DMA channels, which still feels plenty, but the weird logic of sprite addressing and scan-line repetition is handled in the requestor (that is in the video chip). The DMA controller still needs to deal with 2D DMAs (to support smooth scrolling), but that's not all that weird.




Comparing this to the Intel controller, we see two differences: there is some shenanigans around single-cycle vs. block vs. demand DMAs (https://docs.freebsd.org/doc/2.1.7-RELEASE/usr/share/doc/handbook/handbook248.html). Demand mode in particular seems to transfer many bytes so long as DRQ is asserted.

What happens in the intel DMA controller (http://zet.aluzina.org/images/8/8c/Intel-8237-dma.pdf) is that it asserts either /READ or /WRITE during it's memory transfer, along with /DACK. So, it's possible to have several transfers to/from different address within a single DACK cycle by toggling /READ /WRITE several times. Our DMA controller doesn't do that. If we want demand mode, we would toggle /DACK many times, each time we have the data (or need the data) on the data-bus.

We can't really do that, because of this: as we complete a DACK cycle, the original requestor may or may not released the bus. So, we have to go back and re-query the requestor channel by asserting /DCHRD for a cycle.

### Smooth scrolling

Talking about smooth scrolling, here's a problem:

By having a 2D DMA, we can display an arbitrary window in a larger display, but what do we do at the edge? What we would want is the window to wrap around to the beginning of the *same* scan-line. That way SW would always only need to update each scan-line in a ring-buffer fashion and never worry about more than a few columns per frame. This however is beyond what a normal 2D DMA would be required to do, so... weirdness.

An easier way of getting around this would be to wrap the whole DMA at some bit-width. That way the DMA would crawl through - say - 128k of memory, but at the end would start wrapping back, not on an individual scan-line level, but globally.

### DMA Descriptor

Base Addr:   22 (in words)
Line length: 16 (in words)
Line offset: 16 (in words)
Total count: 22 (in words)
Flags:       16 (including wrap)

Total: 92 bits
We probably want around 16 channels in a single DMA controller, which would require ~1500 bits. That's 8800 transistors right there. If my budget is ~20k transistors, that's quite a bit, though not tragic, necessarily.

### Video timing generator pinout


-------- 0
D0
D1
D2
D3
D4
-------- 5
D5
D6
D7
D8
D9
-------- 10
D10
D11
D12
D13
D14
-------- 15
D15
A0
A1
A2
/CS
-------- 20
/DRQ_IN
/DRQ_OUT
/DACK
/WAIT
/WE
-------- 25
VIDEO_CLK
SYS_CLK
/RST
/INT <-- output
R
-------- 30
G
B
HSYNC
VSYNC
VCC
-------- 35
GND



## Sound

If we want CD quality sound, we would need a new sample every 11.3us (stereo, 16-bit). That's... nothing. If we wanted wave-table synthesis, that's a different animal alltogether, but even if we supported 8 (mono) wave-table sounds, that would be ~3us per access.

Sound should also use the previously established DMA engine. Wave-table synthesis involves at least linear interpolation between samples and ADSR envelope generation.

One could also think about sound as simply a 'MOD' accelerator: https://web.archive.org/web/20100921225940/http://io.debian.net/~tar/debian/xmp/xmp-2.7.1/docs/formats/Ultimate_Soundtracker-format.txt or https://www.ocf.berkeley.edu/~eek/index.html/tiny_examples/ptmod/ap12.html

That would include 4 channels of 8-bit samples.

The problem with this is that the access patterns are - yet again - weird: we need two adjacent samples for the interpolation, but from cycle-to-cycle we might jump any number of samples. 0 and 1-sample jumps could theoretically be handled by internal shift-registers, but more than 2-sample jumps can't be easily accommodated. Luckily loop points are 16-bit aligned in the MOD format, so at least we don't have to deal with that.

So, they way trackers get around this issue (and the way Amiga most likely got around this issue as well) is that they don't do any interpolation or sample-skipping. Instead, they change the readout-speed of the sample. What they do is they take the video clock (7159090.5Hz for NTSC) machines, divide it by 2x<period number> and that turns out to be the sample rate for the channel. Than, they simply read (and update the DAC with) the new sample at that sampling period. Period numbers normally range:


            C    C#   D    D#   E    F    F#   G    G#   A    A#   B
    Octave 1: 856, 808, 762, 720, 678, 640, 604, 570, 538, 508, 480, 453
    Octave 2: 428, 404, 381, 360, 339, 320, 302, 285, 269, 254, 240, 226
    Octave 3: 214, 202, 190, 180, 170, 160, 151, 143, 135, 127, 120, 113

    Octave 0:1712,1616,1525,1440,1357,1281,1209,1141,1077,1017, 961, 907
    Octave 4: 107, 101,  95,  90,  85,  80,  76,  71,  67,  64,  60,  57

where octave 0 and 4 are non-standard. These can also be changed by fine-tune values in the samples, but that's not all that interesting here. The point is, that the lowest sample rate supported is 4181Hz, while the highest is 31677Hz (62799Hz with octave 4 support).

The interesting note here is the following: if I had 44100Hz sampling rate in the DAC, my actual sampling rate will always be less then that. So, no cycle-jumping, only cycle-repetitions. With that, we could have a linear interpolator per channel inside the audio chip, and request pairs of samples on different channels consecutively, when needed (we would need 32-bits of internal storage per channel for the current 2 samples and the upcoming two samples). We would then use the 4 existing DMA commands to implement repetitions.

So, overall, cool! This works. Now, for pinout:


-------- 0
D0
D1
D2
D3
D4
-------- 5
D5
D6
D7
D8
D9
-------- 10
D10
D11
D12
D13
D14
-------- 15
D15
A0
A1
A2
/CS
-------- 20
/DRQ_IN
/DRQ_OUT
/DACK
/WAIT
/WE
-------- 25
AUDIO_CLK
SYS_CLK
/RST
/INT <-- output
L_OUT
-------- 30
R_OUT
L_IN
R_IN
VCC
GND
-------- 35
AVCC
AGND

As usual, the FPGA implementation would have more pins as it needs to interface to a DAC (though I2S most likely).
Here I did brake out separate analog supplies as they are most likely needed.

## Serial ports

Now, that's simple, I probably don't even have to re-invent the wheel here. The only question is: do I want to support DMAs. The answer is, probably don't, in those days serial ports were slow enough that CPU interrupts were sufficient.

## Floppy interface

Here I really don't want to re-invent the wheel, so the more pertinent question is: can we handle standard floppy-controllers?

Here's one popular in PCs: https://ardent-tool.com/datasheets/NEC_uPD72065.pdf
http://dunfield.classiccmp.org/r/765.pdf
A much more modern version https://www.mouser.com/datasheet/2/268/37c78-468028.pdf

This guy is a fairly standard 8-bit interface, except for it's DMA capability: DRQ is an output, not inverted. /DACK is the DMA acknowledge and TC is the DMA termination count.

Which brings up an interesting point: why is there a TC signal in PCs and should we have it?

Also, it appears that there should be some interface logic that allows for PC-style DMA peripherals to connect to our engine.

## DMA converter

This thing allows for PC-style DMA peripherals to participate in our crazy DMA scheme.

-------- 0
D0
D1
D2
D3
D4
-------- 5
D5
D6
D7
A0
A1
-------- 10
A2
/CS
/DRQ_IN
/DRQ_OUT
/DACK
-------- 15
/WAIT
/WE
CLK
/RST
/INT
-------- 20
DSRQ0
DSACK0
DSRQ1
DSACK1
DSRQ2
-------- 25
DSACK2
DSRQ3
DSACK3
VCC
GND
-------- 30


