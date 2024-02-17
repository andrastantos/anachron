Exception Handling
==================

Exception cause
---------------

The :code:`csr_ecause_reg` contains the value corresponding to the last exception.

The :code:`csr_ecause_reg` register is cleared when read.

The value of :code:`csr_ecause_reg` is set even in SCHEDULER mode. This is useful for polling for pending interrupts as well as determining the cause of a reset (SCHEDULER mode exceptions cause a jump to address 0). In some cases the cause of the reset can't be fully determined. Consider for instance a TASK-mode exception, resulting in a transfer to SCHEDULER mode. Afterwards, a second SCHEDULER mode exception occurs before the SCHEDULER-mode SW had a chance to read :code:`csr_ecause_reg`. The processor jumps to address 0, but when code starts executing from address 0, only the second exceptions' cause would be available.

The following exception causes are defined:

========== ======================== =================================
Value      Name                     Description
========== ======================== =================================
0x0000     :code:`exc_reset`        Hardware reset
0x0010     :code:`exc_hwi`          Hardware interrupt (only in TASK mode)
0x0020     :code:`exc_swi_0`        SWI 0 instruction executed (FILL)
0x0021     :code:`exc_swi_1`        SWI 1 instruction executed (BREAK)
0x0022     :code:`exc_swi_2`        SWI 2 instruction executed (SYSCALL)
0x0023     :code:`exc_swi_3`        SWI 3 instruction executed
0x0024     :code:`exc_swi_4`        SWI 4 instruction executed
0x0025     :code:`exc_swi_5`        SWI 5 instruction executed
0x0026     :code:`exc_swi_6`        SWI 6 instruction executed
0x0027     :code:`exc_swi_7`        SWI 7 instruction executed
0x0030     :code:`exc_unknown_inst` Undefined instruction
0x0031     :code:`exc_type`         Type error in instruction operands
0x0032     :code:`exc_unaligned`    Unaligned memory access
0x0040     :code:`exc_inst_av`      Instruction fetch access violation
0x0041     :code:`exc_mem_av`       Memory access violation
========== ======================== =================================

.. note:: The :code:`csr_eaddr_reg` clears to zero when read, which is the same value as :code:`exc_reset`. This aliasing is not problematic if SW handles resets and exceptions in different code-paths.

Interrupts
----------

Interrupts can occur both in TASK or SCHEDULER mode. When Espresso is in TASK mode, it transfers execution into SCHEDULER mode. When an interrupt occurs in SCHEDULER mode, the execution flow is not modified, but :code:`csr_ecause_reg` is set to :code:`exc_hwi`. This allows SCHEDULER-mode code to poll for interrupts.

The external interrupt input of Espresso is level-sensitive, active low. This means that each interrupt source must have its own interrupt clear logic, and that interrupt handling SW must clear the pending interrupt at the source.

Multiple external interrupt sources can share the interrupt input of Espresso through wired-and logic.

Exception address
-----------------

The :code:`csr_eaddr_reg` register contains the effective logical address for the operation causing the latest exception. This address could be an instruction address (in case of a fetch AV, :code:`swi` instruction or interrupt) or a memory address (in case of a read/write AV).

CSRs
----

================= =========================== ============ ================================
Offset            Name                        Access       Description
================= =========================== ============ ================================
0x400_0014        :code:`csr_ecause_reg`      R-to-clear   Contains the reason for the last exception.
0x400_0018        :code:`csr_eaddr_reg`       R            The effective address that caused the latest exception
================= =========================== ============ ================================

