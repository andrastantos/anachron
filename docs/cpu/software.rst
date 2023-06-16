System Software considerations
==============================

Operating System
----------------

SCHEDULER-mode is primarily used for interrupt processing (that is to decide which task to schedule after a particular interrupt)

Most OS functions are implemented as tasks, though of course the scheduler context is part of it as well.

Since interrupts are always disabled in SCHEDULER-mode, most of the OS must live in TASK-mode. The consequence of this design is that SYSCALLs need to transition into scheduler mode and out of it again (and the same on the way back). This essentially mean twice as many task switches as a regular ring-based (monolithic kernel) OS design would need. To remedy this problem somewhat, very quick SYSCALLs can be handled in the scheduler completely, if the fact that interrupts are disabled the whole time is an acceptable trade-off.

.. todo::
  I'm not sure how much of hit this actually is: One would think that the OS spends an inordinate amount of time validating inputs from SYSCALLs anyway, and the overhead of actually reaching the kernel is relatively minor. This needs some quantification though which I don't have the tools to do just yet.

To further minimize the overhead, task context switch should be very quick in order to make this architecture anywhere remotely performant:

#. Save registers into the task control block
#. Determine source of interrupt (read interrupt cause register)
#. Determine task to handle interrupt
#. Re-jiggle MMU config for new task
#. Load registers from new tasks control block
#. `stm` - this returns control to the new task
#. jump to step 1.

Most of the penalty comes from the load/restore of register content and the fact that we're changing the MMU config (which might
wreck havoc with the caches).

An idea would be to create a variant of the toolset that uses a limited number of registers (say the top 7) for SCHEDULER task development. This would limit the number of registers to save/restore while allow for te use of high-level languages.

Threads, tasks and processes
----------------------------

**Threads** are simple execution contexts with their own *registers*, *stack*, but shared *memory layout*, *handles* and *heap*.

**Tasks** are more complete contexts which have their own *memory layout* (thus *heap*) as well.

**Processes** are even more complete, having their own *handles*.

For scheduling purposes, these objects are put into several active and inactive lists. The scheduler maintains these lists.

While there is a lot of pointer-chasing involved in the current layout, that should not be a problem for something as simple as Espresso. In fact, compactness of memory matters more. However, the actual container structure might be worth abstracting out (i.e. next pointers) to make migration easier once we get to architectures that hate this kind of thing.

Call State Block (CSB)
----------------------

To support shared library calls, some of the thread state is hoisted out of the thread control block and placed in a separate structure. A stack of these structures create a shared library call stack.

======= ======================== ===================================
Offset   Name                     Notes
======= ======================== ===================================
0x00     next                     Link list manipulation. Set to NULL for last entry.
0x04     pc                       Store for $pc
0x08     task_ptr                 Pointer to the task control block
0x0c     lr                       Store for $lr
======= ======================== ===================================

Thread Control Block (HCB)
--------------------------

Each thread needs 80 bytes of memory for their control blocks with the following layout:

======= ======================== ===================================
Offset   Name                     Notes
======= ======================== ===================================
0x00     next                     Link list manipulation. Set to NULL for last entry.
0x04     csb_stack                Pointer to the top of the call state block stack
0x08     register_store           14 DWORDs to store all registers except $lr
0x40     stack_size               Size of the stack
0x44     process_ptr              Pointer to the process control block
0x48     pad                      Not used at the moment
0x4c     pad                      Not used at the moment
======= ======================== ===================================

Task Control Block (TCB)
------------------------

======= ======================== ===================================
Offset   Name                     Notes
======= ======================== ===================================
0x00     next                     Link list manipulation. Set to NULL for last entry.
0x04     code_base                Base physical address for code
0x08     code_limit               Limit address for code
0x0c     data_base                Base physical address for data
0x10     data_limit               Limit address for data
0x14     process_ptr              Pointer to the process control block
0x18     call_ref_cnt             Reference count for calls in progress
0x1c     handle_ref_cnt           Reference count for handles to this TCB
======= ======================== ===================================

