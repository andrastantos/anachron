Micro-architecture of Espresso
==============================

Implementation in a nutshell
----------------------------

There will be a lot of details coming, but just to set the stage...

Espresso is a rather bare-bones pipelined RISC implementation. It has no caches, no MMU even. It stalls for loads and stores, does completely in-order issue and execution. It doesn't have a branch predictor, or to be more precise, it predicts all branches not taken. Something that might be a tiny bit out of the mold is that it has a pre-fetch stage (and the requisite instruction queue).

Another slightly unusual feature is that the 'execute' stage encompasses memory accesses, but has a two-cycle latency.

All in all, pretty basic.

Memory access patterns
-----------------------------

Espresso supports 8-beat bursts for instruction fetches, and 2-beat bursts for memory accesses. Each beat transfers 16-bits of data. Each burst is preceded and followed by a clock-cycle of extra activity. This means that a 16-byte instruction fetch burst takes 10 clock cycles, while a 32-bit load or store takes 4 clock cycles on the bus.

IPC expectations
----------------

We should expect about 25% of our operations to be memory accesses, stalling for 3 cycles. Branches, which happen about 12.5% of the time would have a penalty of ~5 clock cycles. Other hazards will add about one stall every 8 instructions. On top of this, our instruction length on average is 24 bits, so we should expect 0.5 cycles of stall just from instruction assembly. An extra 2/10th of stall comes from the burst overhead of the DRAM access patterns for fetches. This gives us 2.2 stall cycles for every instruction executed, or an expected IPC of 0.31.

Memory bandwidth calculations
-----------------------------

A video of 320x240 resolution, 8 bits per pixel and 50Hz update rate (this is PAL video) would need 3.84MByte/sec of data on average. Higher during active lines, but nothing during blanking and sync periods. With the 10-cycles-for-16-bytes burst rate, we would need 2.4M memory cycles every second to refresh the screen. However, we should probably add about 4 cycles of memory arbitration lost between the CPU and the video controller for every burst, resulting in 3.36M cycles lost. At a 10MHz clock rate, this leaves us with 6.64M cycles for CPU access.

An IPC of 0.31 at 10MHz means that the processor would need to fetch 3.1M instructions (at 24 bits each) every second, resulting in 9.3MByte/sec fetch requirements. That amount of data needs 5.81M cycles to transfer after considering the burst overhead.

Out of the 3.1M instructions, 0.775M would either a load or a store, each requiring 4 cycles on the bus to complete. This is an extra 3.1M cycles.

Adding it up: 3.36M for video, 5.81M for fetch and 3.1M for load/store = 12.27M cycles. But we're running at 10MHz, we only have 10M cycles to work with in every second.

The result is that the processor will get throttled by video: we won't be able to achieve even our 0.31 IPC once we turn on video. The real number should be around 0.23 instead.

Notice how the trouble of memory bandwidth is most punishing for instruction fetches: they consume inordinate amount of bandwidth. This is why the first order of business in the <<TODO: ADD LINK!!!>> road-map is to add even a teeny-tiny ICache. I checked: sadly, we can't have it in 1.5um; there's just not enough silicon area.

The pipeline
------------

Due to memory bandwidth constraints, aiming for more than a 0.31 IPC is a fools errand. Thus, the pipeline is very very simple, more geared towards being small then efficient. Of course it's also a requirement of the target process: we just don't have all that many transistors to use.

Espresso is using a simple 5-stage pipeline.

Fetch
~~~~~

Fetch is created of three entities:

1. The `InstBuffer` entity fetches instructions from memory and places them in the instruction queue
2. The 11x16-bit entry `InstQueue` is a simple FIFO
3. The `InstQueue` FIFO is emptied by the `InstAssembly` stage, creating full length instructions to pass on to decode.

`InstBuffer` initiates a new burst every time there is at least 8 free entries in `InstQueue`. New bursts are generated whenever there are at least 8 empty entries in the instruction queue.

The bursts can be terminated prematurely if the `break_burst` signal is asserted or if a branch to a new address is requested (through the `do_branch` signal).

Bursts are not aligned, except for the alignment requirement of BREWs instruction alignment: to 16-bit word boundaries.

Bursts are not allowed to cross 256-word page boundaries. This is a (simplified) requirement of the bus controller, which doesn't allow bursts to cross DRAM page boundaries. Since the smallest supported page size is 256 words, the fetch unit, by using the smallest possible page size, adheres to this requirement.

Upon a branch, a burst is allowed to proceed if the target address is in the same page as the current burst, reducing branch latency for short in-page branches.

The instruction buffer is responsible for logical to physical address translation and checking for access violations. If the fetched data is outside of the allowed bounds, the `fetch_av` flag is set and passed along with the data.

Since fetches are speculative (in that Espresso always speculates straight line execution), access violation exceptions are not raised in the fetch state. The `fetch_av` flag is passed along all the way to the execute stage, where it is turned into an actual exception. If a branch earlier in the instruction stream diverts execution from the instruction with the `fetch_av` flag set, it will never reach the execution stage, and its exception flag will be ignored.

