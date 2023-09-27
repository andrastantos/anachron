# Non-DRAM ranges
.set rom_base,                 0x00000000
.set gpio_base,                0x00010000
.set io_apb_base,              0x00020000
# DRAM location
.set dram_base,                0x08000000
.set scheduler_page_size,            1024 # If this changes, the appropriate default load address for the text segment in the LD scripts will have to follow suit
.set scheduler_page,           0xffffffff - scheduler_page_size + 1

# Memory wait-state aliases
.set wait_state_0,             0x10000000
.set wait_state_1,             0x20000000
.set wait_state_2,             0x30000000
.set wait_state_3,             0x40000000
.set wait_state_4,             0x50000000
.set wait_state_5,             0x60000000
.set wait_state_6,             0x70000000
.set wait_state_7,             0x80000000
.set wait_state_8,             0x90000000
.set wait_state_9,             0xa0000000
.set wait_state_10,            0xb0000000
.set wait_state_11,            0xc0000000
.set wait_state_12,            0xd0000000
.set wait_state_13,            0xe0000000
.set wait_state_14,            0xf0000000
.set wait_state_15,            0x00000000

# Detailed I/O registers
.set gpio1_base,               (gpio_base + 0x0000) | wait_state_0
.set gpio2_base,               (gpio_base + 0x1000) | wait_state_0
.set gpio_int_base,            (gpio_base + 0x2000) | wait_state_0
.set gpio3_base,               (io_apb_base + 0x0100) | wait_state_0
.set gpio4_base,               (io_apb_base + 0x0200) | wait_state_0

.set uart1_base,               (io_apb_base + 0x0000) | wait_state_0
