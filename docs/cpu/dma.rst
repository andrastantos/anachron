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
:code:`tc`          Output     Active high terminal count signal
=================== ========== ===============================================

The DMA controller supports single- and burst requests: in single request mode, each assertion of a :code:`drq_x` signal will generate a single transaction. In burst mode, subsequent transactions are generated as long as `drq` is kept asserted.

The DMA controller generates and interrupt (if enabled) and asserts the :code:`tc` (terminal-count) output on the last transfer for a DMA channel. After the transfer is complete, the DMA channel becomes inactive and software needs to re-active the channel if further transfers are needed.

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

The base address for these registers is 0x4000_0c00.

========== =========================== ============ ================================
Offset     Name                        Access       Description
========== =========================== ============ ================================
0x00       :code:`DMA_CH_0_ADDR`       R/W          Channel 0 address register (first/current address of transfer)
0x04       :code:`DMA_CH_0_LIMIT`      R/W          Channel 0 limit register (last address of transfer)
0x08       :code:`DMA_CH_0_CONFIG`     R/W          Channel 0 configuration register
0x0c       :code:`DMA_CH_0_STATUS`     R            Channel 0 status register
0x10       :code:`DMA_CH_1_ADDR`       R/W          Channel 1 address register (first/current address of transfer)
0x14       :code:`DMA_CH_1_LIMIT`      R/W          Channel 1 limit register (last address of transfer)
0x18       :code:`DMA_CH_1_CONFIG`     R/W          Channel 1 configuration register
0x1c       :code:`DMA_CH_1_STATUS`     R            Channel 1 status register
0x20       :code:`DMA_CH_2_ADDR`       R/W          Channel 2 address register (first/current address of transfer)
0x24       :code:`DMA_CH_2_LIMIT`      R/W          Channel 2 limit register (last address of transfer)
0x28       :code:`DMA_CH_2_CONFIG`     R/W          Channel 2 configuration register
0x2c       :code:`DMA_CH_2_STATUS`     R            Channel 2 status register
0x30       :code:`DMA_CH_3_ADDR`       R/W          Channel 3 address register (first/current address of transfer)
0x34       :code:`DMA_CH_3_LIMIT`      R/W          Channel 3 limit register (last address of transfer)
0x38       :code:`DMA_CH_3_CONFIG`     R/W          Channel 3 configuration register
0x3c       :code:`DMA_CH_3_STATUS`     R            Channel 3 status register
0x40       :code:`DMA_INT_STAT`        R/W1C        Interrupt status register (for all channels)
========== =========================== ============ ================================

The configuration register layout is identical for all channels:

========== =================================== ================================
Bit-field  Name                                Description
========== =================================== ================================
0          :code:`DMA_CFG_BIT_SINGLE`          If set, the DMA channel operates in single request mode. If cleared, it operates in burst mode
1          :code:`DMA_CFG_BIT_READ_NOT_WRITE`  If set, the DMA channel transfers from memory. If cleared, it transfers to memory
2          :code:`DMA_CFG_BIT_INT_ENABLE`      If set, interrupts are enabled for the DMA channel. If cleared, no interrupts are generated
2          :code:`DMA_CFG_BIT_IS_MASTER`       If set, the DMA channel is used as a bus-master requestor. If cleared, it is a normal DMA channel
3          :code:`DMA_CFG_BIT_HIGH_PRIORITY`   If set, the DMA channel has high arbitration priority. If cleared, it has low priority
4          :code:`DMA_CFG_BIT_REQ_ACTIVE_LOW`  If set, the DMA channel request pin is active low. If cleared, it is active high
5          :code:`DMA_CFG_BIT_REQ_NO_CDC`      If set, the DMA channel assumes a synchronous requestor. If cleared, an asynchronous requestor is assumed
========== =================================== ================================

The status register layout is identical for all channels:

========== ==================================== ================================
Bit-field  Name                                 Description
========== ==================================== ================================
0          :code:`DMA_STAT_BIT_CH_ACTIVE`       If set, the DMA channel is active and will respond to requests. If cleared, it is inactive
1          :code:`DMA_STAT_BIT_CH_REQ_PENDING`  If set, the DMA channel is actively requesting control of the bus. If cleared, it doesn't
2          :code:`DMA_STAT_BIT_CH_INT_PENDING`  If set, the DMA channel is requesting an interrupt. This bit is a copy of the corresponding bit in the :code:`DMA_INT_STAT` register
========== ==================================== ================================

The :code:`DMA_INT_STAT` register contains a single bit for each channel:

========== ============================= ================================
Bit-field  Name                          Description
========== ============================= ================================
0          :code:`DMA_CH_0_INT_PENDING`  If set, DMA channel 0 is requesting an interrupt. Write 1 to clear pending interrupt.
1          :code:`DMA_CH_1_INT_PENDING`  If set, DMA channel 1 is requesting an interrupt. Write 1 to clear pending interrupt.
2          :code:`DMA_CH_2_INT_PENDING`  If set, DMA channel 2 is requesting an interrupt. Write 1 to clear pending interrupt.
3          :code:`DMA_CH_3_INT_PENDING`  If set, DMA channel 3 is requesting an interrupt. Write 1 to clear pending interrupt.
========== ============================= ================================

These bits are set whenever the corresponding DMA channel starts requesting an interrupt. The bits (and the corresponding interrupt request) can be cleared by writing a '1' into the proper bit in the `DMA_INT_STAT` register.

A DMA transfer is programmed by setting the appropriate configuration register bits, the limit register and finally writing the address register. The act of writing the address register will activate the DMA channel.

An active DMA channel is accepting requests as long its address register is less then or equal to its limit register. Upon the last transfer, the :code:`tc` output pin is asserted to signal the peripheral that the DMA transfer completed. At the same time, a CPU interrupt is raised (if interrupts are enabled). The interrupt pending bit reflects the fact that an interrupt is raised. This bit can be cleared by writing a '1' to the appropriate bit of the :code:`DMA_INT_STAT` register.



