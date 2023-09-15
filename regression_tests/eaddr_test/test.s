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
    $a1 <- mem[.eaddr_save]
    $a1 <- $a1 - 0x01230006
    $a0 <- .fail_str
    if $a1 != 0 $pc <- _fail
    $a0 <- .success_str
_fail:
    CALL uart_write_str
    $a0 <- $a1
    CALL uart_write_hex
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

