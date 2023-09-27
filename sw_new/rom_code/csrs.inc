.set csr_ecause,               0x0000
.set csr_eaddr,                0x0001
.set csr_pmem_base_reg,        0x0080
.set csr_pmem_limit_reg,       0x0081
.set csr_dmem_base_reg,        0x0082
.set csr_dmem_limit_reg,       0x0083

.set csr_event_base,           0x8100
.set csr_bus_if_base,          0x0200
.set csr_dma_base,             0x0300

.set csr_bus_if_cfg_reg,           csr_bus_if_base + 0x0

.set csr_bus_if_cfg_reg.refresh_divider, 1 << 0
.set csr_bus_if_cfg_reg.refresh_divider_size, 8
.set csr_bus_if_cfg_reg.refresh_disable, 1 << 8
.set csr_bus_if_cfg_reg.dram_bank_size, 1 << 9
.set csr_bus_if_cfg_reg.dram_bank_swap, 1 << 11
.set csr_bus_if_cfg_reg.dram_single_bank, 1 << 12


