Micro-architecture of Espresso
==============================

Implementation in a nutshell
----------------------------

Espresso is a rather bare-bones pipelined RISC implementation. It has no caches, no MMU even. It stalls for loads and stores, does in-order issue and execution. It doesn't have a branch predictor, or to be more precise, it predicts all branches not taken. Something that might be a tiny bit out of the mold is that it has a pre-fetch stage (and the requisite instruction queue).

Another slightly unusual feature is that the 'execute' stage encompasses memory accesses, but has a two-cycle latency.

All in all, pretty basic.

Memory model
~~~~~~~~~~~~

Espresso has a rather simplified memory model:

Loads and stores are performed in-order and they stall the pipeline until completion (in case of writes, until all side-effects are reflected in the target).

The pipeline
------------

Espresso is using a simple 5-stage pipeline.

.. todo:: add block diagrams

Fetch
~~~~~

Fetch is comprised of three entities:

1. The :code:`InstBuffer` entity fetches instructions from memory and places them in the instruction queue
2. The 11x16-bit entry :code:`InstQueue` is a simple FIFO
3. The :code:`InstQueue` FIFO is emptied by the :code:`InstAssembly` stage, creating full length instructions to pass on to decode.

:code:`InstBuffer` initiates a new burst every time there is at least 8 free entries in :code:`InstQueue`.

The bursts can be terminated prematurely if the :code:`break_burst` signal is asserted or if a branch to a new address is requested (through the :code:`do_branch` signal).

Bursts are not aligned, except for the alignment requirement of BREWs instruction alignment: to 16-bit word boundaries.

Bursts are not allowed to cross 512-byte page boundaries. This is a (simplified) requirement of the bus controller, which doesn't allow bursts to cross DRAM page boundaries. Since the smallest supported page size is 512 bytes, the fetch unit, by using the smallest possible page size, adheres to this requirement.

Upon a branch, a burst is allowed to proceed if the target address is within the same page as the current burst, reducing branch latency for short in-page branches.

The instruction buffer is responsible for logical to physical address translation and checking for access violations. If the fetched data is outside of the allowed bounds, the :code:`fetch_av` flag is set and passed along with the data.

Since fetches are speculative (in that Espresso always speculates straight line execution), access violation exceptions are not raised in the fetch state. The :code:`fetch_av` flag is maintained all the way to the execute stage, where it is turned into an actual exception. If a branch earlier in the instruction stream diverts execution, the exception flag - along with it's instruction code - will be ignored.

The instruction queue :code:`InstQueue` is not much more than a simple FIFO buffer of eleven 16-bit entries. The depth of the FIFO is set such that a complete 8-beat burst can fit in there, while still holding enough entries for the bus interface latency.

The instruction queue is emptied by the instruction assembler unit, :code:`InstAssembly`. This unit decodes the instruction length and collects the required number of words (one to three words for Espresso) and presenting the complete instruction word to decode. Since instruction length is decoded in this stage, it is also passed along to the decode stage.

Instruction Decode
~~~~~~~~~~~~~~~~~~

Instruction decode deals with decoding the instruction fields and issuing read requests to the register file. It accepts responses from the register file, then muxes the register values and the immediate field (as needed) to the input ports of the execution stage.

The instruction decoder creates several control signals that determine how the execution stage will operate.

While register reservation is handled by the register file, the decode stage is responsible for requesting the appropriate reservations for result registers.

The decode stage has a single-cycle latency, but its outputs are not fully registered. This is a consequence of the register file also having a single cycle latency, which means that register values are returned by the register file as the output of the decode stage is produced. The final muxing of register values onto the input of the execution stage happens after the output registers.

Execution stage
~~~~~~~~~~~~~~~

The execution stage is broken into several execution units:

1. The *ALU* unit deals with integer arithmetic and logical operations. It has a latency of a single cycle
2. The *Shifter* unit deals with arithmetic and logical shift operations. It also has a single cycle latency
3. The *Multiplier* unit performs 32-bit multiplies (with 32-bit results) in two cycles. It is fully pipelined, capable of accepting a new operation in every cycle.
4. The *Load-store* unit is responsible for generating the physical address for loads and stores as well as checking for access violations and alignment problems. This is a single-cycle latency unit, occupying the first cycle of the execution stage
5. The *Memory* unit generates the right transactions for loads and stores towards the bus interface. This is a variable latency unit, starting execution in the second cycle of the execution stage.
6. The *Branch target* unit which computes the branch target address for branch instruction in the first cycle of the execution stage
7. The *Branch* unit, which performs the branches, (based on conditions generated by the ALU in case of conditional branches). It deals with interrupts and exceptions as well. It is placed in the second cycle of the execution stage.

