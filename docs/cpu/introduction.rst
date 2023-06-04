Introduction
============

Espresso is the main processor of the Anachronistic Computer (Anachron). It is a simple, low-end implementation of the Brew processor architecture.

The Brew (as in home-brew) Processor design explores a few ideas that have been rattling in my head for a while. It is at it's heart a RISC architecture, but with some twists that I will quickly introduce:

The processor uses 4-bit fields to encode register addresses, which normally would allow for 16 registers. The ISA however only has 15 addressable registers. This allows us to use the 16th code (0xf) to escape several easy to decode instruction spaces

There are only two execution contexts: TASK mode and SCHEDULER mode. These roughly correspond to user-space and kernel-space in other architectures, but there are differences (described later) that warrants different naming. There is no concept of rings such as on ia32.

There is no way to enable or disable interrupts. To be more precise: interrupts are always enabled in TASK mode and always disabled in SCHEDULER mode. This already shows a key difference between the traditional kernel and user spaces and SCHEDULER and TASK modes on Brew: since interrupts are disabled in SCHEDULER mode, we want to spend as little time in SCHEDULER as possible. SCHEDULER mode code should determine the source of the interrupt and - thus the name - schedule the TASK-mode interrupt handler to be executed. This also means that much of what normally would be the kernel of the OS would need to run in TASK mode.

Each context has its program counter: :code:`TPC` and :code:`SPC`. The processor updates the appropriate program counter depending on the execution context. As we will see in the instruction set description, most instructions deal with the 'program counter of the current context'. We will label that as simply :code:`PC`, but it's important to understand, that that's just an alias to either :code:`TPC` or :code:`SPC`.

There are very limited ways for switching contexts: we can enter SCHEDULER mode though interrupts or exceptions. The only way to enter TASK mode is by the use of the :code:`STM` instruction.

After a mode-switch, execution continues from the contexts :code:`PC`. This means that there is no concept of an interrupt or exception vector: when TASK mode gets interrupted, SCHEDULER mode execution continues from the instruction pointed to by :code:`SPC`. Since the only way to get to ask mode is to execute the :code:`STM` instruction in SCHEDULER mode, the end result is that SCHEDULER-mode execution simply continues after the :code:`STM` instruction.

There are to privileged instructions. Every instruction can be executed in both contexts with exactly the same semantics. Process-separation and protection is achieved by two key concepts:
  - There is a slight imbalance in the ISA: there is a way to influence the current contexts' :code:`PC` and :code:`TPC`; there is no way to influence :code:`SPC` (unless of course that happens to be the current context :code:`PC`).
  - All resources (I/O, memory, even CSRs) are accessed through memory references. These references go through an MMU, which controls per-task access rights.

The end result is that there is no way to influence what SCHEDULER mode code is doing from TASK mode, unless of course the programmer provides one. SCHEDULER mode code then controls (or rather initially controls but later delegates) MMU access-right management for individual TASK-mode processes. These processes have their access rights enforced by the MMU. The MMU registers and page-tables are themselves accessed through the MMU and thus are subject to access control: a process normally can't change it's own memory mapping and access rights.

SCHEDULER mode accesses also go through the MMU, but use a different page table address.The switch between TASK and SCHEDULER mode MMU page tables is automatic, so when SCHEDULER mode gain back execution, it's not limited to the access rights of the last executed task.

.. todo::
    We should consider SCHEDULER mode living in physical address space and bypass the MMU. That results in some simplifications but makes booting more cumbersome.

.. todo::
    The fact the SCHEDULER is so limited puts a lot of overhead on system calls as there are two context switches involved: from user-task to SCHEDULER and from there to system-task. On the way back, a similar double-switch needs to happen. At the same time, this is not any less efficient then a simple task-switch in a pre-emptive OS. It's just that the OS itself is a task. In that regard, this implementation is similar to micro-kernel OS-es.

The ISA is strictly designed for a 2-read;1-write port register file. This means that:
- There are no PUSH/PULL instructions (as PULL would require two writes into the register file). Similarly, there aren't any post-increment post-decrement pre-increment or pre-decrement memory operations.
- There aren't CALL/RETURN instructions either (return would require two writes).

Each register has a type associated with it. This type is set by instructions and can be loaded and saved in batches to memory as well. Crucially, load operations don't change the type of their destination register.

This means that the compiler is best to dedicate types to certain registers and keep them as that type as long as possible.

.. todo::
    Almost all processors have a similar concept for floating-point (and vector) registers: they have their own type, except this type is fixed. One can see Brew way of dealing with register types as a more flexible partitioning of the register-file, something that can be adapted to the needs of the application at hand. It is noteworthy though that with only 15 registers, the benefits of static partitioning are somewhat limited, while the overhead of maintaining register-type information through function-call boundaries is non-trivial.

Register types determine the semantics of many operations, especially in the unary, binary ALU groups and in conditional branches.

Type-less variant
-----------------

A type-less variant of the ISA is possible: in this case, all registers are assumed to have the type of INT32 and type-change instructions have no effect.

MMU-less variant
----------------

For some implementations, a full MMU is not needed or too complex to implement. In this case, some level of process protection can be achieved by the following:

There is a TASK_BASE and TASK_LIMIT register in the processor. In TASK mode, logical addresses are compared against the TASK_LIMIT register. Accesses (instruction fetches or load/store operations) beyond the limit are not permitted and an access violation exception is thrown. The logical-to-physical mapping is achieved by adding TASK_BASE to the logical address. In fact both TASK_LIMIT and TASK_BASE registers can be quantized to 4kB page-boundaries, further simplifying operation.

In SCHEDULER mode TASK_BASE and TASK_LIMIT registers are not consulted and SCHEDULER mode operates in physical addresses.

There are some obvious limitations to this scheme:

#. Tasks can have access to a single, contiguous section of the physical address space. This in practice means they can only have access to DRAM (as they *do* need access to that and we can only control one region), which in turn means that all I/O accesses will have to be marshalled to SCHEDULER mode. Alternatively, one can setup a single TASK with both BASE and LIMIT being set to 0 and use this task as a highly trusted, monolithic God-process with full access to all resources.
#. Since the accessible physical address space for each task must be contiguous, memory fragmentation is a problem, something that can only be solved by de-fragmentation-by-copy.
#. Shared memory between processes is practically not possible.
#. Virtual memory (page files) and memory-mapped files are not practical.

