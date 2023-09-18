.set rom_base,                 0x00000000
.set gpio_base,                0x00010000
.set io_apb_base,              0x00020000
.set dram_base,                0xf8000000 # Setting a different alias so that DRAM appear above I/O with 1 WS
.set dram_top,                 0xf801ffff # Setting a different alias so that DRAM appear above I/O with 1 WS

# Exception sources
.set exc_reset,                0x0000 # Hardware reset
.set exc_hwi,                  0x0010 # Hardware interrupt (only in TASK mode)
.set exc_swi_0,                0x0020 # SWI 0 instruction executed (FILL)
.set exc_swi_1,                0x0021 # SWI 1 instruction executed (BREAK)
.set exc_swi_2,                0x0022 # SWI 2 instruction executed (SYSCALL)
.set exc_swi_3,                0x0023 # SWI 3 instruction executed
.set exc_swi_4,                0x0024 # SWI 4 instruction executed
.set exc_swi_5,                0x0025 # SWI 5 instruction executed
.set exc_swi_6,                0x0026 # SWI 6 instruction executed
.set exc_swi_7,                0x0027 # SWI 7 instruction executed
.set exc_unknown_inst,         0x0030 # Undefined instruction
.set exc_type,                 0x0031 # Type error in instruction operands
.set exc_unaligned,            0x0032 # Unaligned memory access
.set exc_inst_av,              0x0040 # Instruction fetch AV
.set exc_mem_av,               0x0041

.set csr_ecause,               0x0000
.set csr_eaddr,                0x0001
.set csr_pmem_base_reg,        0x0080
.set csr_pmem_limit_reg,       0x0081
.set csr_dmem_base_reg,        0x0082
.set csr_dmem_limit_reg,       0x0083

.set csr_event_base,           0x8100
.set csr_bus_if_base,          0x0200
.set csr_dma_base,             0x0300

.set bus_if_cfg_reg,           csr_bus_if_base + 0x0



.set wait_state_0,             0x10000000
.set wait_state_1,             0x20000000
.set wait_state_2,             0x30000000
.set wait_state_3,             0x40000000
.set wait_state_4,             0x50000000
.set wait_state_5,             0x60000000
.set wait_state_6,             0x70000000
.set wait_state_7,             0x80000000
.set wait_state_8,             0x90000000
.set wait_state_9,             0xa0000000
.set wait_state_10,            0xb0000000
.set wait_state_11,            0xc0000000
.set wait_state_12,            0xd0000000
.set wait_state_13,            0xe0000000
.set wait_state_14,            0xf0000000
.set wait_state_15,            0x00000000

.set gpio1_base,               (gpio_base + 0x0000) | wait_state_0
.set gpio2_base,               (gpio_base + 0x1000) | wait_state_0
.set gpio_int_base,            (gpio_base + 0x2000) | wait_state_0

.set uart1_base,               (io_apb_base + 0x0000) | wait_state_0
.set gpio3_base,               (io_apb_base + 0x0100) | wait_state_0
.set gpio4_base,               (io_apb_base + 0x0200) | wait_state_0

.set uart_data_buf_reg_ofs,    0
.set uart_status_reg_ofs,      1
.set uart_config1_reg_ofs,     2
.set uart_config2_reg_ofs,     3
.set uart_divider_reg_ofs,     4

.set uart_data_buf_reg,    uart1_base + uart_data_buf_reg_ofs
.set uart_status_reg,      uart1_base + uart_status_reg_ofs
.set uart_config1_reg,     uart1_base + uart_config1_reg_ofs
.set uart_config2_reg,     uart1_base + uart_config2_reg_ofs
.set uart_divider_reg,     uart1_base + uart_divider_reg_ofs

.set uart_status_rx_full_bit_mask,                1
.set uart_status_tx_empty_bit_mask,               2
.set uart_status_parity_error_bit_mask,           4
.set uart_status_framing_error_bit_mask,          8
.set uart_status_overrun_error_bit_mask,          16
.set uart_status_cts_pin_bit_mask,                32

.macro CALL label
  $lr <- 1f
  $pc <- \label
1:
.endm

# Register setup:
# bits 7-0: refresh divider
# bit 8: refresh disable (if set)
# bit 10-9: DRAM bank size: 0 - 22 bits, 1 - 20 bits, 2 - 18 bits, 3 - 16 bits
# bit 11: DRAM bank swap: 0 - no swap, 1 - swap

.global _rom_start

.section .rom_init
.p2align        1


# Define start to be at the beginning of DRAM unless someone overrides that

.global _start
.weak _start

_rom_start:
    $pc <- _fast_start # Set WS to 0

.section .init
.p2align        1
_start:
    $pc <- dram_base


.text
.p2align        1

_fast_start:
    $r0 <- table
    $r0 <- $r0 - 8
    $pc <- mem[$r0 + 8]
    $a0 <- .fail_str
    CALL uart_write_str
    $pc <- done

routine:
    $a0 <- .success_str
    CALL uart_write_str
    $pc <- done

    .p2align 2
table:
    .int  routine

done:
    # Terminate under simulation
    $r0 <- gpio4_base
    $r1 <- 0
    mem8[$r0] <- $r0
_end_loop:
    $pc <- _end_loop


    .p2align        2
.success_str:
    .string "success\n"


    .p2align        2
.fail_str:
    .string "FAILED\n"









.global uart_write_str
    .p2align        1
uart_write_str:
    # Clobbers $r0, $r1, $a0, $r10; input pointer in $a0
    $r10 <- $lr # Save off return value
    $r1 <- $a0 # Save off pointer
.uart_write_str_loop:
    $a0 <- mem8[$r1]
    if $a0 == 0 $pc <- .uart_write_str_end
    CALL uart_write_char
    $r1 <- tiny $r1 + 1
    $pc <- .uart_write_str_loop
.uart_write_str_end:
    $lr <- $r10
.global test
.weak test
    test: # Defined as a pure return. If defined outside, should do the proper testing
.global sched_mode_setup
.weak sched_mode_setup
    sched_mode_setup: # Defined as a pure return. If defined outside, should do the proper testing
    $pc <- $lr


.global uart_write_char
    .p2align        1
uart_write_char:
    $r0 <- mem8[gpio_int_base]
    $r0 <- short $r0 & 1
    if $r0 != 0 $pc <- uart_write_char_sim

    # Clobbers $r0, has char to write in $a0
uart_write_char_wait:
    $r0 <- uart_status_reg     # Wait for the UART to be ready
    $r0 <- mem8[$r0]
    $r0 <- short $r0 & uart_status_tx_empty_bit_mask
    if $r0 == 0 $pc <- uart_write_char_wait

    $r0 <- uart_data_buf_reg   # Output to UART
    mem8[$r0] <- $a0
    $pc <- $lr

uart_write_char_sim:
    $r0 <- gpio3_base          # Output to sim
    mem8[$r0] <- $a0

    $pc <- $lr
