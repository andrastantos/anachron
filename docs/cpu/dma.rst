DMA engine
----------

Espresso contains a 4-channel DMA interface. These channels have independent request-grand signals and provide a 'terminal-count' output.

The electrical interface follows the Intel 8257 DMA controller, used in the original IBM PC machines. The register interface is different and the supported types of transfers is limited.

The DMA controller supports I/O to memory, memory to I/O and I/O to I/O transfers. Specifically, memory-to-memory DMAs are not supported.

The DMA engine supports single- and burst requests: in single request mode, each falling edge of a `drq` signal will generate a single transaction. In burst mode, subsequent transactions are generated as long as `drq` is kept asserted.

The DMA controller generates and interrupt and asserts the `tc` (terminal-count) output on the last transfer for a DMA channel. After the transfer is complete, the DMA channel becomes inactive and software needs to re-active the channel if further transfers are needed.

The DMA channels support bus-master requests, if programmed accordingly. In those cases the `drq` signal associated with the channel serves as a 'bus-request' signal. In response to the request (in coordination with the bus-interface) Espresso releases the bus and notifies the bus muster through the appropriate `n_dack` output. The external master is expected to keep the `drq` line asserted for the during of the bus activity. When the external master is ready to relinquish the bus, it de-asserts `drq`, which returns control of the bus to Espresso. The DMA controller acknowledges the fact by de-asserting `n_dack`.

DMA channels can be configured as 'high' or 'low' priority. The DMA controller uses round-robin arbitration among all high- and low-priority channels independently to determine the request to service.

The DMA controller supports programmable polarity on the `drq` lines and allows for lower latency by disabling the CDC crossing on them as well. It is important to note that if no CDC circuitry is used, setup and hold times on the `drq` lines must be observed relative to the clock of Espresso: in this case the DMA requestor must be a synchronous peripheral.

The DMA engine registers are mapped as CSRs. The layout of the registers is as follows:

========== =================== ================================
Offset     Name                Notes
========== =================== ================================
0x00       DMA_CH_0_ADDR       Channel 0 address register (first/current address of transfer)
0x04       DMA_CH_0_LIMIT      Channel 0 limit register (last address of transfer)
0x08       DMA_CH_0_CONFIG     Channel 0 configuration register
0x0c       DMA_CH_0_STATUS     Channel 0 status register
0x10       DMA_CH_1_ADDR       Channel 1 address register (first/current address of transfer)
0x14       DMA_CH_1_LIMIT      Channel 1 limit register (last address of transfer)
0x18       DMA_CH_1_CONFIG     Channel 1 configuration register
0x1c       DMA_CH_1_STATUS     Channel 1 status register
0x20       DMA_CH_2_ADDR       Channel 2 address register (first/current address of transfer)
0x24       DMA_CH_2_LIMIT      Channel 2 limit register (last address of transfer)
0x28       DMA_CH_2_CONFIG     Channel 2 configuration register
0x2c       DMA_CH_2_STATUS     Channel 2 status register
0x30       DMA_CH_3_ADDR       Channel 3 address register (first/current address of transfer)
0x34       DMA_CH_3_LIMIT      Channel 3 limit register (last address of transfer)
0x38       DMA_CH_3_CONFIG     Channel 3 configuration register
0x3c       DMA_CH_3_STATUS     Channel 3 status register
0x40       DMA_INT_STAT        Interrupt status register (for all channels)
========== =================== ================================


The configuration register layout is identical for all channels:

========== =================== ================================
Bit-field  Name                Notes
========== =================== ================================
0          DMA_SINGLE_BIT      If set, the DMA channel operates in single request mode. If cleared, it operates in burst mode
1          DMA_READ_NOT_WRITE  If set, the DMA channel transfers from memory. If cleared, it transfers to memory
2          DMA_INT_ENABLE      If set, interrupts are enabled for the DMA channel. If cleared, no interrupts are generated
2          DMA_IS_MASTER       If set, the DMA channel is used as a bus-master requestor. If cleared, it is a normal DMA channel
3          DMA_HIGH_PRIORITY   If set, the DMA channel has high arbitration priority. If cleared, it has low priority
4          DMA_REQ_ACTIVE_LOW  If set, the DMA channel request pin is active low. If cleared, it is active high
5          DMA_REQ_NO_CDC      If set, the DMA channel assumes a synchronous requestor. If cleared, an asynchronous requestor is assumed
========== =================== ================================

The status register layout is identical for all channels:

========== =================== ================================
Bit-field  Name                Notes
========== =================== ================================
0          DMA_CH_ACTIVE       If set, the DMA channel is active and will respond to requests. If cleared, it is inactive
1          DMA_CH_REQ_PENDING  If set, the DMA channel is actively requesting control of the bus. If cleared, it doesn't
2          DMA_CH_INT_PENDING  If set, the DMA channel is requesting an interrupt. This bit is a copy of the corresponding bit in the `DMA_INT_STAT` register
========== =================== ================================

The `DMA_INT_STAT` register contains a single bit for each channel:

========== ===================== ================================
Bit-field  Name                Notes
========== ===================== ================================
0          DMA_CH_0_INT_PENDING  If set, DMA channel 0 is requesting an interrupt. Write 1 to clear pending interrupt.
1          DMA_CH_1_INT_PENDING  If set, DMA channel 1 is requesting an interrupt. Write 1 to clear pending interrupt.
2          DMA_CH_2_INT_PENDING  If set, DMA channel 2 is requesting an interrupt. Write 1 to clear pending interrupt.
3          DMA_CH_3_INT_PENDING  If set, DMA channel 3 is requesting an interrupt. Write 1 to clear pending interrupt.
========== ===================== ================================

These bits are set whenever the corresponding DMA channel starts requesting an interrupt. The bits (and the corresponding interrupt request) can be cleared by writing a '1' into the proper bit in the `DMA_INT_STAT` register.

A DMA transfer can be programmed by setting the appropriate configuration register bits, the limit register and finally writing the address register. The act of writing the address register will cause the DMA channel to activate.

An active DMA channel is accepting requests, servicing transfers as long its address register is less then or equal to its limit register. Upon the last transfer, the `tc` output pin is asserted to signal the peripheral that the DMA transfer completed. At the same time, a CPU interrupt is raised (if interrupts are enabled). The interrupt pending bit reflects the fact that an interrupt is raised. This bit can be cleared by writing a '1' to the appropriate bit of the `DMA_INT_STAT` register.



