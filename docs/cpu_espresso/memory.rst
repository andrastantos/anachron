External Memory Interface
=========================

.. admonition:: Historical rant

    One thing that annoyed me a lot every time I looked at schematics of machines from the '80s was the interface to DRAM. When I tried to design my own, I also have found the problem very annoying. Now, looking back, it's not only that. It's also very inefficient. This was fine for a processor such as the 6502 in a C64; the processor had a slow enough clock that it didn't matter. Faster machines, such as the Amiga or even the PC needed two groups of memory to get around the inefficiency: one for video, one for the processor. Others, such as the Macintosh could only really support black-and-white graphics, partly due to (originally) memory size limitations, but also because of memory bandwidth issues.

    DRAM memories had a multiplexed *address* bus: every access needed two cycles. That is, in the general, fully random access case. Nearby memory locations could be accessed in a single cycle. This technique was called 'page mode'. Later, this evolved into 'fast page mode', and 'enhanced read-out' (EDO) memories. Eventually, in SDRAMs, the technique became burst-mode accesses. All modern memory implementations make heavy use of this technique.

    Burst access becomes really efficient once caches become common-place, but there are some benefits even without them. Still, machines of the area almost exclusively used discrete logic to implement the DRAM interface, and thus could not take advantage of page mode accesses.

    On the other side, many processors (Intel, I'm looking at you) *also* had a multiplexed bus. It's just that they `multiplexed data and address <https://www.ndr-nkc.de/download/datenbl/i8088.pdf>`_ instead of address bits only.

    A PC design for instance, first needed to de-multiplex the processor bus just to then be able to multiplex it *again* for the DRAMs needs.

    Surely, there must be a better way!

Espresso uses a memory interface that allows direct connection to DRAM. A few extra signals are added to support connection to non-DRAM type devices, namely EPROMs and I/O devices. All external peripherals are accessed through this memory interface.

Memory Interface pins
---------------------

Espresso uses the following pins to interface to external memory:

=========== =============== ===========
Pin Name    Pin Direction   Description
=========== =============== ===========
a[10:0]     Output          Multiplexed address bus
d[7:0]      I/O             Data bus
n_ras_a     Output          Active low row-select, bank A
n_ras_b     Output          Active low row-select, bank B
n_cas_0     Output          Active low column select, byte 0
n_cas_1     Output          Active low column select, byte 1
n_nren      Output          Active low non-DRAM bus cycle qualifier
n_we        Output          Active low write-enable
n_wait      Input           Active low wait-state input
=========== =============== ===========

Address multiplexing
--------------------

The external memory interface uses the same bus conventions as DRAM uses: multiplexed address pins and dedicated data pins. It also uses :code:`n_ras` and :code:`n_cas` signals to qualify parts of the access cycle.

This approach not only give us glue-logic-free access to DRAM, reducing system cost, but also allows maximum bandwidth between the CPU and its memory. Since Espresso is internally aware of the context of a memory access, it can take advantage - and generate - page-mode accesses, further improving performance.

On top of these benefits, the DRAM interface is very efficient in pin-count: it cuts the number of address pins in half for the cost of one extra control signal.

The down-side of this approach is that non-DRAM devices are more complicated and slower to interface. However, this extra complexity is rather minimal and the slow-down affects devices that are already significantly slower then DRAM.

Another down-side is that multiplexing addresses to the same pins is a little complex if one wants to support decent address decoding for peripherals *and* support various DRAM memory sizes at the same time.

Espresso uses two different address-muxing schemes, depending on the target device. These schemes are selected based on the top bit of the physical address.

=========== =========== ========= =========== =========
Pin Name     DRAM accesses         non-DRAM accesses
----------- --------------------- ---------------------
             row         col       row         col
=========== =========== ========= =========== =========
a[0]         addr[9]     addr[1]   addr[12]   addr[1]
a[1]         addr[10]    addr[2]   addr[13]   addr[2]
a[2]         addr[11]    addr[3]   addr[14]   addr[3]
a[3]         addr[12]    addr[4]   addr[15]   addr[4]
a[4]         addr[13]    addr[5]   addr[16]   addr[5]
a[5]         addr[14]    addr[6]   addr[17]   addr[6]
a[6]         addr[15]    addr[7]   addr[18]   addr[7]
a[7]         addr[16]    addr[8]   addr[19]   addr[8]
a[8]         addr[18]    addr[17]  addr[20]   addr[9]
a[9]         addr[20]    addr[19]  addr[21]   addr[10]
a[10]        addr[22]    addr[21]  addr[22]   addr[11]
=========== =========== ========= =========== =========

Data multiplexing (DDR)
-----------------------

DRAM signal timing requires roughly 50% duty-cycle on the :code:`n_cas` signal: it has to be asserted for a certain minimum amount of time, then de-asserted for about the same amount of time. Espresso exploits this feature to support two sets of DRAM on the same data-bus. These sets share address and data lines, but are fed with inverted `n_cas` signals. One set is active in one half of the cycle, the other set in the other.

Espresso utilizes this DDR technique to cut the data bus width in half: even though the data bus is capable of transferring 16-bits of data every clock cycle, it only uses 8 external data-pins.

.. admonition:: Why?

    Why only an 8-bit external bus? In short, to fit in the 40-pin package. This setup also makes it easier to connect to 8-bit peripherals, which was the vast majority of devices on the market at the early '80s.

    What are the down-sides? The major impact comes in interfacing to non-DRAM devices. Firstly, an extra address-latch is required (and a 10-bit one at that if full address decoding is desired, which is extra annoying). The second problem is of course speed. This is not all that problematic for I/O devices of the day, simply because they were slow, 8-bit affairs anyway. ROM memory is a different animal though. They were normally about twice as slow as DRAM devices (for instance you would see 120ns access time DRAM with 250ns EPROMs in the same machine). However, not only each access is about 3-times as slow for EPROM as for DRAM on Espresso, it also uses 8-bit transfers. So, the price we really pay is very slow access to EPROM.

    Machines of the age would normally depend heavily on storing and executing code from EPROM, mostly because of constrains both in RAM size and storage devices. For Espresso, at least for speed-sensitive code, one would have to think hard about moving the code from EPROM to DRAM and executing from there.

Interface to DRAM
-----------------

The total addressable DRAM that Espresso supports is 16MByte. The minimum (using 4164/4464 chips) is 128kByte.

Espresso provides two memory banks. Each bank can contain anywhere from 128kByte to 8MByte of memory. Different sized memories in the two banks are supported. There are two :code:`n_ras_a/b` signals for bank-selection.

Memory Bank Size Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~

During boot, system SW detects the size of the memory attached to each bank, using aliasing. Various DRAM chips use a different number of address pins. Consequently, DRAM will alias content between addresses where the only difference is in address bits the DRAM chips don't use. The alias-boundary is detected during memory test and the memory chip sizes are deduced.

Memory Bank Address Decode
~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a contiguous DRAM memory space, the two DRAM banks need to be decoded to adjacent address ranges. As the size of the memory banks depend on the DRAM chips used (and not necessarily the same for the two banks), the bus interface needs to be programmed with the bank size. A single bank-size configuration option is provided, which needs to be set according to the larger of the two memory banks.

For gap-free DRAM mapping the larger of the two banks needs to appear in the lower physical addresses. Espresso provides a control register bit to swap which :code:`n_ras_a/b` signal corresponds to the lower or the higher bank address space.

The banks are decoded starting at physical address 0x8000_0000.

Interface to ROM and I/O devices
--------------------------------

Espresso only supports memory-mapped I/O devices; both I/O and ROM devices are treated the same way. A special access qualifier, called :code:`n_nren` is used to differentiate these non-DRAM accesses from DRAM accesses (which are using :code:`n_ras_a/b` signals).

:code:`n_nren` is asserted for accesses for the lowest 1GB of physical address space.

Address de-multiplexing is needed to re-create the full address bus for these devices. The external 'row address latch' needs to latch the address pins on the falling edge of :code:`n_nram`. This captures :code:`addr[22:12]`. The subsequent falling edge of either of the :code:`n_cas_0/1` signals is used to mark the beginning of the transfer and the availability of the lower address bits. All non-DRAM accesses are 8-bit wide, while the address bus is providing 16-bit addresses. The LSB of the address (:code:`addr[0]`) can be recovered from :code:`n_cas_0`.

.. todo:: add illustration of address bus re-construction

An address decoder can be used to further differentiate between various I/O devices and ROMs. This address decoder can operate on the top address bits, which are present in the first address cycle, providing more time for the decoder to perform its device selection. It is important to make sure that no actual chip-select signal is issued until the second part of the address cycle, signified by the assertion of one of the :code:`n_cas_0/1` signals.

.. todo:: add illustration of address decode

Wait states
~~~~~~~~~~~

non-DRAM accesses support both internally generated and external wait-states. The number of internal wait-states is decoded from the (internal) address bits :code:`addr[31:28]`. This provides 16 different wait-state settings. The value 0 corresponds to 15 wait-sates. For all other values, the number of wait-states is one less then the value of the top four address bits. For 0 wait-states, the value 1 should be used. The wait-state setting is ignored for DRAM and CSR accesses, even though the top 4 address bits are reserved for those memory regions as well.

All 16 wait-state sections alias to the same memory regions. This mechanism allows for fine-grain wait-state control without sophisticated memory-access configuration logic.

.. admonition:: Why?

    Internal wait-states are assigned such that physical address 0 (the boot vector) generates the maximum number of wait-states, so even very slow ROM devices can be used. If SW determines that fewer wait-states are sufficient, it can perform a jump to the aliased version of the boot code with the right wait-state setting.

    While it appears that cutting the decoded address space to 256MB is wasteful, it is highly unlikely that anyone would have had that much memory in the early '80s. Even the Cray X-MP (released in '82) maxed out at 128MB of RAM. Not to mention that the external bus interface doesn't support more than 16MB of RAM and 4MB of non-RAM space.

