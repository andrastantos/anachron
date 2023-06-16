Control and Status Registers (CSRs)
-----------------------------------

Espresso has a set of internal peripherals and registers controlling its operation. These are collectively called CSRs. This address space is only available for loads and stores (not instruction fetches) and is mapped into the physical memory space from 0x4000_0000 to 0x7fff_ffff. The following CSRs are defined:

DMA controller
~~~~~~~~~~~~~~

The built-in DMA controller and it's CSRs are described in the :ref:`DMA <dma>` chapter.

The base address for the DMA CSRs is 0x4000_0c00

Basic CSRs
~~~~~~~~~~
The currently active base- and limit- registers are set in the following CSRs:

The base address for these CSRs is 0x4000_0000

========= =================================== ============================================
Offset    Name                                Note
========= =================================== ============================================
0x00      csr_cpu_ver_reg                     Version and capability register. For Espresso, this read only register returns 0x0
0x04      csr_pmem_base_reg                   The base address for the code (instruction fetches). The lower 10 bits are ignored and return constant 0. In other words, the base register is 1kByte aligned
0x08      csr_pmem_limit_reg                  The limit address for the code (instruction fetches). The lower 10 bits are ignored and return constant 0. In other words, the base register is 1kByte aligned
0x0c      csr_dmem_base_reg                   The base address for the data (loads and stores). The lower 10 bits are ignored and return constant 0. In other words, the base register is 1kByte aligned
0x10      csr_dmem_limit_reg                  The limit address for the data (loads and stores). The lower 10 bits are ignored and return constant 0. In other words, the base register is 1kByte aligned
0x14      csr_ecause_reg                      Contains the reason for the last exception. This register is cleared by the `stm` instruction.
0x18      csr_eaddr_reg                       The address that caused the latest exception
========= =================================== ============================================

Logical vs. physical addresses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For both code and data, there is a base and limit register. These are 22-bit registers, containing addresses aligned to 1kByte boundaries. For easy access from SW, they are accessible as the top 22 bits of their corresponding CSRs. The bottom 10 bits are ignored on writes and return 0 on reads.

All TASK-mode operations use logical addresses. These addresses are subject to address translation and limit checking.

**Address translation**: The top 22 bits of the logical address is added to the appropriate base register to gain the top 22 bits of the physical address. The bottom 10 bits of the logical and physical addresses are the same.

**Limit checking**: If the top 22 bits of the logical address is greater then the appropriate limit register, an access violation exception is raised.

For instruction fetches, the 'appropriate' base and limit registers are :code:`csr_pmem_base_reg` and :code:`csr_pmem_limit_reg`. For loads and stores, the appropriate registers are :code:`csr_pmem_base_reg` and :code:`csr_pmem_limit_reg`.

In SCHEDULER mode, all operations (instruction fetches, loads or stores) use physical registers.

.. note::
  If a limit register is set to 0, this still allows a TASK mode process to access 1kB of memory. There is no way to disallow any memory access to a TASK mode process

.. note::
  To allow full access to the whole physical address space to a TASK mode process (make logical and physical address one and the same), set base registers to 0 and limit registers to 0xffff_fc00

Exception cause and address
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :code:`csr_ecause_reg` contains a bit-field for where each bit corresponds to a particular possible exception cause.

The ecause register is 'write-one-to-clear', that is to say: to clear a bit in the ecause register SW needs to write a '1' to that bit. If an exception happens on the same cycle when the ecause bit is cleared by SW, the ecause bit stays set.

ecause bits are set even in SCHEDULER mode. This is useful for polling for pending interrupts. Other exceptions in SCHEDULER mode cause a processor reset (to be more precise, a jump to address 0). The ecause register in these cases can be interrogated to determine the (approximate) reset cause. In some cases the cause of the reset can't be fully determined. One instance would be if a TASK-mode exception sets an ecause bit, resulting in a transfer to SCHEDULER mode. Then, a second SCHEDULER mode exception sets a second ecause bit before SCHEDULER-mode SW had a chance to clear the previous ecause bit. When code starts executing from address 0, two ecause bits would be set and the cause of the reset would not be unambiguously determined.