Process Control Block (PCB)
---------------------------

======= ======================== ===================================
Offset   Name                     Notes
======= ======================== ===================================
0x00     next                     Link list manipulation. Set to NULL for last entry.
0x04     handle_table_ptr         Pointer to handle table
0x08     parent_process_ptr       Pointer to the process control block of the parent process (the one that spawned us)
======= ======================== ===================================

.. todo::
    What is the difference between an execution context and task? Or a process? For instance, do we allow for priority changes on shared library calls?

Shared libraries
----------------

Without a proper MMU, shared libraries are somewhat limited. Espresso provides separate base- and limit registers for code and data, which allows for shared libraries in two ways: common data shared libraries share data base- and limit registers with their callers, but have their own code base- and limit registers, while private data shared libraries have their own data and code segments in memory.

In some ways, this is similar to an RPC, but in other, critical ways, it's different.

To maintain a chain of shared library calls (SLCs), a stack of contexts need to be maintained. This stack will contain pointers to TCBs.

The shared library call is issued using the `SHARED_LIB_CALL` syscall. `$lr` contains the shared library handle and `$r3` contains the API call index.

The SCHEDULER will perform the following actions:

#. The context is saved into the current HCB, including the $pc and $lr into the top of the CSB stack. (To be more precise, $pc+4 is stored, so return continues after the syscall.)
#. The TCB of the target library (based on $lr) is looked up. It contains:
    #. The TCB of the library
    #. The entry point for the shared library
#. A new CSB entry is created with the library entry point and TCB. The lr field is populated with the previous top CSB. It is put on the HCBs csb_stack (such that the HCB is pointing to it)
#. Increment `call_ref_cnt` of the TCB
#. Determine if a context switch is needed. If not, the context is restored from the HCB (and thus the newly created CSB entry).

.. note::
    The CSB contains two pointers to the previous entry: one in `next`, one on `lr`. Though `lr` might be obfuscated. Here we also assume that the shared library handle is actually a CSB pointer.

At this point, execution is starting at the entry point of the shared library, with the updated memory base and limit registers. The link register (`$lr`) contains the callers library handle, all other registers retain their values from the caller.

The shared library code will determine the right course of action, as determined by the register values. It can issue further shared library calls, if needed. Upon return, it'll issue a `SHARED_LIB_RETURN` syscall.

The SCHEDULER will perform the following actions:

#. The context is saved into the current HCB, including the $pc and $lr into the top of the CSB stack. (To be more precise, $pc+4 is stored, though it doesn't matter in this case.)
#. The top CSB stack entry is popped (with care that it's not the last one).
#. The `call_ref_cnt` of the TCB pointed to by the CSB is decremented
#. Determine if a context switch is needed. If not, the context is restored from the HCB.

At this point, execution is continuing from after the shared library call, with the original memory base and limit registers. The link register (`$rl`) contains the shared library handle, all other registers return their values as they were when the shared library returned.

Memory sharing and marshalling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Shared libraries can come in one of two versions:

**Common data shared libraries**: These libraries have their unique code-base and limit register settings, but share the data-base and limit registers with their caller. They execute in the stack of the caller process and don't have dedicated static data segments (bbs sections for instance).

Because of this, data pointers and structures are directly available between caller and callee, no translation or marshalling is necessary. Code (function) pointers, including virtual method table entries cannot be shared.

**Private data shared libraries**: These libraries have both their unique code- as well as data- base and limit registers. They have their own stack, static data and heap segments.

Because of this, only data passed through the registers can be shared between caller and callee. No pointer makes sense across the call barrier. Marshalling of data is required.

Call-back functions; applications as shared libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since code can never be shared between shared libraries, call-back functions are complicated. They need to be implemented as shared library calls, which means that even applications would need to be able to operate as shared libraries. The application runtime will interpret shared library calls with anything but API index '1' as if the API index is the address of the callback function.

