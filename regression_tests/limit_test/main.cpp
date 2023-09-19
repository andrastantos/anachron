#include "platform.h"
#include "uart.h"
#include "sim_utils.h"

int main()
{
	uint32_t a = 1000;
	uint32_t ws = 0;
	sim_uart_init(115200);
	sim_uart_write_str("Limit test\n");
	// We're going to try to access DRAM in various WS pages: all sohuld succeed
	for (ws = 0; ws <= 15; ws+=4) {
		uint32_t *pa = (&a)+ws*0x04000000; // We are counting in 32-bit addresses, so WS needs to be shifted to bit-position 25 instead of 27.
		sim_uart_write_str("attempting address: ");
		sim_uart_write_hex(uint32_t(pa));
		sim_uart_write_str(" a: ");
		sim_uart_write_hex(uint32_t(&a));
		sim_uart_write_str(" ws: ");
		sim_uart_write_hex(ws);
		sim_uart_write_str(" ... ");
		*pa = ws;
		if (a != ws) {
			sim_uart_write_str("failed\n");
			return 3;
		}
		sim_uart_write_str("\n");
		
	}
	sim_uart_write_str("test succeeded trying limits...\n");
	asm volatile ( "$a0 <- tiny 2" : : );
	asm volatile ( "nop\n\tnop\n\tnop" : : );
	uint32_t *violation = (uint32_t*)0x08010000;
	*violation = 1;
	asm volatile ( "nop\n\tnop\n\tnop" : : );
	//sim_terminate(1);
	sim_uart_write_str("test failed trying limits...\n");
	return 1;
}
