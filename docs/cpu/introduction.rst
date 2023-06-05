Introduction
============

Espresso is the main processor of the Anachronistic Computer (Anachron). It is a simple, low-end implementation of the `Brew <https://github.com/andrastantos/brew>`_ processor architecture.

There's a lot to say about the Brew processors, but this is not the place. Here, you will only see the differences, additions and implementation details about the Espresso core.

Just like the whole Anachron project, the Espresso processor is aimed as an imaginary design from the early '80s. In that sense, it has to adhere to the technological limitations of the age, and be a 'good citizen' in the ecosystem of the era. So, why Brew for this project? Mostly because ... why not? It's a riff on a variable-instruction-length RISC architecture, which straddles the divide that started to emerge around that time in CPU architecture. In that sense it fits right in. It's also a 32-bit ISA with a 16-bit instruction encoding, something that would have been rather more appealing in those memory-constrained days.

ISA differences
---------------

Espresso mostly adheres to the Brew ISA, but for various reasons there are a few differences:

 - We have a very simple in-order memory model, so no fence instructions make sense
 - We have no caches either, so cache invalidation is out
 - No extension groups: these would make decoding more complex and the functionality provided by them are not needed
 - No types, everything is INT32
 - No floating point ops (especially in unary group)
 - No type overrides loads or stores
 - No reduction sum ($rD <- sum $rA)
 - No lane-swizzle (since we don't have vector types and the requisite muxes are large)
 - No synchronization (load-acquire; store-release) primitives

Implementation in a nutshell
----------------------------

There will be a lot of details on this, but just to set the stage...

Espresso is a rather bare-bones pipelined RISC implementation. It has no caches, no MMU even. It stalls for loads and stores, does completely in-order issue and execution. It doesn't have a branch predictor, or to be more precise, it predicts all branches not taken. Something that might be a tiny bit out of the mold is that it has a pre-fetch stage (and the requisite instruction queue).

Another slightly unusual feature is that the 'execute' stage involves memory accesses, but has a two-cycle latency.

All in all, pretty basic.

