create_clock -name ADC_CLK_10 -period 100.00 [get_ports {ADC_CLK_10}]
#create_clock -name clk_40 -period 25.00 [get_ports {*DecaTop*clk2}]

## Set input delays (for 100ns part https://www.jameco.com/Jameco/Products/ProdDS/2288063.pdf)
## Data from CAS: t_CAC. CAS is delayed by half of a 40MHz clock, so t_CAC counts from there.
#set_input_delay  -clock { ADC_CLK_10 } -clock_fall -max 25+12.5+5 [get_ports {????}]
#set_input_delay  -clock { ADC_CLK_10 }             -max 25+12.5+5 [get_ports {????}]
## n_wait input: it's sampled on the rising edge of the 10MHz clock, but can't be driven before CAS is active.
##               let's allow for 50ns of extra address decode latency
#set_input_delay  -clock { ADC_CLK_10 }             -max 50+12.5+5 [get_ports {????}]
## Data output: data should be stable before CAS is driven
#set_output_delay -clock { ADC_CLK_10 }             -max 12.5    [get_ports {????}]
## Control output: control should arrive very quickly after the 40MHz clock edge
#set_output_delay -clock { clk_40 }     -clock_fall -max 5       [get_ports {????}]

#create_clock -name MAX10_CLK1_50 -period 20.00 [get_ports {MAX10_CLK1_50}]
#create_clock -name clk -period 100.00 [get_ports {*DecaTop*clk}]
#create_clock -name clk2 -period 20.00 [get_ports {*DecaTop*clk2}]

# Cut cross-clock-domain analysys between our fast clock (clk2) and our slow clock (clk)
#set_clock_groups -asynchronous -group [get_clocks {clk ADC_CLK_10}] -group [get_clocks {clk MAX10_CLK1_50}]

# These are the interface signals on the Brew CPU. Some of these are going
# through a CDC to reach the faster fpga_system clock.
#
#	input logic clk,
#	input logic rst,
#	output logic [10:0] dram_addr,      <-- Needs CDC
#	output logic dram_bus_en,           <-- Not used, but would need CDC
#	input logic [7:0] dram_data_in,     <-- comes from fast clock
#	output logic [7:0] dram_data_out,   <-- Needs CDC
#	output logic dram_data_out_en,      <-- Not used, but would need CDC
#	output logic dram_n_cas_0,          <-- Needs CDC
#	output logic dram_n_cas_1,          <-- Needs CDC
#	output logic [3:0] dram_n_dack,     <-- Not used
#	output logic dram_n_nren,           <-- Needs CDC
#	output logic dram_n_ras_a,          <-- Needs CDC
#	output logic dram_n_ras_b,          <-- Needs CDC
#	input logic dram_n_wait,            <-- comes from fast clock, but not used
#	output logic dram_n_we,             <-- Needs CDC
#	output logic dram_tc,               <-- Not used
#
#	input logic [3:0] drq,              <-- Not used
#	input logic n_int                   <-- Async, I think has CDC regs in brew, or at least should. At any rate, not used at the moment.

# What we want is that address and data to be stable on the falling edge or RAS/CAS/NREN.
# So we set a maximum net-delay on these pins, while we set a *minimum* on RAS/CAS/NREN.
# We also are setting a skew between address/data/nWE to make sure they are roughly changign values at the same time.

# The idea is coming from here: https://www.intel.com/content/www/us/en/docs/programmable/683353/21-3/clock-domain-crossing-constraint-guidelines.html
# If any of these settings generate zero hits, it can be found by searching for 'set_net_delay' in the output messages from Quartus.
# The problem is that these constraints are applied on the optimized netlist, so registers that get optimized away generate this warning.
# For now, they're commented out, but that's not a long-term solution.

