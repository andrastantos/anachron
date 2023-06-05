

Generations
-----------

Generation 1
~~~~~~~~~~~~

Very simple, 5- or 6-stage pipeline. No caches, maybe not even branch-prediction. If anything, everything is predicted not taken, i.e. straight line speculative execution. No write buffer, every memory access is stalling. Multiplies could be multi-cycle, if exist at all. Maybe even barrel-shifter is multi-cycle.

Integer-only ISA with no extension groups or prefix instructions.

The 6th stage (if needed) is there to make instruction decode close timing.

No MMU, only offset/length-based memory protection.

Target frequency is ~10MHz.

16-bit external bus.

Virtual market introduction ~'83.

Generation 2
~~~~~~~~~~~~

I think the most important improvement is going to be a very small iCache (maybe direct-mapped 1kB or something rather trivial) and a full MMU.

Target frequency is ~20MHz.

Maybe write-queues are making an appearance.

Support for FPM DRAM.

Virtual market introduction ~'86.

Generation 3
~~~~~~~~~~~~

32-bit external bus, introduction of DCache, probably more capable ICache. External bus is PCI-like, multiplexed 32-bit address-data. If possible, actually PCI.

Actually, PCI is a '92 thingy, so probably would be too early for this processor.

Memory controller goes off-chip, but adds EDO support. <-- this puts is to ~'95, so this is too early for that as well.

Write queues.

More adept branch-prediction.

Maybe types are introduced to support floating points. Still no vector ISA.

Not sure, but maybe de-coupled front-end?

Target frequency is ~33MHz

Virtual market introduction ~'90

Generation 4
~~~~~~~~~~~~

Memory controller moves back into processor, external bus remains PCI for peripherals only. PC100 SDRAM support <-- this puts us to '93.

De-coupled front-end, updated caches (probably write-back DCache).

Maybe introduction of some sort of coherency protocol for multi-processor systems.

Maybe introduction of vector types.

Re-order queues at the back-end, creation of independent execution units.

Target frequency is ~150MHz core, 33MHz front-end bus.

Virtual market introduction ~'93