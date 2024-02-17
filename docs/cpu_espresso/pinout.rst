Pinout
======

Espresso is packaged in a 40-pin DIP package. All signals follow the 3.3V CMOS (TTL compatible) standard and are 5V tolerant.

Espresso uses a single 5V power supply.

Espresso is implemented using the UNiC virtual chip technology

========== =========== =============== ===========
Pin Number Pin Name    Pin Direction   Description
========== =========== =============== ===========
1          a0          Output          Multiplexed address bus
2          a1          Output          Multiplexed address bus
3          a2          Output          Multiplexed address bus
4          a3          Output          Multiplexed address bus
5          a4          Output          Multiplexed address bus
6          a5          Output          Multiplexed address bus
7          a6          Output          Multiplexed address bus
8          a7          Output          Multiplexed address bus
9          a8          Output          Multiplexed address bus
10         a9          Output          Multiplexed address bus
11         a10         Output          Multiplexed address bus
12         d0          I/O             Data bus
13         d1          I/O             Data bus
14         d2          I/O             Data bus
15         d3          I/O             Data bus
16         d4          I/O             Data bus
17         d5          I/O             Data bus
18         d6          I/O             Data bus
19         d7          I/O             Data bus
20         GND         GND             Ground input
21         n_ras_a     Output          Active low row-select, bank A
22         n_ras_b     Output          Active low row-select, bank B
23         n_cas_0     Output          Active low column select, byte 0
24         n_cas_1     Output          Active low column select, byte 1
25         n_nren      Output          Active low non-DRAM bus cycle qualifier
26         n_we        Output          Active low write-enable
27         n_wait      Input           Active low wait-state input
28         sys_clk     Input           Clock input
29         n_rst       Input           Active low reset input
30         n_int       Input           Active low interrupt input
31         drq_0       Input           Active high DMA channel 0 request input
32         n_dack_0    Output          Active low DMA channel 0 grant output
33         drq_1       Input           Active high DMA channel 1 request input
34         n_dack_1    Output          Active low DMA channel 1 grant output
35         drq_2       Input           Active high DMA channel 2 request input
36         n_dack_2    Output          Active low DMA channel 2 grant output
37         drq_3       Input           Active high DMA channel 3 request input
38         n_dack_3    Output          Active low DMA channel 3 grant output
39         dma_tc      Output          Active high DMA terminal count output
40         VCC         5V power        Power input
========== =========== =============== ===========

