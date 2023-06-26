Control and Status Register Summary
===================================

Espresso has a set of internal peripherals and registers controlling its operation. These are collectively called CSRs. This address space is only available for loads and stores (not instruction fetches) and is mapped into the physical memory space from 0x400_0000 to 0x7ff_ffff. The following CSRs are defined:

================= =========================== ============ ============= ================================
Offset            Name                        Access       Reset value   Description
================= =========================== ============ ============= ================================
0x400_0000        :code:`csr_cpu_ver_reg`     R            0x0000_0000   Version and capability register. For Espresso, it's 0x0
0x400_0004        :code:`csr_pmem_base_reg`   R/W          0x0000_0000   The base address for the code (instruction fetches).
0x400_0008        :code:`csr_pmem_limit_reg`  R/W          0x0000_0000   The limit address for the code (instruction fetches).
0x400_000c        :code:`csr_dmem_base_reg`   R/W          0x0000_0000   The base address for the data (loads and stores).
0x400_0010        :code:`csr_dmem_limit_reg`  R/W          0x0000_0000   The limit address for the data (loads and stores).
0x400_0014        :code:`csr_ecause_reg`      R/W1C        0x0000_0000   Contains the reason for the last exception.
0x400_0018        :code:`csr_eaddr_reg`       R            0x0000_0000   The effective address that caused the latest exception

0x400_0404        :code:`event_select_reg_0`  R/W          0x0000_0000   Selects one of the event sources to count for event counter 0
0x400_0408        :code:`event_cnt_reg_0`     R            0x0000_0000   Returns the number of events counted for event counter 0
0x400_040c        :code:`event_select_reg_1`  R/W          0x0000_0000   Selects one of the event sources to count for event counter 1
0x400_0410        :code:`event_cnt_reg_1`     R            0x0000_0000   Returns the number of events counted for event counter 1
0x400_0414        :code:`event_select_reg_2`  R/W          0x0000_0000   Selects one of the event sources to count for event counter 2
0x400_0418        :code:`event_cnt_reg_2`     R            0x0000_0000   Returns the number of events counted for event counter 2
0x400_041c        :code:`event_select_reg_3`  R/W          0x0000_0000   Selects one of the event sources to count for event counter 3
0x400_0420        :code:`event_cnt_reg_3`     R            0x0000_0000   Returns the number of events counted for event counter 3
0x400_0424        :code:`event_select_reg_4`  R/W          0x0000_0000   Selects one of the event sources to count for event counter 4
0x400_0428        :code:`event_cnt_reg_4`     R            0x0000_0000   Returns the number of events counted for event counter 4
0x400_042c        :code:`event_select_reg_5`  R/W          0x0000_0000   Selects one of the event sources to count for event counter 5
0x400_0430        :code:`event_cnt_reg_5`     R            0x0000_0000   Returns the number of events counted for event counter 5
0x400_0434        :code:`event_select_reg_6`  R/W          0x0000_0000   Selects one of the event sources to count for event counter 6
0x400_0438        :code:`event_cnt_reg_6`     R            0x0000_0000   Returns the number of events counted for event counter 6
0x400_043c        :code:`event_select_reg_7`  R/W          0x0000_0000   Selects one of the event sources to count for event counter 7
0x400_0440        :code:`event_cnt_reg_7`     R            0x0000_0000   Returns the number of events counted for event counter 7

0x400_0800        :code:`bus_if_cfg_reg`      R/W          0x0000_0080   Bus interface configuration register

0x400_0c00        :code:`dma_cha_0_addr`      R/W          0x0000_0000   Channel 0 address register (first/current address of transfer)
0x400_0c04        :code:`dma_cha_0_limit`     R/W          0x0000_0000   Channel 0 limit register (last address of transfer)
0x400_0c08        :code:`dma_cha_0_config`    R/W          0x0000_0000   Channel 0 configuration register
0x400_0c0c        :code:`dma_cha_0_status`    R            0x0000_0000   Channel 0 status register
0x400_0c10        :code:`dma_cha_1_addr`      R/W          0x0000_0000   Channel 1 address register (first/current address of transfer)
0x400_0c14        :code:`dma_cha_1_limit`     R/W          0x0000_0000   Channel 1 limit register (last address of transfer)
0x400_0c18        :code:`dma_cha_1_config`    R/W          0x0000_0000   Channel 1 configuration register
0x400_0c1c        :code:`dma_cha_1_status`    R            0x0000_0000   Channel 1 status register
0x400_0c20        :code:`dma_cha_2_addr`      R/W          0x0000_0000   Channel 2 address register (first/current address of transfer)
0x400_0c24        :code:`dma_cha_2_limit`     R/W          0x0000_0000   Channel 2 limit register (last address of transfer)
0x400_0c28        :code:`dma_cha_2_config`    R/W          0x0000_0000   Channel 2 configuration register
0x400_0c2c        :code:`dma_cha_2_status`    R            0x0000_0000   Channel 2 status register
0x400_0c30        :code:`dma_cha_3_addr`      R/W          0x0000_0000   Channel 3 address register (first/current address of transfer)
0x400_0c34        :code:`dma_cha_3_limit`     R/W          0x0000_0000   Channel 3 limit register (last address of transfer)
0x400_0c38        :code:`dma_cha_3_config`    R/W          0x0000_0000   Channel 3 configuration register
0x400_0c3c        :code:`dma_cha_3_status`    R            0x0000_0000   Channel 3 status register
0x400_0c40        :code:`dma_int_stat`        R/W1C        0x0000_0000   Interrupt status register (for all channels)
================= =========================== ============ ============= ================================

