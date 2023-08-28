#pragma once

#include <stdint.h>
#include <stddef.h>

const uint32_t rom_base =    0x00000000;
const uint32_t gpio_base =   0x00010000;
const uint32_t io_apb_base = 0x00020000;
const uint32_t io_apb_size = 4096*16;
const uint32_t gpio_size =   4096;
const uint32_t dram_base =   0x08000000;

const uint32_t wait_state_0  = 0x10000000;
const uint32_t wait_state_1  = 0x20000000;
const uint32_t wait_state_2  = 0x30000000;
const uint32_t wait_state_3  = 0x40000000;
const uint32_t wait_state_4  = 0x50000000;
const uint32_t wait_state_5  = 0x60000000;
const uint32_t wait_state_6  = 0x70000000;
const uint32_t wait_state_7  = 0x80000000;
const uint32_t wait_state_8  = 0x90000000;
const uint32_t wait_state_9  = 0xa0000000;
const uint32_t wait_state_10 = 0xb0000000;
const uint32_t wait_state_11 = 0xc0000000;
const uint32_t wait_state_12 = 0xd0000000;
const uint32_t wait_state_13 = 0xe0000000;
const uint32_t wait_state_14 = 0xf0000000;
const uint32_t wait_state_15 = 0x00000000;
const uint32_t wait_state_default = wait_state_15;

/////////////////////////////////////////////////////////////////////////////////////
// GPIO
/////////////////////////////////////////////////////////////////////////////////////
volatile uint8_t* const gpio1_base = (volatile uint8_t *)(gpio_base);
volatile uint8_t* const gpio2_base = (volatile uint8_t *)(gpio_base + gpio_size);

const uint32_t gpio_data_reg_ofs  = 0;

volatile uint8_t* const gpio3_base = (volatile uint8_t *)((io_apb_base + 0x0100) | wait_state_0);
volatile uint8_t* const gpio4_base = (volatile uint8_t *)((io_apb_base + 0x0200) | wait_state_0);

/////////////////////////////////////////////////////////////////////////////////////
// UART
/////////////////////////////////////////////////////////////////////////////////////

const uint32_t cpu_clock_rate    = 10000000; // 10MHz clock for the processor
const uint32_t system_clock_rate = 50000000; // 50MHz clock for the system

volatile uint8_t* const uart1_base = (volatile uint8_t *)((io_apb_base + 0x0000) | wait_state_0);
const uint32_t uart1_clock_rate = system_clock_rate;

// Baud rate = <clock freq> / <prescaler> / (<divider> + 1) / 2

const uint32_t uart_data_buf_reg_ofs                = 0;
const uint32_t uart_status_reg_ofs                  = 1;
const uint32_t uart_config1_reg_ofs                 = 2;
const uint32_t uart_config2_reg_ofs                 = 3;
const uint32_t uart_divider_reg_ofs                 = 4;

// Status register
const uint8_t uart_status_rx_full_bit               = 0;
const uint8_t uart_status_tx_empty_bit              = 1;
const uint8_t uart_status_parity_error_bit          = 2;
const uint8_t uart_status_framing_error_bit         = 3;
const uint8_t uart_status_overrun_error_bit         = 4;
const uint8_t uart_status_cts_pin_bit               = 5;

// Config1 register
const uint8_t uart_config1_parity_bit               = 0;
const uint8_t uart_config1_stop_cnt_bit             = 2;
const uint8_t uart_config1_word_size_bit            = 4;
const uint8_t uart_config1_flow_control_bit         = 6;
const uint8_t uart_config1_interrupt_enable_bit     = 7;

const uint8_t uart_config1_parity_none              = 0 * (1 << uart_config1_parity_bit);
const uint8_t uart_config1_parity_even              = 1 * (1 << uart_config1_parity_bit);
const uint8_t uart_config1_parity_odd               = 2 * (1 << uart_config1_parity_bit);

const uint8_t uart_config1_stop_one                 = 0 * (1 << uart_config1_stop_cnt_bit);
const uint8_t uart_config1_stop_one_and_half        = 1 * (1 << uart_config1_stop_cnt_bit);
const uint8_t uart_config1_stop_two                 = 2 * (1 << uart_config1_stop_cnt_bit);

const uint8_t uart_config1_word_size_8              = 0 * (1 << uart_config1_word_size_bit);
const uint8_t uart_config1_word_size_7              = 1 * (1 << uart_config1_word_size_bit);
const uint8_t uart_config1_word_size_6              = 2 * (1 << uart_config1_word_size_bit);
const uint8_t uart_config1_word_size_5              = 3 * (1 << uart_config1_word_size_bit);

const uint8_t uart_config1_flow_control_sw          = 0 * (1 << uart_config1_flow_control_bit);
const uint8_t uart_config1_flow_control_hw          = 1 * (1 << uart_config1_flow_control_bit);

const uint8_t uart_config1_interrupt_disable        = 0 * (1 << uart_config1_interrupt_enable_bit);
const uint8_t uart_config1_interrupt_enable         = 1 * (1 << uart_config1_interrupt_enable_bit);

