#include "platform.h"
#include "uart.h"
#include "sim_utils.h"

int main()
{
	if (is_sim()) {
		sim_uart_write_str("Hello sim world\n");
	} else {
		sim_uart_write_str("Hello real world\n");
	}
	sim_uart_write_str("uart_config2_reg_ofs: "); sim_uart_write_hex(uart1_base[uart_config2_reg_ofs]); sim_uart_write_str("\n");
	sim_uart_write_str("uart_divider_reg_ofs: "); sim_uart_write_hex(uart1_base[uart_divider_reg_ofs]); sim_uart_write_str("\n");
	sim_uart_write_str("uart_config1_reg_ofs: "); sim_uart_write_hex(uart1_base[uart_config1_reg_ofs]); sim_uart_write_str("\n");
}
