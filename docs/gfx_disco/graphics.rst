Graphics
========

Preface
-------

Today GPUs rule the world. The basic way of their operation - as far as screen compositing is concerned - is that they re-draw every frame every time. They take each vertex in the scene, project them, shade them, texture-map them, then draw them into the screen-buffer. Probably a lot of other things too. The point is: they read a ton of memory buffers and write the frame buffer many many times over for every screen. This of course needs tons of memory, but maybe even more importantly, it needs a ton of memory bandwidth. In the early '80s both came at a premium; Anachron and Disco simply can't afford this approach, just like none of their 'competitors' could. The alternative is online screen-compositing: creating the image one pixel (one scan-line maybe) at a time as we go, sending the pixels to the CRT output and forgetting about them. Sprites are a typical example of this: small patches of transparent overlays that can be composited with the main frame buffer content real-time, while the screen data was sent out.

Disco follows a similar method, albeit with somewhat more flexibility than usual. Disco is also a somewhat weird chimera beast: while it adheres to the limitations of early '80s tech, it also interfaces to modern monitors by providing HDMI (DVI really) output. This forces some features, most importantly scan-line and pixel replication that would not have been possible in earlier systems. These features require deep (by '80 standards) memories on-chip which are easily implemented today but would have been prohibitively expensive back then. Since they come with (and due to) HDMI support, I decided that such deviations are acceptable.

High level architecture
-----------------------

