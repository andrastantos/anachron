create_clock -name clk -period 10.00 [get_ports {clk}]

#derive_clock_uncertainty

#set_input_delay -clock clk 5 RST

#set_input_delay             -clock clk 2 [get_ports { DRAM_DATA[*] } ]
#set_input_delay -clock_fall -clock clk 2 [get_ports { DRAM_DATA[*] } ]

set_input_delay -max 3 -clock clk [get_ports { DRAM_DATA[*]} ]
set_input_delay -min 2 -clock clk [get_ports { DRAM_DATA[*]} ]

set_max_delay 10 -from [get_ports { DRAM_DATA[*] } ]
set_min_delay 5  -from [get_ports { DRAM_DATA[*] } ]

set_input_delay             -clock clk 5 DRAM_nWAIT
set_input_delay             -clock clk 5 drq[0]
set_input_delay             -clock clk 5 drq[1]
set_input_delay             -clock clk 5 drq[2]
set_input_delay             -clock clk 5 drq[3]
set_input_delay             -clock clk 5 n_int

#set_output_delay             -clock clk 2 [get_ports { DRAM_DATA[*] } ]
#set_output_delay -clock_fall -clock clk 2 [get_ports { DRAM_DATA[*] } ]

set_output_delay -max 3 -clock clk [get_ports { DRAM_DATA[*]} ]
set_output_delay -min 2 -clock clk [get_ports { DRAM_DATA[*]} ]

set_max_delay 10 -to [get_ports { DRAM_DATA[*] } ]
set_min_delay 5  -to [get_ports { DRAM_DATA[*] } ]

set_output_delay -max 3 -clock clk [get_ports { DRAM_ADDR[*]} ]
set_output_delay -min 2 -clock clk [get_ports { DRAM_ADDR[*]} ]

set_max_delay 10 -to [get_ports { DRAM_ADDR[*] } ]
set_min_delay 5  -to [get_ports { DRAM_ADDR[*] } ]

set_output_delay -max 3 -clock clk [get_ports { DRAM_nCAS_*} ]
set_output_delay -min 2 -clock clk [get_ports { DRAM_nCAS_*} ]

set_max_delay 10 -to [get_ports { DRAM_nCAS_* } ]
set_min_delay 5  -to [get_ports { DRAM_nCAS_* } ]

set_output_delay             -clock clk 5 DRAM_nNREN
set_output_delay             -clock clk 5 DRAM_nRAS_A
set_output_delay             -clock clk 5 DRAM_nRAS_B
#set_output_delay             -clock clk 2 DRAM_nCAS_0
#set_output_delay -clock_fall -clock clk 2 DRAM_nCAS_0
#set_output_delay             -clock clk 2 DRAM_nCAS_1
#set_output_delay -clock_fall -clock clk 2 DRAM_nCAS_1
#set_output_delay             -clock clk 2 [get_ports { DRAM_ADDR[*]} ]
#set_output_delay -clock_fall -clock clk 2 [get_ports { DRAM_ADDR[*]} ]
set_output_delay             -clock clk 5 DRAM_nWE
set_output_delay             -clock clk 5 n_dack[0]
set_output_delay             -clock clk 5 n_dack[1]
set_output_delay             -clock clk 5 n_dack[2]
set_output_delay             -clock clk 5 n_dack[3]
set_output_delay             -clock clk 5 tc
