create_clock -name clk -period 100.00 [get_ports {clk}]
create_clock -name clk2 -period 20.00 [get_ports {clk2}]

derive_clock_uncertainty
