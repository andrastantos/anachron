Supported bank configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Espresso supports two memory banks, 16 chips in each bank. With various memory sizes, the following configurations could be supported:

1-bit chips:

====== ======== ========= ======================= ================= =============== ============ ===================
Year   Capacity Word size Number of address lines Capacity per bank Number of banks Max capacity Number of RAM chips
====== ======== ========= ======================= ================= =============== ============ ===================
1978   64kbit   1         8                       128kByte          1               128kByte     16
1978   64kbit   1         8                       128kByte          2               256kByte     32
1982   256kbit  1         9                       512kByte          1               512kByte     16
1982   256kbit  1         9                       512kByte          2               1MByte       32
1986   1Mbit    1         10                      2MByte            1               2MByte       16
1986   1Mbit    1         10                      2MByte            2               4MByte       32
1988   4Mbit    1         11                      8MByte            1               8MByte       16
1988   4Mbit    1         11                      8MByte            2               16MByte      32
====== ======== ========= ======================= ================= =============== ============ ===================

4-bit chips:

====== ======== ========= ======================= ================= =============== ============ ===================
Year   Capacity Word size Number of address lines Capacity per bank Number of banks Max capacity Number of RAM chips
====== ======== ========= ======================= ================= =============== ============ ===================
1982   256kbit  4         8                       128kByte          1               128kByte     4
1982   256kbit  4         8                       128kByte          2               256kByte     8
1986   1Mbit    4         9                       512kByte          1               512kByte     4
1986   1Mbit    4         9                       512kByte          2               1MByte       8
1988   4Mbit    4         10                      2MByte            1               1MByte       4
1988   4Mbit    4         10                      2MByte            2               4MByte       8
1991   16Mbit   4         11                      8MByte            1               8MByte       4
1991   16Mbit   4         11                      8MByte            2               16MByte      8
====== ======== ========= ======================= ================= =============== ============ ===================

This shows that we can't really support all the configurations we might want to with either 1- or 4-bit devices alone. The solution to that problem in the industry was the introduction of SIMM modules. This is a later invention, but there's nothing really ground-breaking in the idea: it's just a small PCB with the memory on it and a connector to attach it to the main PCB. This could have happened in '82, it just didn't. So I will say that we 'invented' SIMM modules and as it happens, we stumbled upon exactly the same form-factor and pin-out that the rest of the world standardized on years later.

There were two standards: first, the 32-pin, 9-bit modules were popular, later the 72-pin, 36 bit ones became vogue. With certain limitations, Anachron can support both: on a 72-pin module, only one side can be utilized, cutting the supported memory in half for double-sided modules.

