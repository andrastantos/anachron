Booting
=======

Espresso boots upon power-on or an external reset.

These conditions cause the processor start executing from address 0, in SCHEDULER mode. CSRs assume their reset value. Processor registers have undefined values.

When a SCHEDULER-mode exception occurs, Espresso starts executing from address 0, which is the same as the reset vector. System software can distinguish between the two conditions by examining the :code:`ecause` register: it reads 0 for reset and non-zero for SCHEDULER-mode exceptions.

