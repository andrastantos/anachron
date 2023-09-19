.text
.p2align        1

.global _start

_start:
	$a0 <- tiny 1
	.hword 0xe0fe, 0x0000 # An invalid instruction
loop:
	$a0 <- tiny 0
	$pc <- loop
	
