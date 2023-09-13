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
	asm volatile ( "$a0 <- tiny 0" : : );
	asm volatile ( "nop" : : );
	asm volatile ( "nop" : : );
	asm volatile ( "$a0 <- tiny $a0 + 1" : : );
	*gpio_int_base = 0xff;
	asm volatile ( "$a0 <- tiny $a0 + 1" : : );
	asm volatile ( "$a0 <- tiny $a0 + 1" : : );
	asm volatile ( "$a0 <- tiny $a0 + 1" : : );
	asm volatile ( "$a0 <- tiny $a0 + 1" : : );
	asm volatile ( "nop" : : );
	asm volatile ( "nop" : : );
	sim_uart_write_str("Should not be here\n");
}
