create_clock -name clk -period 10.00 [get_ports {clk}]

#derive_clock_uncertainty

#set_input_delay -clock clk 5 RST

#set_input_delay             -clock clk 2 [get_ports { dram_data[*] } ]
#set_input_delay -clock_fall -clock clk 2 [get_ports { dram_data[*] } ]

set DDR_INPUTS [get_ports { dram_data[*] } ]
set DDR_OUTPUTS [get_ports { dram_data[*] dram_addr[*] dram_n_cas_* } ]

set INPUTS [get_ports { drq[*] dram_n_wait n_int } ]
set OUTPUTS [get_ports { dram_n_nren dram_n_ras_a dram_n_ras_b dram_n_we n_dack[*] tc } ]

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
