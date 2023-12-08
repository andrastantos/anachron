Introduction
============

For the Anachronistic Computer, we need a properly anachronistic processor. As it turns out, I just have the design! I have been toying around with an instruction set design lately: the `Brew <https://github.com/andrastantos/brew>`_ architecture. Espresso, the main processor of the Anachronistic Computer is a simple, low-end implementation of this architecture.

Espresso is a bit more than just a Brew implementation however. It contains a memory controller, a refresh generator and a DMA controller as well.

Just like the Anachron project as a whole, the Espresso processor is aimed as an imaginary design from the early '80s. It has to adhere to the technological limitations of the age, and be a 'good citizen' in the ecosystem of the era.

I imagine Espresso to be manufactured in 1.5um (N)MOS technology and to have a target clock rate of about 8-10MHz. It is intended to be a contemporary of the Intel 80286 and the Motorola 68010 processors, while being smaller (in die area) and faster. Espresso fits in a 40-pin DIP package, running from a single 5V power supply and a simple 50% duty-cycle clock source.

Putting all these features together, Espresso should have been a cheaper, higher-performance option for the time.

The high-level block diagram of the design is the following:

.. image:: images/espresso_block_diagram.svg
    :width: 100%

.. admonition:: Why?

    So, why Brew for this project? Mostly because ... why not? It's a riff on a variable-instruction-length RISC architecture, which straddles the RISC vs. CISC divide that started to emerge around that time in CPU architecture. It fits right in. It's also a 32-bit ISA with a 16-bit instruction encoding, something that would have been rather valuable in those memory-constrained days.

    One of the biggest, if not *the* biggest obstacle for improving performance of processors is memory speed. The traditional answer to this problem is the introduction of ever deeper levels of cache hierarchy. For our design target, however caches are not really possible: they are too big to have them on die and require too many pins to have them off.

    What's left? Getting the memory interface as fast as possible. The technology landscape, being what it was, forces us to use page-mode (not even fast-page-mode) DRAM memories with access times of 100ns or so.

    I decided the best way to maximize memory bandwidth is to directly interface to DRAM and generate page-mode bursts wherever possible. The consequence of that decision is that the memory controller (including refresh generation) became part of the processor.

    The benefit is highly reduced pin-count; not only I was able to (forced, really) to multiplex the address-bus, I had the opportunity to address two banks of memory in alternating halves of the clock-cycle: effectively implementing DDR access.

    To further improve efficiency (on the system level), spending as little time on bus arbitration as possible is also important. We need some way of accepting request from and granting bus-accesses to external peripherals anyway (chiefly the display controller). Integrating a DMA controller is not that big a leap from there. Such integration is beneficial as we save a lot on package cost (no need for yet another package) and add relatively small amount of silicon to the processor.

ISA differences
---------------

There's a lot to say about the `Brew instruction set architecture <https://github.com/andrastantos/brew>`_, but this is not the place. Here, you will only see the differences, additions and implementation details about the Espresso core.

