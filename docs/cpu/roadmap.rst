Appendix C: CPU generations
===========================

I know, I know: I don't really even have Espresso running, but one can never start too early the planning for the future. More seriously though, it's striking how people (Intel mostly, but Zilog and and Motorola as well) kept getting surprised by the jeopardy of compatibility. Design compromises - sometimes even genuine bugs - were carried over from generation to generation simply because SW became reliant upon them. This is called backwards compatibility. There's another way of thinking about the problem though: forward compatibility. Think through where your product line will (or could) go and make sure you don't make decisions early on that would prevent you from getting there later.

In my case, it would be very tempting to design a 16-bit variant of the Brew instruction set. Use that as the ISA for Espresso. It would be a smaller, cheaper processor. It would be slower too, but maybe not by that much. It would be possible and is a fun exercise to contemplate. However, that would hobble later, true 32-bit implementations with all the backwards compatibility 'stuff'.

Moore's law teaches is that we shouldn't ever think about the past, or even the present. We should always think about the future: by the time you're ready with a product, it's already the future. This industry moves too fast for any other methodology. This should also already have been obvious in the early '80s. One might not have predicted the take-over of CMOS. The emergence of the IP industry . The fab-less design paradigm. But it was obvious that things *will* get faster, *will* get smaller, *will* get cheaper.

So, with that rambling out of the way, let's look at the generations:

Generation 1: Espresso
~~~~~~~~~~~~~~~~~~~~~~

Very simple, 5- or 6-stage pipeline. No caches, not even any true branch-prediction. Speculative execution is cheap as long as we speculate all branches *not* taken. No write buffer, every memory access is stalling. Multiplies might not exist at all.

Integer-only ISA with no extension groups or prefix instructions.

Two-stage execute with fused memory access. The two stages are necessary for the following reasons:

1. 32-bit multiply needs two cycles
2. Effective address calculation (and access-violation check) takes a cycle before memory access.

No MMU, only offset/length-based memory protection.

Target frequency is ~10MHz. Target technology node is 1.5um.

8-bit DDR external bus; 40-pin DIP package

Virtual market introduction ~'83.

Comparative processors: i286

Generation 2: Latte
~~~~~~~~~~~~~~~~~~~

The most important improvement is going to be a very small iCache (maybe direct-mapped 1kB or something rather trivial) and some more capable branch-prediction.

No ISA changes, except the multiplier is a must at this point.

If fits, maybe a full MMU makes a debut, but that's to be seen.

Target frequency is ~20MHz. Target technology node is 1um.

Support for FPM DRAM, otherwise pin-compatible with Espresso.

Virtual market introduction ~'86.

Comparative processors: i386

Generation 3
~~~~~~~~~~~~

Increase of external data-bus to 16-bit DDR. Certainly MMU capability, added DCache and write-queue. Increased cache sizes.

Maybe floating-point operations (and consequently types) make their way into the ISA.

Target frequency is ~33/40MHz, but bus-speed stays unchanged. (In some sense that means that the bus is SDR now, but since we've sufficiently de-coupled from it, that doesn't matter.) Target technology node is 800nm.

Support for FPM DRAM.

Package is 68-pin PLCC.

Virtual market introduction ~'89

Comparative processors: i486

Generation 4
~~~~~~~~~~~~

32-bit, synchronous, PCI-like external bus. If possible, actual PCI.

Memory controller goes off-chip, but adds EDO support as a minor upgrade, when becomes available ('95).

More adept branch-prediction.

For sure, we would have floating points and types. Maybe vector ISA as well.

Maybe some ventures into super-scalar execution. Still in-order decode, but since at this point we most likely decode more than one instructions per cycle, we can play around issuing independent instructions (still in-order), but in parallel. We have independent execution units with different latencies, so out-of-order write-back (and multiple write ports to the register file) is a reasonable approach. Either that, or a reorder buffer at the end of the pipeline, which, with many bypass paths would be the beginnings of register renaming.

Target frequency is ~66/100MHz, target technology node 600nm.

Package is probably some sort of PGA package, pin count is around 100.
Companion memory controller chip is probably a ~200-pin QFP.

Virtual market introduction ~'93

Comparative processors: i486DX4, P5 75/90/100MHz

Generation 5
~~~~~~~~~~~~

Memory controller moves back into processor, external bus remains PCI for peripherals only. PC100 SDRAM support.

De-coupled front-end, updated caches (probably write-back DCache).

Maybe introduction of some sort of coherency protocol for multi-processor systems.

Maybe introduction of vector types.

Re-order queues at the back-end, creation of independent execution units.

Target frequency is ~150MHz core, 33MHz front-end bus; target technology node 350nm.

Virtual market introduction ~'97

Comparative processors: Pentium II (Klamath), AMD K5 and K6.

Notice that we start losing the war: unless we can reach core clock rates of 200+MHz, and a 66MHz FSB, we would not be competitive anymore.

Memory interfaces are multi-banked 64-bit wide affairs at this point: lots of pins, if driven from the CPU...

Also, the feature-set of the competitors is vast, MMX and other integer vector features are coming online, out-of-order execution, super-scalar, register-renaming, all these things are now standard features.

All in all, I'm not sure what happens here.
