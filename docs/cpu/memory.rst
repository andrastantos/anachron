Memory
======

Espresso has a rather simplified memory model:

Loads and stores are performed in-order and they stall the pipeline until completion (in case of writes, until all side-effects are reflected in the target).

Access rights and protection
----------------------------

For TASK mode, there is a `base` and a `limit` register. Memory references are relative to the `base` register and generate an access violation exception, if they reach beyond the `limit` register. This allows for some basic process isolation, but not for any detailed management of access rights. In fact, there is a different pair of registers for instruction fetches and load/store operations. This helps with shared library implementation, but still... simple.

In SCHEDULER mode there's no protection: logical and physical address are one and the same.




There is a TASK_BASE and TASK_LIMIT register in the processor. In TASK mode, logical addresses are compared against the TASK_LIMIT register. Accesses (instruction fetches or load/store operations) beyond the limit are not permitted and an access violation exception is thrown. The logical-to-physical mapping is achieved by adding TASK_BASE to the logical address. In fact both TASK_LIMIT and TASK_BASE registers can be quantized to 4kB page-boundaries, further simplifying operation.

In SCHEDULER mode TASK_BASE and TASK_LIMIT registers are not consulted and SCHEDULER mode operates in physical addresses.

There are some obvious limitations to this scheme:

#. Tasks can have access to a single, contiguous section of the physical address space. This in practice means they can only have access to DRAM (as they *do* need access to that and we can only control one region), which in turn means that all I/O accesses will have to be marshalled to SCHEDULER mode. Alternatively, one can setup a single TASK with both BASE and LIMIT being set to 0 and use this task as a highly trusted, monolithic God-process with full access to all resources.
#. Since the accessible physical address space for each task must be contiguous, memory fragmentation is a problem, something that can only be solved by de-fragmentation-by-copy.
#. Shared memory between processes is practically not possible.
#. Virtual memory (page files) and memory-mapped files are not practical.


Access rights
-------------

Now, on to access rights. The processor architecture doesn't really define any memory protection scheme, all it really does is to make sure that everything goes through whatever this external protection logic is. This includes CPU-specific CSR registers.

While the canonical way of dealing with access rights and protections is through a paging MMU, the implementation of BREW for Anacron doesn't have enough silicon area (remember, we try to work with 1.5um silicon process) to implement that. Thus, a much simpler protection scheme is used:

In TASK mode, every memory access is offset by a `base` register and checked against a `limit` register. This sets up a contiguous window in physical memory, that a the process can access. There is one such window for instructions and another for data. Anything below the `base` is inaccessible (no negative addresses are supported) and anything above the `limit` would generate an access violation exception.

In SCHEDULER mode, these registers are simply assumed to be 0, giving access to the whole physical address space without translation.

Such a simple scheme has limitations. It is sufficient to protect user-mode processes from one another and SCHEDULER mode from user-mode processes. However, drivers and OS components will need complete open access to every HW resource: there's no way to be more granular about permissions. This is a problem, but an acceptable compromise, I decided.

DRAM access
-----------

Historical rant
~~~~~~~~~~~~~~~

One thing that annoyed me a lot every time I looked at schematics of these early machines was the interface to DRAM. When I tried to design my own, I also have found the problem very annoying. Now, looking back, it's not only that: it's also very inefficient. This was fine for a processor such as the 6502 in a C64: the processor had a slow enough clock that it didn't matter. Faster machines, such as the Amiga or even the PC needed two banks of memory to get around the inefficiency: one for video, one for the processor. Others, such as the Macintosh could only really support black-and-white graphics, partly due to (originally) memory size limitations, but also because of memory bandwidth issues.

DRAM memories had a multiplexed address bus: every access needed two cycles. That is, in the general case. Nearby memory locations could be accessed in a single cycle. This technique was called 'page mode'. Later, this evolved into 'fast page mode', and 'enhanced read-out' (EDO) memories. Eventually, in SDRAMs, the technique evolved into burst-mode accesses. However, machines of the area almost exclusively used discrete logic to implement the DRAM interface, and thus could not take advantage of page mode accesses.

