.. _dma:

DMA engine
==========

Espresso contains a 4-channel DMA controller. These channels have independent request-grand signals and provide a 'terminal-count' output.

The DMA controller supports I/O to memory, memory to I/O and I/O to I/O transfers. Specifically, memory-to-memory DMAs are not supported.

Signal interface
----------------

The following external pins are used to communicate with the DMA controller:

=================== ========== ===============================================
Name                Direction  Description
=================== ========== ===============================================
:code:`drq_0`       Input      Programmable polarity DMA request input for channel 0
:code:`n_dack_0`    Output     Active low polarity DMA acknowledge output for channel 0
:code:`drq_1`       Input      Programmable polarity DMA request input for channel 1
:code:`n_dack_1`    Output     Active low polarity DMA acknowledge output for channel 1
:code:`drq_2`       Input      Programmable polarity DMA request input for channel 2
:code:`n_dack_2`    Output     Active low polarity DMA acknowledge output for channel 2
:code:`drq_3`       Input      Programmable polarity DMA request input for channel 3
:code:`n_dack_3`    Output     Active low polarity DMA acknowledge output for channel 3
:code:`dma_tc`      Output     Active high terminal count signal
=================== ========== ===============================================

The DMA controller supports single- and burst requests: in single request mode, each assertion of a :code:`drq_x` signal will generate a single transaction. In burst mode, subsequent transactions are generated as long as `drq` is kept asserted.

The DMA controller generates and interrupt (if enabled) and asserts the :code:`dma_tc` (terminal-count) output on the last transfer for a DMA channel. After the transfer is complete, the DMA channel becomes inactive and software needs to re-active the channel if further transfers are needed.

The DMA controller supports programmable polarity on the `drq` lines and allows for lower latency by disabling the CDC crossing on them as well. It is important to note that if no CDC circuitry is used, setup and hold times on the `drq` lines must be observed relative to the clock of Espresso: in this case the DMA requestor must be a synchronous peripheral.

Bus-master support
------------------

The DMA channels support bus-master requests, if programmed accordingly. In those cases the `drq` signal associated with the channel serves as a 'bus-request' signal. In response to the request Espresso releases the bus and notifies the bus master through the appropriate `n_dack` output. The external master is expected to keep the `drq` line asserted for the during of the bus activity. When the external master is ready to relinquish the bus, it de-asserts `drq`, which returns control of the bus to Espresso. The DMA controller acknowledges the fact by de-asserting `n_dack`.

Channel priority
----------------

DMA channels can be configured as 'high' or 'low' priority. The DMA controller uses round-robin arbitration among all high- and low-priority channels independently to determine the request to service.

Register interface
------------------

The DMA engine registers are mapped as CSRs. The layout of the registers is as follows:

================= =========================== ============ ================================
Offset            Name                        Access       Description
================= =========================== ============ ================================
0x400_0c00        :code:`dma_cha_0_addr`       R/W          Channel 0 address register (first/current address of transfer)
0x400_0c04        :code:`dma_cha_0_limit`      R/W          Channel 0 limit register (last address of transfer)
0x400_0c08        :code:`dma_cha_0_config`     R/W          Channel 0 configuration register
0x400_0c0c        :code:`dma_cha_0_status`     R            Channel 0 status register
0x400_0c10        :code:`dma_cha_1_addr`       R/W          Channel 1 address register (first/current address of transfer)
0x400_0c14        :code:`dma_cha_1_limit`      R/W          Channel 1 limit register (last address of transfer)
0x400_0c18        :code:`dma_cha_1_config`     R/W          Channel 1 configuration register
0x400_0c1c        :code:`dma_cha_1_status`     R            Channel 1 status register
0x400_0c20        :code:`dma_cha_2_addr`       R/W          Channel 2 address register (first/current address of transfer)
0x400_0c24        :code:`dma_cha_2_limit`      R/W          Channel 2 limit register (last address of transfer)
0x400_0c28        :code:`dma_cha_2_config`     R/W          Channel 2 configuration register
0x400_0c2c        :code:`dma_cha_2_status`     R            Channel 2 status register
0x400_0c30        :code:`dma_cha_3_addr`       R/W          Channel 3 address register (first/current address of transfer)
0x400_0c34        :code:`dma_cha_3_limit`      R/W          Channel 3 limit register (last address of transfer)
0x400_0c38        :code:`dma_cha_3_config`     R/W          Channel 3 configuration register
0x400_0c3c        :code:`dma_cha_3_status`     R            Channel 3 status register
0x400_0c40        :code:`dma_int_stat`        R/W1C        Interrupt status register (for all channels)
================= =========================== ============ ================================

