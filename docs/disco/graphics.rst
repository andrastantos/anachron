Graphics
========

According to http://tinyvga.com/vga-timing: VGA pixel clock is 25.175MHz for 640x480. For 320x240, it would be half, 12.5875MHz.

VGA monitors though never really had a resolution of 320x240. The VGA controller instead doubled every scan-line (480 scan-lines) and each pixel (640 pixels). The refresh rate was 60Hz. Since devices at the time surely didn't have the internal memory to store the scan-line needed for doubling, they read it from memory twice. The end result of this is that the average datarate for 640x480 is 18.4Mpixel/s. For 320x240 it's only half of it, around 9.2Mpixel/s. In a modern implementation though we can cheat, and create the internal scan-line store needed for doubling. This would reduce 320x240 datarate to *4.6Mpixel/s*.

NTSC or PAL TV was different: it used 60Hz (50Hz) field rate, but only 30Hz (25Hz) refresh rate. On top, NTSC only guaranteed 200 or so visible scan-lines. So, for TV it was either 320x200x60Hz or 320x240x50Hz. These both turn into the same, *3.84MPixel/s*.

Given that we have give-or-take 16MBps memory bandwidth in the whole system, we can expect to support the following:

1. VGA, 640x480 resolution at 4bpp -> ~9.2MBps bandwidth requirement.
2. QGVA, 320x240 resolution at 8bpp, but *with* internal scan-line doubler -> ~4.6MBps
3. TV resolution 320x200 at 8bpp -> ~3.84MBps