On the other side, many processors (Intel, I'm looking at you) *also* had a multiplexed bus. It's just that they `multiplexed data and address <https://www.ndr-nkc.de/download/datenbl/i8088.pdf>`_ on top of each other.

A PC design for instance, first needed to de-multiplex the processor bus just to then be able to multiplex it *again* for the DRAMs needs.

Surely, there must be a better way!

Address muxing
~~~~~~~~~~~~~~

There are two major benefits for muxing address pins on the external bus interface:

1. This is what the DRAM does: we can have a fast, direct interface to memory
2. We save pins.

The down-side of course that now we made non-DRAM interface more complicated and slower. The saving grace is that most non-DRAM 'things' in a machine are EPROMs or peripherals, both usually being slower than DRAM anyway.

Another down-side is that the CPU and the memory speed are now tied to each other.

Lastly multiplexing addresses to the same pins is a little complex, if one wants to support decent address decoding for peripherals *and* support various DRAM memory sizes at the same time.

Espresso supports the following address-muxing schemes:

=========== ===================== =======================
Pin Name     DRAM accesses         non-DRAM accesses
=========== ===================== =======================
A0           A8   A0               A11  A0
A1           A9   A1               A12  A1
A2           A10  A2               A13  A2
A3           A11  A3               A14  A3
A4           A12  A4               A15  A4
A5           A13  A5               A16  A5
A6           A14  A6               A17  A6
A7           A15  A7               A18  A7
A8           A17  A16              A19  A8
A9           A19  A18              A20  A9
A10          A21  A20              A21  A10
=========== ===================== =======================

Memory size detection
`````````````````````
If the memory is composed of 4164 or 4464-style devices, they will only decode the lowest 8 address bits. Consequently memory starts aliasing after every 128kByte (64kWords). If larger memories are populated, aliasing happens at a different boundary. By testing for aliasing (writing one address and reading the potentially aliasing ones) one can determine the attached memory size.

Memory banks
````````````
Espresso provides two memory banks. Each bank can contain from 128kByte to 8MByte of memory. This allows for a maximum memory configuration of 16MByte. Different sized memories in the two banks are supported.

In order to enable a contiguous memory space, the larger memory bank should be at the lower address and the smaller one at the higher one. If that's not the way memory is populated in the system (and is detected during memory size detection), the two banks can be swapped by SW.

It's important to note that while only 16MByte of DRAM is supported, the physical address space is still 4GB. The limitation comes from the bus interface and should not have been a real problem: 16MB of memory requires 4Mbit devices; this selection of device support should carry us through the the '80s. The 16Mbit DRAM was introduced in '91. If our little line of machines was still alive by then, we would certainly have revved the CPU for something more capable with more pins, most likely with the full 32-bit address bus exposed. So this is fine.

Access to ROM and I/O devices
-----------------------------

Espresso only supports memory-mapped I/O devices; both I/O and ROM devices are treated the same way. A special access qualifier, called `n_nram` is used to differentiate these non-DRAM accesses from DRAM accesses (which are using `n_ras_a/b` signals).

Address de-multiplexing is needed to re-create the customary address bus for these devices. The external 'raw address latch' needs to latch the address pins (addr[10:0]) on the falling edge of `n_nram`. The subsequent falling edge of either `n_cas_0/1` signals is used to mark the beginning of the transfer and the availability of the lower address bits. All non-DRAM accesses are 8-bit wide, while the address bus is providing 16-bit addresses. The LSB of the address can be recovered from `n_cas_0`.

.. todo:: add illustration of address bus re-construction

An address decode can be used to further differentiate between various I/O devices and ROMs. This address decode can operate on the top address bits, which are present in the first address cycle, providing more time for the decoder to perform its selection. It is important to make sure that no actual chip-select signal is issued until the second part of the address cycle, signified by the assertion of either of the `n_cas_0/1` signals.

.. todo:: add illustration of address decode

Wait states
~~~~~~~~~~~

non-DRAM accesses support both internally generated and external wait-states. The number of internal wait-states is decoded from the (internal) address bits A[29:26]. This provides 16 different wait-state settings. The value 0 corresponds to 15 wait-sates, while the value 15 corresponds to 0 wait-states. All of these 16 regions alias to the same externally visible memory regions, the only difference is the number of wait-states generated by Espresso. This mechanism allows for fine-grain wait-state control without sophisticated memory-region configuration logic.

External wait-states can be generated by asserting the `n_wait` input. This input is sampled on every rising edge of `clk`, when both `n_nram` and `n_cas_0/1` are asserted and the internal wait-state counter expired. If it samples '0', the access cycle is extended. If it samples '1', the access cycle completes. Many devices can share the same `n_wait` input using open-collector or open-drain logic and a pull-up resistor. If no external wait-state generation is required, the `n_wait` pin needs to be tied to VCC.

While wait-states are not relevant for DRAM accesses, the same address fields are reserved (and used by the DMA controller) for those regions as well.

External bus
------------

The full external bus interface is comprised of the following  signals:

=============  ============================
Signal name    Description
=============  ============================
n_ras_a        Active low row-address select for DRAM bank A
n_ras_b        Active low row-address select for DRAM bank B
n_cas_0        Active low column-address select for DRAM byte 0
n_cas_1        Active low column-address select for DRAM byte 1
addr[10:0]     Multiplexed address bus signals
n_we           Active low write-enable
data[7:0]      Bi-directional 8-bit data-bus
n_nren         Active low non-DRAM select
n_wait         Active low wait-state input
=============  ============================

DRAM access timing
~~~~~~~~~~~~~~~~~~

The bus support double data-rate accesses to DRAM. The first half of a clock-cycle, lower byte, the second half of the clock cycle the upper byte is accessed. The end result is that 16-bits of memory content can be moved every clock cycle, even though the external data-bus has only 8 data lines. Long bursts within a page are supported by keeping `n_ras_a/b` low while toggling `n_cas_0/1`.  At either end of the burst, some overhead (one cycle each) needs to be paid to return the bus to it's idle state and allow for the DRAM chip to meet pre-charge timing.

A 4-beat (8-byte burst) on the bus would have the following timing:

::
                       <------- 4-beat burst ------------->
    clk            \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^
    n_ras_a/b      ^^^^^^^^^\_____________________________/^
    n_nram         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_cas_0        ^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^
    n_cas_1        ^^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^
    addr           ---------<==X=====X=====X=====X=====>----
    n_we           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    data (read)    --------------<>-<>-<>-<>-<>-<>-<>-<>----
    n_we           ^^^^^^^^^\_____________________________/^
    data (write)   ------------<==X==X==X==X==X==X==X==>----

Two back-to-back 16-bit accesses look like the following:

::
                      <---- single ----><---- single ---->
    clk            \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^
    n_ras_a/b      ^^^^^^^^^\___________/^^^^^\___________/^
    n_nram         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_cas_0        ^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^^^^^^
    n_cas_1        ^^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^^^
    addr           ---------<==X=====>--------<==X=====>----
    n_we           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    data (read)    --------------<>-<>--------------<>-<>---
    n_we           ^^^^^^^^^\___________/^^^^^\___________/^
    data (write)   ------------<==X==>-----------<==X==>----

A memory refresh cycle (RAS-only refresh) has the following waveforms:

::
                       <- refresh->
    clk            \__/^^\__/^^\__/^
    n_ras_a/b      ^^^^^^^^^\_____/^
    n_nram         ^^^^^^^^^^^^^^^^^
    n_cas_0        ^^^^^^^^^^^^^^^^^
    n_cas_1        ^^^^^^^^^^^^^^^^^
    addr           ---------<==>----
    n_we           ^^^^^^^^^^^^^^^^^
    data (read)    -----------------
    n_we           ^^^^^^^^^^^^^^^^^
    data (write)   -----------------

.. note:: Refresh cycles assert both n_ras_a and n_ras_b at the same time. Other cycles assert either of the two, but not both.

.. note:: These timing diagrams aren't really compatible with fast-page-mode memories. The more precise way of saying this is that these timings don't allow us to take advantage of FPM access cycles. We would need to delay both `n_cas_0/1` signals by half a clock-cycle to make FPM work. That would probably result in an extra clock cycle of latency on reads. It would however allow us to double the clock speed.

Non-DRAM access timing
~~~~~~~~~~~~~~~~~~~~~~

For non-DRAM accesses, the waveforms are different in several ways:

1. No bursts are supported
2. Select signals are slowed down
3. External and internal wait-states can be inserted

::
                            <---- access ----><---- internal wait ---><---- external wait --->
    clk            \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/
    n_ras_a/b      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_nram         ^^^^^^^^^\___________/^^^^^\_________________/^^^^^\_________________/^^^^^^
    n_cas_0        ^^^^^^^^^^^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_cas_1        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^^^^^^^\___________/^^^^^^
    addr           ---------<==X========>-----<==X==============>-----<==X==============>------
    n_we           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    data (read)    ---------------------<>----------------- ----<>----------------------<>-----
    n_we           ^^^^^^^^^\___________/^^^^^\_________________/^^^^^\_________________/^^^^^^
    data (write)   ------------<========>-----------<===========>--------<==============>------
    n_wait         ---------------/^^^^^\-----------/^^^^^^^^^^^\-----------\_____/^^^^^\------

.. note:: These timings don't really support external devices with non-0 data hold-time requirements. Maybe we can delay turning off data-bus drivers by half a cycle?

DMA access timing
~~~~~~~~~~~~~~~~~

DMA accesses follow the timing of non-DRAM accesses, but select DRAM instead of non-DRAM devices as their targets:

::
                            <--- even read ---><- odd read with wait ->
    clk            \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/
    n_ras_a/b      ^^^^^^^^^\___________/^^^^^\_________________/^^^^^^
    n_nram         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_cas_0        ^^^^^^^^^^^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_cas_1        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^^
    addr           ---------<==X========>-----<==X==============>------
    n_we           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    data (read)    ---------------------<>----------------------<>-----
    n_we           ^^^^^^^^^\___________/^^^^^\_________________/^^^^^^
    data (write)   ------------<========>--------<==============>------
    n_wait         ---------------/^^^^^\-----------\_____/^^^^^\------
    n_dack_X       ^^^^^^^^^\___________/^^^^^\_________________/^^^^^^
    tc             ---------<===========>-----<=================>------

DMA operations only support 8-bit accesses.

diagrams

Memory refresh
--------------

Espresso contains integrated memory refresh logic. This consists of a timing controller and an address counter. The refresh timing controller has a programmable 8-bit divider, that is used to generate refresh requests. Every time a refresh is requested, the refresh address is incremented, until it wraps around at 2047.

Bus interface CSR
-----------------

There is a single CSR register to control the bus interface, called CSR_BUS_IF. It follows the following layout:

======= ================ ============
Bits     Reset value      Description
======= ================ ============
0..7     128              Refresh divider
8        0                Refresh disable
9..10    0                DRAM bank size 0: 16-bit; 1: 18-bit; 2: 20-bit; 3: 22-bit
11       0                DRAM bank swap
======= ================ ============


Memory map
----------

While most of the memory map is determined by external address decode circuitry, some aspects are controlled by Espresso. The 4GB of total physical address space is broken up into four 1GB regions:

================= ================== ======================== =======================
Start address     End address        Usage                    Access qualifier signal
================= ================== ======================== =======================
0x0000_0000       0x3fff_ffff        non-DRAM address space   n_nram
0x4000_0000       0x7fff_ffff        CSR address space        N/A
0x8000_0000       0xbfff_ffff        DRAM address space       n_ras_a/b
0xc000_0000       0xffff_ffff        reserved                 N/A
================= ================== ======================== =======================

Within each 1GB address space the top 4 of the remaining 32 address pins are used to encode the number of wait-states. This leaves a total of 64MB of unique address space in each region, however the limited number of external address pins further limits the uniquely addressable space to 8MB for non-DRAM and 16MB for DRAM sections.

Why?
----

Espresso doesn't have any internal memory (except for a very shallow prefetch queue). This means that execution speed is limited by the memories ability to supply instructions to the processor. Consequently we want to have as high-speed an interface to DRAM, the primary source of instructions, as possible. To that end, we can't afford any logic between the CPU and memory. No address decode, no buffers, nothing. All such logic would add valuable nanoseconds to the access latency.

The consequence of this logic is that the external memory bus would need to follow exactly the signalling and timing of DRAM interfaces. We need `n_ras` and `n_cas` signals to qualify the access and a multiplexed address bus. DRAM timing also means that any `n_cas` signal can toggle at a 50% duty-cycle (at least when quantized to clock-edges). This presents an opportunity though: one could address two banks of DRAMs on opposite half of a bus-cycle by having two `n_cas` signals toggling in opposite fashion. This double-data-rate access goes hand in hand with another idea: page-mode access. DRAMs don't need repeated row-addresses (and the togging of `n_ras`) as long as the accesses are within the same page, that is, have the same row-address.

The fastest way to talk to DRAM is as follows: try to keep accesses within the same page as much as possible and use two banks of memory. In other words, DDR burst access. There are limitations to this technique though. One is that long bursts starve other requestors (graphics controller, DMA, even the load-store unit within Espresso) and the second is that we need to store the data we got through a burst *somewhere*.

Loads and stores can only use up to 4-beat bursts: Espresso can't deal with more than 32-bits of data at a time. Instruction fetch bursts can be much longer as long as we can put the fetched data in some temporary buffer, but there's a limit: every time the code branches, we have to throw away all the prefetched instruction words and start over from the new location. There is a balance between the amount of data we are willing to throw away and the benefits of a long burst. Profiling shows that the optimum point is 8 word (16-byte) long bursts.

Due to the timing of the DRAM signals we need one clock-cycle worth of setup and one clock-cycle worth of wind-down time on every burst: the setup requires the sending of the row-address and the wind-down is predominantly there for the DRAM pre-charge time. This added time means that an 8-word burst takes 10 clock-cycles on the bus to complete. A single 32-bit read or write takes 4 cycles.

Why only an 8-bit external bus? In short, to fit in the 40-pin package. This setup also makes it easier to connect to 8-bit peripherals, which was the vast majority of devices on the market at the early '80s.

What are the down-sides? The major impact comes in interfacing to non-DRAM devices. Firstly, an extra address-latch is required (and a 10-bit one at that if full address decoding is desired, which is extra annoying). The second problem is of course speed. This is not all that problematic for I/O devices of the day, simply because they were slow, and 8-bit anyway. ROM memory is a different animal though. They were normally about twice as slow as DRAM devices (for instance you would see 120ns access time DRAM with 250ns EPROMs in the same machine). However, not only each access is about 3-times as slow for EPROM as for DRAM on Espresso, it also uses 8-bit transfers. So, the price we really pay is very slow access to EPROM.

Machines of the age would normally depend heavily on storing and executing code from EPROM, mostly because of constrains both in RAM size and storage devices. For Espresso, at least for speed-sensitive codes, one would have to think hard about moving the code from EPROM to DRAM and executing from there.

Background
----------

DRAM History
~~~~~~~~~~~~

Various DRAM capacities according to `this <http://doctord.dyndns.org/Courses/UNH/CS216/Ram-Timeline.pdf>`_ source were introduced in the following years:

======    ========
Year      Capacity
======    ========
1970      1kbit
1973      4kbit
1976      16kbit
1978      64kbit
1982      256kbit
1986      1Mbit
1988      4Mbit
1991      16Mbit
1994      64Mbit
1998      256Mbit
======    ========

Since the Anachronistic Computer is an early '80-s machine, we should plan on 64kBit and 256kBit devices. With our two banks and 16-bits of memory in each, we can scale up to 1MByte of DRAM. That would probably have been very expensive though. A low-end configuration would probably not have had more than 128kByte of RAM. (For comparison, the first PC models supported 64 or 128kByte of RAM and the first Macintosh models in '84 also came with a meager 128k of memory.)

