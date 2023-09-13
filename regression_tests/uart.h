#pragma once

#include <stdint.h>

void uart_init(unsigned int baud_rate);
void uart_write_str(const char *message);
void uart_write_char(char value);
void uart_write_hex(uint8_t value);
void uart_write_hex(uint16_t value);
void uart_write_hex(uint32_t value);
void uart_write_dec(unsigned int value);
void uart_wait_tx();

