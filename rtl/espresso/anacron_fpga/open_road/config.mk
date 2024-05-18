# OpenRoad really doesn't like tri-state pins. It SEGVs on them in the middle of the flow
# Most likely we would need to instantiate tri-state I/O pads and drive the enable pins
# OpenRoad also *really* doesn't like 'initial' statements with non-constant expressions.
# This would be understandable, would such expressions *in the hiararchy* not resolve to
# something constant, but I digress. For now I've patched up the source code to exclude
# those, but every re-generation will have these problems and in general: Silicon should
# take care of these.
#
# Logs are saved to some God-forsaken location: 
#   ~/Work/vlsi/tools/OpenROAD-flow-scripts/flow/logs/sky130hd/BrewV1Top/base
#
# A tutorial of how OpenRoad works:
#   https://openroad-flow-scripts.readthedocs.io/en/latest/tutorials/FlowTutorial.html

export DESIGN_NAME            = BrewV1Top
export PLATFORM               = sky130hd
export SRC_PATH               = ~/brew/rtl/v1/anacron_fpga

#export CORNER                 = tc

#export VERILOG_FILES          = ./designs/src/$(DESIGN_NAME)/brew_v1.sv ./designs/src/$(DESIGN_NAME)/brew_v1_top.sv
#export SDC_FILE               = ./designs/$(PLATFORM)/$(DESIGN_NAME)/constraint.sdc
#export VERILOG_FILES          = $(SRC_PATH)/brew_v1.sv $(SRC_PATH)/brew_v1_top.sv
#export VERILOG_FILES          = $(SRC_PATH)/brew.sv $(SRC_PATH)/open_road/open_road_top.sv
export VERILOG_FILES          = $(SRC_PATH)/brew.sv
export SDC_FILE               = $(SRC_PATH)/open_road/open_road_top.sdc

#export PLACE_DENSITY          = 0.70
#export DIE_AREA               = 0 0 17 17
#export CORE_AREA              = 1.08 1.08 16 16

# Adders degrade ibex setup repair
export ADDER_MAP_FILE :=

export CORE_UTILIZATION = 45
export PLACE_DENSITY_LB_ADDON = 0.2