DRAM Datasheets
~~~~~~~~~~~~~~~

Some DRAM datasheets:

- `16kx1 <https://www.jameco.com/Jameco/Products/ProdDS/2288023.pdf>`_
- `64kx1 <https://www.jameco.com/Jameco/Products/ProdDS/2290535SAM.pdf>`_
- `64kx4 <https://downloads.reactivemicro.com/Electronics/DRAM/NEC%20D41464%2064k%20x%204bit%20DRAM%20Data%20Sheet.pdf>`_
- `256kx1 <https://pdf1.alldatasheet.com/datasheet-pdf/view/37259/SAMSUNG/KM41256A.html>`_
- `256kx4 <https://pdf1.alldatasheet.com/datasheet-pdf/view/45238/SIEMENS/HYB514256B.html>`_
- `1Mx1 <https://datasheetspdf.com/pdf-file/550187/MicronTechnology/MT4C1024/1>`_
- `1Mx16 <https://www.mouser.com/datasheet/2/198/41lv16105b-1169632.pdf>`_
- `4Mx4 <https://www.digikey.com/htmldatasheets/production/1700164/0/0/1/MSM51V17400F.pdf>`_
- `16Mx1 <https://www.digchip.com/datasheets/parts/datasheet/409/KM41C16000CK-pdf.php>`_

