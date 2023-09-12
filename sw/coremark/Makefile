.PRECIOUS: %.o %.elf

CFLAGS = -ffunction-sections -fdata-sections -I.. -I. -DITERATIONS=100 -o2
AFLAGS = -ffunction-sections -fdata-sections
LDFLAGS = -Wl,--gc-sections
DRAM_LDFLAGS = $(LDFLAGS) -T ../dram.lds
#ROM_LDFLAGS = $(LDFLAGS) -T ../rom.lds
ROM_LDFLAGS = --gc-sections --script ../rom.lds

ROM_SOURCES=../rom.s
DRAM_SOURCES=core_list_join.cpp core_main.cpp core_matrix.cpp core_state.cpp core_util.cpp core_portme.cpp ee_printf.cpp ../uart.cpp ../sim_utils.cpp ../event_counters.cpp

#brew-none-elf-g++ -O2 -Iespresso_fpga -I. -DFLAGS_STR=\""-O2   -Wl,--gc-sections -T espresso_sim/dram.lds"\" -ffunction-sections -fdata-sections -DITERATIONS=1
#core_list_join.c core_main.c core_matrix.c core_state.c core_util.c espresso_fpga/core_portme.c espresso_fpga/ee_printf.c espresso_fpga/uart.cpp espresso_fpga/event_counters.cpp -o ./coremark.elf -Wl,--gc-sections -T espresso_sim/dram.lds

OBJ_DIR=_obj
BIN_DIR=_bin

DRAM_OBJ_FILES = $(addprefix $(OBJ_DIR)/,$(addsuffix .o,$(basename $(notdir $(DRAM_SOURCES)))))
ROM_OBJ_FILES = $(addprefix $(OBJ_DIR)/,$(addsuffix .o,$(basename $(notdir $(ROM_SOURCES)))))

#all: rom.mef dram.0.mef dram.1.mef
#all: $(BIN_DIR)/dram.elf $(BIN_DIR)/rom.elf
all: $(BIN_DIR)/dram.0.mef $(BIN_DIR)/dram.1.mef $(BIN_DIR)/rom.mef

$(OBJ_DIR)/%.o: %.s
	-mkdir -p $(OBJ_DIR)
	brew-none-elf-gcc $^ -c -o $@

$(OBJ_DIR)/%.o: ../%.s
	-mkdir -p $(OBJ_DIR)
	brew-none-elf-gcc $^ -c -o $@

$(OBJ_DIR)/%.o: %.cpp
	-mkdir -p $(OBJ_DIR)
	brew-none-elf-g++ $^ -c $(CFLAGS) -O2 -o $@

$(OBJ_DIR)/%.o: ../%.cpp
	-mkdir -p $(OBJ_DIR)
	brew-none-elf-g++ $^ -c $(CFLAGS) -O2 -o $@

$(BIN_DIR)/dram.elf: $(DRAM_OBJ_FILES)
	-mkdir -p $(BIN_DIR)
	brew-none-elf-gcc $(DRAM_LDFLAGS) $(DRAM_OBJ_FILES) -o $@

#$(BIN_DIR)/rom.elf: $(ROM_OBJ_FILES)
#	-mkdir -p $(BIN_DIR)
#	brew-none-elf-gcc $(ROM_LDFLAGS) $(ROM_OBJ_FILES) -o $@

$(BIN_DIR)/rom.elf: $(ROM_OBJ_FILES)
	-mkdir -p $(BIN_DIR)
	brew-none-elf-ld $(ROM_LDFLAGS) $(ROM_OBJ_FILES) -o $@

$(BIN_DIR)/rom.mef: $(BIN_DIR)/rom.elf
	../elf2mef $^ rom $(basename $@)

$(BIN_DIR)/dram.0.mef $(BIN_DIR)/dram.1.mef &: $(BIN_DIR)/dram.elf
	../elf2mef $^ dram $(basename $(basename $@))


