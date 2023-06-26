External bus timing
===================

DRAM access timing
------------------

The bus support DDR accesses to DRAM. The first half of a clock-cycle, lower byte, the second half of the clock cycle the upper byte is accessed. Long bursts within a 512-byte page are supported by keeping `n_ras_a/b` low while toggling `n_cas_0/1`. At either end of the burst, some overhead (one cycle each) needs to be paid to return the bus to it's idle state and allow for the DRAM chip to meet pre-charge timing.

A 4-beat (8-byte burst) on the bus would have the following timing:

::
                        <------- 4-beat burst ------------->
    clk             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^
    n_ras_a/b       ^^^^^^^^^\_____________________________/^
    n_nram          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_cas_0         ^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^
    n_cas_1         ^^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^
    a[10:0]         ---------<==X=====X=====X=====X=====>----
    n_we            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    d[7:0] (read)   --------------<>-<>-<>-<>-<>-<>-<>-<>----
    n_we            ^^^^^^^^^\_____________________________/^
    d[7:0] (write)  ------------<==X==X==X==X==X==X==X==>----

Two back-to-back 16-bit accesses look like the following:

::
                       <---- single ----><---- single ---->
    clk             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^
    n_ras_a/b       ^^^^^^^^^\___________/^^^^^\___________/^
    n_nram          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_cas_0         ^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^^^^^^
    n_cas_1         ^^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^^^
    a[10:0]         ---------<==X=====>--------<==X=====>----
    n_we            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    d[7:0] (read)   --------------<>-<>--------------<>-<>---
    n_we            ^^^^^^^^^\___________/^^^^^\___________/^
    d[7:0] (write)  ------------<==X==>-----------<==X==>----

A memory refresh cycle (RAS-only refresh) has the following waveforms:

::
                        <- refresh->
    clk             \__/^^\__/^^\__/^
    n_ras_a/b       ^^^^^^^^^\_____/^
    n_nram          ^^^^^^^^^^^^^^^^^
    n_cas_0         ^^^^^^^^^^^^^^^^^
    n_cas_1         ^^^^^^^^^^^^^^^^^
    a[10:0]         ---------<==>----
    n_we            ^^^^^^^^^^^^^^^^^
    d[7:0] (read)   -----------------
    n_we            ^^^^^^^^^^^^^^^^^
    d[7:0] (write)  -----------------

.. note:: Refresh cycles assert both n_ras_a and n_ras_b at the same time. Other cycles assert either of the two, but not both.

.. note:: These timing diagrams aren't really compatible with fast-page-mode memories. The more precise way of saying this is that these timings don't allow us to take advantage of FPM access cycles. We would need to delay both `n_cas_0/1` signals by half a clock-cycle to make FPM work. That would probably result in an extra clock cycle of latency on reads. It would however allow us to double the clock speed.

Non-DRAM access timing
----------------------

For non-DRAM accesses, the waveforms are different in several ways:

1. No bursts are supported
2. Select signals are slowed down
3. External and internal wait-states can be inserted

::
                             <---- access ----><---- internal wait ---><---- external wait --->
    clk             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/
    n_ras_a/b       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_nram          ^^^^^^^^^\___________/^^^^^\_________________/^^^^^\_________________/^^^^^^
    n_cas_0         ^^^^^^^^^^^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_cas_1         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^^^^^^^\___________/^^^^^^
    a[10:0]         ---------<==X========>-----<==X==============>-----<==X==============>------
    n_we            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    d[7:0] (read)   ---------------------<>----------------- ----<>----------------------<>-----
    n_we            ^^^^^^^^^\___________/^^^^^\_________________/^^^^^\_________________/^^^^^^
    d[7:0] (write)  ------------<========>-----------<===========>--------<==============>------
    n_wait          ---------------/^^^^^\-----------/^^^^^^^^^^^\-----------\_____/^^^^^\------

.. note:: These timings don't really support external devices with non-0 data hold-time requirements. Maybe we can delay turning off data-bus drivers by half a cycle?

DMA access timing
-----------------

DMA accesses follow the timing of non-DRAM accesses, but select DRAM instead of non-DRAM devices as their targets:

::
                             <--- even read ---><- odd read with wait ->
    clk             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/
    n_ras_a/b       ^^^^^^^^^\___________/^^^^^\_________________/^^^^^^
    n_nram          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_cas_0         ^^^^^^^^^^^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    n_cas_1         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^^
    a[10:0]         ---------<==X========>-----<==X==============>------
    n_we            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    d[7:0] (read)   ---------------------<>----------------------<>-----
    n_we            ^^^^^^^^^\___________/^^^^^\_________________/^^^^^^
    d[7:0] (write)  ------------<========>--------<==============>------
    n_wait          ---------------/^^^^^\-----------\_____/^^^^^\------
    n_dack_X        ^^^^^^^^^\___________/^^^^^\_________________/^^^^^^
    tc              ---------<===========>-----<=================>------

DMA operations only support 8-bit accesses.