The instruction queue `InstQueue` is not much more than a simple FIFO buffer of 11 16-bit entries. The depth of the FIFO is set such that a complete 8-beat burst can fit in there, while still holding enough entries for the bus interface latency.

The instruction queue is emptied by the instruction assembler unit. This unit decodes the instruction length and collects the required number of words (1, 2 or 3 word long instructions are supported by Espresso) and presenting the complete instruction word to decode. Since instruction length is decoded in this stage, it is also passed along to the decode stage.

Instruction Decode
~~~~~~~~~~~~~~~~~~

Instruction decode deals with decoding the instruction fields and issuing read requests to the register file. It also accepts responses from the register file, then muxes the register values and the immediate field (as needed) to the input ports of the execution stage.

It also creates several control signals that determine how the execution stage will operate.

While register reservation is handled by the register file, the decode stage is responsible for requesting the appropriate reservations for result registers.


Execution stage
~~~~~~~~~~~~~~~

The execution stage is broken into several execution units:

1. The ALU unit deals with integer arithmetic and logical operations. It has a latency of a single cycle
2. The Shifter unit deals with arithmetic and logical shift operations. It also has a single cycle latency
3. The multiplier unit performs 32-bit multiplies (with 32-bit results) in two cycles. It is fully pipelined, capable of accepting a new operation in every cycle.
4. The load-store unit is responsible for generating the effective address for loads and stores. This is a single-cycle latency unit, occupying the first cycle of the execution stage
5. The memory unit generates the right transactions for loads and stores towards the bus interface. This is a variable latency unit, starting execution in the second cycle of the execution stage.
6. The branch target unit which computes the branch target address for branch instruction in the first cycle of the execution stage
7. The branch unit, which performs the branches, (based on conditions generated by the ALU in case of conditional branches). It is placed in the second cycle of the execution stage.

The branch target unit is responsible for generating target addresses for both straight-line execution as well as branches.

The load-store unit computes the effective address for memory operations but also checks for access violations. All exceptions, including fetch AV-s, memory AVs and all manners of software interrupts are raised in the second cycle of the execution stage.

The excepting instruction is cancelled (including loads and stores) and their results are not written back into the register file.

Interrupts are treated similarly to exceptions: the currently executing instruction is cancelled and switch to SCHEDULER mode is initiated. Of course.

In case of branches (either due to branch instructions, exceptions or interrupts), the instruction in the first cycle of the execute stage is also cancelled. At the same time the `do_branch` output is asserted. This signal gets registered before being distributed to other stages, helping with timing closure, but resulting in an extra instruction potentially delivered to the execute stage before the flush of the pipeline takes effect. In this case, the extra instruction is flushed from execute.

The memory unit handles interfacing to CSR registers: it understands enough of the address map to peel off CSR accesses and send them on the CSR APB interface instead of the bus interface interface (I know, stupid name).

The memory unit is also responsible for breaking up 32-bit accesses into 2-beat bursts of 16-bit requests each.

Sign-extent stage
~~~~~~~~~~~~~~~~~

A small stage between the execution stage and the write-back port to the register file is responsible for sign- and zero-extension of results as needed. This stage is purely combinational with zero-cycle latency

Register file
~~~~~~~~~~~~~

The register file handles two reads and a single write in every clock cycle. Due to the design decision to implement the register entries in FPGA block-RAM resources, the read latency is 1 clock cycles.

The register file handles reservations, providing the decode stage with the proper hand-shake signals. It is also responsible for result forwarding. The forwarding paths adhere to the same single-cycle latency that normal register reads suffer.

Bus interface
~~~~~~~~~~~~~

The bus interface handles all interfacing needs towards the external bus. It's optimized for page-mode busts towards DRAM memories. It generates the proper timing of signals for page-mode (not fast-page-mode) DRAMs, non-DRAM devices, handles wait-state generation - both internal and external - and minimal address decoding to distinguish between DRAM and non-DRAM memory regions.

The bus interface accepts requests from the following sources (in decreasing priority):

1. Internal DRAM refresh generator
2. DMA engine
3. CPU memory port
4. CPU fetch port

The internal refresh generator - if enabled - periodically generates RAS-only refresh cycles to keep the DRAM content up to date. The row-counter for the refresh engine is 11 bits long to match with the width of the address bus. The refresh rate divider is programmable.

An external DMA engine can generate transactions using the bus interface. These transactions can be 8- or 16-bit wide and are always serviced with non-DRAM timings, even if the target address is in the DRAM region. During DMA transactions, the data bus is floated: for DMA transfers the expectation is that the externally addressed DMA master will provide or accept the data from the transfer.

The DMA engine can also request to completely relinquish control of the bus (for external bus-masters). In these cases the bus interface tri-states all of its outputs and monitors the end of the bus-master activity mediated by the `valid` signal on the DMA request interface. (In other words DMA request and acknowledge signals are used to communicate external bus-request and response handshakes, though those details are part of the DMA engine and not the bus interface).

