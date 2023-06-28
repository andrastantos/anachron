Micro-architecture of Latte
===========================

Major improvements of the Micro-architecture of Latte over Espresso are the following:

#. Introduction of a 1kB instruction cache
#. Introduction of an MMU
#. Introduction of a simple branch-predictor
#. Introduction of a write-buffer

ICache
------

A proper ICache is added to Espresso to de-couple (and off-load) instruction fetches from the ever over-subscribed DRAM bus. This cache is targeting an 80+% hit-rate (TODO: this needs verification through simulation).

The cache organization is the following:

#. Cache line size: 16 bytes
#. Cache way size: 256 bytes (16 lines)
#. Cache way count: 4
#. Replacement strategy: round-robin

The instruction cache performs 16-byte aligned, wrap-around bursts, but doesn't support critical-word-first fetching (I think).

The ICache provides (aligned) 32-bit entries per clock cycle to instruction fetch.

ICache invalidation
~~~~~~~~~~~~~~~~~~~

Whole cache invalidation is initiated through a CSR write. After the write, there must be a tight loop, checking for the invalidation to be completed. That is a CSR read, followed by a jump if invalidation is still in progress. Why? Because of the prefetch queue. Quite likely a number of instructions are already in the queue by the time the write finally reaches the cache controller and the invalidation starts. The act of invalidating will stall any further instruction fetches, but whatever is already in the FE pipeline will go through uninterrupted. So, the loop might execute a few times (if the branch-predictor was right) before the processor finally stalls. NOTE: in this design reads flush the write-queue so it's guaranteed that the first read will see the side-effect of the write. Since the read is not cached, it'll take quite a bit to wind its way through the interconnect to the cache-controller. It's possible that by the time the read reaches the controller, the invalidation has been completed.

Why can't this loop be done in HW? Why can't the cache-controller flush the FE-BE queue? It sure can. However the problem is that there are several instructions executed (or at least partially pushed into the pipeline) by the time the cache controller even realizes that there's an invalidation request.

Cache invalidation happens whenever logical-to-physical address mapping changes. This happens when processes are shuffled around in physical memory or more memory is added to a processes logical address space. Or when an allocate-on-write exception is handled. However the most likely reason still is simply a context change.

I think we can remove the need of flushing the cache for every MMU change by:

#. Tagging using both logical and physical addresses
#. Use logical addresses for look-up, but don't declare victory just yet if there's a hit
#. Comparing physical address to MMU translation results, cancelling the hit if there's a mismatch


Branch prediction
-----------------

Potential branches are identified by checking for branch instruction patterns in fetched instruction.

.. important::

  Even though it would be really enticing to just check every 16-bit word for branches, the branch predictor will have to be instruction-length aware. Let's say, we predict a branch to be taken. We alter the instruction stream, but we should make sure that the immediate field of the branch is correctly fetched from the original location. Because of this, we might as well make sure that we won't predict on words that are not actual instructions. We have the knowledge anyway.

We will have a branch target buffer (BTB), containing:

#. 31-bit target address (16-bit aligned)
#. 1-bit target mode (TASK vs. SCHEDULER)
#. 1-bit match.

The BTB is addressed by the (low-order N-bits) of $pc, that is: it's working on logical addresses.

.. todo::

  should we use logical or physical address for BTB address? Right now it's logical, though with the right sizing, it might not matter: If the BTB is the size of a page or smaller, the bits used to select the BTB entry are the same between the logical and the physical address.

.. todo::

  should the target address be logical or physical? Right now it's logical.

The back-end, when executing a branch, it stores the target address and check it against the already stored value. If the target address matches, we set the match bit. If don't we clear it.

In the front-end, if a branch is encountered, we look up it's BTB entry, based on the logical address for the fetched word. If the match bit is set, we predict the branch taken to the address in the BTB, otherwise we predict not taken.

This means that two consecutive branches to the same address will trigger prediction.

.. admonition:: A bad idea

  We could modify the default behavior for conditional branches with negative offsets, where match == 0: we would predict the branch taken to the address that's coded in the instruction stream. However, this would need us to *understand* the concept of immediate fields in the instruction stream, the fact that there are 32-bit instructions, be able to calculate brach targets, etc. This is too much work, for very little gain, so let's not do it!