#set_max_delay -from [get_registers {*bus_if*data_out_high[*]}] -to [get_registers {*system*ext_if_data_out_nr[*]}] 10
#set_max_delay -from [get_registers {*bus_if*data_out_low[*]}]  -to [get_registers {*system*ext_if_data_out_nr[*]}] 10
#set_max_delay -from [get_registers {*bus_if*data_out_high[*]}] -to [get_registers {*system*ext_if_data_out_r[*]}] 10
#set_max_delay -from [get_registers {*bus_if*data_out_low[*]}]  -to [get_registers {*system*ext_if_data_out_r[*]}] 10
#
#set_max_delay -from [get_registers {*bus_if*col_addr* *bus_if*row_addr*}] -to [get_registers {*system*ext_if_addr*}] 10
#
#set_max_delay -from [get_registers {*bus_if*read_not_write}]  -to [get_registers {*system*ext_if_n_we}] 10
#
##set_max_delay -from [get_registers {FpgaTop:fpga_top|BrewV1Top:brew|brew_BusIf:bus_if|n_dack[*]}] -to [get_registers {FpgaTop:fpga_top|FpgaSystem:system|ext_if_n_dack[*]}] 10
##set_max_delay -from [get_registers {FpgaTop:fpga_top|BrewV1Top:brew|brew_BusIf:bus_if|tc}] -to [get_registers {FpgaTop:fpga_top|FpgaSystem:system|ext_if_tc}] 10
#
##set_max_delay -from [get_registers {FpgaTop:fpga_top|BrewV1Top:brew|brew_BusIf:bus_if|data_out_en}] -to [get_registers {FpgaTop:fpga_top|FpgaSystem:system|ext_if_data_out_en}] 10
#
#set_min_delay -from [get_registers {*bus_if*n_nren}]  -to [get_registers {*system*ext_if_n_nren}] 10
#set_min_delay -from [get_registers {*bus_if*dram_ras_a}] -to [get_registers {*system*ext_if_n_ras_a}] 10
##set_min_delay -from [get_registers {*bus_if*dram_ras_b}] -to [get_registers {*system*ext_if_n_ras_b}] 10
#set_min_delay -from [get_registers {*bus_if*cas_n_window_a_0 *bus_if*cas_n_window_b_0 *bus_if*nr_n_cas_0}] -to [get_registers {*system*ext_if_n_cas_0}] 10
#set_min_delay -from [get_registers {*bus_if*cas_n_window_b_1 *bus_if*cas_n_window_c_1 *bus_if*nr_n_cas_1}] -to [get_registers {*system*ext_if_n_cas_1}] 10
#
#set_max_delay -from [get_registers {*bus_if*n_nren}]  -to [get_registers {*system*ext_if_n_nren}] 18
#set_max_delay -from [get_registers {*bus_if*dram_ras_a}] -to [get_registers {*system*ext_if_n_ras_a}] 18
##set_max_delay -from [get_registers {*bus_if*dram_ras_b}] -to [get_registers {*system*ext_if_n_ras_b}] 18
#set_max_delay -from [get_registers {*bus_if*cas_n_window_a_0 *bus_if*cas_n_window_b_0 *bus_if*nr_n_cas_0}] -to [get_registers {*system*ext_if_n_cas_0}] 18
#set_max_delay -from [get_registers {*bus_if*cas_n_window_b_1 *bus_if*cas_n_window_c_1 *bus_if*nr_n_cas_1}] -to [get_registers {*system*ext_if_n_cas_1}] 18
#
##        ext_if_bus_en = Reg(self.brew_if.bus_en, clock_port=self.clk2)
#
## set_max_skew -from [get_keepers {data_a[*]}] -to [get_keepers {data_b[*]}] -get_skew_value_from_clock_period src_clock_period -skew_value_multiplier 0.8
#set_max_skew -from [get_keepers { \
#    *bus_if*data_out_high[*] \
#    *bus_if*data_out_low[*] \
#    *bus_if*col_addr* \
#    *bus_if*row_addr* \
#    *bus_if*read_not_write \
#}] -to [get_keepers { \
#    *system*ext_if_data_out_nr[*] \
#    *system*ext_if_data_out_r[*] \
#    *system*ext_if_addr* \
#    *system*ext_if_n_we
#}] 5
#
## We'll make sure that the CAS/RAS/NREN lines are really kept close to each other.
#set_max_skew -from [get_keepers { \
#    *bus_if*n_nren,
#    *bus_if*dram_ras_a,
#    *bus_if*dram_ras_b,
#    *bus_if*cas_n_window_a_0 *bus_if*cas_n_window_b_0 *bus_if*nr_n_cas_0 \
#    *bus_if*cas_n_window_b_1 *bus_if*cas_n_window_c_1 *bus_if*nr_n_cas_1 \
#}] -to [get_keepers { \
#    *system*ext_if_n_nren \
#    *system*ext_if_n_ras_a \
#    *system*ext_if_n_ras_b \
#    *system*ext_if_n_cas_0 \
#    *system*ext_if_n_cas_1 \
#}] 2

derive_clock_uncertainty