Bursts are not supported on the DMA engine interface.

The two ports from the CPU core can generate instruction fetch and memory read/write requests. These ports do support burst transactions.

An internal state-machine keeps track of the various cycles involved with generating the right signal-transitions for the many different requestors and bus-transfer-types.

This state-machine always returns to the 'idle' state between requests. Fixed priority requestor arbitration happens in the idle state.

The bus interface uses both clock edges to generate the proper transitions on the bus. Because of this, the clock input to Espresso must have 50% duty-cycle.

To ensure glitch-free drive of the control signals (mostly n_cas_0/1), control signals are registered on the appropriate clock edge and minimal post-flop muxing is utilized. Further logic tricks are used to ensure no more than one signal changes on any particular clock-edge on these output logic signals: this ensures that LUT outputs will not glitch during transitions.

Event counters
---------------


CSRs
----



Memory protection
-----------------

























Micro-architecture V4
=====================

The implementation is going to follow a relatively simple pipeline implementation with the following stages:

- FETCH unit with BRANCH PREDICTION
- DECODE
- EXECUTE (target computation for memory/branch)
- MEMORY (bypassed if not used)
- WRITE-BACK

The following units around the main pipeline support the efficient execution of the instruction stream:

- ICACHE
- DCACHE
- MMU

Front-end
---------

The goal of the front-end is to keep the decode logic fed with (potentially speculative) instructions.

The front-end *doesn't* think in terms of a program counter. It thinks in terms of a FETCH COUNTER, or FC and INSTRUCTION ADDRESS or IA.

The front-end is de-coupled from the back-end of the processor through a queue. This queue contains the following info:

1. up to 64-bit instruction code.
2. Instruction length
3. 31-bit IA of the *next* instruction
4. TASK/SCHEDULER bit

.. note:: If a branch mis-predict is detected, *all* instructions in the pipeline, *including* the queue between the FE and the decoder needs to be cleared.

.. note::
  the problem is the following: if a branch is predicted taken, we'll need to also check that it was predicted to jump to the right address. That's only possible if we've passed the predicted branch target address to the BE. If SWI is predicted, we might also want to pass the TASK/SCHEDULER bit too, though it could be gleaned form the fact that it is an SWI instruction inside the BE. Since the we pass IA along, the 'taken' bit can be inferred, and the comparator can't really be optimized out anyway, since we have to check that the IA actually matches PC.

.. todo::
  There's a good question here: should we pass the IA of the *current* instruction or the IA of the *next* instruction. Right now I'm of the opinion that next IA is better because it allows to detect a mis-predict one cycle earlier and clear the pipeline quicker.

The front-end deals with three caches:
1. Instruction cache read to get the instruction bit-stream.
2. TLB lookups
3. Brach-prediction

Instruction Cache
~~~~~~~~~~~~~~~~~

The instruction cache uses logical addresses to get the cache lines, but the tag contains physical addresses. That means that in order to test for a hit, we'll need to wait for the TLB results.

The ICache can provide 32-bits at a time. This is not the granularity of instructions, so the FE uses an FC pointer to get the next 32-bits from the ICache.

ICache invalidation
~~~~~~~~~~~~~~~~~~~

This is a tricky subject that needs to span the whole front-end of the processor: the ICache, the branch predictor and the instruction fetch. It even has implications on the FE-BE FIFO.

When the ICACHE gets flushed, the most likely reason for it is self-modifying code. That is, when someone put data in main memory and we want to execute it. In some cases (trampolines) we might be able to invalidate just a cache-line, but in more complex JIT scenarios we want to blow the whole cache away.

Whole cache invalidation is initiated through an I/O write. After the write, there must be a tight loop, checking for the invalidation to be completed. That is an I/O read, followed by a jump if invalidation is still in progress. Why? Because of the de-coupled FE behavior. Quite likely a number of instructions are already in the decode queue by the time the write finally reaches the cache controller and the invalidation starts. The act of invalidating will stall any further instruction fetches, but whatever is already in the FE pipeline will go through uninterrupted. So, the loop might execute a few times (if the branch-predictor was right) before the processor finally stalls. NOTE: in this design reads flush the write-queue so it's guaranteed that the first read will see the side-effect of the write. Since the read is not cached, it'll take quite a bit to wind its way through the interconnect to the cache-controller. It's possible that by the time the read reaches the controller, the invalidation has been completed.

Why can't this loop be done in HW? Why can't the cache-controller flush the FE-BE queue? It sure can. However the problem is that there are several instructions executed (or at least partially pushed into the pipeline) by the time the cache controller even realizes that there's an invalidation request.

Branch prediction
~~~~~~~~~~~~~~~~~

Potential branches are identified by the a rather complex :ref:`expression <branch_id_expression>`.

We will have a branch target buffer (BTB), containing:

