Unimplemented features
======================

There are several features of the original Brew concept that the Anacron implementation doesn't support. These are either things that I deemed too complex for the target technology (and era) or things that I'm on the fence on at the moment.

Memory model operations
-----------------------

In a more complex processor, especially in a multi-core system memory model is a big problem. Write queues, instruction and data-caches, out-of-order execution all mess with the real order of memory operations compared to the SW-apparent one. The Brew architecture has support for 'load-acquire' 'store-release' model of synchronization primitives. It has support for various fence instructions and cache-invalidation operations. None of this makes sense in a single-processor, in-order, cache-less processor, which this simple design is. So these operations either revert to regular loads and stores or just don't do anything.

Floating point operations
-------------------------

Floating point support would be nice, of course, but not within the silicon complexity constraints of the early '80s. This feature must go.

Register Types
--------------

This is probably the most controversial feature of Brew, something that I haven't seen in any other processor (maybe for good reasons). The idea is that along every register value, the processor maintains the type of the data stored in that register. This type can be set by a set of instructions and - crucially - used by the processor to determine the semantics of various operations. For instance, the operation `$r4 <- $r5 + $r6` could mean an integer addition if `$r5` and `$r6` hold integer values, but the same bit-pattern can mean a floating-point addition if the source operand types set as such. There are many many corner-cases to be ironed out (what if `$r5` is a float and `$r6` is an integer?) but that is mostly a question of policy.

Another big problem is that now on function entry/return not only register values, but their types will need to be saved and restored. I have instructions that can handle this, but the previously mentioned multiple load-store operations would shine in this aspect: they can handle the type load/store aspect right then and there. A similar save/restore concept needs to be employed during task-switching adding extra time it takes to swap the execution context.

Yet another problem is compiler support: I don't know how to explain this behavior to GCC. How to tell it that it can use *any* register as a floating-point one, but really should not: it should try to group operations and register-assignments by type: type-changes are extra instructions, so should be avoided. This means though that the register-allocator would need to be type-aware.

Finally, there's the question of how to build a high(er) performance processor with this feature? You see, the problem is that the execution-unit selection can't be done until the source operand types are known. This on the surface would mean that out-of-order execution would be really difficult. The saving-grace though is this: the result type of an operation is known right when the source operand types are determined. So, even though the *value* of the result might come several clock cycles later, the *type* of said result can be known immediately and scheduling of operations to execution units (and queues) can continue.

Extension groups
----------------

There are several holes in the instruction set, that can be used to extend the ISA in the future. Some of these are already called for for more complex operations (linear interpolation is one example).


