.set rom_base,          0x00000000
.set gpio_base,         0x00010000
.set dram_base,         0x08000000

.set bus_if_cfg_reg,    csr_bus_if_base + 0x0
# Register setup:
# bits 7-0: refresh divider
# bit 8: refresh disable (if set)
# bit 10-9: DRAM bank size: 0 - 22 bits, 1 - 20 bits, 2 - 18 bits, 3 - 16 bits
# bit 11: DRAM bank swap: 0 - no swap, 1 - swap

.global _start

.text

_start:
    $r0 <- tiny 0
    $r1 <- tiny 0
    $r2 <- tiny 0
    $r3 <- tiny 0
    $r4 <- tiny 0
    $r5 <- tiny 0
    $r6 <- tiny 0
    $r7 <- tiny 0
    $r8 <- tiny 0
    $r9 <- tiny 0
    $r10 <- tiny 0
    $r11 <- tiny 0
    $r12 <- tiny 0
    $r13 <- tiny 0
    $r14 <- tiny 0
    $pc <- dram_base