In general, API numbers with the LSB set (these are invalid call target addresses) are treated as special.

Application startup
~~~~~~~~~~~~~~~~~~~

Applications are started up as if they are a shared library, with a 'SHARED_LIB_CALL' syscall. The API index is set to '1'.

Shared library startup
~~~~~~~~~~~~~~~~~~~~~~

When shared libraries are first loaded into memory, they are started up with a 'SHARED_LIB_CALL' syscall. The API index is set to '1'.

Shared library unload
~~~~~~~~~~~~~~~~~~~~~

A shared library can be unloaded from memory when:

#. Their `call_ref_cnt` is 0
#. Their `handle_ref_cnt` is 0

Share library swapping
~~~~~~~~~~~~~~~~~~~~~~

A shared library is a candidate for swapping if their `call_ref_cnt` is 0.

Remote library calls (RLC)
--------------------------

These are a simplified version of RPC, where the caller and the callee are within the same process. They *do not*

















Remote Procedure Calls (RPC)
----------------------------

RPCs are achieved through the `swi 6` instruction with function code 0, where the library-specific function number is stored in the code segment, following the 16-bit instruction code.

$lr contains the OS-provided handle for the shared library.

The calling convention is extended to `$r3` containing the RPC call handle.

When an `swi 5` instruction is executed, SCHEDULER-mode executing takes over. It performs the following actions, once the fact of a shared library call is recognized:

With async
#. The library handle is de-obfuscated, if needed (for example XOR-ed with a random key) to gain the control-block address for the task associated with the shared library.
#. The current task handle is placed in $lr.
#. The current task handle is also put in the RPC call stack
#. For synchronous RPCs, the caller is removed from the ready-to-run list
#. For async RPCs:
  #. A completion handle is allocated from the corresponding free list
  #. The completion handle is set up as the return value for the caller (in the caller context)
  #. The completion handle is a
#. The context from the task-control-block is restored
#. Execution is returned to the shared library, using the `stm` instruction.

The shared library can call further shared libraries in a similar manner. Return from an RPC is done through the `swi 6` instruction with function code 1. Upon gaining back execution, the SCHEDULER performs the following:

#. The caller task handle is retrieved from the RPC stack
#. For synchronous RPCs:
  #. The caller is returned to the ready-to-run list
  #. The caller context is restored
  #. Execution is returned to the caller, using the `stm` instruction.
#. For asynchronous RPCs:
  #. Don't know, actually.

In terms of function arguments and return values, RPC calls follow the convention for local function calls.

The bottom bit of the library handle is used to describe synchronous v.s. asynchronous RPCs. Synchronous RPCs will remove the caller task from the ready-to-run list until their associated RPC return is executed.

.. todo::
  Here's the problem with async RPCs: we need to return a 'completion' handle of sorts, something that the caller can wait on. This handle will have to come from *somewhere*. That somewhere can be depleted. Also, how do we allocate from that *something*? This sounds like a fixed sized heap, i.e. a free-list.

Scheduler mode operations
-------------------------

Scheduler handles
~~~~~~~~~~~~~~~~~
Scheduler handles are essentially obfuscated pointers. Since these pointers are mostly to structs, they are DWORD aligned, which is to say that the bottom-most two bits are guaranteed to be 0. These bottom two bits can be used to convey additional information.

Either way, the pointers are XOR-ed for obfuscation purposes with a random value (the bottom two of which is guaranteed to be 0). The obfuscation code could be either a per-process or per-boot random value.

APIs
~~~~

SCHEDULER-mode APIs are all accessed by the `swi 6` instruction, with various functions differentiated by the 16-bit function code, stored after the `swi 6` instruction. This is - in this regard - very similar to system calls.

The main difference is that system calls may or may not be implemented directly in SCHEDULER mode. SCHEDULER-mode APIs (by definition) are implemented

CREATE_TASK
GET_RPC_TARGET_HANDLE
