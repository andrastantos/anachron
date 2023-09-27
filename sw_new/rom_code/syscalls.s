.include "mem_layout.inc"
.include "utils.inc"
.include "thread_context.inc"

/*
========     =====================================
Register     Functionality
========     =====================================
$r0          call-clobbered general purpose register; used in thunks for virtual inheritance. Must be call-clobbered
$r1          call-clobbered general purpose register; struct value address (return value area pointer for large return values). EH_RETURN_STACKADJ_RTX BREW_STACKADJ_REG. Must be call-clobbered
$r2          call-clobbered general purpose register; static chain register
$r3          call-clobbered general purpose register
$r4          call-clobbered first argument/return value register.
$r5          call-clobbered second argument/return value register.
$r6          call-clobbered third argument/return value register;
$r7          call-clobbered fourth argument/return value register;

$r8          call-saved general purpose register; EH_RETURN_DATA_REGNO
$r9          call-saved general purpose register; EH_RETURN_DATA_REGNO
$r10         call-saved general purpose register
$r11         call-saved general purpose register
$r12         call-saved register a.k.a. $fp - frame pointer.
$r13         call-saved register a.k.a. $sp - stack pointer.
$r14         call-saved register a.k.a. $lr - link register.
========     =====================================
*/

.global syscall_handler
.extern task_mode_exit
.extern con_write_char
.set EINVAL, 22

.section .rodata.syscall_table
    .p2align        2

syscall_table:
    .int  _sys_invalid    #  0
    .int  _sys_exit       #  1
    .int  _sys_open       #  2
    .int  _sys_close      #  3
    .int  _sys_read       #  4
    .int  _sys_write      #  5
    .int  _sys_lseek      #  6
    .int  _sys_unlink     #  7
    .int  _sys_getpid     #  8
    .int  _sys_kill       #  9
    .int  _sys_fstat      # 10

.set syscall_table_size, .-syscall_table
.set syscall_max, syscall_table_size / 4 - 1

.section .text.syscall_handler, "ax", @progbits
    .p2align        2

# syscall_handler
# ===================================
# Handles syscalls.
# Right now only handles SYS_EXIT and SYS_WRITE though
# a few syscalls that newlib defines are in the table
#
# Inputs: $a0: pointer to thread context
# Outputs: -
# Clobbers: $r0, $r1, $r10, $a0
syscall_handler:
    # Extract syscall number and adjust return address
    $r0 <- $tpc
    $r0 <- $r0 + 2
    $r1 <- mem16[$r0]
    $r0 <- $r0 + 2
    $tpc <- $r0
    $r0 <- syscall_max
    if $r1 <= $r0 $pc <- _syscall_ok
    # We have an invalid syscall number --> simply return with error
_sys_invalid:
    $r0 <- EINVAL
    mem[$a0 + tcontext.lr_save] <- $r0
    $pc <- $lr
    # We have a valid syscall number, jump to the handler
_syscall_ok:
    $r1 <- short $r1 << 2
    $r0 <- $r1 + syscall_table
    $pc <- mem[$r0]

#########################################################

_sys_exit:
    $pc <- task_mode_exit

#########################################################

_sys_write:
    $r0 <- mem[$a0 + tcontext.a0_save] # load file descriptor
    $r0 <- short $r0 - 2
    if $r0 > 0 $pc <- _sys_invalid_arg_return
    $r10 <- $lr # Save off errno value
    $r1 <- mem[$a0 + tcontext.a1_save] # Load string pointer
    $r2 <- mem[$a0 + tcontext.a2_save] # Load buffer size
_sys_write_loop:
    $a0 <- mem8[$r1]
    if $r2 == 0 $pc <- _sys_write_end
    CALL con_write_char
    $r1 <- tiny $r1 + 1
    $r2 <- tiny $r2 - 1
    $pc <- _sys_write_loop
_sys_write_end:
    $pc <- $r10 # Saved $lr

#########################################################

_sys_invalid_arg_return:
_sys_lseek:
_sys_unlink:
_sys_open:
_sys_read:
_sys_kill:
_sys_fstat:
    $r0 <- EINVAL
    mem[$a0 + tcontext.lr_save] <- $r0
_sys_close:
_sys_getpid:
    $r0 <- tiny -1
    mem[$a0 + tcontext.a0_save] <- $r0
    $pc <- $lr


