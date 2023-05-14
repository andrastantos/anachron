#include "uart.h"
#include "platform.h"

// Init UART to 9600 BAUD 8N1P5, based on a 50MHz system clock rate
void uart_init(unsigned int baud_rate) {
	uart1_base[uart_config1_reg_ofs] = uart_config1_stop_one_and_half | uart_config1_word_size_8 | uart_config1_flow_control_sw;
	switch (baud_rate) {
		case 4800:
			uart1_base[uart_config2_reg_ofs] = uart_config2_pre_scaler_64;
			uart1_base[uart_divider_reg_ofs] = 81;
			break;
		case 9600:
			uart1_base[uart_config2_reg_ofs] = uart_config2_pre_scaler_32;
			uart1_base[uart_divider_reg_ofs] = 81;
			break;
		case 19200:
			uart1_base[uart_config2_reg_ofs] = uart_config2_pre_scaler_16;
			uart1_base[uart_divider_reg_ofs] = 81;
			break;
		case 57600:
			uart1_base[uart_config2_reg_ofs] = uart_config2_pre_scaler_4;
			uart1_base[uart_divider_reg_ofs] = 109;
			break;
		case 115200:
			uart1_base[uart_config2_reg_ofs] = uart_config2_pre_scaler_2;
			uart1_base[uart_divider_reg_ofs] = 109;
			break;
		default: {
			unsigned int prescaler = __builtin_clz((uart1_clock_rate / baud_rate) >> 8);
			unsigned int divider = uart1_clock_rate / (1 << prescaler) / divider / 2;
			uart1_base[uart_config2_reg_ofs] = prescaler * (1 << uart_config2_pre_scaler_bit);
			uart1_base[uart_divider_reg_ofs] = divider;
			break;
		}
	}
}

void uart_write_str(const char *message) {
	if (message == nullptr) return;
	if (message[0] == 0) return;
	while (*message != 0) {
		uart_wait_tx();
		uart1_base[uart_data_buf_reg_ofs] = *(uint8_t*)message;
		++message;
	}
}

void uart_write_hex(uint8_t value) {}
void uart_write_hex(uint16_t value) {}
void uart_write_hex(uint32_t value) {}

void uart_wait_tx() {
	while ((uart1_base[uart_status_reg_ofs] & (1 << uart_status_tx_empty_bit)) == 0);
}


void sim_uart_init(unsigned int baud_rate) {}
void sim_uart_write_str(const char *message) {
	if (message == nullptr) return;
	if (message[0] == 0) return;
	while (*message != 0) {
		gpio3_base[0] = *(uint8_t*)message;
		++message;
	}
}

void sim_uart_write_hex(uint8_t value);
void sim_uart_write_hex(uint16_t value);
void sim_uart_write_hex(uint32_t value);

void sim_uart_wait_tx() {}
