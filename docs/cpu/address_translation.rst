Address Translation
===================

Logical and Physical Addresses
------------------------------

Espresso supports logical addresses in TASK mode. Logical addresses are mapped to physical addresses using a simple offset mechanism::

    <physical_address> = <logical_address> + <base_reg>

A pair of base registers are provided. One (:code:`csr_pmem_base_reg`) used for instruction fetches, the other (:code:`csr_dmem_base_reg`) for memory loads and stores.

In SCHEDULER mode, logical and physical addresses are the same, no translation is performed by Espresso.

Access rights and protection
----------------------------

For TASK mode, each logical (effective) address is compared to limit register before it is allowed to reach the memory. If the top 22 bits of the logical address is greater then the limit register, an access violation exception is thrown.

A pair of limit registers are provided. One (:code:`csr_pmem_limit_reg`) used for instruction fetches, the other (:code:`csr_dmem_limit_reg`) for memory loads and stores.

In SCHEDULER mode there's no protection: all accesses are allowed.

.. note::
  If a limit register is set to 0, this still allows a TASK mode process to access 1kB of memory. There is no way to disallow any memory access to a TASK mode process

.. note::
  To allow full access to the whole physical address space to a TASK mode process (make logical and physical address one and the same), set base registers to 0 and limit registers to 0xffff_fc00

This simple scheme enables basic process isolation, but any detailed management of access rights. There are some obvious limitations:

#. Tasks can have access to up to two, contiguous section of the physical address space. One for data, one for code. This in practice means they can only have access to DRAM (as they *do* need access to that and we can only control one region), which in turn means that all I/O accesses will have to be marshalled through SCHEDULER mode. Alternatively, one can setup a tasks with unhindered access to everything (similar to SCHEDULER-mode), but, obviously the task needs to be highly trustworthy.
#. Since the accessible physical address space for each task must be contiguous, memory fragmentation is a problem, something that can only be solved by de-fragmentation-by-copy.
#. Shared memory between processes is practically impossible.
#. Virtual memory (page files) and memory-mapped files are not practical.

.. admonition:: Why?

    The canonical way of dealing with access rights and protections is through a paging MMU. Espresso doesn't have enough silicon area (remember, we try to work with 1.5um silicon process) to implement that. Thus, a much simpler protection scheme was needed.

    The separation of base- and limit-registers for code and data allows for some interesting shared library (and process) implementations. If a library (or an executable) is loaded multiple times, the code segments can be shared; only new data-segments need to be allocated: this is particularly important for memory-constrained systems.

CSRs
----

================= =========================== ============ ================================
Offset            Name                        Access       Description
================= =========================== ============ ================================
0x400_0004        :code:`csr_pmem_base_reg`   R/W          The base address for the code (instruction fetches).
0x400_0008        :code:`csr_pmem_limit_reg`  R/W          The limit address for the code (instruction fetches).
0x400_000c        :code:`csr_dmem_base_reg`   R/W          The base address for the data (loads and stores).
0x400_0010        :code:`csr_dmem_limit_reg`  R/W          The limit address for the data (loads and stores).
================= =========================== ============ ================================

For all these registers, the lower 10 bits are ignored and return constant 0. In other words, the base register is 1kByte aligned.

.. todo::
    Should we use 4k aligned limit and base registers to make it easier for future MMU-based re-enactment of the address map of as TASK-mode process?


