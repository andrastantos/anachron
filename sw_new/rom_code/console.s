.include "mem_layout.inc"
.include "utils.inc"

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


# Config1 register
.set uart_config1_parity_bit,                0
.set uart_config1_stop_cnt_bit,              2
.set uart_config1_word_size_bit,             4
.set uart_config1_flow_control_bit,          6
.set uart_config1_interrupt_enable_bit,      7

.set uart_config1_parity_none,               0 * (1 << uart_config1_parity_bit)
.set uart_config1_parity_even,               1 * (1 << uart_config1_parity_bit)
.set uart_config1_parity_odd,                2 * (1 << uart_config1_parity_bit)

.set uart_config1_stop_one,                  0 * (1 << uart_config1_stop_cnt_bit)
.set uart_config1_stop_one_and_half,         1 * (1 << uart_config1_stop_cnt_bit)
.set uart_config1_stop_two,                  2 * (1 << uart_config1_stop_cnt_bit)

.set uart_config1_word_size_8,               0 * (1 << uart_config1_word_size_bit)
.set uart_config1_word_size_7,               1 * (1 << uart_config1_word_size_bit)
.set uart_config1_word_size_6,               2 * (1 << uart_config1_word_size_bit)
.set uart_config1_word_size_5,               3 * (1 << uart_config1_word_size_bit)

.set uart_config1_flow_control_sw,           0 * (1 << uart_config1_flow_control_bit)
.set uart_config1_flow_control_hw,           1 * (1 << uart_config1_flow_control_bit)

.set uart_config1_interrupt_disable,         0 * (1 << uart_config1_interrupt_enable_bit)
.set uart_config1_interrupt_enable,          1 * (1 << uart_config1_interrupt_enable_bit)





.global con_init
.global con_wait_tx
.global con_write_str
.global con_write_hex
.global con_write_char



# con_init
# ===================================
# Initializes console to 115200 baud 8N1P5, soft flow ctrl
# Inputs: -
# Outputs: -
# Clobbers: $r0
.section .text.con_init, "ax", @progbits
    .p2align        2
con_init:
    $r0 <- uart_config1_stop_one_and_half | uart_config1_word_size_8 | uart_config1_flow_control_sw
    mem8[uart_config1_reg] <- $r0
    $r0 <- 0x20
    mem8[uart_config2_reg] <- $r0
    $r0 <- 0x56
    mem8[uart_divider_reg] <- $r0
    $pc <- $lr




# con_wait_tx
# ===================================
# Wait for console TX buffer to be empty
# Inputs: -
# Outputs: -
# Clobbers: $r0
.section .text.con_wait_tx, "ax", @progbits
    .p2align        2
con_wait_tx:
    $r0 <- mem8[gpio_int_base]
    $r0 <- short $r0 & 1
    if $r0 != 0 $pc <- _con_wait_tx_return
_con_wait_tx_loop:
    $r0 <- uart_status_reg
    $r0 <- mem8[$r0]
    $r0 <- short $r0 & uart_status_tx_empty_bit_mask
    if $r0 == 0 $pc <- _con_wait_tx_loop
_con_wait_tx_return:
    $pc <- $lr



# con_write_char
# ===================================
# Sends a single character to the console
# Inputs: $a0: character to be written
# Outputs: -
# Clobbers: $r0
.section .text.con_write_char, "ax", @progbits
    .p2align        2
con_write_char:
    $r0 <- mem8[gpio_int_base]
    $r0 <- short $r0 & 1
    if $r0 != 0 $pc <- _con_write_char_sim
_con_write_char_wait:
    $r0 <- uart_status_reg     # Wait for the UART to be ready
    $r0 <- mem8[$r0]
    $r0 <- short $r0 & uart_status_tx_empty_bit_mask
    if $r0 == 0 $pc <- _con_write_char_wait

    $r0 <- uart_data_buf_reg   # Output to UART
    mem8[$r0] <- $a0
    $pc <- $lr

_con_write_char_sim:
    $r0 <- gpio3_base          # Output to sim
    mem8[$r0] <- $a0

    $pc <- $lr




# con_write_hex
# ===================================
# Sends a 32-bit integer in hex to the console
# Inputs: $a0: integer to be written
# Outputs: -
# Clobbers: $r0, $r1, $r2, $r3, $r10, $a0
.section .text.con_write_hex, "ax", @progbits
    .p2align        2
con_write_hex:
    $r1 <- $a0 # Save off value
    $r10 <- $lr # Save off return value
    $r2 <- _hex_conv_str
    $r3 <- 28
_con_write_hex_loop:
    $a0 <- $a0 >> $r3
    $a0 <- short $a0 & 15
    $a0 <- $a0 + $r2
    $a0 <- mem8[$a0]
    CALL con_write_char
    if $r3 == 0 $pc <- _con_write_hex_end
    $r3 <- tiny $r3 - 4
    $a0 <- $r1
    $pc <- _con_write_hex_loop
_con_write_hex_end:
    $lr <- $r10
    $pc <- $lr

.section .rodata.rom_start_strings
    .p2align        2
_hex_conv_str:
    .string         "0123456789abcdef"



# con_write_str
# ===================================
# Sends a NULL-terminated string to the console
# Inputs: $a0: pointer to the string
# Outputs: -
# Clobbers: $r0, $r1, $r10, $a0
.section .text.con_write_str, "ax", @progbits
    .p2align        2
con_write_str:
    $r10 <- $lr # Save off return value
    $r1 <- $a0 # Save off pointer
_con_write_str_loop:
    $a0 <- mem8[$r1]
    if $a0 == 0 $pc <- _con_write_str_end
    CALL con_write_char
    $r1 <- tiny $r1 + 1
    $pc <- _con_write_str_loop
_con_write_str_end:
    $pc <- $r10
