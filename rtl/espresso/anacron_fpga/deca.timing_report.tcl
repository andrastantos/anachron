set PRJ anacron_fpga/deca.qpf
set OUT output_files/deca.timing_report.txt
project_open $PRJ
create_timing_netlist
read_sdc
update_timing_netlist
report_sdc -file $OUT
report_clocks -file $OUT -append
report_clock_fmax_summary -file $OUT -append
report_timing -from_clock {ADC_CLK_10} -to_clock {ADC_CLK_10} -setup -npaths 10 -detail summary -multi_corner -file $OUT -append
report_timing -from_clock {MAX10_CLK1_50} -to_clock {MAX10_CLK1_50} -setup -npaths 10 -detail summary -multi_corner -file $OUT -append
report_timing -from_clock {ADC_CLK_10} -to_clock {ADC_CLK_10} -setup -npaths 10 -detail full_path -multi_corner -file $OUT -append
report_timing -from_clock {MAX10_CLK1_50} -to_clock {MAX10_CLK1_50} -setup -npaths 10 -detail full_path -multi_corner -file $OUT -append
