#	input logic clk,
#	input logic rst,
#	output logic [10:0] dram_addr,
#	output logic dram_bus_en,
#	input logic [7:0] dram_data_in,
#	output logic [7:0] dram_data_out,
#	output logic dram_data_out_en,
#	output logic dram_n_cas_0,
#	output logic dram_n_cas_1,
#	output logic [3:0] dram_n_dack,
#	output logic dram_n_nren,
#	output logic dram_n_ras_a,
#	output logic dram_n_ras_b,
#	input logic dram_n_wait,
#	output logic dram_n_we,
#	output logic dram_tc,
#
#	input logic [3:0] drq,
#	input logic n_int

create_clock -name clk -period 10.00 [get_ports {clk}]

#derive_clock_uncertainty

#set_input_delay -clock clk 5 RST

#set_input_delay             -clock clk 2 [get_ports { dram_data[*] } ]
#set_input_delay -clock_fall -clock clk 2 [get_ports { dram_data[*] } ]

set DDR_INPUTS [get_ports { dram_data_in[*] } ]
set DDR_OUTPUTS [get_ports { dram_data_out[*] dram_addr[*] dram_n_cas_* } ]

set INPUTS [get_ports { drq[*] dram_n_wait n_int } ]
set OUTPUTS [get_ports { dram_n_nren dram_n_ras_a dram_n_ras_b dram_n_we n_dack[*] tc dram_bus_en dram_data_out_en } ]

set_input_delay -max 3 -clock clk $DDR_INPUTS
set_input_delay -min 2 -clock clk $DDR_INPUTS

#set_multicycle_path -from $DDR_INPUTS 20

set_max_delay 10 -from $DDR_INPUTS
set_min_delay 5  -from $DDR_INPUTS


set_output_delay -max 3 -clock clk $DDR_OUTPUTS
set_output_delay -min 2 -clock clk $DDR_OUTPUTS

#set_multicycle_path -to $DDR_OUTPUTS 20

set_max_delay 10 -to $DDR_OUTPUTS
set_min_delay 5  -to $DDR_OUTPUTS



set_input_delay -clock clk 2 $INPUTS
#set_multicycle_path -from $INPUTS 20
set_output_delay -clock clk 2 $OUTPUTS
#set_multicycle_path -to $OUTPUTS 20
