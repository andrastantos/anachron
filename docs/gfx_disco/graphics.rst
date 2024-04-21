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

The drawing priority is fixed for all planes: plane 0 being drawn first, plane 3 being drawn last. The transparency palette index is fixed as index 0 for all planes. This means that palette index 0 on plane 0 reveals the screen background color; palette index 0. The corresponding color is programmable in the palette and will be used by the RGB mapper.

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

.. todo:: should we support collision detection? If so, we need to remember what was the plane or sprite index that was replaced last (this is a 4-bit value) and the plane or sprite index that is colliding with it. This is not terribly hard, but there could be many collisions even within a single pixel, let alone in the whole screen. So how to report all this back to SW?

Smooth-scrolling
----------------

Smooth scrolling is a shared feature between the DMA and the graphics controller. The DMA can shift it's starting read-out position, but only by 32 bits. That's (depending on the bit-depth of the screen) somewhere between 4 and 32 pixels.

.. todo:: is that true? Shouldn't we be able to shift it by 16-bits??

For horizontal smooth scrolling, the compositor supports throwing away of excess data at the beginning of the scan-line to implement the pixel-level part of scrolling.

The programmer would need to be careful to set the active portion of the 2D DMA in the fractional pixel cases to include these excess reads and to set the post_increment register appropriately as well.

Vertical smooth scrolling of course is purely a function of the DMA controller by moving the address of the buffer-start.

To allow for 'infinite' smooth horizontal (or vertical) scrolling, the DMA controller supports wrap-around addressing mode. This way the whole transfer can be kept within a fixed region of memory independent of the start-address. The :code:`update_mask` register controls how many address bits participate in the incrementing of DMA addresses. The remaining top bits are fixed during the whole DMA operation.

This allows SW to keep scrolling in any direction, and only ever needing to paint a small section of the screen: the few columns or rows that newly became visible, but care should be taken as the frame buffer might not be contiguous is physical address space.

TODO: how to do smooth-scrolling in high-resolution mode? In that case we need to deal with sub-byte and sub-clock-cycle shifts. Do we want the associated shifters?

High- and low-color modes
-------------------------

The pipeline supports two main operating modes: high- and low-color modes.

In high-color mode, each pixel on the screen can take up one of 256 color values, each pixel is comprised of 8 bits. Every clock cycle, a single output pixel is produced.

In low-color mode, each pixel on the screen can take up one of 16 color values, each pixel is comprised of 4 bits. Every clock cycle, two pixels are rendered.


Compositing
-----------

Pixel extraction
~~~~~~~~~~~~~~~~

On each plane, a programmable block (shift register, really) converts a byte-stream into a pixel stream. In high-color mode, each clock cycle some number of bits (based on the plane bit-depth) is pulled and a programmable palette offset is added it. This creates an 8-bit pixel value that is used further down the pipeline during compositing. In low-color mode, a pair of pixels is pulled in each clock cycle. The top pixel is shifted to bit-position four, then the palette offset is added to each nibble (i.e. an 8-bit addition with the carry cut between bit 4 and 5). This means that a different palette offset can be applied to odd and even pixels. The result is an 8-bit value, that is treated as a pair of 4-bit pixels by the compositor.

.. note:: in low-color mode, pulled values have to be optionally rotated such that pixel-level smooth horizontal scrolling is possible. Smooth scrolling also requires the throwing away of some of the leading pixels as they are pulled from the DMA queues.

Sprites have a fixed 2-bits-per-pixel representation with index 0 reserved for transparency. For each sprite 3 independent 8-bit palette registers are available to select the three remaining colors. In high-color mode a single 2-bit pixel value is extracted for every clock cycle (index 0 is used for the regions where the sprite is not visible). The index is then used to select one of the three palette registers (or 0 for index 0). In low-color mode, a 4-bit double pixel value is extracted every clock-cycle (index 0 is used for regions where the sprite is not visible). Special care must be taken to rotate the bits to the right position so that pixel-level horizontal positioning of sprites is possible. The thus created 4-bit value is than spit into two 2-bit values. The upper 2 bits are used to select one of the upper nibbles of one of the three palette registers (or 0). The lower two bits are used to select one of the lower nibbles of the three palette registers (or 0). The two selected nibbles are then recombined into a single 8-bit value which is then used as a pair of pixels during compositing.

