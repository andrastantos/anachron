#pragma once

#include <stdint.h>

void sim_uart_init(unsigned int baud_rate);
void sim_uart_write_str(const char *message);
void sim_uart_write_char(char value);
void sim_uart_write_hex(uint8_t value);
void sim_uart_write_hex(uint16_t value);
void sim_uart_write_hex(uint32_t value);
void sim_uart_write_dec(unsigned int value);
void sim_uart_wait_tx();

void sim_terminate(uint8_t exit_code);

// Where the software runs. The interrupt GPIO's inputs tell them apart: the RTL
// ties bit 0 to the 'is_sim' input, which the iverilog test bench
// (anacron_fpga/sim_top.sv) sets and the FPGA boards tie low; the instruction
// set simulator (brew-none-elf-run --environment operating) reads 0x02.
enum class Environment {
	fpga,    // real hardware
	rtl_sim, // the RTL under iverilog
	iss      // the instruction set simulator
};

Environment get_environment();