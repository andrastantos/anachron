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


Dedicated VRAM
==============

Let's decide that we won't have a unified memory architecture: instead we have a dedicated bank of DRAM (one bank of the CPU). This has priority access from the Disco. The other CPU DRAM bank is dedicated to the CPU and Disco doesn't have access to it.

External isolators are used to make sure Disco accesses are not colliding with those of the CPU. These isolators are controlled by the **nBUSY** output.

The CPU also gets it's nWAIT pulled whenever nBUSY is asserted as well as nRAS_B.

The CPU timing is quite a bit tight: after asserting nRAS, it assert nCAS within half a clock-cycle. We need to be able to signal nWAIT within that window. That's about 50ns. However, a single open-collector OR gate should be able to accomplish that even in LS logic.

The handshake is working as follows:

1. Espresso needs to monitor nWAIT during DRAM accesses **on the falling edge of the clock**. If asserted, it needs to stay put in the RAS-only cycle.
   a. This doesn't apply to refresh cycles. Those can go forward.
   b. If nWAIT is asserted, espresso re-samples it on every falling edge, unit it finds it de-asserted. It continues where it left off (i.e. asserting nCAS) after.
   c. This means that nWAIT is combinatorially included in nCAS generation. We need to also combine in a registered version of nWAIT to ensure nCAS doesn't toggle uncontrollably at the end of nWAIT.
2. Disco will have to keep nBUSY asserted all the way to the end of its DRAM burst **including** the precharge cycle at the end. This allows for proper timing for when nBUSY is de-asserted and Espresso gets control of the bus (and has it's nRAS signal already asserted)
3. Disco will have to assert nBUSY on the rising edge of the clock.

How to resolve races?
---------------------
Let's say that Disco and Espresso decided to start a memory transfer on the same cycle! In this case as soon as nBUSY is asserted, the isolators step in, but it's possible that nRAS already went active from Espresso and the row-address is captured by the DRAM. This can be prevented by early-asserting nBUSY, but that brings up another problem: we might create an invalid nRAS cycle on the DRAM. From a logic perspective, this would look like a RAS-only refresh, but we don't respect timing and take nRAS away too early.

This problem cannot be avoided easily. The best we can do is to flip Disco timing by half cycle: start cycles on the falling edge in general. This gives us an interesting option:

Time 0 - falling edge of clock: Disco sample it's own nRAS. If it samples low, CPU access is in progress --> wait (this is a potential priority-inversion, but oh-well). If it samples high, Disco asserts nBUSY, isolating the bus
Time 1 - half cycle after nBUSY got asserted, rising edge of the clock. At this point Disco doesn't do anything, but Espresso might start a new cycle. If it does, nWAIT gets immediately asserted on it, bit it's nRAS is already down.
Time 2 - full cycle after nBUSY got asserted, falling edge of the clock: Disco drives nRAS low, Espresso detects nWAIT and stalls.
Time N - last half-cycle of Disco access, falling edge of the clock: Disco nRAS goes high.
Time N+2 - nBusy gets de-asserted. If at this point Espresso's nRAS was asserted, the isolators dis-engage, and a new falling-edge on nRAS for DRAM is generated. It's important that the addresses are driven by Espresso at this point **tricky timing on isolators**. Since a full clock-cycle has passed since any nRAS activity, precharge is observed. If of course Espresso doesn't drive the bus at this point, the DRAM remains idle.
Time N+3 - this is a rising edge on Espresso. Disco does nothing, Espresso might start a DRAM cycle, if it haven't been waiting already, or it can do what it was doing before: driving nRAS low
Time N+4 - falling edge of the clock: Espresso realizes that nWAIT got removed and continues with its cycle; At the same time Disco samples nRAS and sees the ongoing cycle, not asserting nBUSY.

Quite a convoluted dance, but doable. The bus hand-over takes some time too, and I think it means Disco has to idle one extra cycle between bursts, but seems to be working otherwise.

Except of course the priority inversion: what happens if Disco sees nRAS asserted? It re-samples it on every clock falling edge. Since there's at least one full cycle of idle (precharge really) from Espresso between bursts, it's guaranteed that Disco will see the bus go inactive. At that point it asserts nBUSY, preventing Espresso from starting another burst (to be more precise the burst can start but can't proceed). So really, the inversion only applies to a single burst, not for consecutive ones.

Lastly, we can assume - at least for the more expensive setups - that Espresso doesn't **execute** out of VRAM thus, it's bursts are limited to 32-bit reads and writes, lasting 3 active clock-cycles (plus one for precharge).

Bandwidth
---------

Discos cycles are:
1. Check for bus-access
2. N+1 active cycles
3. Pre-charge

So, if Disco runs on an 8MHz clock (125ns cycle-time), and a burst rate of 16 bytes, it can fetch those 16 bytes in 11 cycles, or 1375ns. That's a 86ns average access time per byte or 11.6MBps. With 32-byte bursts, this improves to 13.5MBps, with 8-byte bursts, it's only 9.1MBps.

============  ===========================  ===========================  ===========================
Burst size    Max data throughput (8MHz)   Max data throughput (10MHz)  Worst-case throughput (10MHz)
============  ===========================  ===========================  ===========================
8              9.1MBps                     11.4MBps                      6.6MBps
16            11.6MBps                     14.5MBps                     10.0MBps
32            13.5MBps                     16.8MBps                     13.3MBps
============  ===========================  ===========================  ===========================

Given that the VGA pixel clock is 25MHz, this still doesn't quite give us VGA (620x480@4bpp) performance. For that, we would need to run at 10MHz **and** 32-byte bursts to be comfortable. This one manages, even if in every burst it gets unlucky and first loses arbitration to Espresso.

**So, it is decided: 10MHz clock, 32-byte burst-rate**

NOTE: since we can make VGA at 4bpp, we can make QVGA at 8bpp without an internal scanline buffer. Or, with an internal scanline buffer, we can shoot for QVGA at 16bpp!

Pinout
------

This change gives us quite a bit though: we can get rid of a number of pins, freeing up enough to only only support DVI, but an I2S interface (sans BCLK, but that's a copy of SYSCLK anyway) as well:

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

NOTE: a 48-pin version would allow for:
- I2S signals for a DAC (SCLK/SDATA_IN/SDATA_OUT/FRAME/MCLK) 5 pins (but saved 2), so +3
- Adding back the lost address bits +2

Memory use for audio
--------------------
How would one handle audio memory accesses? Those would need to go into the blanking periods. Since the horizontal sync-rate is ~15kHz for QVGA (worst case) and ~31kHz for VGA, we won't need more than 3 samples per channel per line. That's 12 bytes per scan-line, or a 15-cycle burst. We have about 100 cycles of blanking, so this is fine.

8 sprites (with 4 bytes each) would take another 40 cycles, still well within timing budget. We might have to be greedy and assert nBusy for the whole duration of sprite fetching, even though it's multiple bursts to make sure we don't incur too much penalty.

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