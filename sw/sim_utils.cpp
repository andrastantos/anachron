#include "sim_utils.h"
#include "platform.h"
#include "uart.h"

static const char *hex_digit_table = "0123456789abcdef";

void sim_uart_init(unsigned int baud_rate) {
	uart_init(baud_rate);
}

void sim_uart_write_str(const char *message) {
	if (message == nullptr) return;
	if (message[0] == 0) return;
	while (*message != 0) {
		sim_uart_write_char(*message);
		++message;
	}
}

void sim_uart_write_char(char value) {
	gpio3_base[0] = (uint8_t)value;
	uart_write_char(value);
}

void sim_uart_write_hex(uint8_t value) {
	sim_uart_write_str("0x");
	sim_uart_write_char(hex_digit_table[(value >> 4) & 0xf]);
	sim_uart_write_char(hex_digit_table[(value >> 0) & 0xf]);
}

void sim_uart_write_hex(uint16_t value) {
	sim_uart_write_str("0x");
	sim_uart_write_char(hex_digit_table[(value >> 12) & 0xf]);
	sim_uart_write_char(hex_digit_table[(value >>  8) & 0xf]);
	sim_uart_write_char(hex_digit_table[(value >>  4) & 0xf]);
	sim_uart_write_char(hex_digit_table[(value >>  0) & 0xf]);
}

void sim_uart_write_hex(uint32_t value) {
	sim_uart_write_str("0x");
	sim_uart_write_char(hex_digit_table[(value >> 28) & 0xf]);
	sim_uart_write_char(hex_digit_table[(value >> 24) & 0xf]);
	sim_uart_write_char(hex_digit_table[(value >> 20) & 0xf]);
	sim_uart_write_char(hex_digit_table[(value >> 16) & 0xf]);
	sim_uart_write_char(hex_digit_table[(value >> 12) & 0xf]);
	sim_uart_write_char(hex_digit_table[(value >>  8) & 0xf]);
	sim_uart_write_char(hex_digit_table[(value >>  4) & 0xf]);
	sim_uart_write_char(hex_digit_table[(value >>  0) & 0xf]);
}

void sim_uart_wait_tx() {}

void sim_terminate(uint8_t exit_code) {
	gpio4_base[0] = exit_code;
}

void sim_uart_write_dec(unsigned int value) {
	char digits[10]; // A 32-bit integer can at most have 10 digits
	int idx = 0;
	if (value == 0) {
		sim_uart_write_char('0');
		return;
	}
	while (value > 0) {
		char digit = value % 10;
		digits[idx] = digit;
		value /= 10;
		++idx;
		if (idx > sizeof(digits)) break;
	}
	while (idx > 0) {
		sim_uart_write_char(char('0'+digits[--idx]));
	}
}
