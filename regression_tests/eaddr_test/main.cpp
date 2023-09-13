#include "platform.h"
#include "uart.h"
#include "sim_utils.h"

// Here we will cause an unaligned exception and test (manually unfortunately) that eaddr is set as expected
int main()
{
	asm volatile (
		"$r0 <- 0x01230006\n\t"
		"$r1 <- 0x12340002\n\t"
		"$r2 <- 0xdeadbeef\n\t"
		"mem32[$r0] <- $r2\n\t"
		"mem32[$r1] <- $r2\n\t"
		:
		:
	);
	//volatile int32_t *x = (int32_t *)(0x01230006); // This is unaligned
	//volatile int32_t *y = (int32_t *)(0x12340002); // This is unaligned
	//*x = 12;
	//*y = 32;
	sim_terminate(0);
}