The memory for the BTB needs two read ports *and* a write port:
- 1 read port to get the values in the predictor during fetch
- 1 read port to read the stored target address for branches during execute
- 1 write port to write back the target address and the match bit during execute

.. note::

  Due to the 2-cycle write latency (read-modify-write) in case of back-to-back branches that collide on the BTB entry, we will have to be a bit careful, though I think any implementation will be OK-ish. There is actually almost no chance for this to happen. Adjacent addresses never collide on the BTB entry, so back-to-back branches in the code-stream would never collide. If there is branch, that's predicted properly, jumping to a next branch, which could be gotten from the cache without a hick-up, *and* that branch target happens to alias the first branch in the BTB, we get into this situation. Very unlikely. And even if it happens, the end result of the confusion of the updates is that we might predict a further jump incorrectly. This is not worth the complexity, so simply ignoring the problem is the right avenue to take.

FPGA BRAM sizes are all over the map, but the largest (18kbit) gives us 512 entries. This gives us mapping for the lower 9 bits of the :code:`$pc`, or a total of 1kByte before aliasing, if a simple direct-mapped lookup is used.

.. note::

  since we're predicting if the target is in SCHEDULER or TASK mode, we can correctly predict SWI instructions. STM will probably mis-predict, as we usually would not return to the same address in TASK mode, thus the match bit would never be set - *as such, it's probably not worth even decoding it as a branch*.

.. note::

  since target address is logical, it's important that we predict the TASK/SCHEDULER bit too. Otherwise the TLB lookup could be incorrect. The alternative is that we don't predict any of the SWI or STM instructions, but that slows down SYSCALLs quite a bit.

Every time a branch predictor makes a 'taken' prediction, it puts the target address (including TASk/SCHEDULER mode bit) into a queue. It also sets a :code:`predicted_taken` but in the instruction buffer. This bit gets carried through instruction assembly, decode and execute. In execute, if the bit is set, the target address is pulled from the queue, compared to the computed target and the proper action is taken (update of BTB, flush in case of a mis-predict, etc.).

If the queue is full, the branch predictor continues to predict every branch not taken.

.. note::

  Unless the branch predictor is part of instruction assembly, it needs to deal with the fact, that 32-bits are returned by the ICache. We can't predict two instructions in parallel (we don't have enough BTB ports), but luckily, 16-bit instructions are not likely to be branches. Even if they are, back-to-back versions of them (:code:`swi` followed by :code:`swi`) are almost non-existent, and even if they are, the first one takes precedence. We either predict it taken, in which case the second is irrelevant, or we predict it not taken, in which case there will be a mis-predict later on; again, the prediction on the second one is irrelevant.

  Because of this, the branch predictor only looks at the first instruction in the 32-bit fetch (which could be either the low- or the high-order word, depending on the size and alignment of the previous instruction)


MMU
---

The MMU follows a rather traditional design, except it has a three-level structure with 1kB leaf pages and a 34-bit physical address space, where the top 2 bits are ignored.

The MMU is bypassed for SCHEDULER-mode code, logical and physical addresses are identical in that case.

Each page table is 1kB large. The page entries describe either 1kB (S), 256kB (M) or 64MB (L) pages.

Page table entries are 32 bits long with the following layout::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+
  |                                       P_PA_ADDR                                       | C |   MODE    |               .       |
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
6      :code:`LINK`      entry is link to next-level page table
7      :code:`RWX`       entry has all access rights
=====  ================= ================

The :code:`C` bit is set to 1 for cacheable entries, set to 0 for non-cacheable ones.

P_PA_ADDR:
  top 22 bits of 1kB aligned physical address. Either for a next-level page table or for physical memory. For M pages, the bottom 8 bits are expected to be 0. For L pages the bottom 16-bits are expected to be 0.

.. note::
  Most MMU implementations have D (dirty) and A (accessed) bits. These are redundant: one could start with a page being invalid. Any access would raise an exception, at which point, the OS can set the page to read-only. If a write is attempted, another exception is fired, at which point the page can be set with write permissions. All the time, the exception handler can keep track of accessed and dirty pages. The D and A bits are only useful if the HW sets them automatically, but I don't intend to do that: that makes the MMU implementation super complicated.

.. note::
  Most MMU implementations have a 'G' (global) bit. With this MMU, we almost never globally invalidate the TLBs, so the global bit on a page is not really useful. In fact it's also rather dangerous as any mistake in setting the global bit on a page will potentially cause a TLB corruption and result in hard to find crashes and vulnerabilities.

