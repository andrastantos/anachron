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