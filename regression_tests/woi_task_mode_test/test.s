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


sched_mode_setup:
    ########### Set up interrupt timer
    $r0 <- 10000
    $r1 <- 1
    csr[csr_timer_limit] <- $r0
    csr[csr_timer_ctrl] <- $r1
    $pc <- $lr


test:
    $a2 <- $lr
    $a0 <- .fail_str
    # Testing ecause
    $a1 <- mem[.ecause_save]
    $a1 <- $a1 - 0x10
    if $a1 != 0 $pc <- _fail
    # Testing interrupt status register
    $a0 <- csr[csr_timer_status]
    $a1 <- tiny 1
    if $a0 != $a1 $pc <- _fail
    csr[csr_timer_status] <- $a0
    $a0 <- csr[csr_timer_status]
    $a1 <- tiny 0
    if $a0 != $a1 $pc <- _fail

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