The first resolution is going to slow the CPU to a crawl. It's OK for interactive, non-CPU intensive tasks, such as GUIs, but not for games, I don't think. The second and the third modes are roughly the same. The second one would not have been possible with the chip-technology of the time (the scan-line buffer is too large to fit, I'm afraid), but it's doable for an FPGA implementation. The third would have been the main way of using the machine originally, but pointless to implement today.

So, the two supported resolutions are:
1. VGA: 640x680@60Hz, 4bpp (or less)
2. QVGA: 320x240@60Hz, 8bpp (or less)

Let's see timing-wise where we end up!

VGA@4bbp resolution needs 156,600 bytes for every refresh. Using 16-byte bursts, each burst would take 16/2+2=10 cycles. A frame takes 9600 such bursts, or 96,000 clock-cycles. At 60Hz refresh rate this turns into 5.76M clock cycles. If our system runs at an 8MHz clock rate, that's a whopping 72% of the available bus bandwidth.

A QVGA@8bpp would need half the memory for a frame, thus half the clock cycles: only 48,000 per frame or 28.8M clock cycles every second. This is a 36% bus utilization.

We certainly can't use shorter bursts, that would result in even worse bus utilization. Longer ones are problematic from a buffering perspective, but 32-byte bursts would result in a 65%/32.4% bus utilization respectively. Maybe worth it...

Things of course get dramatically better with lower bit-depth.

Sprites
-------

If we wanted to support sprites, we would need scan-line buffers for them, probably around 64-bits worth each (16x16 and 4bpp). That would be 512 bits total.

Disco would use several DMA channels to read video-data: one for the main screen buffer and one each for each sprite.

Screen compositing
------------------

We might want to support several layers of screen data. For instance: overlay of two 320x240, 4bpp planes. This is the same memory bandwidth, but with supporting two independent smooth-scroll settings for each, a game can a foreground/background semi-3D illusion. Combined with scan-line interrupts, where registers can be reprogrammed, even more effects can be supported.

For each plane we would need to replicate the 2D DMA engines and pixel shifters. We could share the pixel buffers though. This will sacrifice some bus efficiency, but we're off-loading a ton of CPU work in screen composition, so it's probably the right call. Palette lookups are also more complicated, but potentially can be done after merging: the transparency color is not defined by the palette, it is simply hard-coded as index 0, for example. Having independent palettes for the layers is also solvable because of the reduced per-layer bit-width. We just need to carry over the layer selection so we can use the right section of the palette ram.

Since we can't really expect to close timing beyond ~10MHz, we would certainly need to handle 2 VGA pixels in parallel, maybe even two QVGA pixels, which would mean up to 6 palette lookups per clock cycle.

Clocks
------

We have to independent clock inputs (and two internal clock-domains): one for the system clock to interface with the bus and the other for the video generation logic. We would need to transition from the :code:`sys_clk` to the :code:`video_clk` domain, the logical place to do that is the pixel buffer. This would need to become a CDC FIFO.

.. admonition:: Why?

    Many computers of the era (maybe most) used a single clock source and derived their system clock from their video clock (the IBM PC is an obvious exception). I would not want to go that route. The strict division ratios (we couldn't have had fancy PLLs) would mean that we can't maximize system performance as :code:`sys_clk` would be slower than it could otherwise be. It would also have meant that PAL and NTSC versions would have run at different speed. So, I decided to eat the extra cost and include a second crystal oscillator.

Output signals
--------------

R/G/B output would be analog signals, which of course we can't do on an FPGA: we would need to depend on external DACs.

.. note::
    The Amiga and the Atari ST depended on external resistor-network based DACs for video. In the A500, it became a 'hybrid', which is not much better...

Pixel buffer
------------

We have to have an internal buffer for a full burst from the DMA controller and then some to weather the latency-jitter: probably 16 to 32 bytes worth.

Sprites
-------

If we wanted to support sprites, we would need scan-line buffers for them, probably around 64-bits worth each (16x16 and 4bpp). That would be 512 bits total.

We would have 8 DMA channels too: one for each sprite. These DMA channels would access their associated tiny frame-buffers during the horizontal blank period to fill the internal buffers. Since they read 8 bytes at a time, they use 4-beat bursts.

Line-replication
----------------

320x240 screens were a 'hack' in the VGA standard. Or, to be more precise, the scan-lines would have been too far away from each other on a progressive-scan CRT. As a result, the display worked in 480 scan-line mode and each scan-line is painted twice to make the impression of a 240-pixel vertical resolution. If we were to work with these monitors, and timing, we would need to do the same.

Since VGA is a later standard, we won't have to be bother by how it would have been supported back in the day, but in our FPGA implementation, this is the only format that really matters. TV: who cares anymore.

In the FPGA world, a scan-line buffer can easily be used to replicate the screen image. In fact, this buffer would be placed after the palette, so that all sprites and layers would get replicated properly.

A second scan-line worth of buffer is added to stretch out the time the engines prior have two (VGA) scan-lines worth of time constructing the following one. This trick doesn't change the average datarate needed on the bus. It however lowers the burst data-rate, which not only helps with meeting DRAM timing, but allows for smoother CPU execution and closer actual bus behavior to what a TV outputting machine would have experienced.

The fact that the scan-line buffers are after the palette means that they contain 18-bit pixel information. They are 2 scan-lines worth, at 320 pixels each, so a total of 11520 bits are needed. This is just a little over what a single (GoWin) BRAM can support, so we'll need 2 instances.

Interlace support
-----------------

If we wanted to do *more* than ~240 scan-lines on a TV screen, we would have had to implement interlaced mode. In that operating mode, even fields would end on a half-scan-line and odd fields would start with them. This way, the CRT would shift the fields half a scan-line from one another, creating the impression of double the vertical resolution.

So, to support 640x480 screens on a TV (or a monitor supporting NTSC-style timings) we would need to support interlaced mode.

.. note::
    It's interesting to see how in the 'old world' 640x480 needed special treatment, while in the 'new world' it's the other, the 320x240 resolution that requires it.

The problem with emulating interlace on a VGA monitor is the following: in interlace mode the frame-rate drops to 25/30Hz respectively. In VGA, being a progressive scan standard, the frame-rate is a constant 60Hz. To emulate the setup we would need to store a full frame worth of data on-chip and playing it back twice for each update. This is not really doable with small and cheap FPGAs, however the GoWin 1NR series, with it's built-in PSRAM might be up to the task. Actually, the PSRAM is an 8MB device, with a relatively simply interface and plenty of bandwidth: we can run it at 166MHz, 8-bit wide (but DDR), with 4-beat bursts. We can issue a 32-bit read/write every 6 clock cycles, so 221MBps data-rates are achievable. Even with 32-bit pixels, we get 55Mpixels/s of transfer rate. The VGA read-out would need 25Mpixels/s, so there's more than enough for writing the frame-buffer.

Smooth-scrolling
----------------

Smooth scrolling is a shared feature between the DMA and the graphics controller. The DMA can shift it's starting read-out position, but only by 16 bits. That's (depending on the bit-depth of the screen) either 2,4, 8 or 16 pixels.

The graphics controller will have to support the throwing away of the excess data at the beginning (and end) of the scan-line to implement pixel-level smooth scrolling.

The programmer would need to be careful to set the active portion of the 2D DMA in the fractional pixel cases to include these excess reads.

Vertical smooth scrolling of course is purely a function of the DMA controller by moving the address of the buffer-start.

To allow for 'infinite' smooth horizontal (or vertical) scrolling, the DMA controller supports a wrap-around addressing mode. This way the whole transfer can be kept within a fixed region of memory independent of the start-address. This allows SW to keep scrolling to the left or right, and only ever needing to paint a small section of the screen: the few columns that newly became visible.

2D DMA
------

There are two 2D DMA engines, one for each layer. The 2D DMA has the following registers:

#. BASE_ADDR: 32-bit physical address (16-bit aligned, LSB is not implemented)
#. LINE_LEN: length of a scan-line in 16-bit increments. This is an 8-bit register, though occupies a 32-bit location
#. LINE_OFS: offset to the next scan-line in 16-bit increments. This is an 10-bit register, though occupied a 32-bit location
#. WRAP_BITS: Number of bits used for addressing. This is a 5-bit register. When incrementing the address, only the specified bits are changed. The top bits are determined by BASE_ADDR and never change

.. note:: The (re)start of the DMA is controlled by the timing module: it is restarted at the beginning of the last scan-line that is part of the vertical blanking.

.. note:: 2D DMA generates 16-byte (8-beat) bursts in single-layer and 8-byte (4-beat) bursts in dual-layer mode. It needs to check for and early-terminate page-crossing bursts.

.. note:: Do we want to support scan-line replication in DMA as well? That's how it would have been done in the days of yore...

Sprite DMA
~~~~~~~~~~

#. BASE_ADDR: 32-bit physical address (32-bit aligned, lower two bits are not implemented)

.. note:: Timing (including re-start and gating) of the DMA is directed from the timing module: no need to specify the total DMA size

.. note:: there's one sprite DMA for each HW sprite

.. note:: Sprite DMAs generate 8-byte (4-beat) bursts. They can't generate and thus are not interested in page-crossing bursts.

.. note:: Do we want to support scan-line replication in DMA as well? That's how it would have been done in the days of yore...


Data FIFOs
~~~~~~~~~~

The 2D DMA feeds a CDC-fifo into the pixel domain. This FIFO is somewhere between 1 and 2 bursts deep, again very similar to the fetch queue, except it transitions between two clock domains.

The data FIFO is significantly more complicated by the fact of the support for two layers: the same underlying memory is used, so the buffer size depends on the operating mode. On the feeding side, the 2D DMAs never active at the same time, so we won't ever see two writes into the two virtual FIFOs. On the reading side the compositor has to make sure that it's multiplexing the reads so that they don't happen on the same clock-cycle. This is doable as our per-stream data-rate is half in dual-layer mode, but it's still extra complexity.

Sprite DMAs directly write into their own, dedicated shift-register-style short FIFOs. No empty-full handshaking is needed (and no real CDC either) since filling of these buffers happens during blanking and reading during the active screen period.

Pixel extraction
~~~~~~~~~~~~~~~~

On each FIFO pull path, a programmable block (shift register, really) converts a byte-stream into a pixel stream. For 8bpp modes, this is trivial. For 1/2/4bpp QVGA modes, we pad 0-s to the top of each pixel data, outputting 8bpp pixels.

.. note:: we have to careful with the padding so that 0-s are entered into the 'interpolation' bits of the palette lookup.

For VGA modes, 2 pixels are extracted every clock cycle. This involves pair-wise 0-padding in each nibble independently.

Smooth scrolling requires the ability to 'invent' 0 pixels at the front/back of the pixel stream as well as throwing away pixels.

.. note:: throwing away is needed for layers where the DMA engine will need to be programmed with 16-bit aligned transactions. Pixel invention is needed for sprites in VGA mode, which have fixed width, but pixel-aligned position. zero pixels are invented into sprite streams that are not visible at the currently processed pixels.

The end of this process is 10 independent pixel streams, one for each of the layers and sprites. The pixel streams contain 1 pixel per byte for all QVGA and 2 pixels per byte for all VGA modes. Pixel value 0 is used as a transparency index. All streams are aligned in time to one another.

.. note:: An extra complexity in dual-layer mode is that the FIFO pulls will have to be multiplexed to avoid read-conflicts. Since in this mode, we generate 4bpp pixels in QVGA mode, we need a new byte for each on every other clock-cycle, so this is fine, but complexity to be dealt with.

Compositing
~~~~~~~~~~~

Compositing consists of combining the 10 pixel streams from above to a single pixel stream, ready to be converted to analog video.

The logic of compositing is as follows:

For each pixel, the compositor starts with a pixel value of 0. Then, it loops through all layers and sprites in inverse z-order. If the value in the pixel stream is non-0, the value is replaced and the stream index is updated. If not, the previous values are used. In VGA mode, the process is done independently on the two nibbles of the pixel value.

Of course this loop is unrolled and pipelined into as many stages as needed to close timing. The complexity is in programmable z-order. The bottom is always the primary layer. Since sprites are interchangeable, dynamic ordering of them is not needed. But where to put the second layer? This needs to be programmable. Some sprites might want to be under it, while others above it. This results in an enormous mux, in the unrolled loop. We'll have to see. It's possible - as a compromise - to say that the second layer *replaces* one of the sprites. Any sprite can be replaced, but at least we have a per-iteration 2:1 mux instead of a 3:1 mux.

The end result of this process is a pixel stream, containing an 8-bit pixel value, a 4-bit source stream index for QVGA and a pair of 4-bit pixel values and a pair of 4-bit stream index values for VGA modes.

.. todo:: if we wanted to do collision detection, this is the place to do it.

Palette mapping
~~~~~~~~~~~~~~~

We can't afford to have independent palettes for all the streams.

**QVGA modes**: We have a single 256-color palette and allow each stream to select which 15 colors of those 256 they use. If the stream index is 0, this means that we're dealing with the base layer, and palette mapping is bypassed. If not, the palette value (which at this point must be between 1 and 15) is appended to the stream index, decremented by 1 (which after decrement should fall into the range of 0 to 8). The result is an 7-bit index, that is packed to contain values from 0 to 136. This value is used as the address to the pallette mapping RAM.

.. note:: What we will do is that for sprites, the pixel value is in the bottom 4 bits, while the sprite index is in the top 3 bits. This - since pixel value 0 is never used - leaves entry 0;8;16... unused. These entries (8 of them) are used for layer 1, if the pixel value is less then 8. If pixel value is greater 8, 120 is added to it. This way, only palette mapping address 0 is left unused, and the minimum-sized RAM can be used. The address generation logic is not terribly complicated or later. A similar de-mapping strategy can be used on the register-interface facing side to hide the confusing mapping from the user.

The palette mapping RAM provides an 8-bit result, which is the final palette value for he pixel to be displayed.

**VGA modes**: We have two 4-bit pixel values and two 4-bit stream-indices. Since the palette in this case only contains 16 entries, there's no real reason to do any palette mapping, at least for sprites. So palette mapping lookup is bypassed for anything but the secondary layer. Even for the secondary layer, palette mapping only makes sense if this layer is in 1bpp or 2bpp mode. So, palette mapping can be bypassed for this layer as well by a programmable register. If not bypassed, the bottom 2 bits from each nibble is concatenated together to form a 4-bit lookup. This lookup value is used as an address to the palette mapping RAM. The resulting 8-bit value is used as the pixel (pair) value to be displayed.

Palette logic
~~~~~~~~~~~~~

The palette logic gets one 8-bit pixel value in every clock-cycle and outputs a pair of 15-bit RGB values.

Since we can't afford a full 256-entry palette, we do the following:

We will have a pair of palette RAMs, each containing 16 entries, 15-bit wide.

Palette in QVGA mode
````````````````````

The incoming pixel data is divided into two portions: the bottom 4 bits select a palette entry, the top 4 bits encode an 'interpolation' value. The palette RAMs are looked up using the same palette entry index, yielding two colors. The interpolation factor used to linearly interpolate between these two end values for each of the R/G/B channels.

The interpolation could be done in the analog domain, using `multiplying DACs <https://www.analogictips.com/what-is-a-multiplying-dac/>`_, but I'm afraid that would rather large.

Probably a better idea is to use a digital interpolator: a multiplier-like circuit that instead of containing AND gates, contains 2:1 muxes to select one or the other value for each adder layer. Since we only have a 4-bit multiply to do, this is a rather manageable complexity. The resulting 8-bit per channel value can be quantized (or rounded if we feel fancy) to 5 bits.

The resulting value is replicated for both output color channels.

Palette in VGA mode
```````````````````

The incoming pixel data contains 2 pixels per clock pulse. This data is divided into an upper and lower nibbles. The two nibbles are independently used to look up a palette entry in each of the palette RAMs. The palette entries in this case are not interpolated and the RAM outputs is placed without modification into the output color channels.

DDR DACs
~~~~~~~~

The palette logic produces a pair of color values for each clock cycle. A double-speed DAC is used to convert these to analog values: one on the low phase of the pixel clock, one on the high phase.

The DACs are also responsible for blanking generation

Timing module
~~~~~~~~~~~~~

Register setup:

1. Horizontal total: 8 bits
2. Visible start: 5 bits
3. Pixel start: 8 bits
4. Visible end: 5 bits
5. HSync start: 5 bits
6. Vertical total: 10 bits
7. Visible start: 5 bits
8. Visible end: 5 bits
9. VSync start: 5 bits

The timing module works on the resolution of 4 QVGA pixels per clock, but operates in the pixel clock domain.

Pixel start and visible start are different to support smooth scrolling. Pixel start is actually measured in (QVGA), and controls the start of pixel shifting.

Mainly following this document: http://tinyvga.com/vga-timing/640x480@60Hz for timing

On top of the above, there are several signals generated by the timing module to control:

#. Sprite locations
#. Smooth scrolling (Pixel drops and insertions)
#. Layer 1 offsets
#. DMA gating, triggering and restarts

It's fair to say that there are a lot more registers then what's listed above.

.. note:: There are deep latencies in the pipeline. This means that blanking Hsync/Vsync are not strictly aligned with other timing signals. The timing module will need to suck it up and re-align these signals as needed. Some of that burden can be shifted over to SW, but sub-4-pixel alignment is still something that the timing module will have to deal with.


Interrupts
~~~~~~~~~~

Interrupts can be generated on the following events:

1. When a complete scan-line is read from DRAM (based on 2D DMA), scan-line index is programmable
2. On horizontal blanking start, scan-line index is programmable
3. When a complete frame is read from DRAM (based on 2D DMA)
4. On vertical blanking start
5. Sprite collision


RAMs
~~~~

We have the following RAMs:

I finally have found a `RAM example <https://github.com/ShonTaware/SRAM_SKY130#openram-configuration-for-skywater-sky130-pdks>`_ for the sky130 SDK: it's a 32x1024bit RAM (single-ported, 6T cells).

It's size is 0.534mm^2, closes timing at about 80MHz. Back-scaling it to 1.5u, gives us a scaling factor of 133:1. Taking all of this, gives us 71mm^2 for this 32kbit SRAM or 0.00217mm^2/bit.

#. Input stream RAM: 32x8=256 bits -> 0.56mm^2
#. Palette mapping RAM: 136*8=1088 bits -> 2.36mm^2
#. Palette RAM: 32x30=960 bits -> 2.08mm^2

These are probably optimistic somewhat for the following reasons:
- We need more than a single port
- The overhead is greater for smaller memories (sense amps, etc.).

Still, it's highly questionable, whether the extra complexity of sharing the input stream RAM between the two layers is worth the savings of doubling that RAM.

More on OpenRAM and sky130:

http://ef.content.s3.amazonaws.com/OpenRAM_%20FOSSI%20Dial-Up%202020.pdf
https://openram.org/docs/source/


HDMI out
--------

A nice, open-source HDMI output core, with audio support.

https://github.com/hdl-util/hdmi/