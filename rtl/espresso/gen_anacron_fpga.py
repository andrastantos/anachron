import sys
from pathlib import Path
import itertools

sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon"))
sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon" / "unit_tests"))

try:
    from .brew_types import *
    from .scan import *
    from .synth import *
    from .fpga_system import FpgaSystem
    from .brew_v1 import BrewV1Top
    from .apb_uart import ApbUart
    from .apb_gpio import ApbGpio
except ImportError:
    from brew_types import *
    from scan import *
    from synth import *
    from fpga_system import FpgaSystem
    from brew_v1 import BrewV1Top
    from apb_uart import ApbUart
    from apb_gpio import ApbGpio

from silicon import *
from os import makedirs

target_dir="anacron_fpga"

makedirs(target_dir, exist_ok=True)

def create_back_end():
    back_end = SystemVerilog()
    back_end.support_unique_case = False
    return back_end

def generate_system(
    file_name: Union[str, Path],
    rom_content: str,
    dram0_content: str = None,
    dram1_content: str = None,
    dram_size: int=128*1024,
    rom_size: int=8*1024
) :
    def copy_file(source: str) -> str:
        """
        Copies the file 'source' to the destination folder (if exists) and returns it's name
        """
        from shutil import copyfile
        dst_name = str(Path(target_dir) / Path(source).name)
        try:
            copyfile(source, dst_name)
        except FileNotFoundError:
            pass
        return Path(source).name

    if rom_content is not None: rom_content = copy_file(rom_content)
    if dram0_content is not None: dram0_content = copy_file(dram0_content)
    if dram1_content is not None: dram1_content = copy_file(dram1_content)

    def top():
        return FpgaSystem(
            rom_content=rom_content,
            dram0_content=dram0_content,
            dram1_content=dram1_content,
            dram_size=dram_size,
            rom_size=rom_size
        )

    netlist = Build.generate_rtl(
        top,
        Path(target_dir) / file_name,
        back_end=create_back_end(),
        name_prefix = "fpga_system",
        top_level_prefix = None
    )
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    return top_level_name

def generate_brew(file_name: Union[str, Path]):
    def top():
        return BrewV1Top(
            nram_base    = 0x0,
            has_multiply = True,
            has_shift    = True,
            page_bits    = 7
        )

    netlist = Build.generate_rtl(
        top,
        Path(target_dir) / file_name,
        back_end=create_back_end(),
        name_prefix = "brew",
        top_level_prefix = None
    )
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    return top_level_name

def generate_uart(file_name: Union[str, Path]):
    class ApbUart(globals()["ApbUart"]):
        def construct(self):
            self.bus_if.paddr.set_net_type(Unsigned(3))

    def top(): return ApbUart()

    netlist = Build.generate_rtl(
        top,
        Path(target_dir) / file_name,
        back_end=create_back_end(),
        name_prefix = "apb_uart",
        top_level_prefix = None
    )
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    return top_level_name

def generate_gpio(file_name: Union[str, Path]):
    class ApbGpio(globals()["ApbGpio"]):
        def construct(self):
            self.bus_if.paddr.set_net_type(Unsigned(3))

    def top(): return ApbGpio()

    netlist = Build.generate_rtl(
        top,
        Path(target_dir) / file_name,
        back_end=create_back_end(),
        name_prefix = "apb_gpio",
        top_level_prefix = None
    )
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    return top_level_name


def gen(
    *,
    rom_content: str,
    dram0_content: str = None,
    dram1_content: str = None
):
    generate_brew("brew.sv")
    generate_system("fpga_system.sv", rom_content=rom_content, dram0_content=dram0_content, dram1_content=dram1_content)
    generate_uart("apb_uart.sv")
    generate_gpio("apb_gpio.sv")


