transcript on
if {[file exists gate_work]} {
	vdel -lib gate_work -all
}
vlib gate_work
vmap work gate_work

vlog -sv -work work output_files/sim/deca.svo

vlog -sv -work work sim_top_gate_level.sv

vsim -t 1ps -L altera_ver -L altera_lnsim_ver -L fiftyfivenm_ver -L gate_work -L work -voptargs="+acc"  top

#source fpga_top_dump_all_vcd_nodes.tcl
add wave *
view structure
view signals
run -all