.. svgbob::

    .-------------------------------------------------------------------------------.
    |                               Register interface                              |
    `-------+---------------------+--------------------+--------------------+-------'
            |          :          |                    |                    |
    .-------+-------.  :  .-------+-------.     .------+------.     .-------+-------.
    |               |  :  |               |     |   Palette   |     |               |
    |  DMA engine   |--:->|   Compositor  |     `------+------'     | Video timing  |
    |               |--:->|               |            |            |      and      |     +-.
    |               |--:->|               |     .------+------.     |    Upscaler   |     | |
    |               |--:->|               |---->| RGB mapper  |---->|               |---->| | HDMI
    |               |  :  |               |     `-------------'     |               |     | |
    |               |--:->|               |                         |               |     +-'
    |               |  :  |               |                         |               |
    |               |  :  |               |                         |               |
    `---------------'  :  `---------------'                         `---------------'

    \________________/   \__________________________________________________________/
         sys_clk                                   video_clk
         domain                                     domain


The pipeline starts with the DMA engine. This is responsible for generating the appropriate read bursts to fill the various pixel queues full. There's a queue for each plane and a single queue for all sprites combined. The DMA engine is not aware of the meaning of the data (bit-depth for instance), only of it's memory layout. It is capable of 2D DMAs, which is to say that plane strides don't have to match screen width. Control signals between it and the compositor enure that the DMA memory pointers are advanced and reset at the appropriate times.

.. todo:: should we have individual queues for sprites? Is there even a queue or are we just filling a buffer?

The pixel queues are drained by the Compositor. This engine interprets the pixel data in each of the plane queues, maps them to palette indexes and composes a single pixel-stream. Composition involves overlaying the (enabled) planes with the (enabled) sprites in the right priority order while observing transparency settings. The compositor translates each stream into 8-bit palette indexes before composition; all planes and sprites share a single, 256-color palette. The resulting pixel stream is output to the RGB mapper.

.. todo:: how to deal with high-resolution modes? In those cases we would want to output two pixels per clock, but then it would only be 4 bits per pixel. Or even less. How does the compositor work in that case?

The RGB mapper performs palette lookups to male the 8-bit palette entry to a 24-bit RGB pixel. For 8-bit color modes, the palette is a interpolated one (i.e. we don't have a full 256x24-bit palette RAM, only a 32x24-bit one); this interpolation is also performed here. The mapped RGB pixel stream is output towards the video timing and upscaler module.

The video timing and upsaceler module ensures that pixels are sent to the HDMI connector at the right time; that synchronization (horizontal and vertical) pulses are emitted at the right time and that the right amount of pixels are presented in each scan-line and frame. The module is also responsible for the TMDS signal generation.

A set of registers control the operation of each of these modules. These registers are programmable from the bus interface, the same one that the DMA engine generates transactions on. A separate chip-select signal differentiates between the two uses of the bus interface.

Clocks
------

The memory interface timing is determined by the speed of the DRAM memory used and is shared with Espresso. The timing of the HDMI output is determined by that standard and the resolution used. There's no reason to believe or assume that there is a nice relationship between the two clock requirements. Thus, Disco supports two independent clock inputs for these two functions. This in turn necessitates a clock-domain crossing somewhere within the timeline. This transition happens at the output of the DMA engine; the pixel queues are a natural point for a CDC.

.. admonition:: Why?

    Many computers of the era (maybe most) used a single clock source and derived their system clock from their video clock (the IBM PC is an obvious exception). I would not want to go that route. The strict division ratios (we couldn't have had fancy PLLs) would mean that we can't maximize system performance as :code:`sys_clk` would be slower than it could otherwise be. It would also have meant that PAL and NTSC versions would have run at different speed. So, I decided to eat the extra cost and include a second crystal oscillator.

The reality of modern output standards (HDMI) forces us to use several video_clk rates for various resolutions. This would not have been a huge issue in the old days (we would have needed a different clock for NTSC vs. PAL television sets, but no other variations would have been necessary). Luckily, the technology to implement Disco is based on FPGAs, which feature internal PLLs. So we can still generate (in fact we have to generate because HDMI pixel and bit-clocks are quite different in frequency) several clocks from a single externally supplied :code:`video_clk` source. This would not have been possible but nor would have been necessary in the '80s, so I think it's an acceptable creep of 'modernity'.

Pixel queues
------------

We have to have an internal buffer for a full burst from the DMA controller and then some to weather the latency-jitter: minimum 32 bytes worth, probably higher. There's a big question if a single buffer shared by all queues is the way to go (more complicated logic, less resources) or individual buffers for each plane at least.

.. todo:: do the queues share a memory buffer or are implemented individually?

Bitmap planes
-------------

Disco supports up to 4 bitmap planes. Each plane can be set to different bit-widths, strides and X and Y offsets on the screen. Through the X offset the start-position within the final frame can be adjusted for each plane, however from that starting point the plane is visible through the remainder of the scan-line. Similarly, the Y offset can affect the starting scan-line for a plane, but from then on, the plane is going to be visible all the way to the bottom of the screen.

This means that while the resolution of the planes need not be the same, the can't be set completely independently either: their X resolution and X offset must add up to the horizontal screen resolution; similarly their Y offset and resolution must add up to the vertical screen resolution.

The drawing priority is fixed for all planes: plane 0 being drawn first, plane 3 being drawn last. The transparency palette index is fixed as index 0 for all planes. This means that palette index 0 on plane 0 reveals the screen background color; palette index 0. The corresponding color is programmable in the palette and will be used by the RBG mapper.

Sprites
-------

Disco supports up to 8 sprites, each being 32 pixels wide and 3 colors (plus transparency) for each pixel. The height of the sprites is programmable from one rows to full screen-height.

Sprite data is stored in memory consecutively starting at a base address. Each row consists of 8 bytes of data. A row for a sprite is read by the DMA engine in one burst during horizontal retrace and stored in internal storage.

Sprite positions are programmable both in the X and Y direction in pixel precision. They can be placed partially or completely outside the visible area in the horizontal direction. Vertically, the can be placed after the bottom of the screen, but if they are to be partially shown on the top, the base address register needs to be modified to hide the first few rows.

.. todo:: should we support 2D DMAs for spites with a post-increment register?

The drawing priority is fixed for all sprites: sprite 0 being drawn first, sprite 7 being drawn last.

Sprite and plane interactions
-----------------------------

The priority of the planes and sprites is programmable; even though the drawing order within planes themselves and sprites themselves is fixed, sprites and planes can freely intermix in the drawing order. So for instance, both of the following drawing orders are valid:

================    ==============     ==============
Drawing order       Example 1          Example 2
================    ==============     ==============
0                   plane 0            sprite 0
1                   plane 1            plane 0
2                   sprite 0           sprite 1
3                   plane 2            sprite 2
4                   sprite 1           sprite 3
5                   plane 3            sprite 4
================    ==============     ==============

.. todo:: should we support collision detection? It's rather easy to implement which plane or sprite collides (replacement of non-0 pixel value) but it's rather hard to know with what it collided with.

Line- and pixel replication (upscaler)
--------------------------------------

https://images.anandtech.com/doci/12095/hdmitable.png
https://onlinelibrary.wiley.com/doi/pdf/10.1002/9781119415572.app3

HDMI has no real 320x240 or anything similar. Neither did analog VGA for that matter. They were a 'hack'. Or, to be more precise, the scan-lines would have been too far away from each other on a progressive-scan CRT. As a result, the display worked in 480 scan-line mode and each scan-line is painted twice to make the impression of a 240-pixel vertical resolution. This got carried over to the digital standards such as HDMI.

A new twist in HDMI is that - due to the minimum pixel clock requirement of 25MHz) low resolution modes need to draw pixels multiple times even in the horizontal direction.

In the FPGA world, a scan-line buffer can easily be used to replicate the screen image. Pixel doubling or quadrupling can be done on the fly, but two scan-lines worth of buffer is needed to support scan-line doubling. That is, unless we expect to re-read scan-lines multiple times, which not only wastes DRAM bandwidth but complicates DMA engine design.

Placing this scan-line buffer after palette mapping is the logical place (that's the part of the system that is 'modern' and deals with HDMI), but it does mean that we have to store full RBG pixels, not just 8-bit palette indices.

Using two scan-line buffers also allows for lowering the burst DRAM data-rate, which not only helps with meeting DRAM timing, but allows for smoother CPU execution and closer actual bus behavior to what a TV outputting machine would have experienced.

Smooth-scrolling
----------------

Smooth scrolling is a shared feature between the DMA and the graphics controller. The DMA can shift it's starting read-out position, but only by 32 bits. That's (depending on the bit-depth of the screen) somewhere between 4 and 32 pixels.

.. todo:: is that true? Shouldn't we be able to shift it by 16-bits??

The compositor supports throwing away of excess data at the beginning of the scan-line to implement pixel-level smooth scrolling.

The programmer would need to be careful to set the active portion of the 2D DMA in the fractional pixel cases to include these excess reads and to set the post_increment register appropriately as well.

Vertical smooth scrolling of course is purely a function of the DMA controller by moving the address of the buffer-start.

To allow for 'infinite' smooth horizontal (or vertical) scrolling, the DMA controller supports wrap-around addressing mode. This way the whole transfer can be kept within a fixed region of memory independent of the start-address. The 'update_mask' register controls how many address bits participate in the incrementing of DMA addresses. The remaining top bits are fixed during the whole DMA operation.

This allows SW to keep scrolling to the left or right, and only ever needing to paint a small section of the screen: the few columns that newly became visible.

Registers
---------

2D DMA
~~~~~~~~~~

There is a 2D DMA engine for each layer. The 2D DMA has the following registers:

===============  ===============  ===========
Size             Name             Notes
===============  ===============  ===========
30               base_addr        Physical base address; bottom 2 bits are always 0 (i.e. measured in 32-bit quantities)
5                update_mask      Number of bits to update during DMA address updates
8                post_increment   Signed end-of-line post-increment value, measured in DWORDs
30               cur_addr         Physical current address; bottom 2 bits are always 0 (i.e. measured in 32-bit quantities)
===============  ===============  ===========

Sprite DMA
~~~~~~~~~~

===============  ===============  ===========
Size             Name             Notes
===============  ===============  ===========
30               base_addr        Physical base address; bottom 2 bits are always 0 (i.e. measured in 32-bit quantities)
===============  ===============  ===========

.. note:: there's one sprite DMA for each HW sprite


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