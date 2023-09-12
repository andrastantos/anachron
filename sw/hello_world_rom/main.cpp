#include "platform.h"
#include "uart.h"
#include "sim_utils.h"

int main()
{
	sim_uart_init(115200);
	sim_uart_write_str("Hello world from ROM!\n");
}
