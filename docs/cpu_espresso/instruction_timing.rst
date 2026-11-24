Instruction timing
==================

This chapter lists how many clock cycles instructions take on Espresso. The numbers come from the RTL (:code:`rtl/espresso/*.py`): they were read from the code and then measured by running short instruction sequences on the full core (:code:`BrewV1Top`) in the test rig of :code:`rtl/espresso/test/rig.py`, assembled with the Brew toolchain, with code and data in DRAM.

The numbers assume:

* code and data in DRAM with no wait states: after the initial latency, memory supplies 16 bits every clock cycle (the :code:`page-mode` bursts described in :doc:`external_bus_timing`);
* no DMA activity. DRAM refresh (every 128 cycles by default, 2 bus cycles each) is ignored;
* the default configuration with a multiplier and a shifter.

A cycle count of an instruction is measured from the cycle it enters the first cycle of the execute stage. "Latency" is the distance between a producer and a dependent instruction entering execute; an instruction that depends on nothing would enter execute one cycle after its predecessor.

Summary
-------

Instruction fetch, not execution, sets the pace of straight-line code, and every taken branch costs 9 cycles. Memory accesses share the 16-bit bus with fetch and stall the pipeline until they complete. For a compiler, that means: code size is speed, taken branches and calls are expensive, and results should not be used by the very next instruction.

Bus interface
-------------

================================================= ================== =================================================================
Item                                              Cycles             Notes
================================================= ================== =================================================================
Request accepted to read data returned            3                  Data comes back through two registers after the DRAM beat.
Burst of *n* 16-bit beats (bus occupancy)         *n* + 2            One beat per cycle, then a pre-charge and an idle (arbitration) cycle.
Single 16-bit access (bus occupancy)              3
32-bit access                                     4                  A 2-beat burst.
8-bit access                                      3                  A 16-bit beat with one byte enabled.
Arbitration                                       --                 Only in the idle state, fixed priority: refresh, DMA, memory, fetch. A burst is never interrupted, so a load or store waits for a running fetch burst (up to 12 cycles).
Non-DRAM access                                   4 + wait states    8-bit transfers only; a 16-bit access is two transfers, a 32-bit access four (15 cycles for a 32-bit load with one wait state). Wait states come from address bits 31..28 (see :doc:`memory`).
================================================= ================== =================================================================

Instruction fetch
-----------------

================================================= ================== =================================================================
Item                                              Cycles             Notes
================================================= ================== =================================================================
Fetch burst                                       up to 10 beats     A new burst starts when more than 8 entries of the 11-entry instruction queue are free, counting requests still outstanding; it is cut short when decode passes a load or store on to execute, so that the access doesn't wait behind it.
Sustained fetch rate                              12 per 10 words    10 instruction words per 12 cycles (bursts of 10 beats plus 2 turn-around cycles), about 1.2 cycles per 16-bit word.
16-bit instruction (fetch-bound)                  1.2                Independent 16-bit instructions execute at one per cycle until the queue drains, then wait 2-3 cycles every 10 instructions.
32-bit instruction (fetch-bound)                  2.4
48-bit instruction (fetch-bound)                  3.6
================================================= ================== =================================================================

Execution
---------

Espresso issues one instruction per cycle, in order. A register written by an instruction is reserved in the register file until its write-back; any instruction reading *or writing* a reserved register waits. Write-after-write therefore stalls exactly like a true dependency.

================================================= ================== =================================================================
Instruction                                       Cycles             Notes
================================================= ================== =================================================================
ALU (add, subtract, logic, move, immediate)       1, latency 3       A dependent instruction right after it waits 2 cycles; with one instruction in between, 1 cycle; with two, none.
Shift                                             1, latency 3       Same as ALU.
Multiply                                          2, latency 3       The multiplier blocks the next instruction for one cycle (one multiply every 2 cycles, even if independent).
Output dependency (same destination register)     latency 3          :code:`$r3 <- ...` followed by :code:`$r3 <- ...` waits 2 cycles.
ALU result used as a load/store address           latency 3          Same as any other operand.
Conditional branch operand from an ALU result     latency 3
================================================= ================== =================================================================

Loads and stores
----------------

Loads stall the pipeline: the instruction after a load enters execute, but everything after that waits until the load's data is back. The table assumes the bus is free when the load or store reaches the memory unit; otherwise add the wait for the running fetch burst.

================================================= ================== =================================================================
Instruction                                       Cycles             Notes
================================================= ================== =================================================================
32-bit load                                       5, latency 6       Bus request in the cycle after the load enters execute, data 3 and 4 cycles later.
16-bit or 8-bit load                              4, latency 5
Back-to-back 32-bit loads                         4 each             Bus-bound; they also starve instruction fetch, which then costs a 12-14 cycle refill.
Back-to-back 16-bit or 8-bit loads                3 each
Loaded value stored by the next instruction       latency 8-9
32-bit store                                      2                  Posted: the memory unit only waits until the bus accepts both beats.
16-bit or 8-bit store                             1
Back-to-back 32-bit stores                        4 each             Bus-bound.
Back-to-back 16-bit or 8-bit stores               3 each
================================================= ================== =================================================================

Branches
--------

Espresso predicts every branch not taken. A branch is decided in the second cycle of the execute stage; the :code:`do_branch` signal is registered, the fetch burst in flight is ended, and fetch restarts at the target.

================================================= ================== =================================================================
Instruction                                       Cycles             Notes
================================================= ================== =================================================================
Taken branch (conditional or unconditional)       10                 The target enters execute 10 cycles after the branch (a 9-cycle penalty): 2 cycles to resolve, 1 for :code:`do_branch`, 2 bus turn-around cycles, 3 cycles memory latency, 2 cycles through the instruction queue and decode. Short loops and in-page targets cost the same as distant ones.
Not-taken conditional branch                      fetch only         2.4 cycles for the 32-bit forms; no penalty.
Call (:code:`$lr <- $pc + N; $pc <- target`)      10                 Same as a taken branch.
Return (:code:`$pc <- $lr`) and indirect jumps    10                 A call/return pair adds about 20 cycles.
================================================= ================== =================================================================

Differences from the micro-architecture description
---------------------------------------------------

The measurements disagree with :doc:`uarch` in two places:

* The multiplier is not fully pipelined at the issue level: the execute stage locks out the instruction after a multiply for one cycle.
* Branches to a target in the same 512-byte page do not continue the running fetch burst in practice: a taken branch empties the instruction queue and drops the responses still outstanding, so fetch restarts at the target either way. (The fetch unit could also end a burst at a fetched word that could be a branch, but that option, :code:`break_on_branch_early`, is off; bursts end at loads and stores instead.)
