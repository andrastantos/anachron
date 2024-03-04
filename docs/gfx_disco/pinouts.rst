Pinouts
=======

Disco uses a standard 40-pin DIP package and supports HDMI (DVI really) video and I2S audio outputs. Due to the limited number of pins, the I2S interface uses SYSCLK as the I2C bit-clock signal. It also depends on other chips to implement HPD, CEC and DDC functionality needed for a full HDMI implementation.

The addressable memory is 512kBytes, driven by nine (multiplexed) address pins and two n_cas signals.

========== ================ =============== ===========
Pin Number Pin Name         Pin Direction   Description
========== ================ =============== ===========
1          TMDS Data 2+     Output          HDMI/DVI signal
2          TMDS Data 2-     Output          HDMI/DVI signal
3          TMDS Data 1+     Output          HDMI/DVI signal
4          TMDS Data 1-     Output          HDMI/DVI signal
5          TMDS Data 0+     Output          HDMI/DVI signal
6          TMDS Data 0-     Output          HDMI/DVI signal
7          TMDS Clock+      Output          HDMI/DVI signal
8          TMDS Clock-      Output          HDMI/DVI signal
9          a0               I/O             Multiplexed address bus
10         a1               I/O             Multiplexed address bus
11         a2               I/O             Multiplexed address bus
12         a3               I/O             Multiplexed address bus
13         a4               I/O             Multiplexed address bus
14         a5               I/O             Multiplexed address bus
15         a6               I/O             Multiplexed address bus
16         a7               I/O             Multiplexed address bus
17         a8               I/O             Multiplexed address bus
18         video_clk        input           ???MHz video clock input
19         audio_sfrm       Output          I2S Audio output frame signal (clock is sys_clk)
20         GND              GND             Ground input

21         audio_sdata_out  Output          I2S Audio output data signal (clock is sys_clk)
22         audio_sdata_in   Input           I2S Audio data input signal (clock is sys_clk)
23         n_ras_a          Output          Active low row-select, bank A
24         n_cas_0          I/O             Active low column select, byte 0
25         n_cas_1          Output          Active low column select, byte 1
26         n_reg_sel        Input           Active low chip-select for register accesses
27         n_we             Output          Active low write-enable
28         n_rst            Input           Active low reset input
29         sys_clk          Input           System clock input
30         n_int            Input           Active low interrupt input
31         n_busy           Output          Active low signal that VRAM is busy
32         d0               I/O             Data bus
33         d1               I/O             Data bus
34         d2               I/O             Data bus
35         d3               I/O             Data bus
36         d4               I/O             Data bus
37         d5               I/O             Data bus
38         d6               I/O             Data bus
39         d7               I/O             Data bus
40         VCC              5V power        Power input
========== ================ =============== ===========

NOTE: pinout is such that UnIC diff pairs are mapped to HDMI signals. Other variations are certainly possible, but pinout is not 100% arbitrary.

