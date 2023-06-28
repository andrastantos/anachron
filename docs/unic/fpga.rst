FPGA selection options
======================

There seem to be a lot of options to select from:

#. Intel Max10 series
#. Lattice iCE40 series
#. MicroSemi IGLOO2 series
#. GoWin GW1N series
#. https://www.efinixinc.com/ Trion series


Memory size comparison

================= ==================== =============================================== ============================================================
Vendor/series     BRAM size            BRAM width                                      Notes
================= ==================== =============================================== ============================================================
GoWin GW1N        18kbit               36 (simple dual-port only) 18 (true dual-port)
Intel Max10       9kbit                36
MicroSemi IGLOO2  18kbit               36
MicroSemi IGLOO2  1kbit                18                                              triple-ported, ideal for 2R/1W applications
Lattice iCE40     4kbit                16                                              only simple dual-port supported
================= ==================== =============================================== ============================================================

These are all 3.3V compatible parts, but only GoWin lists LVTTL compatibility. However, LVTTL and LVCMOS33 is the same, it seems. None of them are 5V tolerant though, it seems.