Page-table-walk
~~~~~~~~~~~~~~~

The MMU has a CSR that points it to the start of the page-table walk and determines the level of this entry as well. This allows for very compact page tables for small applications. If an application needs only 256kB of memory, only a 3rd level page table needs to be created and 1kB of memory used. If the application uses less than 64MB of memory, a 2nd level page table (and it's potentially linked 3rd level tables) are needed.

The logical address to be looked up is broken into the following sections::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+
  |   1st level index     |        2nd level index        |        3rd level index        |                offset                 |
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+

If the walk starts on a 2nd or 3rd level page table, unused indices are checked to be 0. If not, an AV exception is raised.

After that, the walk starts at the appropriate level. The page table entry address is computed from the page table address and the N-th level index. This entry (32-bits) is read from memory (or the TLB in case of a hit). The entry is then analyzed:

If the entry links to a sub-page (:code:`MODE` == :code:`LINK`), the walk is continued by updating the page table address and incrementing the level by 1.

If the entry is not a link, the walk terminates. The physical address is calculated by masking the logical address with the looked-up levels (top 6, 14, 22 bits) and OR-ing it with the :code:`P_PA_ADDR` field from the page table entry.

Access rights are checked against the request and the appropriate exceptions are raised in case of a violation.

.. note::
  1st level page tables only contain 64 valid entries. The remaining 192 entries are never accessed by HW and can be used for administrative purposes by the operating system.


CSR registers
~~~~~~~~~~~~~

There are several CSRs controlling the operation of the MMU.

CSR_MMU_TABLE_ROOT
``````````````````

The physical page where the page walk starts

::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+
  |                                    P_TABLE_ROOT                                       |            unused             | LEVEL |
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+

Possible values for LEVEL:

======= ========== ============================================================
Value   Mnemonic   Description
======= ========== ============================================================
0       LVL_INV    MMU is disabled, logical and physical addresses are the same
1       LVL_1      Page walk starts on a 1st level page table
2       LVL_2      Page walk starts on a 2nd level page table
3       LVL_3      Page walk starts on a 3rd level page table
======= ========== ============================================================

The register default to 0 upon reset.


TLB_LA
``````

Logical address for TLB updates

::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+
  |                                     LA_ADDR                                           |            TID                | LEVEL |
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+

The bottom 12 bits are ignored on write and read 0.


TLB_DATA
````````

Associated TLB entry for the given logical address in TLB_LA. The layout follows the page table entry format::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+
  |                                            P_PA                                       | C |   MODE    |    not implemented    |
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+

These are *write only* registers. Upon write, the value is entered to the TLB entry for the associated logical address stored
in TLB_LA1/TLB_LA2.

TLB_INV
```````

Write only register to invalidate the entire TLB.



TLB organization
~~~~~~~~~~~~~~~~

TLB tag::

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+
  |                                      TAG_L_PA                                         |
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+
  |                        TAG_TABLE_ROOT[17:0]                           |
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+

  +---+---+
  |TAG_LVL|
  +---+---+

The tag is 42 bits long.

.. note:: The top 4 bits of the P_TABLE_ROOT entry is not stores as they only decode wait-state information.

The TLB entries are looked up by a hash of the logical page address (L_PA) and the current P_TABLE_ROOT value: the two are XOR-ed, and the low-order N bits are used as the address for the way lookup.

For a hit-check, the the top 6/14/22-bits of L_PA is matched to TAG_L_PA based on TAG_LVL, while the appropriate bits of P_TABLE_ROOT is matched against TAG_TABLE_ROOT.

Each TLB entry contains the following data:

  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+
  |                                       P_PA_LVL1                                       | C |   MODE    |VERSION|
  +---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---#---+---+---+---+

The VERSION field is used for quick whole-TLB invalidation.

Latte uses a small number of TLB entries, on the order of 8. These form a direct-mapped cache, based on the aforementioned has of L_PA and P_TABLE_ROOT. Because of this, only leaf pages are stored in the TLB: all other pages would alias to it anyway.

The total storage needed for the TLB is 70 bits per entry, a total of 364 bits, or 70 bytes. This roughly matches the size of the register file.

TLBs and the access ports
`````````````````````````

Both the fetch and the load/store port optimizes TLB lookups: they store the last-looked-up page and only issue a new TLB request if the page changes. This allows a great reduction in TLB requests from fetch (essentially only ~one per branch) and even from load/store (most loads/stores happen to the stack-frame which is mostly within one page). This reduction in turn enables a single TLB implementation to serve both load/store and fetch: conflicts should be rather rare.

The last-looked-up page entry should be invalidated every time the P_TABLE_ROOT value is written (not changed necessarily!) or when any entry in the TLB is invalidated.


FPGA implementation notes
`````````````````````````

The TLB is implemented using 2 BRAMs (total of 72 bits per entry). The VERSION field is increased to 4 bits. Since only single-port lookup is needed, no duplication is needed as on the register file. The independent write port is used by the table walker and invalidation logic (to simply things, not necessarily as speedup).

Since this BRAM can store 512 entries on a GoWin FPGA, 256 entries on a Max10, it's questionable if we should just simply let the core take advantage of it. Maybe it could be a configuration (or CSR) option to trim the address bits both on lookup and update.

TLB management
~~~~~~~~~~~~~~

Since the TLB is a cache of the page table entries and since page table updates are not snooped by the MMU, the OS is required to either copy any page updates into the TLB or invalidate the TLB.

A facility is provided through a pair of CSRs where such updates can be propagated into the TLB. An update will perform a TLB lookup and if a match is found, the entry is updated. In case of a miss, no action is taken.

This technique allows the OS to perform relatively cheap MMU updates: no complete TLB invalidation is needed when a page table is updated.

Complete TLB invalidation is also necessary. This can be achieved by writing to the TLB root register. Even if the same value that is contained there is written back, the whole TLB is invalidated.

.. note::
  Since scheduler mode bypasses the MMU - and the TLB - this flushing doesn't adversely impact that. However, the idea was that most Kernel and OS functions are *not* in scheduler mode, but are spread around in various TASK mode processes. Since a context-switch involves re-writing the TLB root register, this effectively invalidates the whole of TLB for every switch. Bad design!


.. note::
  if a 1st or 2nd level page entry is updated (such that it changes where a next-level page is pointed to) that operation potentially invalidates a whole lot of next-level TLB entries. It's impossible to know how many of those 2nd level entries were indeed cached in the TLB, individually updating them (all 256 of them) would certainly be very time-consuming.

TLB in i486
~~~~~~~~~~~

The `i486 <http://tnm.engin.umich.edu/wp-content/uploads/sites/353/2019/04/1997-A-Case-Study-of-a-Hardware-Managed-TLB-in-a-Multi-Tasking-Envionment-pdf-pages-4-6-8.pdf>`_ had 32 TLB entries, in a 8-entries by 4-way associative setup. The only way to deal with SW modifying the page tables was a complete flush of the TLB, which was accomplished by reloading the root address of the page table. The TLB also didn't deal with process IDs, so it could easily evict kernel pages.

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

Upon an MMU exception, the logical address for the excepting operation is stored in the :code:`CSR_EADDR` register. To simplify OS operation, the TLB_LA registers are also updated with the appropriate sections of the failing LA.

.. todo:: I'm not sure we want to update TLB_LA: the reason is that if we cause an MMU exception during a TLB update, we would stomp over the value in the register, irrevocably altering process state. At the same time, an MMU exception during MMU updates (such as TLB updates) is arguably a rather edge-case. Maybe we should defer this question and allow both behavior through an MMU configuration bit.

.. note:: There must be a way to convey the type of operation (read/write/execute) that caused the exception. This is done through the exception type. In other words, there are three individual exceptions that the MMU can raise, up from two in Espresso.

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


Exceptions and Interrupts
-----------------------------

There are a few new exception causes due to the more complex access rights model. These checks still happen (just like in Espresso) before the memory unit get hold of the operation, so exceptions are still precise.

Write Queue
-----------

There are fence instructions to explicitly flush the write queue. In this implementation, the write queue is also flushed by any read (because we don't want to be in the business of testing all WQ entries for a read-match).

.. todo::
  We also have to think about how the write queue and DCACHE (write-through or write-back) interact.

The load-store unit handles LA->PA translation. Thus, the write queue only stores PA and write-related exceptions are precise and happen during the execution phase of the instruction.

