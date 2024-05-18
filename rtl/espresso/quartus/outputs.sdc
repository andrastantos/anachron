#set_output_delay -clock { clk } -add_delay 0 [get_ports { insn_16_bit insn_32_bit insn_branch }]
#set_output_delay -clock clk -add_delay 0 [all_outputs]