#. 31-bit target address (16-bit aligned)
#. 1-bit TASK v. SCHEDULER
#. 1-bit match.

The BTB is addressed by the (low-order N-bits) of $pc.

.. todo::
  should we use logical or physical address for BTB address? Right now it's logical, though with the right sizing, it might not matter: If the BTB is the size of a page or smaller, the bits used to select the BTB entry are the same between the logical and the physical address.

.. todo:: should the target address be logical or physical? Right now it's logical.

The back-end, when executing a branch, it stores the target address and check it against the already stored value. If the values match, we set the match bit. If don't we clear it.

In the front-end, if a branch is encountered, we look up it's BTB entry. If the match bit is set, we predict the branch taken to the address in the BTB, otherwise we predict not taken.

This means that two consecutive branches to the same address will trigger prediction.

We can modify the default behavior for conditional branches with negative offsets, where match == 0: we would predict the branch taken to the address that's coded in the instruction stream.

The memory for the BTB needs two read ports *and* a write port:
- 1 read port to get the values in the predictor during fetch
- 1 read port to read the stored target address for branches during execute
- 1 write port to write back the target address and the match bit during execute

This would still give us 2 cycle update latency, but at least we could update on every cycle.

.. todo::
   If we think that back-to-back branches are rare, we could take the hit of a two-cycle update and cut the BRAM usage in half. I think I won't take this approach initially.

In case of a 2-cycle write latency (read-modify-write) and back-to-back branches that collide on the BTB entry, we will have to be a bit careful, though I think any implementation will be OK-ish. It's probably best if the read gets the old value, and the corresponding write will stomp on the one preceding it.

.. note::
  back-to-back branches should almost never collide on the BTB entry: adjacent branches should never hash to the same entry. We would need one jump that is taken, predicted taken, was possible to fetch in a single cycle, and hash to the same BTB entry. And even then, the worst case is that we mis-set the match bit.

2 BRAMs would give us 256 entries. The entries are direct-mapped, based on a hash of the PC and its type (that is the TASK/SCHEDULER bit). The simplest hash is the lower N bits of PC, which is probably good enough.

.. note:: BTB implementations are rather forgiving for errors; they are harmless in terms of accuracy, they only cause stalls.

.. note::
  since we're predicting if the target is in SCHEDULER or TASK mode, we'll have to make sure that we truly don't ever leak SCHEDULER context into TASK mode. On the plus side, we can correctly predict SWI instructions. STM will probably mis-predict, as we usually would not return to the same address in TASK mode, thus the match bit would never be set - as such, it's probably not worth even decoding it as a branch.

.. note::
  since target address is logical, it's important that we predict the TASK/SCHEDULER bit too. Otherwise the TLB lookup could be incorrect. The alternative is that we don't predict any of the SWI or STM instructions, but that slows down SYSCALLs quite a bit.

.. note::
  branch prediction will have to take instruction length into consideration and keep predicting the next address for a 48-bit instruction, even on a predicted taken branch.

.. note::
  branch prediction will also have to work around the mismatch between the 32-bit ingest port from ICACHE and the 16/48-bit instruction length. It also has to take into account the fact that the PC is incremented in 16-bit quantities.

.. todo::
  OOPS!!!! HOW DO WE DO LOOKUP for branches for the 32-bit aligned FC? We will have to be careful: if the first instruction is predicted taken, the second 16-bit suddenly becomes invalid.

  Branch prediction works on FA and not on PC. This means that it's 32-bit granular - can't differentiate between two 16-bit back-to-back branches (which I suspect is rare, but who knows?)

Instruction Fetch
-----------------

The ICache (and the TLB and the BP module) can provide up to 32-bits of instruction bytes. This could be broken up in many ways, depending on what the previous bytes were, since our instruction length varies between 16- and 64 bits. So, it's possible that the full 32 bits is part of the previous instruction. It's possible that one or the other 16-bit part is (the start of) an instruction. It's also possible that both are (potentially full) instructions.

We need to decode the instruction length and the branch-check in parallel on both halves and properly gate them with previous knowledge to generate the two result sets. For each half we have:

1. Instruction start bit
2. Instruction length (maybe co-encoded with 'start')
3. Branch bit
4. IA
5. Target address from prediction.

We also need the ability to push up to two instructions per clock cycle into the decode queue; that's because 48- 64-bit instructions take more than one cycle to fetch, so we want to be able to catch up: our average instruction size is less then 32-bits, but we can only take advantage of this fact if we can push up to two instructions into the queue.

The target address from the predictor applies to both halves. It almost never happens that both halves are actually branches (the only exception would be two consecutive SWIs), so that's fine.

.. important::
  If there are two instructions ready to be pushed into the queue and the first is a predicted-taken branch, the second instruction should not be pushed into the queue.

.. todo::
  There are two separate ideas mixed here: one where the predictor works on 32-bit quantized addresses and one that works on precise instruction addresses. I should make up my mind about that.

.. important::
  We can save a lot of headache if we simply didn't predict 16-bit branches, that is SWIs and STMs. Maybe we should do that...

