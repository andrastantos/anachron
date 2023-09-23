#include "platform.h"
#include "uart.h"
#include "sim_utils.h"

volatile uint32_t* const dram = (volatile uint32_t *)(dram_base);

const uint32_t test_step = 1;

inline uint32_t test_data(uint32_t addr) {
	return
		(((addr + 0) & 0xff) <<  0) |
		(((addr + 1) & 0xff) <<  8) |
		(((addr + 2) & 0xff) << 16) |
		(((addr + 3) & 0xff) << 24)
	;
}

extern "C" uint32_t mem_size_detect(uint32_t);

int main()
{
	sim_uart_init(115200);
	sim_uart_write_str("filling memory...");
	for(size_t idx=0;idx<1024*1024/sizeof(uint32_t);idx+=1024) dram[idx] = 0;
	sim_uart_write_str(" done\n");
	sim_uart_write_str("detecting mem size...");
	uint32_t mem_size = mem_size_detect(dram_base);
	sim_uart_write_str(" got ");
	sim_uart_write_hex(mem_size);
	sim_uart_write_str("\n");

	sim_uart_write_str("Memtest started!\n");
	sim_uart_write_str("Writing pattern...\n");
	for(size_t idx=0;idx<mem_size/sizeof(uint32_t);idx+=test_step) {
		dram[idx] = test_data(idx);
	}
	for(size_t rb_cnt=0;rb_cnt<2;++rb_cnt) {
		sim_uart_write_str("Read-back #");
		sim_uart_write_dec(rb_cnt);
		sim_uart_write_str("\n");
		bool failed = false;
		for(size_t idx=0;idx<mem_size/sizeof(uint32_t);idx+=test_step) {
			volatile uint32_t val = dram[idx];
			uint32_t expected = test_data(idx);
			if (val != expected) {
				sim_uart_write_str("    Mismatch at idx: ");
				sim_uart_write_hex(uint32_t(idx));
				sim_uart_write_str(" expected: ");
				sim_uart_write_hex(expected);
				sim_uart_write_str(" actual: ");
				sim_uart_write_hex(val);
				sim_uart_write_str("\n");
				failed = true;
			}
		}
	}
	sim_uart_write_str("Done\n");
}
