# Exception sources
.set exc_reset,                0x0000 # Hardware reset
.set exc_hwi,                  0x0010 # Hardware interrupt (only in TASK mode)
.set exc_swi_0,                0x0020 # SWI 0 instruction executed (FILL)
.set exc_swi_1,                0x0021 # SWI 1 instruction executed (BREAK)
.set exc_swi_2,                0x0022 # SWI 2 instruction executed (SYSCALL)
.set exc_swi_3,                0x0023 # SWI 3 instruction executed
.set exc_swi_4,                0x0024 # SWI 4 instruction executed
.set exc_swi_5,                0x0025 # SWI 5 instruction executed
.set exc_swi_6,                0x0026 # SWI 6 instruction executed
.set exc_swi_7,                0x0027 # SWI 7 instruction executed
.set exc_unknown_inst,         0x0030 # Undefined instruction
.set exc_type,                 0x0031 # Type error in instruction operands
.set exc_unaligned,            0x0032 # Unaligned memory access
.set exc_inst_av,              0x0040 # Instruction fetch AV
.set exc_mem_av,               0x0041 # Memory access AV

.set exc_syscall,              0x0022 # SWI 2 instruction executed (SYSCALL)