A second register :code:`csr_eaddr_reg` contains the address for the operating causing the latest exception. This address could be an instruction address (in case of a fetch AV) or a memory address (in case of a read/write AV). Care should be take when interpreting this data: :code:`$pc` is stored as a logical address, while memory access addresses are stores as physical addresses.












We should have self-describing HW, I think. That would mean that the highest few bytes of anything in the address space should
say what that thing is.

Now, this is not possible for all things (memories for example), so the interconnect should step in for those items.

'Things' are identified by UUIDs, which are 128-bit long.

The interconnect also contains a descriptor of the following format:

32-bit region length (32-bit aligned)
32-bit region start (32-bit aligned)
Optional 128-bit UUID for region, if LSB of region start is set

The table is read backwards from the highest offset (which is the interconnect UUID) and read until region-length 0 is encountered. Regions must not be overlapping, but they are not necessarily listed in any particular order.

Region length 0 terminates the scan.

Each subsection either contains its own UUID or the UUID is in the interconnect descriptor one level above.

This setup allows SW to completely scan and understand the address map of the HW without any prior knowledge. (NOTE: since the tables and IDs are hard-coded, there's no HW complexity involved in coding them, except of course for the need of the actual storage)

.. note::
  Most peripherals simply need to have a 128-bit read-only register, containing their UUID decoded at their highest addressable I/O region. If peripherals also have memory mapped memories, those are described by the interconnect.

.. todo::
  This needs thought, way more though. The UUID approach gives you exact HW versioning, but not revisioning or any sort of capability listing. Thus, any minor HW change would require a complete SW recompile. There's no backwards compatibility what so ever. So, maybe a list of compatible UUIDs? But then how long is the list? What if there's partial compatibility with some other IP? (Such as two interconnects that have completely different control mechanisms (thus different UUIDs), but would still need to support the above discovery process? How about a backwards compatible, but increased functionality serial port of instance?

Booting
-------

If SCHEDULER-mode goes through the MMU, the following process works: on reset, we start in SCHEDULER mode, at (logical) address 0. This generates a TLB mis-compare upon address translation. The MMU page table address is also set to 0, so the first entry of the top-level page table is loaded from physical address 0. Based on that, the second-level (if that's how it is set up) page table entry is also loaded, from whatever address (say 4096). At this point the physical address for the first instruction can be determined (say 8192) and the fetch can progress.

If SCHEDULER-mode uses physical addresses, the MMU is not involved, so we can still simply start executing from address 0. Even though the MMU top level page table also points to address 0, that only starts playing a role when we enter TASK mode. So, boot code simply need to make sure to set up the MMU properly before exiting to the first task.

The end result is that we can boot the machine with all registers defaulting to 0.

I/O AND CSR
-----------

The process doesn't have a separate address space for I/Os and CSRs. This means that all such things need to be memory mapped. They probably would occupy high ranges of the physical address space, so that they don't interfere with booting. The difference between CSRs and I/O is that there is one copy of CSRs for each processor (in a multi-processor system) while there is only one copy of I/O. This is something that can be handled on the interconnect level (CSR peripherals are replicated and the CPUID is pre-pended to the physical address coming out of the CPUs).

CSRs occupy the top physical page, that is PA_FFFFE000...PA_FFFFFFFF

The following CSRs are defined:

Cache and TLB
~~~~~~~~~~~~~

TBASE - see above
SBASE - see above
TLB_LA1
TLB_DATA1
TLB_LA2
TLB_DATA2
TINV  - if written, invalidates TASK mode TLB entries
SINV  - if written, invalidates SCHEDULER mode TLB entries
CINV  - bit 0: invalidate INST CACHE, bit 1: invalidate DATA CACHE

Perf counters
~~~~~~~~~~~~~

PERF_CNT0
PERF_CNT1
PERF_CNT2
PERF_CNT3
PERF_CFG0
PERF_CFG1
PERF_CFG2
PERF_CFG3

Interrupt / reset cause
~~~~~~~~~~~~~~~~~~~~~~~

ECAUSE - exception cause
EADDR - exception address
RCAUSE - reset cause
RADDR

.. todo::
  We have the exception code (read/write/execute) as well. We can probably put that in ECAUSE.

.. todo::
  How to handle interrupts in a multi-core system? This could be just an interrupt routing problem...

.. todo::
  What of the above is truly replicated per core?