There were two memory module formats: 30 pin and 72 pin.

- `<https://en.wikipedia.org/wiki/SIMM>`_
- `<https://www.pjrc.com/tech/mp3/simm/datasheet.html>`_

EDO datasheets:

- `4/8MB module <https://www.digchip.com/datasheets/download_datasheet.php?id=687767&part-number=MT2D132>`_
- `JEDEC standard extract <https://www.ele.uri.edu/iced/protosys/hardware/datasheets/simm/Jedec-Clearpoint-8MB.pdf>`_
- `16/32MB module <https://www.digchip.com/datasheets/download_datasheet.php?id=987285&part-number=TM893GBK32S>`_
- `Another 16/32MB Module <https://docs.rs-online.com/1faa/0900766b80027c7f.pdf>`_
- `Socket ($0.88 apiece) <https://www.peconnectors.com/sockets-pga-cpu-and-memory/hws8182/>`_

DRAM speeds
~~~~~~~~~~~

There are four important timing parameters for DRAM timing:

.. figure:: dram-timing.png
   :alt: DRAM timing

256kbit devices (and more modern 64-kbit variants as well) came in the following speed-grades:

=========== ===== ===== ===== ===== ===== =====
Part number       uPD41464         KM41256
----------- ----------------- -----------------
Speed grade  -80   -10   -12   -10   -12   -15
=========== ===== ===== ===== ===== ===== =====
t_rcd        40ns  50ns  60ns  50ns  60ns  75ns
t_cas        40ns  50ns  60ns  50ns  60ns  75ns
t_cp         30ns  40ns  50ns  45ns  50ns  60ns
t_rp         70ns  90ns  90ns  90ns 100ns 100ns
=========== ===== ===== ===== ===== ===== =====

