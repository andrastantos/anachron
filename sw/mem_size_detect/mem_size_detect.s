.set dram_base,                0x08000000

.global mem_size_detect

.set min_step_size,       32*1024 # Start with 32kByte (two 16kByte modules)
.set max_step_size,     8096*1024 # We end with 8MByte (two 4MByte modules)

# mem_size_detect
# ===================================
# Detects memory size by trying aliasing addresses
# Doesn't permanently alter memory contents
# Inputs: $a0: DRAM base address
# Outputs: $a0: detected memory size
# Clobbers: $r0, $r1, $r2, $r3, $a1
.section .text.mem_size_detect, "ax", @progbits
    .p2align        2
mem_size_detect:
    $r1 <- min_step_size
    $r0 <- mem[$a0] # Read out original value, increment to create a unique test value
    $r0 <- $r0 + 1
    # Now we're looping through a few memory sizes and see if we get an alias
mem_size_detect_loop:
    $r2 <- $r1 + $a0
    $r3 <- mem[$r2]
    mem[$r2] <- $r0
    $a1 <- mem[$a0] # Read back aliased address
    if $a1 == $r0 $pc <- mem_size_found
    # We didn't alias: continue with the next size
    mem[$r2] <- $r3
    $r1 <- $r1 + $r1
    $pc <- mem_size_detect_loop
mem_size_found:
    mem[$r2] <- $r3
    $r0 <- $r0 - 1
    mem[$a0] <- $r0
    $a0 <- short $r1 >> 1 # We need to divide by two: we detected the aliasing size, so the actual size is half
    #$a0 <- $r1
    $pc <- $lr