def gen_quartus_proj():
    sv_files = []
    sv_files.append(Path(target_dir) / "brew.sv")
    sv_files.append(Path(target_dir) / "fpga_system.sv")
    sv_files.append(Path(target_dir) / "apb_uart.sv")
    sv_files.append(Path(target_dir) / "apb_gpio.sv")

    flow = QuartusFlow(
        target_dir=target_dir,
        top_level="DecaTop",
        source_files=(Path(target_dir) / "deca_board_wrapper.sv", Path(target_dir) / "fpga_top.sv",*sv_files),
        clocks=(("ADC_CLK_10", 10), ("MAX10_CLK1_50", 50)),
        project_name="deca",
        device="10M50DAF484C6G" # Device on the DECA board
    )

    flow.add_custom_setting("#============================================================")
    flow.add_custom_setting("# disable config pin so bank8 can use 1.2V ")
    flow.add_custom_setting("#============================================================")
    flow.add_custom_setting("set_global_assignment -name AUTO_RESTART_CONFIGURATION ON")
    flow.add_custom_setting("set_global_assignment -name ENABLE_CONFIGURATION_PINS OFF")
    flow.add_custom_setting("set_global_assignment -name ENABLE_BOOT_SEL_PIN OFF")

    # Clocks
    flow.add_pin_assignment("ADC_CLK_10",    "PIN_M9", "2.5 V") # 10MHz clock
    flow.add_pin_assignment("MAX10_CLK1_50", "PIN_M8", "2.5 V") # 50MHz clock
    #flow.add_pin_assignment("MAX10_CLK2_50", "PIN_P11", "3.3-V LVTTL") # 50MHz clock

    # Push buttons
    flow.add_pin_assignment("KEY[0]",    "PIN_H21", "1.5 V Schmitt Trigger")
    flow.add_pin_assignment("KEY[1]",    "PIN_H22", "1.5 V Schmitt Trigger")

    # Switches
    flow.add_pin_assignment("SW[0]", "PIN_J21", "1.5 V Schmitt Trigger")
    flow.add_pin_assignment("SW[1]", "PIN_J22", "1.5 V Schmitt Trigger")

    # LEDs
    flow.add_pin_assignment("LED[0]", "PIN_C7", "1.2 V")
    flow.add_pin_assignment("LED[1]", "PIN_C8", "1.2 V")
    flow.add_pin_assignment("LED[2]", "PIN_A6", "1.2 V")
    flow.add_pin_assignment("LED[3]", "PIN_B7", "1.2 V")
    flow.add_pin_assignment("LED[4]", "PIN_C4", "1.2 V")
    flow.add_pin_assignment("LED[5]", "PIN_A5", "1.2 V")
    flow.add_pin_assignment("LED[6]", "PIN_B4", "1.2 V")
    flow.add_pin_assignment("LED[7]", "PIN_C5", "1.2 V")

    flow.add_pin_assignment("GPIO0_D[0]",      "PIN_W18",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[1]",      "PIN_Y18",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[2]",      "PIN_Y19",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[3]",      "PIN_AA17",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[4]",      "PIN_AA20",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[5]",      "PIN_AA19",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[6]",      "PIN_AB21",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[7]",      "PIN_AB20",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[8]",      "PIN_AB19",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[9]",      "PIN_Y16",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[10]",     "PIN_V16",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[11]",     "PIN_AB18",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[12]",     "PIN_V15",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[13]",     "PIN_W17",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[14]",     "PIN_AB17",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[15]",     "PIN_AA16",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[16]",     "PIN_AB16",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[17]",     "PIN_W16",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[18]",     "PIN_AB15",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[19]",     "PIN_W15",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[20]",     "PIN_Y14",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[21]",     "PIN_AA15",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[22]",     "PIN_AB14",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[23]",     "PIN_AA14",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[24]",     "PIN_AB13",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[25]",     "PIN_AA13",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[26]",     "PIN_AB12",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[27]",     "PIN_AA12",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[28]",     "PIN_AB11",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[29]",     "PIN_AA11",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[30]",     "PIN_AB10",  "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[31]",     "PIN_Y13",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[32]",     "PIN_Y11",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[33]",     "PIN_W13",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[34]",     "PIN_W12",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[35]",     "PIN_W11",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[36]",     "PIN_V12",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[37]",     "PIN_V11",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[38]",     "PIN_V13",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[39]",     "PIN_V14",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[40]",     "PIN_Y17",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[41]",     "PIN_W14",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[42]",     "PIN_U15",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO0_D[43]",     "PIN_R13",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[0]",      "PIN_Y5",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[1]",      "PIN_Y6",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[2]",      "PIN_W6",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[3]",      "PIN_W7",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[4]",      "PIN_W8",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[5]",      "PIN_V8",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[6]",      "PIN_AB8",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[7]",      "PIN_V7",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[8]",      "PIN_R11",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[9]",      "PIN_AB7",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[10]",     "PIN_AB6",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[11]",     "PIN_AA7",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[12]",     "PIN_AA6",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[13]",     "PIN_Y7",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[14]",     "PIN_V10",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[15]",     "PIN_U7",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[16]",     "PIN_W9",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[17]",     "PIN_W5",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[18]",     "PIN_R9",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[19]",     "PIN_W4",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[20]",     "PIN_P9",    "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[21]",     "PIN_V17",   "3.3-V LVTTL")
    flow.add_pin_assignment("GPIO1_D[22]",     "PIN_W3",    "3.3-V LVTTL")
    #flow.add_pin_assignment("BBB_PWR_BUT",     "PIN_U6",    "3.3-V LVTTL")
    #flow.add_pin_assignment("BBB_SYS_RESET_n", "PIN_AA2",   "3.3-V LVTTL")

    flow.generate()

gen(
    rom_content="rom.mef",
    dram0_content="dram.0.mef",
    dram1_content="dram.1.mef"
)
#gen_quartus_proj()

