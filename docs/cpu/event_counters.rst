Event Counters
==============

Espresso contains a number of event sources and counters. These events and their counters can be used to profile the performance of code or certain aspects of the hardware.

The following events are defined:

================================ =============== ==========================================
Event name                       Event index     Description
================================ =============== ==========================================
:code:`event_clk_cycles`         0               This event occurs every clock cycle
:code:`event_fetch_wait_on_bus`  1               Occurs when the instruction fetch stage waits on the bus interface
:code:`event_decode_wait_on_rf`  2               Occurs when the decode stage is waiting on the register file
:code:`event_mem_wait_on_bus`    3               Occurs when the memory unit waits on the bus interface
:code:`event_branch_taken`       4               Occurs whenever a branch is taken
:code:`event_branch`             5               Occurs when a branch instruction is executed
:code:`event_load`               6               Occurs when a load is performed by the memory unit
:code:`event_store`              7               Occurs when a store is performed by the memory unit
:code:`event_load_or_store`      8               Occurs when either a load or a store is performed by the memory unit
:code:`event_execute`            9               Occurs when an instruction is executed
:code:`event_bus_idle`           10              Occurs when the bus interface is in idle
:code:`event_fetch`              11              Occurs when a word is fetched from memory
:code:`event_fetch_drop`         12              Occurs when a word is dropped from the instruction queue
:code:`event_inst_word`          13              Occurs when a word is handed to instruction decode
================================ =============== ==========================================

These events are counted by a number of event counters. The number of counters is a synthesis-time configuration parameter for Espresso. In it's default configuration there are 8 event counters.

For each event counter, there is a pair of registers: one for selecting the event to count and another to read the number of counted events.

The base address for these CSRs is 0x4000_0404+8*event_counter_idx

================ =================================== ============ ============================================
Offset           Name                                Access       Description
================ =================================== ============ ============================================
0x4000_0404      :code:`event_select_reg_0`          R/W          Selects one of the event sources to count for event counter 0
0x4000_0408      :code:`event_cnt_reg_0`             R            Returns the number of events counted for event counter 0
0x4000_040c      :code:`event_select_reg_1`          R/W          Selects one of the event sources to count for event counter 1
0x4000_0410      :code:`event_cnt_reg_1`             R            Returns the number of events counted for event counter 1
0x4000_0414      :code:`event_select_reg_2`          R/W          Selects one of the event sources to count for event counter 2
0x4000_0418      :code:`event_cnt_reg_2`             R            Returns the number of events counted for event counter 2
0x4000_041c      :code:`event_select_reg_3`          R/W          Selects one of the event sources to count for event counter 3
0x4000_0420      :code:`event_cnt_reg_3`             R            Returns the number of events counted for event counter 3
0x4000_0424      :code:`event_select_reg_4`          R/W          Selects one of the event sources to count for event counter 4
0x4000_0428      :code:`event_cnt_reg_4`             R            Returns the number of events counted for event counter 4
0x4000_042c      :code:`event_select_reg_5`          R/W          Selects one of the event sources to count for event counter 5
0x4000_0430      :code:`event_cnt_reg_5`             R            Returns the number of events counted for event counter 5
0x4000_0434      :code:`event_select_reg_6`          R/W          Selects one of the event sources to count for event counter 6
0x4000_0438      :code:`event_cnt_reg_6`             R            Returns the number of events counted for event counter 6
0x4000_043c      :code:`event_select_reg_7`          R/W          Selects one of the event sources to count for event counter 7
0x4000_0440      :code:`event_cnt_reg_7`             R            Returns the number of events counted for event counter 7
================ =================================== ============ ============================================

There is no way to reset the counter. Instead, the counter value should be read at the beginning of the measurement, then again at the end and subtracted from one another to attain the number of events counted. For frequent events, or long measurements care should be taken for counter overflows. The counters themselves have 20 bits so can count a little over 1 million events before rolling over.

The recommended way of dealing with counter overflows is to regularly read them and use SW-managed accumulators to store the values; Whenever the read value is smaller then the previous value, an overflow has occurred and 2^21 should be added to the accumulator. If the readout periodicity is less then about 1 million clock cycles, it is guaranteed that no more than a single overflow occurs between read-outs.

To allow for precise measurement of code sections, a global event counter enable register is provided. This allows for setup of event counters then a single, atomic write operation to enable all of them. At the end ofr the measurement interval a second write operation can be used to freeze the value of all registers at the exact same clock cycle.

================ ===================== ============ ============================================
Offset           Name                  Access       Description
================ ===================== ============ ============================================
0x4000_0400      :code:`event_enable`  R/W          Writing a '1' enables event counters; a '0' disables counting of events
================ ===================== ============ ============================================