Very early devices also had a -20 (200ns) speed-grade to them, but that's too slow for us.

Fast-page-mode devices, such as the one used in late-issue Amiga A500 boards have significantly improved timing:

=========== ===== ===== ===== ===== ===== =====
Part number     HYB514256B         MT4C1024
----------- ----------------- -----------------
Speed grade  -50   -60   -70   -6    -7    -8
=========== ===== ===== ===== ===== ===== =====
t_rcd        35ns  45ns  50ns  40ns  50ns  60ns
t_cas        15ns  15ns  20ns  20ns  20ns  20ns
t_cp         10ns  10ns  10ns  10ns  10ns  10ns
t_rp         35ns  40ns  50ns  40ns  50ns  60ns
=========== ===== ===== ===== ===== ===== =====

=========== ====== ====== ====== ======
Part number  KM41C16000C  IS41LV16105B
----------- ------------- -------------
Speed grade   -5     -6     -50    -60
=========== ====== ====== ====== ======
t_rcd        37ns   45ns   37ns   45ns
t_cas        13ns   15ns    8ns   10ns
t_cp         10ns   10ns    9ns    9ns
t_rp         35ns   40ns   30ns   40ns
=========== ====== ====== ====== ======

EDO, when introduced in '95 was even faster. For Espresso, we are focusing on page-mode devices and their timing characteristics. Newer devices will work with those timings as well, but you can't take advantage of their special modes.