The branch target unit is responsible for generating target addresses for both straight-line execution as well as branches.

The load-store unit computes the physical address for memory operations but also checks for access violations and alignment issues.

All exceptions, including fetch AV-s, memory AVs and all manners of software and hardware interrupts are raised in the second cycle of the execution stage. The excepting instruction is cancelled (including loads and stores) and their results are not written back into the register file. Interrupts are treated similarly to exceptions: the currently executing instruction is cancelled and switch to SCHEDULER mode is initiated. If an exception occurs while in SCHEDULER mode, a branch to address 0 is initiated (and the current instruction is cancelled). If an interrupt occurs in SCHEDULER mode, it is simply ignored.

In case of branches (either due to branch instructions, exceptions or interrupts), the instruction in the first cycle of the execute stage is also cancelled. At the same time the :code:`do_branch` output is asserted. This signal gets registered before being distributed to other stages, helping with timing closure, but resulting in an extra instruction potentially delivered to the execute stage before the flush of the pipeline takes effect. In this case, the extra instruction is flushed from the first stage of execute.

The memory unit handles interfacing to CSR registers: it understands enough of the address map to peel off CSR accesses and send them on the CSR APB interface instead of the bus interface. Since the bus interface is 16-bit wide, the memory unit deals with breaking up 32-bit loads and stores into multiple cycles. The memory unit stalls until read responses come back from the bus interface. While stores are posted in the sense that the pipeline is not stalled for completion of the store, they are not accepted by the bus interface until they are ready to be presented on the external bus. The memory unit stalls until the request is accepted.

Sign-extent stage
~~~~~~~~~~~~~~~~~

This small stage between the execution stage and the write-back port to the register file is responsible for sign- and zero-extension of results as needed. This stage is purely combinational with zero-cycle latency.

Register file
~~~~~~~~~~~~~

The register file handles two reads and a single write in every clock cycle. Due to the design decision to implement the register entries in FPGA block-RAM resources, the read latency is 1 clock cycle.

The register file handles reservations, providing the decode stage with the proper hand-shake signals. It is also responsible for result forwarding. The forwarding paths adhere to the same single-cycle latency that normal register reads suffer.

Bus interface
~~~~~~~~~~~~~

The bus interface handles all interfacing needs towards the external bus. It is optimized for page-mode busts towards DRAM memories. It generates the proper timing of signals for page-mode (not fast-page-mode) DRAMs, non-DRAM devices, handles wait-state generation - both internal and external - and minimal address decoding to distinguish between DRAM and non-DRAM memory regions.

The bus interface accepts requests from the following sources (in decreasing priority):

1. Internal DRAM refresh generator
2. DMA engine
3. CPU memory port
4. CPU fetch port

The internal refresh generator - if enabled - periodically generates RAS-only refresh cycles needed by DRAM.

The integrated DMA engine of Espresso can generate transactions using the bus interface. These transactions are 8-bit wide and are serviced using non-DRAM timings, even if the target address is in the DRAM region. During DMA transactions, the data bus is floated: for DMA transfers the expectation is that the externally addressed DMA master will provide or accept the data from the transfer.

The DMA engine can also request the bus interface to completely relinquish control of the bus (for external bus-masters). In these cases the bus interface tri-states all of its outputs and monitors the end of the bus-master activity mediated by the :code:`valid` signal on the DMA request interface.

Bursts are not supported on the DMA engine interface.

The two ports from the CPU core can generate instruction fetch and memory read/write requests respectively. These ports support burst transactions.

An internal state-machine keeps track of the various cycles involved in generating the right signal transitions for the many different requestors and bus transfer types.

This state-machine always returns to the 'idle' state between requests. Fixed priority requestor arbitration happens in the 'idle' state.

The bus interface uses both clock edges to generate the proper transitions on the bus. Because of this, the clock input to Espresso must have 50% duty-cycle.

To ensure glitch-free drive of the control signals (mostly n_cas_0/1), control signals are registered on the appropriate clock edge and minimal post-flop muxing is utilized. Further logic tricks are used to ensure no more than one signal changes on any particular clock-edge on these output logic signals ensuring that LUT outputs will not glitch during transitions.

The bus interface needs some basic understanding of the attached memory devices. This is achieved through a single CSR:

