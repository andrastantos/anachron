#set_input_delay -clock { clk } -add_delay 5 [get_ports {insn[*] rst}]
#set_input_delay -clock clk -add_delay 0 [all_inputs]