Since we snap timings to half-clock-cycle boundaries, the bus (and thus CPU) clock rates we can support are as follows:

=========== ========= ========= ========= ========= ========= =========
Part number           uPD41464                       KM41256
----------- ----------------------------- -----------------------------
Speed grade  -80       -10       -12       -10       -12       -15
=========== ========= ========= ========= ========= ========= =========
t_rcd        40ns      50ns       60ns     50ns      60ns      75ns
t_cas        40ns      50ns       60ns     50ns      60ns      75ns
t_cp         30ns      40ns       50ns     45ns      50ns      60ns
t_rp         70ns      90ns       90ns     90ns     100ns     100ns
f_cpu        12.5Mhz   10Mhz      8.3MHz   10Mhz     8.3MHz    6.6MHz
=========== ========= ========= ========= ========= ========= =========

.. _dram_banks::

Supported bank configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since, I don't think we could neither afford nor drive more than 32 memory chips on the bus, with up to 4 banks we could support the following memory sizes:

1-bit chips:

====== ======== ========= ======================= ================= =============== ============ ===================
Year   Capacity Word size Number of address lines Capacity per bank Number of banks Max capacity Number of RAM chips
====== ======== ========= ======================= ================= =============== ============ ===================
1978   64kbit   1         8                       128kByte          1               128kByte     16
1978   64kbit   1         8                       128kByte          2               256kByte     32*
1982   256kbit  1         9                       512kByte          1               512kByte     16
1982   256kbit  1         9                       512kByte          2               1MByte       32*
1986   1Mbit    1         10                      2MByte            1               2MByte       16
1986   1Mbit    1         10                      2MByte            2               4MByte       32*
1988   4Mbit    1         11                      8MByte            1               8MByte       16
1988   4Mbit    1         11                      8MByte            2               16MByte      32*
====== ======== ========= ======================= ================= =============== ============ ===================

