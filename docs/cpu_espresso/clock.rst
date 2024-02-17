Clock
=====

The clock to Espresso must be 50% duty cycle. The maximum clock frequency supported by Espresso is 20MHz, though in practice, it is limited by the timing requirements of the attached DRAM.

Some standard clock rates depending on DRAM speed-grade:

=========== ========= ========= ========= ========= ========= =========
Part number           uPD41464                       KM41256
----------- ----------------------------- -----------------------------
Speed grade  -80       -10       -12       -10       -12       -15
=========== ========= ========= ========= ========= ========= =========
t_rcd        40ns      50ns       60ns     50ns      60ns      75ns
t_cas        40ns      50ns       60ns     50ns      60ns      75ns
t_cp         30ns      40ns       50ns     45ns      50ns      60ns
t_rp         70ns      90ns       90ns     90ns     100ns     100ns
sys_clk      12.5Mhz   10Mhz      8.3MHz   10Mhz     8.3MHz    6.6MHz
=========== ========= ========= ========= ========= ========= =========

Espresso is a static device, meaning that the clock can be arbitrarily low, even stopped without loosing state in the processor. However, it should be noted, that DRAM refresh is also stopped when the clock to Espresso is. Unless external means are used to maintain DRAM content, stopping or slowing the clock is ill-advised.