.. important::
  if we have a branch to an odd 16-bit address, the FE will fetch the corresponding bottom 16-bits as well, which *should not* be put into the decode queue - indeed should not even be decoded as an instruction as it could be the tail-end of a longer one. This only happen on the first fetch after a taken branch, but could happen both due to predication or actual jump, even due to exceptions.

MMU
---

We would need a traditional two-level MMU, nothing really fancy. The page table address would need to be selected based on SCHEDULER v. TASK mode; unless of course we decided that there's no translation in SCHEDULER mode.

There are two kinds of pages: 4MB super pages and 4kb (regular) pages. All pages are naturally aligned, that is super pages are 4MB aligned while regular pages are 4kb aligned.

Page table entries are 32 bits long with only 24 bits used by the HW::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+
  |                                   P_PA_ADDR                                   | C |   MODE    |               .               |
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+

=====  ================= ================
MODE   MNEMONIC          EXPLANATION
=====  ================= ================
0      :code:`INV`       entry is not valid (or no access). Any access generates an exception
1      :code:`R`         entry is readable
2      :code:` W`        entry is writable
3      :code:`RW`        entry is readable and writeable
4      :code:`  X`       entry is executable
5      :code:`R X`       entry is read/executable
6      :code:`LINK`      entry is link to 2nd level page table, if appears in the 1st level page table
6      :code:` WX`       entry is writable and executable, if appears in the 2nd level page table
7      :code:`RWX`       entry has all access rights
=====  ================= ================

:code:`somehing`
.. note:: every MODE other than 6 (LINK) is considered a super page in the 1st level TLB table. This includes mode 0 (INV) as well.

The C bit is set to 1 for cacheable entries, set to 0 for non-cacheable ones.

P_PA_ADDR:
  top 20 bits of 4kB aligned physical address. Either for 2nd level page tables or for physical memory. For super-pages the bottom 10 bits of this field are ignored.

.. todo::
  Not that any MMU implementation I know of do this, but do we want sub-page access rights? That would allow us to do more granular access control that would create better page-heaps, where all allocations have HW-enforced bounds (ish). Think AppVerifier, but with less overhead. If we want to have - say - 256 byte sub-pages, that would mean 16 sets of mode bits, that is 48 bits total. Adding the 20 address and the cache-able bit, that adds up to 69. Too many! Maybe we can have a common 'execute' bit, but individual R and W bits. That would make for 20+1+1+32 = 54 bits. It would mean 64-bit page table entries, but a trivial encoding for the LINK pages by the use of yet another bit.

.. note::
  Most MMU implementations have D (dirty) and A (accessed) bits. These are redundant: one could start with a page being invalid. Any access would raise an exception, at which point, the OS can set the page to read-only. If a write is attempted, another exception is fired, at which point the page can be set with permissions. All the time, the exception handler can keep track of accessed and dirty pages. The D and A bits are only useful if the HW sets them automatically, but I don't intend to do that: that makes the MMU implementation super complicated.

.. note::
  Most MMU implementations have a 'G' (global) bit. With this MMU, we almost never globally invalidate the TLBs, so the global bit on a page is not really useful. In fact it's also rather dangerous as any mistake in setting the global bit on a page will potentially cause a TLB corruption and result in hard to find crashes and vulnerabilities.

The MMU can be programmed through the following (memory-mapped) registers:

SBASE/TBASE
~~~~~~~~~~~

The physical page where the 1st level page tables are found for SCHEDULER and TASK modes respectively

::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+
  |                                   ADDR                                        |                     .                         |
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+

They default to 0 upon reset. See notes about how to boot the system.

TLB_LA1
~~~~~~~

Logical address for 1st level TLB updates

::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+
  |                ADDR                   |                                     .                                                 |
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+

The bottom 22 bits are ignored on write and read 0.

TLB_LA2
~~~~~~~

Logical address for 2st level TLB updates

::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+
  |                                     ADDR                                      |                       .                       |
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+

The bottom 12 bits are ignored on write and read 0.


TLB_DATA1/TLB_DATA2:
~~~~~~~~~~~~~~~~~~~~

Associated TLB entry for the given logical address in TLB_LA1/TLB_LA2 respectively. The layout follows the page table entry format.

These are *write only* registers. Upon write, the value is entered to the TLB entry for the associated logical address stored
in TLB_LA1/TLB_LA2.

.. important::
  since the TLB is a cache of the page tables and since page table updates are not snooped by the MMU, the OS is required to either copy any page updates into the TLB or invalidate the TLB.

.. note::
  if the 1st level page entry is updated (such that it changes where the 2nd level page is pointed to) that operations potentially invalidates a whole lot of 2nd level TLB entries. It's impossible to know how many of those 2nd level entries were in deed cached in the TLB, and individually updating them (all 1024 of them) would certainly completely trash the TLB, the recommended action is that if a 1st level page entry is changed in such a way that the 2nd level page address is changed, the whole 2nd level TLB is invalidated. !!!!!!!!!!!!!!! I DONT THINK THIS IS TRUE ANYMORE !!!!!!!!!!!!!!!

