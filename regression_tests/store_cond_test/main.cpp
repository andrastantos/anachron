#include "platform.h"
#include "uart.h"
#include "sim_utils.h"

int main()
{
	int a = 0;
	int r0 = 1;
	sim_uart_init(115200);
	sim_uart_write_str("Store conditional test\n");
	asm volatile ( "$r0 <-1\n\tmemsc[%0] <- $r0\n\tmem[%1] <- $r0" : :"m"(a), "m"(r0):"$r0" );
	if (a != 1) {
		sim_uart_write_str("store failed\n");
	} else {
		sim_uart_write_str("store succeeded\n");
	}
	if (r0 != 0) {
		sim_uart_write_str("r0 failed\n");
	} else {
		sim_uart_write_str("r0 succeeded\n");
	}
}
