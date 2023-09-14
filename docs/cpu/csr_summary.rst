Control and Status Register Summary
===================================

Espresso has a set of internal peripherals and registers controlling its operation. These are collectively called CSRs. CSRs are accessible though special instructions. There are a total of 65536 CSR register addresses available, however most of them are not used.

Accessing

CSR addresses above 0x8000 are accessible from both TASK and SCHEDULER mode, while addresses below that are only accessible from SCHEDULER mode.

Some CSRs have pre-defined meaning in the Brew architecture, while there is a set that's specific to Espresso.

The following CSRs are defined:

========== ============================== ============== ================= ===================================================
Address    Name                           Access type    Reset value       Description
========== ============================== ============== ================= ===================================================
0x0000     :code:`csr_ecause`             R              0x0000_0000       Exception cause register
0x0001     :code:`csr_eaddr`              RC             Undefined         Exception address register
0x0080     :code:`csr_pmem_base_reg`      R/W            0x0000_0000       The base address for the code (instruction fetches).
0x0081     :code:`csr_pmem_limit_reg`     R/W            0x0000_0000       The limit address for the code (instruction fetches).
0x0082     :code:`csr_dmem_base_reg`      R/W            0x0000_0000       The base address for the data (loads and stores).
0x0083     :code:`csr_dmem_limit_reg`     R/W            0x0000_0000       The limit address for the data (loads and stores).

0x0200     :code:`bus_if_cfg_reg`         R/W            0x0000_0080       Bus interface configuration register

0x0300     :code:`dma_cha_0_addr`         R/W            0x0000_0000       Channel 0 address register (first/current address of transfer)
0x0301     :code:`dma_cha_0_limit`        R/W            0x0000_0000       Channel 0 limit register (last address of transfer)
0x0302     :code:`dma_cha_0_config`       R/W            0x0000_0000       Channel 0 configuration register
0x0303     :code:`dma_cha_0_status`       R              0x0000_0000       Channel 0 status register
0x0304     :code:`dma_cha_1_addr`         R/W            0x0000_0000       Channel 1 address register (first/current address of transfer)
0x0305     :code:`dma_cha_1_limit`        R/W            0x0000_0000       Channel 1 limit register (last address of transfer)
0x0306     :code:`dma_cha_1_config`       R/W            0x0000_0000       Channel 1 configuration register
0x0307     :code:`dma_cha_1_status`       R              0x0000_0000       Channel 1 status register
0x0308     :code:`dma_cha_2_addr`         R/W            0x0000_0000       Channel 2 address register (first/current address of transfer)
0x0309     :code:`dma_cha_2_limit`        R/W            0x0000_0000       Channel 2 limit register (last address of transfer)
0x030a     :code:`dma_cha_2_config`       R/W            0x0000_0000       Channel 2 configuration register
0x030b     :code:`dma_cha_2_status`       R              0x0000_0000       Channel 2 status register
0x030c     :code:`dma_cha_3_addr`         R/W            0x0000_0000       Channel 3 address register (first/current address of transfer)
0x030d     :code:`dma_cha_3_limit`        R/W            0x0000_0000       Channel 3 limit register (last address of transfer)
0x030e     :code:`dma_cha_3_config`       R/W            0x0000_0000       Channel 3 configuration register
0x030f     :code:`dma_cha_3_status`       R              0x0000_0000       Channel 3 status register
0x0310     :code:`dma_int_stat`           R/W1C          0x0000_0000       DMA Interrupt status register (for all channels)

0x0400     :code:`timer_val_limit`        R/W            0x0000_0000       Timer counter limit register when written, current timer count when read
0x0401     :code:`timer_int_status`       R/W1C          0x0000_0000       Bit 0: when set, timer interrupt is pending
0x0402     :code:`timer_ctrl`             R/W            0x0000_0000       Bit 0: when set, timer is enabled
========== ============================== ============== ================= ===================================================

========== ============================== ============== ================= ===================================================
Address    Name                           Access type    Reset value       Description
========== ============================== ============== ================= ===================================================
0x8000     :code:`csr_mach_arch`          R              0x0000_0000       Machine architecture and version register
0x8001     :code:`csr_capability`         R              0x0000_0000       Capability bit-field

0x8100     :code:`event_select_reg_0`     R/W            0x0000_0000       Selects one of the event sources to count for event counter 0
0x8102     :code:`event_cnt_reg_0`        R              0x0000_0000       Returns the number of events counted for event counter 0
0x8103     :code:`event_select_reg_1`     R/W            0x0000_0000       Selects one of the event sources to count for event counter 1
0x8104     :code:`event_cnt_reg_1`        R              0x0000_0000       Returns the number of events counted for event counter 1
0x8105     :code:`event_select_reg_2`     R/W            0x0000_0000       Selects one of the event sources to count for event counter 2
0x8106     :code:`event_cnt_reg_2`        R              0x0000_0000       Returns the number of events counted for event counter 2
0x8107     :code:`event_select_reg_3`     R/W            0x0000_0000       Selects one of the event sources to count for event counter 3
0x8108     :code:`event_cnt_reg_3`        R              0x0000_0000       Returns the number of events counted for event counter 3
0x8109     :code:`event_select_reg_4`     R/W            0x0000_0000       Selects one of the event sources to count for event counter 4
0x810a     :code:`event_cnt_reg_4`        R              0x0000_0000       Returns the number of events counted for event counter 4
0x810b     :code:`event_select_reg_5`     R/W            0x0000_0000       Selects one of the event sources to count for event counter 5
0x810c     :code:`event_cnt_reg_5`        R              0x0000_0000       Returns the number of events counted for event counter 5
0x810d     :code:`event_select_reg_6`     R/W            0x0000_0000       Selects one of the event sources to count for event counter 6
0x810e     :code:`event_cnt_reg_6`        R              0x0000_0000       Returns the number of events counted for event counter 6
0x810f     :code:`event_select_reg_7`     R/W            0x0000_0000       Selects one of the event sources to count for event counter 7
0x8110     :code:`event_cnt_reg_7`        R              0x0000_0000       Returns the number of events counted for event counter 7
========== ============================== ============== ================= ===================================================

Access types:
  R: readable
  W: writable
  RC: clear on read
  W1C: write one to clear
