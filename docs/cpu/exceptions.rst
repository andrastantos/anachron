Exception Handling
==================

Espresso has several exception sources. Exceptions are precise, meaning that when the exception handling mechanism is invoked:

#. All the side-effects of instructions preceding the excepting one have fully taken effect
#. None of the side-effects of the excepting or any subsequent instructions have taken effect

Exceptions in TASK mode cause the processor to enter SCHEDULER mode. Interrupts are considered one of the possible exceptions.

When a TASK mode exception occurs, Espresso starts execution in SCHEDULER mode. :code:`$tpc` points to the excepting instruction.

Exceptions in SCHEDULER mode cause the processor to jump to address 0 (the reset vector). Interrupts in SCHEDULER mode are masked and don't take effect.

Exception cause
---------------

The :code:`csr_ecause_reg` contains a bit-field where each bit corresponds to a particular possible exception cause.

The :code:`csr_ecause_reg` register is 'write-one-to-clear', that is to say: to clear a bit in the ecause register SW needs to write a '1' to that bit. If an exception happens on the same cycle when the :code:`csr_ecause_reg` bit is cleared by SW, the bit stays set.

:code:`csr_ecause_reg` bits are set even in SCHEDULER mode. This is useful for polling for pending interrupts. Other exceptions in SCHEDULER mode cause the processor to jump to address 0. The :code:`csr_ecause_reg` register in these cases can be interrogated to determine the (approximate) reset cause.

In some cases the cause of the reset can't be fully determined. Consider for instance a TASK-mode exception, resulting in a transfer to SCHEDULER mode. Afterwards, a second SCHEDULER mode exception occurs before the SCHEDULER-mode SW had a chance to clear the previous :code:`csr_ecause_reg` bit. The processor jumps to address 0, but when code starts executing from address 0, two :code:`csr_ecause_reg` bits would be set and the cause of the reset could not be unambiguously determined.

The following exception causes are defined:

========== ==================== =================================
Bit-field  Name                 Description
========== ==================== =================================
 0         :code:`exc_swi_0`    SWI 0 instruction executed
 1         :code:`exc_swi_1`    SWI 1 instruction executed
 2         :code:`exc_swi_2`    SWI 2 instruction executed
 3         :code:`exc_swi_3`    SWI 3 instruction executed
 4         :code:`exc_swi_4`    SWI 4 instruction executed
 5         :code:`exc_swi_5`    SWI 5 instruction executed
 6         :code:`exc_swi_6`    SWI 6 instruction executed
 7         :code:`exc_swi_7`    SWI 7 instruction executed
 8         :code:`exc_cua`      Unaligned memory access
 9         :code:`exc_mdp`      Memory access AV (only in TASK mode)
10         :code:`exc_mip`      Instruction fetch AV (only in TASK mode)
11         :code:`exc_hwi`      Hardware interrupt (only in TASK mode)
========== ==================== =================================

.. admonition:: Why?

    There are special branch instructions in Espresso that can test a bit in a register and branch based on them being set or cleared. Using these instructions, the SCHEDULER-mode code can very quickly determine the (rough) source of the exception and jump to the appropriate handler. Having a simple exception code would require several more instructions, slowing exception handling down.

    Another reason to have a bit-vector is that there could actually be multiple simultaneous exceptions occurring for an instruction, even though that is a rather rare occasion.

    Finally, clearing exception sources is easiest with a write-1-to-clear semantics: not only does it allow for each individual handler to simply clear it's own 'cause' bit, but it allows the collection of further exceptions (interrupts) while in SCHEDULER mode.

Interrupts
----------

Interrupts can occur both in TASK or SCHEDULER mode. When Espresso is in TASK mode, it transfers execution into SCHEDULER mode. When an interrupt occurs in SCHEDULER mode, the execution flow is not modified, by the :code:`exc_hwi` bit in :code:`csr_ecause_reg` is set. This allows SCHEDULER-mode code to poll for interrupts.

The external interrupt input of Espresso is level-sensitive, active low. This means that each interrupt source must have its own interrupt clear logic, and that interrupt handling SW must clear the pending interrupt both at the source as well as in :code:`csr_ecause_reg`.

Multiple external interrupt sources can share the interrupt input of Espresso through wired-and logic.

Exception address
-----------------

The :code:`csr_eaddr_reg` register contains the effective logical address for the operation causing the latest exception. This address could be an instruction address (in case of a fetch AV, :code:`swi` instruction or interrupt) or a memory address (in case of a read/write AV).

CSRs
----

================= =========================== ============ ================================
Offset            Name                        Access       Description
================= =========================== ============ ================================
0x400_0014        :code:`csr_ecause_reg`      R/W1C        Contains the reason for the last exception.
0x400_0018        :code:`csr_eaddr_reg`       R            The effective address that caused the latest exception
================= =========================== ============ ================================