The configuration register layout is identical for all channels:

========== =================================== ================================
Bit-field  Name                                Description
========== =================================== ================================
0          :code:`dma_cfg_bit_single`          If set, the DMA channel operates in single request mode. If cleared, it operates in burst mode
1          :code:`dma_cfg_bit_read_not_write`  If set, the DMA channel transfers from memory. If cleared, it transfers to memory
2          :code:`dma_cfg_bit_int_enable`      If set, interrupts are enabled for the DMA channel. If cleared, no interrupts are generated
2          :code:`dma_cfg_bit_is_master`       If set, the DMA channel is used as a bus-master requestor. If cleared, it is a normal DMA channel
3          :code:`dma_cfg_bit_high_priority`   If set, the DMA channel has high arbitration priority. If cleared, it has low priority
4          :code:`dma_cfg_bit_req_active_low`  If set, the DMA channel request pin is active low. If cleared, it is active high
5          :code:`dma_cfg_bit_req_no_cdc`      If set, the DMA channel assumes a synchronous requestor. If cleared, an asynchronous requestor is assumed
========== =================================== ================================

The status register layout is identical for all channels:

========== ==================================== ================================
Bit-field  Name                                 Description
========== ==================================== ================================
0          :code:`dma_stat_bit_ch_active`       If set, the DMA channel is active and will respond to requests. If cleared, it is inactive
1          :code:`dma_stat_bit_ch_req_pending`  If set, the DMA channel is actively requesting control of the bus. If cleared, it doesn't
2          :code:`dma_stat_bit_ch_int_pending`  If set, the DMA channel is requesting an interrupt. This bit is a copy of the corresponding bit in the :code:`dma_int_stat` register
========== ==================================== ================================

The :code:`dma_int_stat` register contains a single bit for each channel:

========== ============================= ================================
Bit-field  Name                          Description
========== ============================= ================================
0          :code:`dma_ch_0_int_pending`  If set, DMA channel 0 is requesting an interrupt. Write 1 to clear pending interrupt.
1          :code:`dma_ch_1_int_pending`  If set, DMA channel 1 is requesting an interrupt. Write 1 to clear pending interrupt.
2          :code:`dma_ch_2_int_pending`  If set, DMA channel 2 is requesting an interrupt. Write 1 to clear pending interrupt.
3          :code:`dma_ch_3_int_pending`  If set, DMA channel 3 is requesting an interrupt. Write 1 to clear pending interrupt.
========== ============================= ================================

These bits are set whenever the corresponding DMA channel starts requesting an interrupt. The bits (and the corresponding interrupt request) can be cleared by writing a '1' into the proper bit in the `dma_int_stat` register.

A DMA transfer is programmed by setting the appropriate configuration register bits, the limit register and finally writing the address register. The act of writing the address register will activate the DMA channel.

An active DMA channel is accepting requests as long its address register is less then or equal to its limit register. Upon the last transfer, the :code:`dma_tc` output pin is asserted to signal the peripheral that the DMA transfer completed. At the same time, a CPU interrupt is raised (if interrupts are enabled). The interrupt pending bit reflects the fact that an interrupt is raised. This bit can be cleared by writing a '1' to the appropriate bit of the :code:`dma_int_stat` register.

Data transfer during DMA cycles
-------------------------------

The integrated DMA controller is responsible for generating the appropriate bus control signals and addresses. It doesn't generate any data. For an I/O to memory transfer, this means that the DMA controller will generate a write cycle for DRAM while asserting :code:`n_dack_X`. It is dependent on the peripheral to put the data on the data bus and the DRAM to latch that data from the bus.

Conversely, for memory to I/O transfers a DRAM read cycle will be generated, but the addressed DMA peripheral is expected to latch the data presented on the data bus by the DRAM.

.. _wait_states_and_dma_access:


Wait states and DMA access
--------------------------

The timing and the number of wait-states for an I/O device to respond and complete the transfer is determined by the wait-states set in the top four bits of the transfer address. The programmed wait-states are always used, even for DRAM transfer targets. The transfer can be further extended by asserting the :code:`n_wait` signal.

Bus-master support
------------------

Any channel fo the DMA controller can be configured to support an external bus-master. In this setup, the external master request control of the bus by asserting
the :code:`drq_X` signal. Espresso - after completing any active burst and internal arbitration - tri-states all external bus interface pins and acknowledges the request by asserting the associated :code:`n_dack_X` signal as the bus-grant handshake. The external master is in full control of the bus at this point. The :code:`drq_X` signal needs to remain asserted as long as the external master requires control of the bus. Once the external master is ready to relinquish the bus, it de-asserts :code:`drq_X`