4-bit chips:

====== ======== ========= ======================= ================= =============== ============ ===================
Year   Capacity Word size Number of address lines Capacity per bank Number of banks Max capacity Number of RAM chips
====== ======== ========= ======================= ================= =============== ============ ===================
1982   256kbit  4         8                       128kByte          1               128kByte     4
1982   256kbit  4         8                       128kByte          2               256kByte     8
1986   1Mbit    4         9                       512kByte          1               512kByte     4
1986   1Mbit    4         9                       512kByte          2               1MByte       8
1988   4Mbit    4         10                      2MByte            1               1MByte       4
1988   4Mbit    4         10                      2MByte            2               4MByte       8
1991   16Mbit   4         11                      8MByte            1               8MByte       4
1991   16Mbit   4         11                      8MByte            2               16MByte      8
====== ======== ========= ======================= ================= =============== ============ ===================

This shows that we can't really support all the configurations we might want to with either 1- or 4-bit devices alone. The solution to that problem in the industry was the introduction of SIMM modules. This is a later invention, but there's nothing really ground-breaking in the idea: it's just a small PCB with the memory on it and a connector to attach it to the main PCB. This could have happened in '82, it just didn't. So I will say that we 'invented' SIMM modules and as it happens, we stumbled upon exactly the same form-factor and pin-out that the rest of the world standardized on years later.

There were two standards: first, the 32-pin, 9-bit modules were popular, later the 72-pin, 36 bit ones became vogue. With certain limitations, Anachron can support both: on a 72-pin module, only one side can be utilized, cutting the supported memory in half for double-sided modules.

EPROM
-----

`Timeline <https://en.wikipedia.org/wiki/EPROM>`_:

======    ========
Year      Capacity
======    ========
1975      2704
1975      2708
1977      2716
1979      2732
1981      2764 (https://timeline.intel.com/1981/a-new-era-for-eprom)
1982      27128 (https://timeline.intel.com/1982/the-eprom-evolution-continues)
?         27256
?         27512
1986      27010 (https://timeline.intel.com/1986/one-megabit-eprom)
======    ========


EPOM Timing
~~~~~~~~~~~

Here's a typical datasheet: https://datasheet.octopart.com/D27256-2-Intel-datasheet-17852618.pdf

Access times are 250ns, though there are several speed-grades available.

By '91, CMOS EPROMs were available with access times roughly half of that: 120ns was the highest speed-grade.

At that time same-capacity (and speed) FLASH parts started to appear too - not 5V programmable parts though. They required ~10ns hold-times on data (relative to the rising edge of nWE), which is something that DRAMs didn't have.