External wait-states can be generated by asserting the :code:`n_wait` input. This input is sampled on every rising edge of :code:`sys_clk`, when both :code:`n_nren` and :code:`n_cas_0/1` are asserted and the internal wait-state counter expired. If it samples '0', the access cycle is extended. If it samples '1', the access cycle completes. Many devices can share the same :code:`n_wait` input using a wired 'and' (open-collector) circuit. If no external wait-state generation is required, the :code:`n_wait` pin needs to be tied to VCC or left floating: an internal weak pull-up is provided.

The :code:`n_wait` signal is ignored for DRAM and CSR accesses.

For wait-state handling during DMA transfers see the :ref:`Wait states and DMA access <wait_states_and_dma_access>` chapter.

Memory map
----------

While most of the memory map is determined by external address decode circuitry, some aspects are controlled by Espresso. The top 4 address bits of the 4GB physical address space is used to define the number of wait-states. This leaves 256MB of physical address space, which is broken into 4 equally sized, 64MB regions:

================= ================== ======================== =======================
Start address     End address        Usage                    Access qualifier signal
================= ================== ======================== =======================
0x000_0000        0x3ff_ffff         non-DRAM address space   n_nram
0x400_0000        0x7ff_ffff         reserved                 N/A
0x800_0000        0xbff_ffff         DRAM address space       n_ras_a/b
0xc00_0000        0xfff_ffff         reserved                 N/A
================= ================== ======================== =======================

