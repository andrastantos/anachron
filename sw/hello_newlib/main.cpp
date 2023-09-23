#include <stdio.h>
#include "uart.h"

int main() {
	uart_init(115200);
	printf("Hello world through newlib\n");
	return 0;
}
