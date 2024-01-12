Pinouts
=======

I haven't quite decided on the pinout. Here are a few variants:

Combined graphics/sound, analog signals
---------------------------------------

This would have been the most likely pinout to use in the day.

========== ================ =============== ===========
Pin Number Pin Name         Pin Direction   Description
========== ================ =============== ===========
1          a0               I/O             Multiplexed address bus
2          a1               I/O             Multiplexed address bus
3          a2               I/O             Multiplexed address bus
4          a3               I/O             Multiplexed address bus
5          a4               I/O             Multiplexed address bus
6          a5               I/O             Multiplexed address bus
7          a6               I/O             Multiplexed address bus
8          a7               I/O             Multiplexed address bus
9          a8               I/O             Multiplexed address bus
10         a9               I/O             Multiplexed address bus
11         a10              I/O             Multiplexed address bus
12         d0               I/O             Data bus
13         d1               I/O             Data bus
14         d2               I/O             Data bus
15         d3               I/O             Data bus
16         d4               I/O             Data bus
17         d5               I/O             Data bus
18         d6               I/O             Data bus
19         d7               I/O             Data bus
20         GND              GND             Ground input
21         n_ras_a          Output          Active low row-select, bank A
22         n_ras_b          Output          Active low row-select, bank B
23         n_cas_0          I/O             Active low column select, byte 0
24         n_cas_1          Output          Active low column select, byte 1
25         n_reg_sel        Input           Active low chip-select for register accesses
26         n_we             Output          Active low write-enable
27         sys_clk          Input           System clock input
28         n_rst            Input           Active low reset input
29         n_int            Input           Active low interrupt input
30         n_breq           Output          Active low bus-request output
31         n_bgrant         Input           Active low bus-grant input
32         video_r          Analog          Analog 'red' channel output
33         video_g          Analog          Analog 'green' channel output
34         video_b          Analog          Analog 'blue' channel output
35         video_h_sync     Output          Horizontal video sync output with programmable polarity
36         video_v_sync     Output          Vertical video sync output with programmable polarity
37         audio_l_out      Analog          Audio output left channel
38         audio_r_out_in   Analog          Audio output right channel; audio input
39         video_clk        input           28.63636MHz video clock input
40         VCC              5V power        Power input
========== ================ =============== ===========

This pinout is highly notional. There's no way for instance that audio pins can be sandwiched between v-sync and video-clk. Honestly, it's highly questionable, if audio will work at any reasonable quality without a dedicated ground.


Single-bank DRAM and HDMI
=========================

Let's decide that we won't allow addressing both DRAM banks from the video chip. This puts some restrictions on what memory can be used for frame-buffers, but the payoff is rather large:

1. We can have dedicated VRAM (if dual-bank memories are used).
2. We can have shared DRAM in a single-bank (i.e. cheap computer) config.

I'm not sure if it's possible to upgrade one config to the other yet, but that's not a huge issue.

In either case, the video controller needs to only access a single bank, something that's also smaller then what Espresso supports: up to 512k. (In the single-bank config, the to address bits need to be handled somehow, which might be annoying.)

This means that only A0..A8 are needed, so the top 2 address bits can be removed. We would only have a single bank, so the second RAS can be removed as well.

Hand-shaking with Espresso is very different in the two modes, but either way, need two pins:

1. Dedicated VRAM:
   a. nWAIT: we need to be able to hold off CPU access to registers when the bus is not accessible.
   b. nBUSY: we need to prevent the CPU from accessing video ram when we need it.
2. Shared memory:
   a. nBRQ: request bus from the CPU
   b. nBGNT: bus grant signal from the CPU

Overall, we've saved 3 pins.

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

21         audio_sdata      Output          I2S Audio output data signal (clock is sys_clk)
22         n_ras_a          Output          Active low row-select, bank A
23         n_cas_0          I/O             Active low column select, byte 0
24         n_cas_1          Output          Active low column select, byte 1
25         n_reg_sel        Input           Active low chip-select for register accesses
26         n_we             Output          Active low write-enable
27         n_rst            Input           Active low reset input
28         sys_clk          Input           System clock input
29         n_int            Input           Active low interrupt input
30         busy/brq         Output          Active high signal that VRAM is busy; bus request output
31         n_wait/n_bgnt    I/O             Active low, open-drain signal to delay I/O transfer completion; bus grant input
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

NOTE: a 48-pin version would allow for:
- I2S signals for a DAC (SCLK/SDATA_IN/SDATA_OUT/FRAME/MCLK) 5 pins (but saved 2), so +3
- Adding back the lost address bits +2
With this, HDMI output and mono Audio is possible, with an extra GND for audio.

For digital audio, S/PDIF in/out could be used on the two audio pins - that's about 3Mbps for stereo 48kHz audio, so plenty. And easily over-sampled on the receiver end for a digital CDR.
Overall the standard is rather simple, it seems as long we we won't bother ourselves with DRM. Resources:

https://www.st.com/resource/en/application_note/an5073-receiving-spdif-audio-stream-with-the-stm32f4f7h7-series-stmicroelectronics.pdf
https://www.nti-audio.com/Portals/0/data/en/NTi-Audio-AppNote-AES3-AES-EBU.pdf
https://opencores.org/websvn/filedetails?repname=spdif_interface&path=%2Fspdif_interface%2Ftrunk%2Fdoc%2Fspdif.pdf&rev=2
https://inst.eecs.berkeley.edu/~cs150/fa01/labs/project/SPDIF_explanation.pdf

Upon power-up, the chip would start in VRAM mode (i.e. busy/n_wait mode), but, crucially, it doesn't actually drive video. As such, it never asserts busy and doesn't drive n_wait low either.

In either use-case, the chip will accept register reads/writes and will no interfere with the operation of Espresso. Through register writes, the appropriate mode can be configured, after which the proper handshaking will become activated.

To be fair, HDMI is rather orthogonal to the problem of single-bank support.

The curious case of missing address bits
----------------------------------------

What to do about the missing address bits?

This is a problem in the single-bank setup.

Espresso uses the following muxing scheme when talking to DRAM:

=========== =========== =========
Pin Name     DRAM accesses
----------- ---------------------
             row         col
=========== =========== =========
a[0]         addr[9]     addr[1]
a[1]         addr[10]    addr[2]
a[2]         addr[11]    addr[3]
a[3]         addr[12]    addr[4]
a[4]         addr[13]    addr[5]
a[5]         addr[14]    addr[6]
a[6]         addr[15]    addr[7]
a[7]         addr[16]    addr[8]
a[8]         addr[18]    addr[17]
a[9]         addr[20]    addr[19]
a[10]        addr[22]    addr[21]
=========== =========== =========

The video controller thus is missing addr[22:19], four address bits. If these bits are pulled low, video memory will reside in the lowest physical address region. If pulled high, it will reside in the highest section.

Either way, if memory size is smaller than the maximum addressable, the previous statement holds true. I'm thinking adding two GPIOs to drive the top-most two address bits. That allows for some strange in-the-middle modes. Or, a single GPIO with resistors connecting to the two missing address lines, generating programmable pull-ups or pull-downs. This allows for deferring the decision to later.

BTW: the two missing address bits can be gained back by ditching audio (or embedding it in HDMI).