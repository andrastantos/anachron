.macro CALL label
    $lr <- 1f
    $pc <- \label
1:
.endm

.global test
.global sched_mode_setup

.text
.p2align        1

.set csr_timer_base,    0x0400
.set csr_timer_limit,   csr_timer_base + 0
.set csr_timer_status,  csr_timer_base + 1
.set csr_timer_ctrl,    csr_timer_base + 2


test:
    $a2 <- $lr
    $a0 <- .fail_str
    # Testing ecause
    $a1 <- mem[.ecause_save]
    $a1 <- $a1 - 0x30
    if $a1 != 0 $pc <- _fail
    # Testing a0
    $a1 <- mem[.a0_save]
    $a1 <- $a1 - 0x1
    if $a1 != 0 $pc <- _fail
    $a0 <- .success_str
_fail:
    CALL uart_write_str
    $a0 <- .newline_str
    CALL uart_write_str
    $lr <- $a2
    $pc <- $lr

    .p2align        2
.fail_str:
    .string "TEST FAILED\n"

    .p2align        2
.success_str:
    .string "test succeeded\n"