TLB_INV:
~~~~~~~~

Write only register to invalidate the entire TLB.

EX_ADDR:
~~~~~~~~

Contains the LA of the last excepting operation

::

  +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  |                                                       ADDR                                                                    |
  +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

.. note:: this is not the :code:`$pc` for the excepting instruction. This is the address of the access that caused the exception.

EX_OP:
~~~~~~

Contains the operation attempted for the last excepting operation

::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+
  |                                                                                   | X | W | R |                               |
  +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

TLBs:
~~~~~

There are two TLBs. One for first-level entries and one for second-level ones. TLBs are direct-mapped caches, using LA[29:22]
for the 1st level and LA[19:12] for the 2nd level TLB as index.

Each TLB consists of 256 entries, containing 24 bits of data and a 24-bit tag.

The 32-bit tag contains:

::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#
  |                                 TLB_P_PA_ADDR                                 |LA_TAG |VERSION|
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#

*For the 1st level TLB:*

TLB_P_PA_ADDR:
  contains the page table address for the entry. In 1st the level TLB, this is either the contents of SBASE or TBASE based on the execution context.

LA_TAG:
  contains LA[31:30]

*For the 2st level TLB:*

TLB_P_PA_ADDR:
  contains the page table address for the 1st level table that this entry belongs to.

LA_TAG:
  contains LA[21:20]

The version number is used the same way as in the I and D cache tags to quickly invalidate the whole table.

The entry itself contains the top 24 bits of the the page table entry.

MMU operation
~~~~~~~~~~~~~

When a memory access is initiated, two operations are performed:
- Address translation
- Permission check

MMU operation starts by reading both the 1st and 2nd level TLBs, using the appropriate sections of the LA as index.

For the 1st level entry, the read-back LA_TAG is compared to LA[31:30] while TLB_P_PA_ADDR is compared the the active SBASE/TBASE register. The VERSION field is compared to the internally maintained TLB_VERSION register. If all fields match, we declare a 1st-level TLB hit, otherwise, we declare a 1st level TLB miss, and initiate a fill operation.

For the 2nd level entry, the read-back LA_TAG is compared to LA[21:20] while TLB_P_PA_ADDR is compared to the P_PA_ADDR field of the 1st level TLB entry (or the value that is used to fill the entry in case of a miss). The VERSION field is compared to the internally maintained TLB_VERSION register. If the 1st level TLB entry is a super page, we ignore any hit or miss test on the 2nd level TLB. Otherwise, if all fields match, we declare a 2st-level TLB hit or a 2st level TLB miss, and initiate a fill operation.

At the end of the process we have either an up-to-date 1st level TLB entry with a super page or up-to-date 1st and 2nd level TLB entries.

The TLB entry used for address translation and permission check is the data from the 1st level TLB entry in case of a super page or the 2nd level TLB entry otherwise. This entry is called the PAGE_DESC from now on.

The PAGE_DESC is used for both address translation and permission check.

Address translation takes the P_PA_ADDR and concatenates it with LA[11:0] to generate the full PA; in case of a super-page, P_PA_ADDR gets concatenated with LA[21:0].

Permission check AND-s the request operation mask (XWR bits) with the MODE bits in PAGE_DESC. The result is reduction-AND-ed together. If the result is '1', the operation is permitted, otherwise it is denied.

.. note:: in other words, all request operation bits must be set for the operation to be permitted. Normally, only one of the three bits will be set.

.. note:: PAGE_DESC can't contain LINK mode anymore: that is only a valid entry in the 1st level page table, and if that were the case, PAGE_DESC would be a copy of the 2nd level entry. mode 6 is always interpreted as WX and checked against that.

If the permission check fails, an MAV exception is raised.

Coordination with I/D caches
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Address translation is done in parallel with cache accesses. Caches are logically addressed but physically tagged, so if there is a hit in the cache, the associated P_PA_ADDR is also know. This P_PA_ADDR is compared with the result of the address translation (PAGE_DESC.P_PA_ADDR). In case of a miss-compare, the cache hit is overridden to a miss and a cache fill is initiated.

.. note:: A cache hit can occur with an incorrect P_PA_ADDR if there was an MMU page-table update, but no cache invalidation.

If the translation shows the address to be non-cacheable, the cache hit (if any) is overriden to a miss, but no cache fill is initiated.

In case the translation results in an exception, the memory operation (instruction fetch or load/store) is aborted and the exception generation mechanism is initiated.

MMU exceptions
~~~~~~~~~~~~~~

Since the MMU handles two lookups in parallel (one for the fetch unit and one for memory accesses), it's possible that both of them generate exceptions in the same cycle. If that's the case, the fetch exception is suppressed and the memory access exception is raised.

.. note:: Fetch always runs ahead of execution, so the memory exception must be earlier in the instruction stream.

