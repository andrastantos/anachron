################
#
# DRAM layout is as follows:
#
# 0xffff_fc00 - 0xffff_ffff: 1kB SCHEDULER mode work area
# 0x0800_0000 - ???: TASK mode DRAM
#
# We use a trick here (which will need slight modification once the second RAM bank
# comes online): we're placing the SCHEDULER mode work area at the end of the
# DRAM physical address region, at 0xffff_fc00. This region is guaranteed to
# alias to the very last 1kB of the physically present DRAM.
#
# For it to work now, we'll have to engage 'dram_single_bank' register, which
# is default 0. Once we have dual-bank RAM detection working, this register will
# need to be set according to the detected bank configuration.
#
#
#
# Normal TASK mode applications, which are mapped to work with logical addresses
# don't care about any of this, they are linked to start execution at address 0.
# Their init code should assume that $sp is set to the (rather, after) the last
# addressable memory location
#
# Exclusive TASK mode applications (such as the OS kernel) are using
# physical addresses, so they do see this 1kB SCHEDULER mode work area.
# They need to be linked to start address 0x0800_0400. Their $sp is also set
# to the top of the addressable space, which is the end of DRAM for now.
#
# TODO: this eventually will have to get more complicalted: there could be several
# exclusive mode applications loaded, or at least two: the kernel and a game.
# While they are not protected from one another necessarily, they would somehow
# at least not stomp on each other if they were written properly. Not sure how
# to deal with that at the moment. Maybe the kernel should be relocatable?
#
################
.include "thread_context.inc"
.include "utils.inc"
.include "mem_layout.inc"
.include "csrs.inc"
.include "exceptions.inc"

# Register setup:
# bits 7-0: refresh divider
# bit 8: refresh disable (if set)
# bit 10-9: DRAM bank size: 0 - 22 bits, 1 - 20 bits, 2 - 18 bits, 3 - 16 bits
# bit 11: DRAM bank swap: 0 - no swap, 1 - swap

.global _rom_start
.global _start
.weak _start
.global reg_save
.global eaddr_save
.global ecause_save
.global tpc_save
.global test
.weak test
.global sched_mode_setup
.weak sched_mode_setup
.global task_mode_exit

#########################################################################
# Entry point after reset. This piece of code will be put at address 0
# by the linker.
#########################################################################

# All we do here is to jump to the real start of the code, but
# changing wait-states at the same time
.section .rom_init, "ax", @progbits
.p2align        1

_rom_start:
    $pc <- fast_start # Set WS to 0



#########################################################################
# Meaningful entry point after reset.
#########################################################################

.section .text.fast_start, "ax", @progbits
    .p2align        2

fast_start:
    CALL con_init # set up console serial port
    $r11 <- csr[csr_ecause]
    if $r11 == 0 $pc <- _reset # Upon reset let's go to the reset vector
    # We get here if we are recovering from a SCHEDULER mode exception.

    $a0 <- _sys_halt_str
    CALL con_write_str

    $a0 <- _ecause_str
    CALL con_write_str
    $a0 <- $r11
    CALL con_write_hex
    $a0 <- _newline_str
    CALL con_write_str

    $a0 <- _eaddr_str
    CALL con_write_str
    $a0 <- csr[csr_eaddr]
    CALL con_write_hex
    $a0 <- _newline_str
    CALL con_write_str

_halt:
    woi
    $pc <- _halt

_reset:
    # Initialize all registers to make the simulator happy
    $r0 <- tiny 0 # No nee to set $r0, it's already set.
    $r2 <- tiny 0
    $r3 <- tiny 0
    $r4 <- tiny 0
    $r5 <- tiny 0
    $r6 <- tiny 0
    $r7 <- tiny 0
    $r8 <- tiny 0
    $r9 <- tiny 0
    $r10 <- tiny 0
    $r11 <- tiny 0
    $r12 <- tiny 0
    $r13 <- tiny 0
    $r14 <- tiny 0

    # Detect DRAM size
    # TODO: we need to detect both DRAM banks and set up memory controller
    #       to create a unified view of memory. For now, we're only detecting
    #       memory in the first bank (n_ras_a).
    $a0 <- dram_base
    CALL mem_size_detect
    # Setting up base and limit registers.
    # Reserve some of the top of DRAM for scheduler mode use,
    # allow the rest for TASK mode
    # We are using $r8 as it is caller-saved, so we can expect
    # it to survive 'sched_mode_setup' below
    $r8 <- $a0 + dram_base - scheduler_page_size
    $r0 <- tiny 0
    csr[csr_pmem_base_reg] <- $r0
    csr[csr_dmem_base_reg] <- $r0
    csr[csr_pmem_limit_reg] <- $r8
    csr[csr_dmem_limit_reg] <- $r8
    # Setting up bus interface config according to memory sizes detected.
    # TODO: we need to update this once we can detect memory in both banks
    $r0 <- csr[csr_bus_if_cfg_reg]
    $r0 <- $r0 | csr_bus_if_cfg_reg.dram_single_bank
    csr[csr_bus_if_cfg_reg] <- $r0


    # Setting up the context pointer. For now, simply point to the region in the scheduler page, right after the context pointer itself
    $r0 <- current_tcontext
    $r0 <- tiny $r0 + 4
    mem[current_tcontext] <- $r0

    # We're ready to enter task mode, but we do it in a stealthy way.
    # First, we allow for customization of the startup by providing a
    # a weak symbol 'sched_mode_setup'. It's just a return in there,
    # but could be provided externally.
    # Second, we use another weak symbol '_start' to enter task mode.
    # The default implementation just jumps to the bottom of DRAM,
    # but can be provided externally in which case more TASK-mode
    # ROM-code can be executed. The trick here is that '_start' is
    # the  normal entry-point for the linker, so any executable
    # linked with newlib would expect execution to start there.
    $lr <- _end_loop
    $tpc <- _start
    CALL sched_mode_setup
    $sp <- $r8 # Set up default stack.
    $a0 <- $r8 # Move top of DRAM into first argument to _start
    ####################################################################################
    # We are ready to enter task mode
