# The thread context structure contains all the state info
# we need to be able to context switch between threads

.struct 0
    tcontext.next:        .space 4 # Allows for linked-lists (or rings) for scheduling
    tcontext.process:     .space 4 # Pointer to process descriptor
    tcontext.r0_save:     .space 4
    tcontext.r1_save:     .space 4
    tcontext.r2_save:     .space 4
    tcontext.r3_save:     .space 4
    tcontext.a0_save:
    tcontext.r4_save:     .space 4
    tcontext.a1_save:
    tcontext.r5_save:     .space 4
    tcontext.a2_save:
    tcontext.r6_save:     .space 4
    tcontext.a3_save:
    tcontext.r7_save:     .space 4
    tcontext.r8_save:     .space 4
    tcontext.r9_save:     .space 4
    tcontext.r10_save:    .space 4
    tcontext.r11_save:    .space 4
    tcontext.fp_save:
    tcontext.r12_save:    .space 4
    tcontext.sp_save:
    tcontext.r13_save:    .space 4
    tcontext.lr_save:
    tcontext.r14_save:    .space 4
    tcontext.tpc_save:    .space 4
    tcontext.ecause_save: .space 4
