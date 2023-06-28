Pinouts
=======

According to https://en.wikipedia.org/wiki/Dual_in-line_package:

Common DIP package pin counts are: 24, 28, 32, and 40; less common are 36, 48, 52, and 64. So if we blow over 40 pins, the next step up is 48.

Classic I/O
-----------

========== =========== ===========
Pin Number Pin Name    Description
========== =========== ===========
1          D0          Data bus
2          D1          Data bus
3          D2          Data bus
4          D3          Data bus
5          D4          Data bus
6          D5          Data bus
7          D6          Data bus
8          D7          Data bus
9          A0          Register address bus (data/command port select)
10         nCS         Active low chip-select for register accesses
11         nWE         Active low register write-enable input
12         nRST        Active low reset input
13         nINT        Open collector, active low interrupt output
14         SYS_CLK     System clock input
15         PA_0_EN1_A  Port A bit 0; Quadrature encoder 1 input A
16         PA_1_EN1_B  Port A bit 1; Quadrature encoder 1 input B
17         PA_2_EN2_A  Port A bit 2; Quadrature encoder 2 input A
18         PA_3_EN2_B  Port A bit 3; Quadrature encoder 2 input B
19         PA_4_TMR1   Port A bit 4; Timer input/output 1
20         PA_5_TMR2   Port A bit 5; Timer input/output 2
21         PA_6_SDA    Port A bit 6; I2C data
22         PA_7_SCL    Port A bit 7; I2C clock
23         PB_0_EN2_A  Port B bit 0; Quadrature encoder 3 input A
24         PB_1_EN2_B  Port B bit 1; Quadrature encoder 3 input B
25         PB_2_EN3_A  Port B bit 2; Quadrature encoder 4 input A
26         PB_3_EN3_B  Port B bit 3; Quadrature encoder 4 input B
27         PB_4_TMR2   Port B bit 4; Timer input/output 3
28         PB_5_TMR3   Port B bit 5; Timer input/output 4
29         PB_6        Port B bit 6;
30         PB_7        Port B bit 7;
31         PC_0_TXD    Port C bit 0; serial RX
32         PC_1_RXD    Port C bit 1; serial TX
33         PC_2_RST    Port C bit 2; serial RST/TX_EN
34         PC_3_CTS    Port C bit 3; serial CST
35         PC_4_KB_C   Port C but 4; PS/2 keyboard port clock pin
36         PC_5_KB_D   Port C but 5; PS/2 keyboard port data pin
37         PC_6_MS_C   Port C but 6; PS/2 mouse port clock pin
38         PC_7_MS_D   Port C but 7; PS/2 mouse port data pin
39         VCC         Power input
40         GND         Ground input
========== =========== ===========

Nuvou I/O
---------

========== =========== ===========
Pin Number Pin Name    Description
========== =========== ===========
1          A0          Address bus
2          A1          Address bus
3          A2          Address bus
4          A3          Address bus
5          D0          Data bus
6          D1          Data bus
7          D2          Data bus
8          D3          Data bus
9          D4          Data bus
10         D5          Data bus
11         D6          Data bus
12         D7          Data bus
13         nDRQ        Active low DMA request
14         nDACK       Active low DMA response
15         nDMA_TC     DMA terminal count
16         nCS         Active low chip select
17         nWE         Active low write-enable
18         SYS_CLK     Clock input
19         nRST        Active low reset input
20         nINT        Active low interrupt output
21         D+          USB D+
22         D-          USB D-
23         SD_D0       SD card connector
24         SD_D1       SD card connector
25         SD_D2       SD card connector
26         SD_D3       SD card connector
27         SD_CMD      SD card connector
28         SD_CLK      SD card connector
29         XTAL_IN     48MHz crystal oscillator pins
30         XTAL_OUT    48MHz crystal oscillator pins
31         PA_0_TXD    Port A bit 0; serial RX
32         PA_1_RXD    Port A bit 1; serial TX
33         PA_2_RST    Port A bit 2; serial RST/TX_EN
34         PA_3_CTS    Port A bit 3; serial CST
35         PA_4_KB_C   Port A but 4; PS/2 keyboard port clock pin
36         PA_5_KB_D   Port A but 5; PS/2 keyboard port data pin
37         PA_6_SDA    Port A bit 6; I2C data
38         PA_7_SCL    Port A bit 7; I2C clock
39         VCC         Power input
40         GND         Ground input
========== =========== ===========


Bus extender
------------

========== =========== ===========
Pin Number Pin Name    Description
========== =========== ===========
1          A8_0        Multiplexed address bus
2          A9_1        Multiplexed address bus
3          A10_2       Multiplexed address bus
4          A11_3       Multiplexed address bus
5          A12_4       Multiplexed address bus
6          A13_5       Multiplexed address bus
7          A14_6       Multiplexed address bus
8          A15_7       Multiplexed address bus
9          A17_16      Multiplexed address bus
10         A19_18      Multiplexed address bus, nRAS_C for bank C
11         A20_21      Multiplexed address bus, nRAS_D for bank D
12         D0          Data bus
13         D1          Data bus
14         D2          Data bus
15         D3          Data bus
16         D4          Data bus
17         D5          Data bus
18         D6          Data bus
19         D7          Data bus
20         nRAS_A      Active low row-select, bank A
21         nRAS_B      Active low row-select, bank B
22         nCAS_0      Active low column select, byte 0
23         nCAS_1      Active low column select, byte 1
24         nWE         Active low write-enable
25         SYS_CLK     Clock input
26         nRST        Active low reset input
27         nINT        Active low interrupt output
28         nBREQ_IN    Active low bus-request daisy-chain input
29         nBREQ_OUT   Active low bus-request daisy-chain output
30         nBGRANT     Active low bus-grant input
31         nWAIT       Active low wait-state output
32         nREG_CS     Active low chip-select for register accesses
33         nDRQ_A      DMA channel A request input
34         nDACK_A     DMA channel A acknowledge output
35         nDRQ_B      DMA channel B request input
36         nDACK_B     DMA channel B acknowledge output
37         nDRQ_C      DMA channel C request input
38         nDACK_C     DMA channel C acknowledge output
39         DMA_TC      DMA terminal count output
41         IRQ_A       Interrupt signal A
42         IRQ_B       Interrupt signal B
43         IRQ_C       Interrupt signal C
44         IRQ_D       Interrupt signal D
45         IRQ_E       Interrupt signal E
46
47         VCC         Power input
48         GND         Ground input
========== =========== ===========

