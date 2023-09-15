.PRECIOUS: %.o %.elf

SW_BASE ?= ..
CFLAGS += -ffunction-sections -fdata-sections -I$(SW_BASE)
AFLAGS += -ffunction-sections -fdata-sections
LDFLAGS += -Wl,--gc-sections
DRAM_LDFLAGS = $(LDFLAGS) -T $(SW_BASE)/dram.lds
ROM_LDFLAGS = $(LDFLAGS) -T $(SW_BASE)/rom.lds
ifneq ($(TARGET),rom)
  ROM_LDFLAGS += -nostdlib
endif

RTL?=../../rtl/v1/anacron_fpga

all: rom_bin dram_bin

run: all
	cp $(BIN_DIR)/dram.0.mef $(RTL)/
	cp $(BIN_DIR)/dram.1.mef $(RTL)/
	cp $(BIN_DIR)/rom.mef $(RTL)/
	cd $(RTL)
	./run

OBJ_DIR=_obj
BIN_DIR=_bin

DRAM_OBJ_FILES = $(addprefix $(OBJ_DIR)/,$(addsuffix .o,$(basename $(notdir $(DRAM_SOURCES)))))
ROM_OBJ_FILES = $(addprefix $(OBJ_DIR)/,$(addsuffix .o,$(basename $(notdir $(ROM_SOURCES)))))

dram_bin: $(BIN_DIR)/dram.0.mef $(BIN_DIR)/dram.1.mef
rom_bin: $(BIN_DIR)/rom.mef

$(OBJ_DIR)/%.o: %.s
	-mkdir -p $(OBJ_DIR)
	brew-none-elf-gcc $^ -c -o $@

$(OBJ_DIR)/%.o: ../%.s
	-mkdir -p $(OBJ_DIR)
	brew-none-elf-gcc $^ -c -o $@

$(OBJ_DIR)/%.o: $(SW_BASE)/%.s
	-mkdir -p $(OBJ_DIR)
	brew-none-elf-gcc $^ -c -o $@

$(OBJ_DIR)/%.o: %.cpp
	-mkdir -p $(OBJ_DIR)
	brew-none-elf-g++ $^ -c $(CFLAGS) -O2 -o $@

$(OBJ_DIR)/%.o: ../%.cpp
	-mkdir -p $(OBJ_DIR)
	brew-none-elf-g++ $^ -c $(CFLAGS) -O2 -o $@

$(OBJ_DIR)/%.o: $(SW_BASE)/%.cpp
	-mkdir -p $(OBJ_DIR)
	brew-none-elf-g++ $^ -c $(CFLAGS) -O2 -o $@

$(BIN_DIR)/dram.elf: $(DRAM_OBJ_FILES)
	-mkdir -p $(BIN_DIR)
	brew-none-elf-gcc $(DRAM_LDFLAGS) $(DRAM_OBJ_FILES) -Xlinker -Map=$(addsuffix .map, $(basename $@)) -o $@

#$(BIN_DIR)/rom.elf: $(ROM_OBJ_FILES)
#	-mkdir -p $(BIN_DIR)
#	brew-none-elf-gcc $(ROM_LDFLAGS) $(ROM_OBJ_FILES) -o $@

$(BIN_DIR)/rom.elf: $(ROM_OBJ_FILES)
	-mkdir -p $(BIN_DIR)
	brew-none-elf-gcc $(ROM_LDFLAGS) $(ROM_OBJ_FILES) -Xlinker -Map=$(addsuffix .map, $(basename $@)) -o $@

$(BIN_DIR)/rom.mef: $(BIN_DIR)/rom.elf
	$(SW_BASE)/elf2mef $^ rom $(basename $@)

ifeq ($(TARGET),rom)
$(BIN_DIR)/dram.0.mef $(BIN_DIR)/dram.1.mef &:
	echo > $(BIN_DIR)/dram.0.mef
	echo > $(BIN_DIR)/dram.1.mef
else
$(BIN_DIR)/dram.0.mef $(BIN_DIR)/dram.1.mef &: $(BIN_DIR)/dram.elf
	$(SW_BASE)/elf2mef $^ dram $(basename $(basename $@))
endif

