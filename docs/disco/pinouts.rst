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
20         n_ras_a          Output          Active low row-select, bank A
21         n_ras_b          Output          Active low row-select, bank B
22         n_cas_0          I/O             Active low column select, byte 0
23         n_cas_1          Output          Active low column select, byte 1
24         n_reg_sel        Input           Active low chip-select for register accesses
25         n_we             Output          Active low write-enable
26         sys_clk          Input           System clock input
27         n_rst            Input           Active low reset input
28         n_int            Input           Active low interrupt input
29         n_breq           Output          Active low bus-request output
30         n_bgrant         Input           Active low bus-grant input
31         video_r          Analog          Analog 'red' channel output
32         video_g          Analog          Analog 'green' channel output
33         video_b          Analog          Analog 'blue' channel output
34         video_h_sync     Output          Horizontal video sync output with programmable polarity
35         video_v_sync     Output          Vertical video sync output with programmable polarity
36         audio_l_out      Analog          Audio output left channel
37         audio_r_out_in   Analog          Audio output right channel; audio input
38         video_clk        input           28.63636MHz video clock input
39         VCC              5V power        Power input
40         GND              GND             Ground input
========== ================ =============== ===========

This pinout is highly notional. There's no way for instance that audio pins can be sandwiched between v-sync and video-clk. Honestly, it's highly questionable, if audio will work at any reasonable quality without a dedicated ground.

HDMI version
------------

This is the most likely one I will build. I still include integrated audio in this one, but we shall see... Maybe a dedicated chip will be needed.

.. note:: This chip - being high speed, differential, probably can't be based off of the unic design completely: I doubt the signal integrity over the protection circuit would be sufficiently good. In fact, I'm including extra grounds just to be on the safe(er) side.

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
20         n_ras_a          Output          Active low row-select, bank A
21         n_ras_b          Output          Active low row-select, bank B
22         n_cas_0          I/O             Active low column select, byte 0
23         n_cas_1          Output          Active low column select, byte 1
24         n_reg_sel        Input           Active low chip-select for register accesses
25         n_we             Output          Active low write-enable
26         sys_clk          Input           System clock input
27         n_rst            Input           Active low reset input
28         n_int            Input           Active low interrupt input
29         n_breq           Output          Active low bus-request output
30         n_bgrant         Input           Active low bus-grant input
31         GND              GND             Ground input
32         TMDS Date 2+
33         TMDS Data 2-
34         GND              GND             Ground input
35         TMDS Data 1+
36         TMDS Data 1-
37         GND              GND             Ground input
38         TMDS Data 0+
39         TMDS Data 0-
40         GND              GND             Ground input
41         TMDS Clock+
42         TMDS Clock-
43         GND              GND             Ground input
44         audio_l_out      Analog          Audio output left channel
45         audio_r_out_in   Analog          Audio output right channel; audio input
46         video_clk        input           28.63636MHz video clock input
47         VCC              5V power        Power input
48         GND              GND             Ground input
========== ================ =============== ===========

This pinout still leaves all the side-band signals off, which would need to be provided by an I/O chip (which is fine, I guess). These include the DDC channel and the hot-plug detect.