Upon an MMU exception, the logical address for the excepting operation is stored in the EX_ADDR register. The bit-pattern associated with the attempted operation is stored in the EX_OP register. To simplify OS operation, the TLB_LAx registers are also updated with the appropriate sections of the failing LA.

.. todo:: I'm not sure we want to update TLB_LAx: the reason is that if we cause an MMU exception during a TLB update, we would stomp over the value in the register, irrevocably altering process state. At the same time, an MMU exception during MMU updates (such as TLB updates) is arguably a rather edge-case. Maybe we should defer this question and allow both behavior through an MMU configuration bit.


TLB invalidation
~~~~~~~~~~~~~~~~

For TLB invalidation, a 2-bit TLB_VERSION and a 2-bit LAST_FULL_INVALIDATE_VERSION value is maintained. Any TLB entry with a VERSION field that doesn't match TLB_VERSION is considered invalid. When the TLB is invalidated, the TLB_VERSION is incremented and the invalidation state-machine starts (or re-starts if already active). The state-machine goes through each TLB entry
and writes the TAG with TLB_VERSION-1. Once the state-machine is done, it updates LAST_FULL_INVALIDATE_VERSION to TLB_VERSION-1.

The invaldation state-machine usually operates in the background (using free cycles on the TLB memory ports). However, if LAST_FULL_INVALIDATE_VERSION == TLB_VERSION, that indicates that there are entries in the TLB that would alias as valid even though their VERSION field is from a previous generation. So, if a TLB invalidation results in LAST_FULL_INVALIDATE_VERSION == TLB_VERSION, the MMU is stalled until the invalidation state-machine is done (which clears the condition automatically).

TLB memories
~~~~~~~~~~~~

The TLB has two port: one towards the fetch unit and one towards the load-store unit. Each port corresponds to a read/write port on both the 1st and 2nd level TLB memories.

Each memory port handles lookups for their associated units as well as writes for fills in case of misses.

The memory ports that are connected to the load-store unit are also the ones that the invalidation state-machine uses.

TLB updates through the TLB_DATA1/TLB_DATA2 registers go through the memory ports that are connected to the load-store unit.

.. note::
  since TLB_DATA1/TLB_DATA2 are memory mapped, these stores are sitting in the write queue just like any other write. Consequently they become effective when the write queue 'gets to them' or the write queue is flushed. Since reads flush the write queue, it is not possible for a TLB lookup for a read to have a port conflict with a write to TLB_DATA1/TLB_DATA2. It is possible however that a TLB lookup for a write has a port-conflict with a previous write to TLB_DATA1/TLB_DATA2 that just entered the head of the write-queue. In this instance, the TLB lookup takes priority and the write is delayed (the interconnect should already be ready to deal with this kind of thing). Worst case, we have a ton of writes back-to-back, so the TLB_DATA1/TLB_DATA2 write keeps getting delayed, but eventually the write-queue gets full, the CPU is stalled, which allows the TLB_DATA1/TLB_DATA2 write to proceed and the conflict is resolved.

