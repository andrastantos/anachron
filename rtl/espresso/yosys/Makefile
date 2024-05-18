DEVICE = hx8k
PNR_DEVICE = 8k
PNR_PACKAGE = tq144:4k

SOURCES = ../brew_v1.sv ../brew_v1_top.sv
PCF = brew_v1.pcf

all: brew_v1.bin

brew_v1.blif: $(SOURCES)
	yosys -p "synth_ice40 -top BREW_V1 -blif brew_v1.blif" $^

brew_v1.bin: brew_v1.blif brew_v1.pcf
#	arachne-pnr -d $(PNR_DEVICE) -P $(PNR_PACKAGE) -p $(PCF) brew_v1.blif -o brew_v1.asc
	nextpnr-ice40 --$(DEVICE) --package $(PNR_PACKAGE) --pcf $(PCF) brew_v1.blif --asc brew_v1.asc
	icebox_explain brew_v1.asc > brew_v1.ex
	icetime -d $(DEVICE) brew_v1.asc
	icepack brew_v1.asc brew_v1.bin