// Config 2 register
const uint8_t uart_config2_pre_scaler_bit           = 0;
const uint8_t uart_config2_rts_pin_bit              = 4;
const uint8_t uart_config2_rx_enable_bit            = 5;
const uint8_t uart_config2_use_hw_tx_en_bit         = 6;
const uint8_t uart_config2_tx_en_bit                = 7;

const uint8_t uart_config2_pre_scaler_1             = 0 * (1 << uart_config2_pre_scaler_bit);
const uint8_t uart_config2_pre_scaler_2             = 1 * (1 << uart_config2_pre_scaler_bit);
const uint8_t uart_config2_pre_scaler_4             = 2 * (1 << uart_config2_pre_scaler_bit);
const uint8_t uart_config2_pre_scaler_8             = 3 * (1 << uart_config2_pre_scaler_bit);
const uint8_t uart_config2_pre_scaler_16            = 4 * (1 << uart_config2_pre_scaler_bit);
const uint8_t uart_config2_pre_scaler_32            = 5 * (1 << uart_config2_pre_scaler_bit);
const uint8_t uart_config2_pre_scaler_64            = 6 * (1 << uart_config2_pre_scaler_bit);
const uint8_t uart_config2_pre_scaler_128           = 7 * (1 << uart_config2_pre_scaler_bit);
const uint8_t uart_config2_rts                      = 1 * (1 << uart_config2_rts_pin_bit);
const uint8_t uart_config2_rx_enable                = 1 * (1 << uart_config2_rx_enable_bit);
const uint8_t uart_config2_use_hw_tx_en             = 1 * (1 << uart_config2_use_hw_tx_en_bit);
const uint8_t uart_config2_tx_en                    = 1 * (1 << uart_config2_tx_en_bit);

/*
inline uint32_t next_power_of_2(uint32_t v) {
    v--;
    v |= v >> 1;
    v |= v >> 2;
    v |= v >> 4;
    v |= v >> 8;
    v |= v >> 16;
    v++;
    return v;
}
*/

/////////////////////////////////////////////////////////////////////////////////////
// CSRs
/////////////////////////////////////////////////////////////////////////////////////

const size_t csr_event_base =  0x0100;
const size_t csr_bus_if_base = 0x0200;
const size_t csr_dma_base =    0x0300;

volatile uint32_t* const csr_ver_cap_reg = (volatile uint32_t *)(0x0000);
volatile uint32_t* const csr_pmem_base   = (volatile uint32_t *)(0x0001);
volatile uint32_t* const csr_pmem_limit  = (volatile uint32_t *)(0x0002);
volatile uint32_t* const csr_dmem_base   = (volatile uint32_t *)(0x0003);
volatile uint32_t* const csr_dmem_limit  = (volatile uint32_t *)(0x0004);
volatile uint32_t* const csr_ecause      = (volatile uint32_t *)(0x0005);
volatile uint32_t* const csr_eaddr       = (volatile uint32_t *)(0x0006);

volatile uint32_t* const csr_event_regs    = (volatile uint32_t *)(csr_event_base + 0x0002);

const size_t event_sel_ofs = 0;
const size_t event_cnt_ofs = 1;
const size_t event_reg_size = 2;

volatile uint32_t* const csr_event_enable  = (volatile uint32_t *)(csr_event_base + 0x0000);
volatile uint32_t* const csr_event_sel0    = (volatile uint32_t *)(csr_event_base + 0x0002);
volatile uint32_t* const csr_event_cnt0    = (volatile uint32_t *)(csr_event_base + 0x0003);
volatile uint32_t* const csr_event_sel1    = (volatile uint32_t *)(csr_event_base + 0x0004);
volatile uint32_t* const csr_event_cnt1    = (volatile uint32_t *)(csr_event_base + 0x0005);
volatile uint32_t* const csr_event_sel2    = (volatile uint32_t *)(csr_event_base + 0x0006);
volatile uint32_t* const csr_event_cnt2    = (volatile uint32_t *)(csr_event_base + 0x0007);
volatile uint32_t* const csr_event_sel3    = (volatile uint32_t *)(csr_event_base + 0x0008);
volatile uint32_t* const csr_event_cnt3    = (volatile uint32_t *)(csr_event_base + 0x0009);

const uint8_t event_clk_cycles        = 0;
const uint8_t event_fetch_wait_on_bus = 1;
const uint8_t event_decode_wait_on_rf = 2;
const uint8_t event_mem_wait_on_bus   = 3;
const uint8_t event_branch_taken      = 4;
const uint8_t event_branch            = 5;
const uint8_t event_load              = 6;
const uint8_t event_store             = 7;
const uint8_t event_load_or_store     = 8;
const uint8_t event_execute           = 9;
const uint8_t event_bus_idle          = 10;
const uint8_t event_fetch             = 11;
const uint8_t event_fetch_drop        = 12;
const uint8_t event_inst_word         = 13;

const size_t event_cnt_count = 8;