.. note:: the trick about nibble selection simplifies data-path design but also allows to select different palette values for odd and even pixels of sprites.

The end of this process is 12 independent pixel streams, one for each of the planes and sprites. The pixel streams are aligned both horizontally and vertically for composition. In high-color mode, each stream contains a single palette index for a single pixel. For low-color mode each stream contains a pair of 4-bit palette indices. Either way palette index 0 represents transparency.

Compositing
~~~~~~~~~~~

Compositing consists of combining the 12 pixel streams from above to a single pixel stream, ready to be converted to analog video.

The logic of compositing is as follows:

For each pixel, the compositor maintains a pixel value (8 bits) and a pair of stream indices (4 bit value each). It starts with a pixel value of 0 and a stream indices of 0xff. Then, it loops through all layers and sprites in drawing order. If the value in the pixel stream is non-0, the value is replaced and the stream indices are updated. If not, the previous values are used. In high-color mode, the test and replacement is done on the whole 8-bit value (so the steam indices are always identical), for low-color mode, each nibble is individually considered.

Of course this loop is unrolled and pipelined into as many stages as needed to close timing. The complexity is in programmable drawing order.

The end result of this process is a pixel stream, containing an 8-bit pixel value, a pair of 4-bit source stream indices.

.. todo:: if we wanted to do collision detection, this is the place to do it. If not, stream indices can be removed.

RGB mapping
-----------

We can't afford to have independent palettes for all the streams. In fact, we can't even afford a fully programmable 8-bit palette.

The palette itself contains only 32 entries, each being an RGB value.

.. todo:: how many bits per color should we consider?

The RGB mapper logic
~~~~~~~~~~~~~~~~~~~~

The RGB mapper logic gets one 8-bit pixel value in every clock-cycle and outputs a pair of RGB values.

Since we can't afford a full 256-entry palette, we do the following:

We will have a pair of palette RAMs, each containing 16 RGB entries.

For each clock cycle, an 8-bit value is consumed from the compositor (containing either an 8-bit or a pair of 4-bit pixels) and a pair of RGB values are produced.

Operation in high-color mode
````````````````````````````

The incoming pixel data is divided into two portions: the bottom 4 bits select a palette entry, the top 4 bits encode an 'interpolation' value. The palette RAMs are looked up using the same palette entry index, yielding two colors. The interpolation factor used to linearly interpolate between these two end values for each of the R/G/B channels.

The interpolation could be done in the analog domain, using `multiplying DACs <https://www.analogictips.com/what-is-a-multiplying-dac/>`_, but I'm afraid that would rather large.

Probably a better idea is to use a digital interpolator: a multiplier-like circuit that instead of containing AND gates, contains 2:1 muxes to select one or the other value for each adder layer. Since we only have a 4-bit multiply to do, this is a rather manageable complexity, especially since only the top 8-bits of the result is used as the color channel value.

The output color is then replicated for both output channels.