Bus interface CSR
.................

================ =================================== ============ =========== ============================================
Offset           Name                                Access       Reset value Description
================ =================================== ============ =========== ============================================
0x400_0800       :code:`bus_if_cfg_reg`              R/W          0x0000_0080 Bus interface configuration register
================ =================================== ============ =========== ============================================

Various bit-fields in this register control the aspects of the operation of the bus interface:

======== ================================ =========== =======================================
Bits     Name                             Reset value Description
======== ================================ =========== =======================================
0..7     refresh_counter                  0x80        The divider counter to control the DRAM refresh period.
8        refresh_disable                  0           Write '1' to disable DRAM refresh operation
9..10    dram_bank_size                   0           Select DRAM bank size; 0: 128k, 1: 512k, 2: 2M, 3: 8M
11       dram_bank_swap                   0           Write '1' to swap DRAM banks in the memory map
======== ================================ =========== =======================================

Memory refresh
..............

Espresso contains integrated memory refresh logic. This consists of a timing controller and an address counter. The refresh timing controller has a programmable 8-bit divider, that is used to generate refresh requests. Every time a refresh is requested, the refresh address is incremented, until it wraps around at 2047.

The refresh counter defaults to a value of 0x80, resulting in a refresh request every 128 clock cycles. At a clock frequency of 8.3MHz or higher, this default setting provides proper refresh for most DRAM devices. If a different clock rate is used, or if the DRAM used requires special timing, the refresh rate needs to be re-programmed.

.. note::

  The default setting is sufficient to maintain 2ms/128 address, 4ms/256 address, 8ms/512 address, 16ms/1024 address or 32ms/2048 address refresh requirements. This satisfies most DRAM devices on the market, but consult DRAM datasheet to ensure proper operation.

Memory access patterns
......................

Espresso supports 8-beat bursts for instruction fetches, and 2-beat bursts for memory accesses. Each beat transfers 16-bits of data. Each burst is preceded and followed by a clock-cycle of extra activity (to satisfy DRAM timing requirements). This means that a 16-byte instruction fetch burst takes 10 clock cycles, while a 32-bit load or store takes 4 clock cycles on the bus.

.. admonition:: Why?

    Loads and stores can only use up to 4-beat bursts; Espresso can't deal with more than 32-bits of data at a time. Instruction fetch bursts can be much longer as long as we can put the fetched data in some temporary buffer, but there's a limit: every time the code branches, we have to throw away all the prefetched instruction words and start over from the new location. There is a balance between the amount of data we are willing to throw away and the benefits of a long burst. Profiling shows that the optimum point is 8 word (16-byte) long bursts.



IPC expectations
----------------

We should expect about 25% of our operations to be memory accesses, stalling for 3 cycles. Branches, which happen about 12.5% of the time would have a penalty of ~5 clock cycles. Other hazards will add about one stall every 8 instructions. On top of this, our instruction length on average is 24 bits, so we should expect 0.5 cycles of stall just from instruction assembly. An extra 2/10th of stall comes from the burst overhead of the DRAM access patterns for fetches. This gives us 2.2 stall cycles for every instruction executed, or an expected IPC of 0.31.

Memory bandwidth implications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A video of 320x240 resolution, 8 bits per pixel and 50Hz update rate (this is PAL video) would need 3.84MByte/sec of data on average. Higher during active lines, but nothing during blanking and sync periods. With the 10-cycles-for-16-bytes burst rate, we would need 2.4M memory cycles every second to refresh the screen. However, we should probably add about 4 cycles of memory arbitration lost between the CPU and the video controller for every burst, resulting in 3.36M cycles for display activity. At a 10MHz clock rate, this leaves us with 6.64M cycles for CPU access.

An IPC of 0.31 at 10MHz means that the processor would need to fetch 3.1M instructions (at 24 bits each) every second, resulting in 9.3MByte/sec fetch requirements. That amount of data needs 5.81M cycles to transfer after considering the burst overhead.

Out of the 3.1M instructions, 0.775M would either a load or a store, each requiring 4 cycles on the bus to complete. This is an extra 3.1M cycles.

Adding it up: 3.36M for video, 5.81M for fetch and 3.1M for load/store = 12.27M cycles. But we're running at 10MHz, we only have 10M cycles to work with in every second.

The result is that the processor will get throttled by video: we won't be able to achieve even our 0.31 IPC once we turn on video. The real number should be around 0.23 instead.
