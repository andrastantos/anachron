.macro CALL label
    $lr <- 1f
    $pc <- \label
1:
.endm

.global test

.text
.p2align        1


test:
    $a2 <- $lr
    $a0 <- .fail_str
    # Testing $tpc
    $a1 <- $tpc
    $a1 <- $a1 - 0x080000b6
    if $a1 != 0 $pc <- _fail
    # Testing ecause
    $a1 <- mem[.ecause_save]
    $a1 <- $a1 - 0x10
    if $a1 != 0 $pc <- _fail
    # Testing $a0
    $a1 <- mem32[.a0_save]
    $a1 <- $a1 - 2
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