Accesses to the TLB have the following priority (in decreasing order):
1. TLB lookups
2. TLB fills (these can't happen at the same time as lookups)
3. Writes through TLB_DATA1/TLB_DATA2 (only happens on the port towards the load-store unit)
4. Invalidation state-machine (only happens on the port towards the load-store unit)

Since we have two MMU ports, this translates to two read-write TLB ports on each of the TLB memories. It's possible in theory
that we encounter simultaneous writes to TLB entries from both ports, and into the same address. In that case, the fetch port wins.

.. important::
  in order for this to work, all TLB updates need to be single-cycle and atomic. That is, both the TAG and the DATA for the TLB entry will need to be written in one cycle. This is doable, as long as we don't play tricks, such as try to fill adjacent TLB entries with a read burst.

.. note::
  the write collision due to concurrent fills is actually theoretical. Since both fills would come from main memory and main memory will not provide read responses (through the interconnect) to both fill requests in the same cycle, the corresponding TLB writes would never actually coincide. What *is* possible though is that a fetch TLB fill comes back at the same time as a TLB_DATA1/TLB_DATA2 write - if the interconnect is powerful enough - and it's certainly possible that a TLB fill coincides with an invalidation state-machine write. If we were to handle these situations fully, it's possible to simply disallow these two low-priority writes until the complete TLB fill on the fetch port is done. This setup would allow for burst-fills of the TLBs.



Exceptions and Interrupts
-----------------------------

Exception handling
~~~~~~~~~~~~~~~~~~

All CPU-originated exceptions are precise, which is to say that all the side-effects of all previous instructions have fully taken effect and none of the side-effects of the excepting instruction or anything following it did.

Exception sources can only generate exceptions while the processor is in TASK mode.

In TASK mode, the source of the exception is stored in the ECAUSE register and the address of the last executed instruction is in :code:`$tpc`. The write-queue is NOT flushed before the exception mechanism is invoked. The processor is switched to SCHEDULER mode and executing continues from the current :code:`$spc` address. The TLBs or the caches are not invalidated.

.. important::
  In SCHEDULER mode, exceptions are not possible. If one is raised, the source is stored in the RCAUSE register, while the address of the excepting instruction is stored in RADDR. After this, the processor is reset.

The following exceptions are supported:

- MIP: MMU Exception on the instruction port (details are in EX_ADDR_I/EX_OP_I)
- MDP: MMU Exception on the data port (details are in EX_ADDR_D/EX_OP_D)
- SWI: SWI instruction (details are in the ECAUSE/RCAUSE registers)
- CUA: unaligned access
- HWI: HW interrupt

Since we do posted writes (or at least should supported it), we can't really do precise bus error exceptions. So, those are not precise:

- IAV: interconnect access violation
- IIA: interconnect invalid address (address decode failure)
- ITF: interconnect target fault (target signaled failure)

These - being imprecise - can't be retried, so if they occur in TASK mode, the only recourse is to terminate the app, and if they happen in SCHEDULER mode, they will reboot, after setting RCAUSE and, if possible, RADDR.

All these sources are mapped into the ECAUSE and RCAUSE registers:

+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|IAV|IIA|ITF|HWI|MIP|MDP|CUA|SW7|SW6|SW5|SW4|SW3|SW2|SW1|SW0|
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

Interrupt handling
~~~~~~~~~~~~~~~~~~

There's only a single (level-sensitive) external interrupt source, which is equivalent to the execution of the HWI instruction. In fact, the preferred implementation is to inject a virtual HWI instruction into the instruction stream by instruction fetch.

Interrupts trigger a transition from TASK to SCHEDULER mode, or gets ignored during SCHEDULER mode (if it's not cleared, it will trigger as soon as the CPU returns to TASK mode).

The EADDR register contain the PC where the interrupt/exception occurred.

Since we have single, conditional branch instructions for testing the first 12 bits of any register, we can rather quickly check for the interrupt/exception source and jump to their associated handler.

.. note::
  one can argue that SWx should be binary encoded instead of 1-hot encoded. Similarly IAV/IIA/ITF cannot happen at the same time. This could save us a few bits, but would reduce our ability to use the bit-test jumps to quickly get to the handlers. So, I think it's fine as is. If even more sources are needed in the future, we're still better off, as a single shift can get us to the next 12 bits, which we can continue to branch upon. Really, the interrupt router code is something like this::

	except_handler:
	      $r5 <- ECAUSE
		  if $r5 == 0 $pc <- except_done
		  $r4 <- $r5
	      if $r5[0]  $pc <- SW0_handler
	h1:   if $r5[1]  $pc <- SW1_handler
	h2:   if $r5[2]  $pc <- SW2_handler
	      ...
	h11:  if $r5[11] $pc <- IAA_handler
	      $r5 <= $r5 >> 12
	h12:  if $r5[0]  $pc <- IAV_handler
	      ...
	      // Clear handled exceptions, check for more
	      ECAUSE <- $r4
	      $pc <- except_handler


	// handler code
	SW0_handler:
	// do the things we need to do
	// ...
	// jump back to test for next handler
	$pc <- h1

.. todo::
  In the exception handler code, how do we clear exceptions? Probably by writing back into ECAUSE

Performance Counters
--------------------

We have 4 performance counters, but lots of events. For now, the following ones are defined:

	ICACHE_MISS
	DCACHE_MISS
	ICACHE_INVALIDATE
	DCACHE_INVALIDATE
	TLB_MISS
	TLB_MISS_1ST_LEVEL
	TLB_MISS_2ND_LEVEL
	INST_FETCH
	PIPELINE_STALL_RAW_HAZARD
	PIPELINE_STALL_WRITE_QUEUE_FLUSH
	PIPELINE_STALL_READ
	PIPELINE_STALL_BRANCH
	PIPELINE_STALL_FETCH
	PIPELINE_STALL_MMU
	PIPELINE_STALL_DCACHE_MISS
	PIPELINE_STALL_MEM_READ
	BRANCH_MIS_PREDICT
	BRANCH_TAKEN
	BRANCH_NOT_TAKEN

Write Queue
-----------

There are fence instructions to explicitly flush the write queue. In this implementation, the write queue is also flushed by any read (because we don't want to be in the business of testing all WQ entries for a read-match). It's important to note that fences are important even though reads can't go around writes in the queue. The reason is the interconnect and the fact that reads and writes can reach different targets with different routing latencies. Consequently, side-effects can still happen out-of-order, even if the transactions themselves leave the core in-order. Fence instructions thus also wait for write-responses to come back, something that normal reads (that flush the write-queue) don't do.

.. todo::
  We also have to think about how the write queue and DCACHE (write-through or write-back) interact.

Load-store unit and write-queue
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The load-store unit handles LA->PA translation. Thus, the write queue only stores PA and write-related exceptions are precise and happen during the execution phase of the instruction.