_reset_enter_task_mode:
    stm
    ####################################################################################
    # We save off the current context
    # From here on $a1 will be context pointer
    mem[reg_save] <- $a1
    $a1 <- mem[current_tcontext]
    mem[$a1 + tcontext.r0_save] <- $r0
    mem[$a1 + tcontext.r1_save] <- $r1
    mem[$a1 + tcontext.r2_save] <- $r2
    mem[$a1 + tcontext.r3_save] <- $r3
    mem[$a1 + tcontext.r4_save] <- $r4
    $r0 <- mem[reg_save]
    mem[$a1 + tcontext.r5_save] <- $r0
    mem[$a1 + tcontext.r6_save] <- $r6
    mem[$a1 + tcontext.r7_save] <- $r7
    mem[$a1 + tcontext.r8_save] <- $r8
    mem[$a1 + tcontext.r9_save] <- $r9
    mem[$a1 + tcontext.r10_save] <- $r10
    mem[$a1 + tcontext.r11_save] <- $r11
    mem[$a1 + tcontext.r12_save] <- $r12
    mem[$a1 + tcontext.r13_save] <- $r13
    mem[$a1 + tcontext.r14_save] <- $r14
    $r0 <- $tpc
    mem[$a1 + tcontext.tpc_save] <- $r0
    $r11 <- csr[csr_ecause]
    mem[$a1 + tcontext.ecause_save] <- $r11
    $r11 <- $r11 - exc_syscall
    if $r11 != 0 $pc <- task_mode_exit
    $pc <- syscall_handler
    # This wasn't a syscall: dump all registers and terminate
task_mode_exit:
    $r11 <- tiny 0 # $r11 counts the registers we've dumped
_reg_dump_loop:
    $a0 <- _reg_str # print '$r'
    CALL con_write_str
    $a0 <- $r11
    $a0 <- short $a0 & 15
    $r0 <- 10
    $a2 <- _reg_after_str
    if $a0 < $r0 $pc <- _single_digit
    # We have a two-digit register name
    $r1 <- short $a0 - 10
    $a0 <- '1 # print '1'
    CALL con_write_char
    $a0 <- $r1
    $a2 <- tiny $a2 + 1
_single_digit:
    $a0 <- short $a0 + '0'
    CALL con_write_char

    $a0 <- $a2
    CALL con_write_str
    # load the saved register value
    $a1 <- mem[current_tcontext]
    $a0 <- short $r11 << 2
    $a0 <- $a1 + $a0
    $a0 <- $a0 + tcontext.r0_save
    $a0 <- mem[$a0]
    CALL con_write_hex
    $a0 <- _newline_str
    CALL con_write_str
    $r11 <- short $r11 + 1
    $a0 <- short 15
    if $r11 != $a0 $pc <- _reg_dump_loop

    ## dump special registers

    $a0 <- _ecause_str
    CALL con_write_str
    $a0 <- mem[$a1 + tcontext.ecause_save]
    CALL con_write_hex
    $a0 <- _newline_str
    CALL con_write_str

    $a0 <- _eaddr_str
    CALL con_write_str
    $a0 <- csr[csr_eaddr]
    CALL con_write_hex
    $a0 <- _newline_str
    CALL con_write_str

    $a0 <- _tpc_str
    CALL con_write_str
    $a0 <- mem[$a1 + tcontext.tpc_save]
    CALL con_write_hex
    $a0 <- _newline_str
    CALL con_write_str

    # Call any test function we might habe defined
    CALL test

    # Terminate under simulation
    $r0 <- gpio4_base
    $r1 <- 0
    mem8[$r0] <- $r0
_end_loop:
    $pc <- _end_loop

# Weak definitions for functions that are called from here, but could be provided elsewhere
.section .text.weak_functions, "ax", @progbits
    .p2align        2
test: # If defined outside, should do the proper testing
sched_mode_setup: # If defined outside, should do the proper testing
    $pc <- $lr


# Weak definition for _start. This allows for ROM-based code to coexist with DRAM based one.
# The default behavior is to simply jump to the beginning of DRAM, but if linked with something
# that defines this, it'll jump to there instead. Either way, '_start' gets executed in TASK mode.
.section .init._start, "ax", @progbits
    .p2align        2
_start:
    $pc <- dram_base


.struct scheduler_page
    reg_save:         .space 4 # Space for saving a single register during context save
    current_tcontext: .space 4 # Pointer to currently running thread context


################## Strings used in the above code
.section .rodata.rom_start_strings
    .p2align        2
_eaddr_str:
    .string "eaddr:  "

    .p2align        2
_ecause_str:
    .string "ecause: "

    .p2align        2
_tpc_str:
    .string "$tpc:   "

    .p2align        2
_newline_str:
    .string "\n"

    .p2align        2
_reg_str:
    .string "$r"

    .p2align        2
_reg_after_str:
    .string "     "

_sys_halt_str:
    .string "EXCEPTION IN SCHEDULER MODE\n"
