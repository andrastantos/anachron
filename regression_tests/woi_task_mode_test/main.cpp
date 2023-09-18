#include "platform.h"
#include "uart.h"
#include "sim_utils.h"

int main()
{
	sim_uart_init(115200);
	if (is_sim()) {
		sim_uart_write_str("Hello sim world\n");
	} else {
		sim_uart_write_str("Hello real world\n");
	}
	asm volatile ( "woi" : : );
	sim_uart_write_str("Should not be here\n");
}
