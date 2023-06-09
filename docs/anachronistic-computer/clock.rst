.. _clock_rates:

Clock
=====

As we will see, we will want about 12.6MBps of transfer rate for 320x240 8bpp resolution. That would be 160ns between video accesses over a 16-bit bus.

Looking at :ref:`average access times<average_access_times>` table, and comparing it with :ref:`the proposed DRAM timings<dram_timing>` we will support two clock speeds.

1. We will pretend that early version of our dream machine is clocked at 12.5MHz/10MHz/8MHz for the three common speed-grades of page-mode DRAMs.
2. A later revision of the machine would have supported FPM memory, running at double the clock-rate: 25MHz/20MHz/16MHz.

