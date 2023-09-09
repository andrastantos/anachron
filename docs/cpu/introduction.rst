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


Comparison
----------

==============   ========   ==========================   =========
Chip             Year       Cost (small quantities)      MIPS/MHz `* <https://en.wikipedia.org/wiki/Instructions_per_second>`_
==============   ========   ==========================   =========
6502             1977       $25 ('77)                      0.43
Z80              1976       $20 ('77)                      0.145
Intel 8088       1979       $125 ('79) $14 ('81)           0.075
MC68000          1979       ~$400 ('79) $125 ('81)         0.175
Intel 80286      1982       $155 ('85)                     0.107
MC68010          1982                                      0.193
**Espresso**     *1982*     *~$85* [#note_cost]_         *~0.27*
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
**Espresso**       *6MHz*      *15.9*     *2.65*
80286               6MHz         2.59      0.43        Turbo off
80286              12MHz         5.38      0.45        Turbo on
80386              28MHz         7.53      0.27        16-bit mode, turbo off, 64kB external cache
80386              40MHz        21.59      0.54        16-bit mode, turbo on, 64kB external cache
80386              40MHz        26.47      0.66        32-bit mode, 64kB external cache
80486              33MHz        15.49      0.47        16-bit mode, turbo off, 256kB external cache
80486              33MHz        35.58      1.08        16-bit mode, turbo on, 256kB external cache
80486              33MHz        44.94      1.36        32-bit mode, 256kB external cache
80486DX2           66MHz        71.78      1.09        16-bit mode, 256kB external cache
80486DX2           66MHz        89.77      1.36        32-bit mode, 256kB external cache
================= ============ ======== ============= =========================

*Methodology for PCs:*

I've used :ref:`ia16-elf-gcc <https://launchpad.net/~tkchia/+archive/ubuntu/build-ia16/>` for 16-bit mode compilations. This generated a 'tiny' .com file, running under DOS in real mode.
I've used :ref:`djgpp <https://github.com/andrewwutw/build-djgpp>` (version 12.2.0) for 32-bit compilations. This generated an .exe file that run under a dos-extender in protected mode.

For the operating system, I've used :ref:`FreeDOS 1.3 <https://www.freedos.org/>`, with as minimal amount of drivers loaded as I could. All the machines used a VGA card for display and a CFCard and a 1.44" floppy for storage. Not that any of this should matter...

*Methodology for Espresso:*

I've used my port of GCC and NewLib to the platform. I ran the test under RTL simulation, where I simulated 128kB of DRAM with the system. I captured run-time using performance counters, counting up the number of simulated clock-cycles the execution takes. Needless to say, such a run takes forever, so I've only ran one iteration. That is against the official rules, but since the setup is perfectly deterministic, I don't see how it should matter. DRAM refresh was active during the simulation, but no other disturbance was simulated. The code executed in SCHEDULER mode, again, not that it matters. Being a simulation, the results needed to be scaled to an arbitrarily chosen clock rate (6MHz in this case). This clock rate would be easily achievable in real HW though, even with very slow (and cheap) DRAM.

*Observations*:

It's interesting to see that - while the 16- or 32-bit version of the code does have measurable delta on the same platform, the jump is not as dramatic as I thought it would be. The benchmark is certainly a 32-bit one, and a 16-bit compiled variant would have needed to use multiple instructions to compute any and all 32-bit results.

The behavior of the 'turbo' switch on these motherboards is strange. On the 80286, it's straight-forward: it cuts the clock rate in half. On the 80386 one, it's more complicated. This motherboard also contains an external cache, maybe the turbo switch mocks with that? Since the CoreMark/MHz rating changes depending on the turbo status, it can't simply be the change in clock rate. For the 80486 motherboard, I have even less clue what it does.

The fact that the 80486DX is almost twice as performant as the 80486 shows that not much of the external world impacts the benchmark results: the code probably is running almost entirely inside the on-chip cache. That of course makes it even more mysterious how the turbo switch can influence the results in such a dramatic way then.

It's also surprising how *well* Espresso stacks up. From the MIPS/MHz numbers above, I would have expected it to be around a 80486. It is way passed that threshold. Of course, it's heard-warming to see that my little creation outperforms (MHz to MHz) a 80486, but I have doubts that this would translate to real-world performance. This is just one benchmark after all, one that is arguably not all that close to what these processors would do in reality.

This also shows the future potential of the Brew architecture, if it can be scaled to the same clock speeds that subsequent Intel processors achieved.
