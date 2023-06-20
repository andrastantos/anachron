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

A second register, :code:`csr_eaddr_reg` contains the address for the operating causing the latest exception. This address could be an instruction address (in case of a fetch AV) or a memory address (in case of a read/write AV). The address stored in this register is a logical address.

The following exception causes are defined:

========== ============ =================================
Bit-field  Name         Description
========== ============ =================================
 0         exc_swi_0    SWI 0 instruction executed
 1         exc_swi_1    SWI 1 instruction executed
 2         exc_swi_2    SWI 2 instruction executed
 3         exc_swi_3    SWI 3 instruction executed
 4         exc_swi_4    SWI 4 instruction executed
 5         exc_swi_5    SWI 5 instruction executed
 6         exc_swi_6    SWI 6 instruction executed
 7         exc_swi_7    SWI 7 instruction executed
 8         exc_cua      Unaligned memory access
 9         exc_mdp      Memory access AV
10         exc_mip      Instruction fetch AV
11         exc_hwi      Hardware interrupt
========== ============ =================================


Event Counters
~~~~~~~~~~~~~~

Espresso contains a number of event sources and a number of event counters. These events and counters can be used to profile the performance of code or certain aspects of the hardware.

The following events are defined:

======================== =============== ==========================================
Event name               Event index     Description
======================== =============== ==========================================
event_clk_cycles         0               This event occurs every clock cycle
event_fetch_wait_on_bus  1               Occurs when the instruction fetch stage waits on the bus interface
event_decode_wait_on_rf  2               Occurs when the decode stage is waiting on the register file
event_mem_wait_on_bus    3               Occurs when the memory unit waits on the bus interface
event_branch_taken       4               Occurs whenever a branch is taken
event_branch             5               Occurs when a branch instruction is executed
event_load               6               Occurs when a load is performed by the memory unit
event_store              7               Occurs when a store is performed by the memory unit
event_load_or_store      8               Occurs when either a load or a store is performed by the memory unit
event_execute            9               Occurs when an instruction is executed
event_bus_idle           10              Occurs when the bus interface is in idle
event_fetch              11              Occurs when a word is fetched from memory
event_fetch_drop         12              Occurs when a word is dropped from the instruction queue
event_inst_word          13              Occurs when a word is handed to instruction decode
======================== =============== ==========================================

These events are counted by a number of event counters. The number of counters is a configuration parameter for Espresso. In it's default configuration there are 8 event counters.

For each event counter, there is a pair of registers: one for selecting the event to count and another to read the number of counted events.

The base address for these CSRs is 0x4000_0404+8*event_counter_idx

========= =================================== ============================================
Offset    Name                                Note
========= =================================== ============================================
0x00      event_select_reg                    Selects one of the event sources to count
0x04      event_cnt_reg                       Returns the number of events counted (20 bits)
========= =================================== ============================================

There is no way to reset the counter. Instead, the counter value should be read at the beginning of the measurement, then again at the end and subtracted from one another to attain the number of events counted. For frequent events, or long measurements care should be taken for counter overflows. The counters themselves have 20 bits so can count a little over 1 million events before rolling over.

The recommended way of dealing with counter overflows is to regularly read them and use SW-controlled accumulators to store the values. Whenever the read value is smaller then the previous value, an overflow has occurred and 2^21 should be added to the accumulator. If the readout periodicity is less then about 1 million clock cycles, it is guaranteed that no more than a single overflow occurs between read-outs.

To allow for precise measurement of code sections, a global event counter enable register is provided. This allows for setup of event counters then a single, atomic write operation to enable all of them. At the end ofr the measurement interval a second write operation can be used to freeze the value of all registers at the exact same clock cycle.

The base address for this CSR is 0x4000_0400

========= =================================== ============================================
Offset    Name                                Note
========= =================================== ============================================
0x00      event_enable                        Writing a '1' enables event counters; a '0' disables counting of events
========= =================================== ============================================

Bus interface configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The bus interface needs some basic understanding of the attached memory devices. A single register is provided at offset 0x4000_0800 for this purpose:

======== ================================ =======================================
Bits     Name                             Description
======== ================================ =======================================
0..7     refresh_counter                  The divider counter to control the DRAM refresh period. Reset value is 128, so a refresh is generated every 128th clock cycle.
8        refresh_disable                  Write '1' to disable DRAM refresh operation
9..10    dram_bank_size                   Select DRAM bank size; 0: 128k, 1: 512k, 2: 2M, 3: 8M
11       dram_bank_swap                   Write '1' to swap DRAM banks in the memory map
======== ================================ =======================================

Booting
-------

Upon reset, Espresso starts executing from address 0, in SCHEDULER mode. Registers, including CSRs assume their reset value only on power-on, or external reset. If a SCHEDULER mode exception occurs, that only vectors the processor to address 0, but doesn't reset registers. Because of that, the state of Espresso can only be assumed to be initialized, if the :code:`ecause` register reads 0.