Espresso mostly adheres to the Brew ISA, but for various reasons there are a few differences:

 - It has a very simple in-order memory model, so no fence instructions make sense
 - It has no caches either, so cache invalidation is out
 - No extension groups: these would make decoding more complex and the functionality provided by them are not needed
 - No types, everything is INT32
 - No floating point ops (especially in unary group)
 - No type override loads or stores
 - No reduction sum (:code:`$rD <- sum $rA`)
 - No lane-swizzle (since we don't have vector types and the requisite muxes are large)
 - No synchronization (load-acquire; store-release) primitives



Memory access patterns
----------------------

Since Espressos internal implementation is tightly coupled to - and optimized for - its external memory interface, it's performance is largely predicted by the memory access patterns on this interface.

Espresso supports 8-beat bursts for instruction fetches, and 2-beat bursts for memory accesses. Each beat transfers 16-bits of data. Each burst is preceded and followed by a clock-cycle of extra activity (to satisfy DRAM timing requirements). This means that a 16-byte instruction fetch burst takes 10 clock cycles, while a 32-bit load or store takes 4 clock cycles on the bus.

.. admonition:: Why?

    Loads and stores can only use up to 4-beat bursts; Espresso can't deal with more than 32-bits of data at a time. Instruction fetch bursts can be much longer as long as we can put the fetched data in some temporary buffer, but there's a limit: every time the code branches, we have to throw away all the prefetched instruction words and start over from the new location. There is a balance between the amount of data we are willing to throw away and the benefits of a long burst. Profiling shows that the optimum point is 8 word (16-byte) long bursts.



Mips/MHz (IPC) expectations
---------------------------

We should expect about 25% of our operations to be memory accesses, stalling for 3 cycles. Branches, which happen about 12.5% of the time would have a penalty of ~5 clock cycles. Other hazards will add about one stall every 8 instructions. On top of this, our instruction length on average is 24 bits, so we should expect 0.5 cycles of stall just from instruction assembly. An extra 2/10th of stall comes from the burst overhead of the DRAM access patterns for fetches. This gives us 2.2 stall cycles for every instruction executed, or an expected IPC of 0.31.

Memory bandwidth implications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A video of 320x240 resolution, 8 bits per pixel and 50Hz update rate (this is PAL video) would need 3.84MByte/sec of data on average. Higher during active lines, but nothing during blanking and sync periods. With the 10-cycles-for-16-bytes burst rate, we would need 2.4M memory cycles every second to refresh the screen. However, we should probably add about 4 cycles of memory arbitration lost between the CPU and the video controller for every burst, resulting in 3.36M cycles for display activity. At a 10MHz clock rate, this leaves us with 6.64M cycles for CPU access.

An IPC of 0.31 at 10MHz means that the processor would need to fetch 3.1M instructions (at 24 bits each) every second, resulting in 9.3MByte/sec fetch requirements. That amount of data needs 5.81M cycles to transfer after considering the burst overhead.

Out of the 3.1M instructions, 0.775M would either a load or a store, each requiring 4 cycles on the bus to complete. This is an extra 3.1M cycles.

Adding it up: 3.36M for video, 5.81M for fetch and 3.1M for load/store = 12.27M cycles. But we're running at 10MHz, we only have 10M cycles to work with in every second.

The result is that the processor will get throttled by video: we won't be able to achieve our 0.31 IPC once we turn video on. The real number should be around 0.23 instead.

Comparison
----------

Let's quickly compare Espresso to its imaginary contemporaries:

==============   ========   ==========================   =========
Chip             Year       Cost (small quantities)      MIPS/MHz `* <https://en.wikipedia.org/wiki/Instructions_per_second>`_
==============   ========   ==========================   =========
6502             1977       $25 ('77)                      0.43
Z80              1976       $20 ('77)                      0.145
Intel 8088       1979       $125 ('79) $14 ('81)           0.075
MC68000          1979       ~$400 ('79) $125 ('81)         0.175
Intel 80286      1982       $155 ('85)                     0.107
MC68010          1982                                      0.193
**Espresso**     *1982*     *~$85* [#note_cost]_         *~0.23*
MC68020          1984       $487 ('84)                     0.303
Intel 80386      1985       $300 ('85)                     0.134
ARM2             1986                                      0.5
MC68040          1987                                      0.36
Intel 80486      1989                                      0.3
==============   ========   ==========================   =========

.. [#note_cost] Cost estimation is based on silicon area ratio and package pin-count ratio of the Intel 80286.

CoreMark
........

I managed to get my hands on a number of old PC motherboards, so I could actually run some comparisons. I've used CoreMark as the benchmark of choice, because it's relatively modern, yet - being targeted at embedded platforms - it's rather unassuming. It doesn't try to draw on a display, not interested in vector processing or 3D graphics performance, the stuff of modern benchmarks.

It also doesn't depend on an underlying OS (with file-system, process- and memory-management) like the 'spec' benchmarks do. Also, it's free.

So, the results:

================= ============ ======== ============= =========================
Processor         Clock speed  CoreMark CoreMark/MHz
================= ============ ======== ============= =========================
**Espresso**       *6MHz*       *4.19*    *0.70*
80286               6MHz         2.59      0.43        Turbo off
80286              12MHz         5.38      0.45        Turbo on
80386              28MHz         7.53      0.27        16-bit mode, turbo off, 64kB external cache
80386              40MHz         8.98      0.22        16-bit mode, turbo on, no external cache
80386              40MHz        12.05      0.30        32-bit mode, no cache
80386              40MHz        21.59      0.54        16-bit mode, turbo on, 64kB external cache
80386              40MHz        26.47      0.66        32-bit mode, 64kB external cache
80486              33MHz        15.49      0.47        16-bit mode, turbo off, 256kB external cache
80486              33MHz        35.58      1.08        16-bit mode, turbo on, 256kB external cache
80486              33MHz        44.94      1.36        32-bit mode, 256kB external cache
80486DX2           66MHz        71.78      1.09        16-bit mode, 256kB external cache
80486DX2           66MHz        89.77      1.36        32-bit mode, 256kB external cache
================= ============ ======== ============= =========================

*Methodology for PCs:*

I've used `ia16-elf-gcc <https://launchpad.net/~tkchia/+archive/ubuntu/build-ia16/>`_ for 16-bit mode compilations. This generated a 'tiny' .com file, running under DOS in real mode.
I've used `djgpp <https://github.com/andrewwutw/build-djgpp>`_ (version 12.2.0) for 32-bit compilations. This generated an .exe file that run under a dos-extender in protected mode.

For the operating system, I've used `FreeDOS 1.3 <https://www.freedos.org/>`_, with as minimal amount of drivers loaded as I could. All the machines used a VGA card for display and a CFCard and a 1.44" floppy for storage. Not that any of this should matter...

*Methodology for Espresso:*

I've used my port of GCC and NewLib to the platform, with -o2. I ran the test on an FPGA platform, with 100 iterations. I captured run-time using performance counters, counting up the number of clock-cycles the execution took. DRAM refresh was active during the simulation, but there were no other disturbance. The code executed in TASK mode, not that it matters. Since the results are reported in clock cycles, they need to be scaled to a chosen clock rate (6MHz in this case). I chose this clock rate to match that of the 80286. It would be easily achievable in real HW, even with very slow (and cheap) DRAM.

*Observations*:

It's interesting to see that - while the 16- or 32-bit version of the code does have measurable delta on the same platform, the jump is not as dramatic as I thought it would be. The benchmark is certainly a 32-bit one, and a 16-bit compiled variant would use multiple instructions to compute any and all 32-bit results.

The behavior of the 'turbo' switch on these motherboards is strange. On the 80286, it's straight-forward: it cuts the clock rate in half. On the 80386 one, it's more complicated. This motherboard also contains an external cache, maybe the turbo switch mocks with that? Since the CoreMark/MHz rating changes depending on the turbo status, it can't simply be the change in clock rate. For the 80486 motherboard, I have even less clue what is going on.

The fact that the 80486DX2 is almost twice as performant as the 80486 shows that not much of the external world impacts the benchmark results: the code probably is running almost entirely inside the on-chip cache. That of course makes it even more mysterious how the turbo switch can influence the results in such a dramatic way.

It's also nice to see how Espresso stacks up. From the MIPS/MHz numbers above, I have expected it to be in between a 80386 and a 80486. In fact it is. More or less. Of course, it's heard-warming to see that my little creation holds its own (MHz to MHz) gainst a 80386, even compares reasonable well to a 80486, but I have doubts that this would translate to real-world performance. This is just one benchmark after all, one that is arguably not all that close to what these processors would do in reality.

It's also important to note that Espresso would not be able to run at 33MHz or anything close to it: not only would it be limited by the clock rates achievable in 1.5u, it's architecture directly ties it to the memory speed. It would max out at around 12MHz with the highest speed (non-FPM) DRAMs that were available.

Still, the comparison shows the future potential of the Brew architecture: an updated memory interface (with FPM support), some internal instruction cache to decouple the CPU clock for memory speed and it would be quite competitive with more advanced Intel processors.

