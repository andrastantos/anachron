//Copyright (C)2014-2023 GOWIN Semiconductor Corporation.
//All rights reserved.
//File Title: Timing Constraints file
//GOWIN Version: 1.9.9 Beta-1
//Created Time: 2023-05-31 17:33:24
create_clock -name CLK_IN_27MHZ -period 37.037 -waveform {0 18.518} [get_ports {CLK_IN_27MHZ}]
create_clock -name clk -period 100 -waveform {0 50} [get_pins {clk_div/clkdiv_inst/CLKOUT}]
create_clock -name clk2 -period 20 -waveform {0 10} [get_pins {pll/rpll_inst/CLKOUT}]
