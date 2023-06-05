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

Memory interface
----------------

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

Non-DRAM memory
```````````````
External Non-DRAM address space is 8MByte, but only 8-bit accesses are supported.

Memory CSR
```````````
The selection between the schemes is done through the CSR_BIS_IF register. The default setting is for 16-bit addresses.

CSR_BUS_IF register layout:

======= ============
Bits     Notes
======= ============
0..7     Refresh divider
8        Refresh disable
9..10    DRAM bank size 0: 16-bit; 1: 18-bit; 2: 20-bit; 3: 22-bit
11       DRAM bank swap
======= ============












To meet timing requirements on the DRAM interface, DRAM chips *directly* interfaced to the processor. No address decode, no latches, no buffers can be in between,

For other devices on the bus, `nLCAS` and `nUCAS` can still work as a byte-select/enable signal. We need another RAS-style qualifier to know that we need to latch the address and start decoding. That's `nNREN` above.

To fit in the 40-pin package, we needed to limit the addressable memory quite a bit. This is not a problem for an early '80-s machine, but for the next iteration (and FPM DRAM support) we will have to go up to a 44-pin package. This allows:

1. Two extra address lines to support 4Mx1 or even 16Mx1 devices
2. Two extra nRAS_Bx signals to support two extra banks

These changes allow to support up to 32MBytes of RAM per bank for a total of 128MByte RAM.

DRAM decode
~~~~~~~~~~~

To support various DRAM sizes, the address decode regions for nRAS_Bx needs to be programmable. They all are qualified by A31, that is they belong to the upper 2GB of the total address space. However, which address bits are used to select between nRAS_Bx has to be programmable, otherwise it can't be guaranteed that DRAM banks create a contiguous space.

This programming can be done at boot time, while testing for memory sizes: the default decode should allow for very large DRAM banks, and by testing for aliasing, the right boundary can be selected.

.. note::
    The same programmability needs to exist in the DMA controller too.

Wait states
~~~~~~~~~~~

The CPU has three programmable address regions:

=============  ===========  ===========
Start address  End address  Description
=============  ===========  ===========
0x0000_0000    0x0003_ffff  ROM space
0x0004_0000    0x0007_ffff  I/O spaces
0x8000_0000    0xffff_ffff  DRAM space
=============  ===========  ===========

For each of these I/O spaces, a different number of wait-states can be programmed as a 4-bit value. The value 0 means 15 wait-states, other wise value N means N-1 wait-states. The register resets to 0.