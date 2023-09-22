#include "uart.h"
#include "platform.h"

// Init UART to 9600 BAUD 8N1P5, based on a 50MHz system clock rate
void uart_init(unsigned int baud_rate) {
	uart1_base[uart_config1_reg_ofs] = uart_config1_stop_one_and_half | uart_config1_word_size_8 | uart_config1_flow_control_sw;
	switch (baud_rate) {
		default: {
			unsigned int prescaler = 32-__builtin_clz((uart1_clock_rate / baud_rate) >> 8);
			unsigned int divider = uart1_clock_rate / (1 << prescaler) / baud_rate / 2;
			uart1_base[uart_config2_reg_ofs] = prescaler * (1 << uart_config2_pre_scaler_bit);
			uart1_base[uart_divider_reg_ofs] = divider;
			break;
		}
	}
}

void uart_write_char(char value) {
	uart_wait_tx();
	uart1_base[uart_data_buf_reg_ofs] = (uint8_t)value;
}

void uart_write_str(const char *message) {
	if (message == nullptr) return;
	if (message[0] == 0) return;
	while (*message != 0) {
		uart_write_char(*message);
		++message;
	}
}

static const char *hex_digit_table = "0123456789abcdef";

void uart_write_hex(uint8_t value) {
	uart_write_str("0x");
	uart_write_char(hex_digit_table[(value >> 4) & 0xf]);
	uart_write_char(hex_digit_table[(value >> 0) & 0xf]);
}

void uart_write_hex(uint16_t value) {
	uart_write_str("0x");
	uart_write_char(hex_digit_table[(value >> 12) & 0xf]);
	uart_write_char(hex_digit_table[(value >>  8) & 0xf]);
	uart_write_char(hex_digit_table[(value >>  4) & 0xf]);
	uart_write_char(hex_digit_table[(value >>  0) & 0xf]);
}

void uart_write_hex(uint32_t value) {
	uart_write_str("0x");
	uart_write_char(hex_digit_table[(value >> 28) & 0xf]);
	uart_write_char(hex_digit_table[(value >> 24) & 0xf]);
	uart_write_char(hex_digit_table[(value >> 20) & 0xf]);
	uart_write_char(hex_digit_table[(value >> 16) & 0xf]);
	uart_write_char(hex_digit_table[(value >> 12) & 0xf]);
	uart_write_char(hex_digit_table[(value >>  8) & 0xf]);
	uart_write_char(hex_digit_table[(value >>  4) & 0xf]);
	uart_write_char(hex_digit_table[(value >>  0) & 0xf]);
}
void uart_wait_tx() {
	while ((uart1_base[uart_status_reg_ofs] & (1 << uart_status_tx_empty_bit)) == 0);
}

void uart_write_dec(unsigned int value) {
	char digits[10]; // A 32-bit integer can at most have 10 digits
	int idx = 0;
	if (value == 0) {
		uart_write_char('0');
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
		uart_write_char(char('0'+digits[--idx]));
	}
}