Operation in low-color mode
```````````````````````````

The incoming pixel data contains 2 pixels per clock pulse, one in each nibble. The two nibbles are independently used to look up a palette entry in each of the palette RAMs. The palette entries in this case are not interpolated and the RAM outputs is placed without modification into the output color channels.

Video timing and upsaceler
--------------------------

While there would have been a similar module (sans upscaler) in the version of Disco, if developed in the '80, times have changed drastically since those days. Up to this point in the pipeline, there are fairly limited changes required for these modern times, but the video timing generation and - especially - the upscaler modules are very different in deed and tied closely to modern technologies. As such, I'm going to concentrate much more on functionality then on resource utilization: the goal is to interface to modernity instead of staying true to the capabilities of the past.

The role of video timing is rather obvious: generate the required signals to synchronize the display device (an HDMI display in our case) with the inner workings of Disco. This involves generating horizontal and vertical retrace pulses as well as front- and back-porch periods (essentially blanking before and after the sync pulses). The duration of all these periods is programmable. For horizontal timing, periods are specified in 2-clock-cycle resolution (this is two pixels for high-color and four pixels in low-color modes). Vertical timing is specified in scan-lines.

Pixels are consumed from the RGB mapper in, well, RGB format: two pixels per clock for low-color and one pixel per clock for high-color modes. For high-color mode, pixels are fed to the upscaler logic, which - on its output - provides two pixels every clock cycle. This means that after this point, there is no difference between low- and high-color modes: in all cases, two pixels are processed for every clock cycle.

These pixels, along with the horizontal and vertical sync pulses are fed to a set of TMDS serializers, which drive the LVDS output stages for HDMI transmission.

The rest of the timing information (horizontal and vertical blanking; start of a new scan-line or frame among other things) are generated and distributed to the rest of Disco as individual pulses.

Due to the needs of serialization, several, higher frequency clocks are used internally, as needed.

Finally, the timing module takes into account the latency of the processing pipeline and adjusts synchronization signals according to that.

Line- and pixel replication (upscaler)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

https://images.anandtech.com/doci/12095/hdmitable.png


HDMI has no real 320x240 or anything similar. Neither did analog VGA for that matter. They were a 'hack'. Or, to be more precise, the scan-lines would have been too far away from each other on a progressive-scan CRT. As a result, the display worked in 480 scan-line mode and each scan-line is painted twice to make the impression of a 240-pixel vertical resolution. This got carried over to the digital standards such as HDMI.

.. note:: interestingly https://onlinelibrary.wiley.com/doi/pdf/10.1002/9781119415572.app3 lists a set of very low resolution display modes (240p for instance as CEA mode 8), but it's unclear how these would have been implemented with relation to the minimum 25MHz HDMI pixel clock requirement. Adoption rate is also unclear.

A new twist in HDMI is that - due to the minimum pixel clock requirement of 25MHz - low resolution modes also need to draw pixels multiple times in the horizontal direction.

In the FPGA world, a scan-line buffer can easily be used to replicate the screen image. Pixel doubling or quadrupling can be done on the fly, but two scan-lines worth of buffer is needed to support scan-line doubling. That is, unless we expect to re-read scan-lines multiple times from memory, which not only wastes DRAM bandwidth but complicates DMA engine design.

Placing this scan-line buffer after palette mapping is the logical place (that's the part of the system that is 'modern' and deals with HDMI), but it does mean that we have to store full RGB pixels, not just 8-bit palette indices.

Using two scan-line buffers also allows for lowering the burst DRAM data-rate, which not only helps with meeting DRAM timing, but allows for smoother CPU execution and a bus behavior closer to what a TV outputting machine would have experienced.

.. todo:: should we do full on-chip frame-buffer store? The GoWin FPGAs actually integrate enough DRAM (SDRAM or PSRAM depending on the model) to store a full frame-buffer. If used, this could completely de-couple memory read-out rate from screen refresh rate and - potentially - even allow tear-free screen updates. The downside (apart from the implementation complexity) is that it would tie the core rather closely to a particular FPGA family.



How to get VGA (analog) output from HDMI: https://www.retrorgb.com/mister-240p-over-hdmi.html

Register interface
------------------

Registers can be read and written in Disco with zero wait-states.

Registers are not double-buffered, changes to their values have immediate impact.

.. TODO:: we should be way more explicit about this. For each register, we should document when the register value is used, thus when is it safe to change.

Interrupts
----------

Interrupts can be generated on the following events:

1. On horizontal blanking start, scan-line index is programmable
2. On vertical blanking start

.. NOTE:: horizontal blanking start interrupt could be potentially pre-triggered by the depth of the display pipeline. Either way, the point is that when the interrupt triggers, it is guaranteed that no register or memory changes will affect the currently displayed scan-line.

Extra Notes
-----------

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

Still, it's highly questionable, whether the extra complexity of sharing the input stream RAM between plane DMAs is worth the savings of doubling that RAM.

More on OpenRAM and sky130:

http://ef.content.s3.amazonaws.com/OpenRAM_%20FOSSI%20Dial-Up%202020.pdf
https://openram.org/docs/source/


HDMI out
~~~~~~~~

A nice, open-source HDMI output core, with audio support.

https://github.com/hdl-util/hdmi/


scan-racing GPU
===============

Can we think of a way to make the graphics more GPU-like? We can have a very specialized instruction set that allows for pixel composition and pointer (bit-level one) manipulation. We could have the DMAs be replaced by prefetch machines and the pixel FIFO becoming a prefetch cache of sorts. Loops would handle horizontal and vertical resolution, predication would handle 'if' statements (such as spites).

This would need to be massively parallelized otherwise we wouldn't be able to execute it, but that's the thing that GPUs are good at anyway. The only question is how to handle loop-carried dependencies. I think staggered execution instead of straight-up SIMD might be the answer here.

I will need to experiment with an ISA and some sample code in it to see if any of this makes sense. If it does however, we would have a very interesting graphics architecture in our hand indeed.

BTW: since Disco has an nWE signal towards DRAM, we could even have store operations and work into frame-buffers instead of direct-to-screen if we wanted to, something that we wouldn't have the bandwidth to do so, but might result in some interesting effects for demos.

This, combined with a similar approach to audio might result in something rather unique.

Loads
-----

So, in this world, there would be prefetchers. These would prefetch a programmable number of bytes based on a prefetch miss.
The addresses would either increment or decrement from the miss-address. The results are stored in prefetch buffers.

There are 16 prefetch buffers, each 4 bytes large (I think). This gives us 64 bytes of prefetch buffer.

The prefetch units are also assigned to prefetch buffers somehow, semi-statically.

A load operation specifies:
- A source address (bit-level)
- Number of bits to load
- Prefetcher to use (and through that which prefetch buffers to use).

A prefetch buffer contains:
- Start address
- Valid bit

A prefetch miss is stalled until the full prefetch buffer is loaded.
Loads can't cross byte-boundaries, even though addresses as 16-bit aligned.

Prefetch buffers are assigned sequentially to a prefetcher in powers of two increments. So, for instance 'prefetcher 0' is assigned 'buffer 0..3'. Prefetch buffers are assigned based on low-order (word) addresses. This means that a given load can only hit in at most one prefetch buffer, so a single comparator can be used to detect a miss (though a large number of muxes are still required, I think).

Index registers
---------------

Loads/stores use index registers to access content. The memory is bit-addressable through these registers. The addresses contain:

18 bits for 16-bit word address
4  bits for bit-address
10 bits for accumulator

Thus, index registers are 32-bit long

Index registers are updated using Bresanham interpolation:

    Acc += Increment
    if Acc > Overflow:
        Index += Update # sign-extend to 22 bits before addition
        Acc -= Overflow

Both Increment and Overflow are 10-bit values, while update is an 12-bit, signed integer.

A single 'step' instruction can be used to update an index register. There are a total of 16 (?) index and another 16 inc/update/ovfl registers; though the examples below spell out the constants as immediates. Not sure which one is better.

'zero' instructions can be used for zeroing out the accumulator part.

Loads and stores can have an auto-update feature.

Pixel values are loaded into Pixel registers. Simple BLIT/ALU operations are supported between pixel registers. There's a total of 4 pixel registers. Pixel registers are 8-bit wide.

Loops
-----

We have 4 loop registers. These are used with 0-overhead loops. The way it works is there's a 4-depth loop FIFO. Each loop instruction pushes it's loop pointers into the loop FIFO. Instruction fetch checks current PC against top of FIFO and in case of a match, does a decrement of the requisite loop register and conditionally jumps to the head address.

The loop FIFO contains two program addresses of (?) bits each and a 2-bit loop-register index.

The main complication comes in when we consider performance: we don't just want to execute one instruction per cycle. We want to execute one *inner loop* per cycle.

The way to achieve that is staggered execution of inner loop iterations on parallel engines. This is indicated by the PLOOP instruction.

There are a number of complexities here, mostly revolving around loop-carried dependencies. These are:

1. Only registers allowed to carry dependencies through iterations are the 'index' registers.
2. An index register can only be updated once in a loop (or loop segment or something)

Sample code
-----------

8-bpp frame buffer
~~~~~~~~~~~~~~~~~~

I0 = 0 # Index register 0 starts at address 0 (base address for the frame buffer)
LOOP L0, 240: # loop for each scan line, that is 240 times
    PLOOP L1, 320, 2: # loop for each pixel, that is 320 times, unroll the loop 2 times
        LD P0, 8, I0, (1,1,8) # Load 8-bit pixel into P0, update I0 using simple linear addressing with 8-bit increments
        PX_PUSH P0 # Push P0 into pixel render FIFO
    NOP # Needed as nested loops can't end on the same address


8-bpp frame buffer with single 2-bpp sprite
-------------------------------------------

I0 = 0 # Index register 0 starts at address 0 (base address for the frame buffer)
I1 = Sprite1Base
LOOP L0, 240: # loop for each scan line, that is 240 times
    PLOOP L1, 320, 5: # loop for each pixel, that is 320 times, unroll the loop 5 times
        LD P0, 8, I0, (1,1,8) # Load 8-bit pixel into P0, update I0 using simple linear addressing with 8-bit increments
        LD P1, 2, I1, (1,1,2) # Load 2-bit sprite into P1, update I1 using simple linear addressing with 2-bit increments
        LOOKUP P1, P1, Sprite1Palette # Use lookup to make P1 into a palette index
        MASK P0, P1, P0 # Blit registers together
        PX_PUSH P0 # Push P0 into pixel render FIFO
    NOP # Needed as nested loops can't end on the same address

Let's look at how the 2nd algorithm would execute. We need 5 engines:


Cycle 1:    LD P0, 8, I0, A0         ---------------------    ---------------------    ---------------------    ---------------------
Cycle 2:    LD P1, 2, I1, A1         LD P0, 8, I0, A0         ---------------------    ---------------------    ---------------------
Cycle 3:    LOOKUP P1, P1, s1p       LD P1, 2, I1, A1         LD P0, 8, I0, A0         ---------------------    ---------------------
Cycle 4:    MASK P0, P1, P0          LOOKUP P1, P1, s1p       LD P1, 2, I1, A1         LD P0, 8, I0, A0         ---------------------
Cycle 5:    PX_PUSH P0               MASK P0, P1, P0          LOOKUP P1, P1, s1p       LD P1, 2, I1, A1         LD P0, 8, I0, A0
Cycle 6:    LD P0, 8, I0, A0         PX_PUSH P0               MASK P0, P1, P0          LOOKUP P1, P1, s1p       LD P1, 2, I1, A1
Cycle 7:    LD P1, 2, I1, A1         LD P0, 8, I0, A0         PX_PUSH P0               MASK P0, P1, P0          LOOKUP P1, P1, s1p
Cycle 8:    LOOKUP P1, P1, s1p       LD P1, 2, I1, A1         LD P0, 8, I0, A0         PX_PUSH P0               MASK P0, P1, P0
Cycle 9:    MASK P0, P1, P0          LOOKUP P1, P1, s1p       LD P1, 2, I1, A1         LD P0, 8, I0, A0         PX_PUSH P0
Cycle 10:   PX_PUSH P0               MASK P0, P1, P0          LOOKUP P1, P1, s1p       LD P1, 2, I1, A1         LD P0, 8, I0, A0

You can see how - after warming up the pipeline, we generate a pixel every clock-cycle. This does mean though that we need to be able to execute 5 (!!) instruction streams in parallel.
Once the warmup is complete, we write P0, P1, I0, I1, A0, I1, P1', P0' in every clock cycle. This means:

1. We need individual accumulator engines for every I register.
2. We need many copies of the P registers: these need to be per pipeline instances - that's many many small register files; 32-bits each. Not *that* much, given all the other complexity, but it adds up.
4. We need per pipeline ALUs, most likely
5. We need per pipeline LOOKUP engines (and associated lookup tables) that's **LARGE**

And of course the real algorithm is not this simple: we need to keep track of start and end coordinates both in X and Y direction for sprites and predicate the MASK operation based on those results.

The full algorithm is something like this:

I0 = 0 # Index register 0 starts at address 0 (base address for the frame buffer)
I1 = Sprite1Base
C0 = Sprite1X # Constant register contains the X coordinate for the sprite
C1 = Sprite1Y # Constant register contains the Y coordinate for the sprite
C2 = Sprite1X+32 # Constant register contains the Y coordinate for the sprite
C3 = Sprite1Y+32 # Constant register contains the Y coordinate for the sprite
LOOP L0, 240: # loop for each scan line, that is 240 times
    SET_PR PR1, L0 >= C1
    IF PR1 SET_PR PR1, L0 < C3
    PLOOP L1, 320, 8: # loop for each pixel, that is 320 times, unroll the loop 5 times
        LD P0, 8, I0, (1,1,8) # Load 8-bit pixel into P0, update I0 using simple linear addressing with 8-bit increments
        CLR_PR PR0
        IF PR1 SET_PR PR0, L1 >= C0
        IF PR0 SET_PR PR0, L1 < C2
        IF PR0 LD P1, 2, I1, (1,1,2) # Load 2-bit sprite into P1, update I1 using simple linear addressing with 2-bit increments
        IF PR0 LOOKUP P1, P1, Sprite1Palette # Use lookup to make P1 into a palette index
        IF PR0 MASK P0, P1, P0 # Blit registers together
        PX_PUSH P0 # Push P0 into pixel render FIFO
    NOP # Needed as nested loops can't end on the same address

Now the inner loop is 8 instructions long. By the time we have 7 sprites, the loop length grows 6*7+2=44 instructions long. And we haven't even done anything 'fancy', such as collision detection. For this to generate one pixel at a time, we would need **64 independent instruction pipelines**.

Since we can't guarantee that pipelines don't access C (constant) registers in parallel, they would need a copy of those too. Checking L (loop) registers is also complex, albeit maybe not all that complex: each pipeline by definition has a fixed value for all the loop registers; still those copies need to be maintained somewhere.

In other words, there's a lot of state per pipeline to keep track of and there are a ton of pipelines. This doesn't look terribly feasible.

Descriptor-based controller
===========================

What if, instead of having a complete GPU - which is prohibitively expensive, we did something simpler: the pipeline is still fixed-function with the plane-compositor and the sprites and the character mode and all that. But!

There's an extra DMA channel that can pull a a linked-list of descriptors. These descriptors contain register address/value pairs, have a length and a 'next' pointer plus some trigger mechanism.

This way, we can set up a 'program', rather Amiga-style, to change the display controller behavior. What's more, one can imagine this being the primary method of programming the display controller, meaning that most registers don't even need to be mapped. A descriptor would look something like this:

<Next pointer (16 bits, 8-byte aligned)>
<Length (16-bits)>
<Trigger (4-bit type, 12-bit parameter) - triggers the start of the fetch of the *next* descriptor>
<register update (8-bit address, 8-bit value)>
...

The trigger could be:
- unconditional
- specific scan-line (end of that scan-line)
- frame-end
- specific position in scan-line
- sprite collision
- never

Multiple cascaded descriptors can be used to set up complex triggers (such as X-Y triggers).

I'm wondering about double-buffering of registers for atomic updates, though that sounds very expensive. Maybe a few crucial ones can be handled that way?

The shortest descriptor is 6 bytes long, but due to the 8-byte alignment they would consume 8 bytes.

Descriptors are normally put into a loop, where one of them would trigger on frame-end, thus synchronizing the execution with the frame-rate. 'never' triggers can be used to terminate the chain.

Prefetch
========

This is another idea we can resurrect from the GPU discussion above:

1. We would have a single prefetcher engine that fills in buffers. These buffers - in a way - are a direct mapped cache. We have to be careful though in that collisions between streams would be very common. Maybe requestor-index is part of the hash or something. We could also allocate certain parts of the cache to certain requestors in a configurable manner.

Every cache line would have a physical address and a valid bit, potentially a valid bit-mask. Each line should be 32-bits long. The physical address is 18 bits. Since we fetch from 16-bit boundaries, the two valid bits would extend that to 20 bits total.

Let's say we have a static set of buffers allocated for each requestors. These are:

- Plane 0..3
- Sprite 0..7
- Audio ???
- Descriptor chaser

Each sprite needs two blocks (that's 16 total), planes would need 8 total, which leaves 8 for other needs.

The block assignment for planes is dependent on bit-depth: the number of blocks allocated is the same as the number of bits used: 8; 4; 2 or 1. Each block contains an extra byte of 'last read' buffer. As long as the (byte) address doesn't change, reads can served from this buffer. If the byte address changes, but still hits in the buffer, the read is served from the block and the last-accessed byte is stored in the buffer. There's also a counter that increments every time the address changes. When this counter reaches 3, the prefetch logic is activated, starting to fill the block with the 'next' assigned values. This assignment is based on:
- The number of blocks assigned for the same consumer (i.e. if 4 blocks are assigned, the block base address is incremented/decremented by 16)
- The direction of the addressing; this can be determined by whether the first or the last byte was accessed when the trigger to refill happened - really just bit-2 of the address.
- Refills can also be triggered by a full blown address mis-compare; this is simply a cache miss.

Refills of buffers are *not* critical-word-first and a buffer becomes useable again only after it is fully filled. Till then the 1-byte buffer can serve further requests, if the addresses line up, otherwise the requestor is blocked.

**This triggering mechanism and buffering is sub-optimal**. What we should be doing instead is to interleave the buffers: for a 4-buffer configuration, block 0 would contain bytes for address A; A+4; A+8 and A+12. Block 1 would similarly contain A+1; A+5; A+9 and A+13. This complicates filling the buffers somewhat, but allows for the 1-byte buffers to contain the last 8 pixels worth of data for any bit-depth and also trigger multi-block refills in one go (with some effort, we'll have to be careful of not causing full-on misses by being too quick with pre-fetch).

Let's think about this extra effort: the pre-fetch gets triggered when the first of (say 4) blocks accesses the last byte. The prefetch starts 1 cycles later, and 2 cycles after that the byte for the second block arrives. At this point we should load the last (we know which from the pre-fetch direction) byte into the buffer and mark the block 'update pending'. In this mode, the address compare still works, but if the accessed byte is not in the buffer, a full-on miss is triggered. Eventually, after 6 cycles (in case of a 16-byte burst to fill the 4 blocks), the last byte of each buffer starts to arrive. At this point, we need to update the address contained in the block and clear the 'update pending' bit, plus invalidate the data in the buffer byte. If at that point the requestor is still not done with the previous address range, we will have some misses, which will stall the requestor. **This means that programming must be done carefully: block count is not really a function of bit-depth, but of pull-rate**. For instance, fractional addressing and lots of pixel repetition can cause misses even in 8-bit mode at high resolutions. Not only that, but as the fractional addressing rate is changed (for instance to draw a magnified sprite) the block assignment might need changing as well. That sounds ... well ... difficult to deal with.

I think the idea should be that - instead of reprogramming the number of blocks - one could specify which of the bocks trigger the pre-fetch operation. In fact, maybe this can be learned? Such as, if we run into an overrun, we terminate the pre-fetch, but change the trigger block by as many as we've overrun by. Similarly, if we underrun, we block the requestor and move the trigger block earlier.

This starts to be a rather complex little thing, so I think I will need to lock it up on a fixed 4-block (or 8-block) variant.

Each cache block would be
--------------------------

32-bit cache-line
 8-bit last-read buffer
 1-bit last-read-valid
 2-bit last-read address (maybe single-bit is sufficient)
 1-bit update pending
16-bit base address (since blocks are 32-bit aligned)
 1-bit line valid
 2-bit edge-accessed state
-------------------------
63 bits of state information

Interface wise they would have:

Towards the bus interface:
- SOS request output (triggered in case of a blocking miss)
- prefetch request output (triggered when the second edge byte is accessed)
- prefetch direction output (decrementing or incrementing prefetch)
- request address (either the base address or the miss-address; in case of a base-address, it is incremented/decremented by the prefetcher, in case of a miss-address, it is not touched by it)

From the bus interface:
- Set update pending
- Clear update pending
- Write data (8-bits)
- Write data address (2-bits)
- Base address (16 bits) - gets written with 'clear update pending'

From a requestor:
- Request address (18-bit byte and 3-bit bit-address)
- Request width (2 bits for 1;2;4;8 bits)
- Pre-request (1-bit, signifies that we want to load the last-read buffer, if possible, but don't want to trigger a miss or a prefetch)

Towards requestor:
- Miss (or stall or valid or something similar, though all these are ready-valid interfaces anyways)
- Data (8-bits)

Block-to-requestor connectivity
--------------------------------

There is some muxing here as there could be multiple blocks connecting to a single requestor. This is based on the lower order (1;2;3) bits of the request address and controls the 'pre-request' bit as well as where the data and the potential stalling is coming from. This muxing is dynamic and is based on register settings.

Block to prefetcher connectivity
---------------------------------

The prefetcher looks at all the 16 blocks in every clock-cycle and determines which one to serve, based on the following:

- SOS requests have priority (these are served by a single-block fill)
- Fixed lowest-to-highest block priority (masked by block-grouping and trigger-block selection)

If there is a valid request, the appropriate burst is initiated to fetch the blocks for memory, including:
- generating (inc/dec) the base address
- masking the low-order bits to align the request
- control burst size based on block grouping

While fetching, it pays attention to over-fetching (how???, there's no signal exposed for this???) and terminates the burst

Bus interface
--------------

This is the usual affair of dealing with bus contention, DRAM signalling etc. We can lift - I think - a lot of this from Espresso, but it's going to be greatly simplified as there's just one client (the requestor) and just one access type (DRAM burst into a single bank). So maybe a cleaner re-implementation is better choice.

Pipelining
-----------

We should not be terribly sensitive to pipeline depth, except for the misses and their associated SOS requests. Those stall, so the deeper the pipeline, the more painful they are. However, they should not be terribly common to being with, so maybe it's not a big deal. Also, stalls can be hidden further down the pipeline by a pixel FIFO after compositing.

Size estimation
---------------

The cache itself has 63*16~=1024 bits of data. That's ... a lot.

.. NOTE::
    Given that the above setup requires 1024 bits of storage, what if we tried to do this with some embedded memories? We know that:

    - We write no more than 16 bits in every (8MHz) clock cycle
    - We read no more than 8 bits in every (12.5MHz) clock cycle (this assumes that sprite buffers are still separate and those reads are managed in the blanking interval; based on 640x480@4bpp).

    So, if we think we can close timing at 12.5MHz, which is more or less a requirement for all that we do here, we can say that no more than 16 bits are read or written from the memory at any clock cycle. That however doesn't mean that we read consecutive 16 bits. We really should have 16 independent bit-planes, that are individually addressable. This is problematic though as the bus interface might want to write 16-bits into a single bit-plane on a single clock cycle and do that for the duration of a burst. So, while the average write rate is low, the burst is very high. There's also the problem that by the time we split the memory into 16 units to deal with the per-bit-plane addressability, we're not any better off than the previous setup: we'll end up with mere 64 bits per plane.

    It's also very unclear how to handle the address generation for reads and writes while de-conflicting all the contenders.

    I don't think this is a viable route forward.

Still, this doesn't solve the problem of needing to conjure up 1kbit registers. For comparison, Espressos register file is 15x32~=512 bits. So this is twice that.

Character mode
===============

Let's assume for a minute that we do have this prefetch mechanism. That works well for sequential addressing, but not for character modes, that's horrible. So, how should we do character mode?

The idea there would be - to be nice with the memory subsystem is the following:

The organization of the character map is such that the same scan-line of each character is adjacent to one another and occupy a 256-byte long (naturally aligned) region of memory. That way, a single burst can be used to retrieve the whole scan-line worth of character patterns, provided we have the character codes in on-chip RAM already.

To minimize on-chip storage, we also store tha character codes in one array and the attributes in another.

To limit burst length, we only have a 32-character buffer on chip. The process is the following:

1. read 32 character codes using a single burst (32-byte transfer, using 4 blocks)
2. read 32 character scan-line values using a single burst, but **bypassing** the prefetcher. Replace the character codes with the results in the prefetch buffers
3. read 32 attribute bytes using a single burst (32-byte transfer, using another 4 blocks)

While we're reading the attributes from memory we can also consume them as well as the character scan-lines and produce the pixel output.

32 of course is a random number, it could be any value. In fact, 16 might be better as it divides 80 evenly.

The thing to note here is the funky use of the prefetcher blocks in step 2: we're replacing the content without updating the metadata, or, maybe by replacing the metadata with something special. Also, while that operation is a burst, it's not a prefetch: it's a 'gather' burst.
