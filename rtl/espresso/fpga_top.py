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
    from .assembler import *
except ImportError:
    from brew_types import *
    from scan import *
    from synth import *
    from fpga_system import FpgaSystem
    from brew_v1 import BrewV1Top
    from assembler import *

from silicon import *

class FpgaTop(GenericModule):
    clk               = ClkPort()
    clk2              = ClkPort()
    n_rst             = Input(logic)

    output_pins = Output(BrewByte)
    output_pins2 = Output(BrewByte)
    input_pins = Input(BrewByte)

    is_sim = Input(logic)

    def construct(
        self,
        *,
        program_generator: Callable = None,
        rom_content: str = None,
        dram0_content: str = None,
        dram1_content: str = None
    ) -> None:
        self.program_generator = program_generator
        self.rom_content = rom_content
        self.dram0_content = dram0_content
        self.dram1_content = dram1_content
        return super().construct()

    def body(self):
        rst = Wire(logic)
        rst <<= ~self.n_rst

        brew = BrewV1Top()

        ext_bus = Wire(ExternalBusIf)

        brew.clk <<= self.clk
        brew.rst <<= rst
        ext_bus <<= brew.dram

        brew.drq <<= 0
        brew.n_int <<= 1

        def create_mif(file_name, content):
            with open(file_name, "wt") as f:
                for byte in content:
                    f.write(f"{byte:02x}\n")

        if self.program_generator is not None:
            clear_asm()
            self.program_generator()
            reloc()
            rom_content = None
            dram0_content = None
            dram1_content = None
            for segment in get_all_segments():
                section = segment.base_addr & 0xc000_0000
                if section == FpgaSystem.rom_base:
                    rom_content = copy(segment.content)
                    #rom_content = "fpga_top_rom_content.mif"
                    #create_mif(rom_content, segment.content)
                elif section == FpgaSystem.dram_base:
                    dram0_content = segment.content[0::2]
                    dram1_content = segment.content[1::2]
                    #dram0_content = "fpga_top_dram0_content.mif"
                    #dram1_content = "fpga_top_dram1_content.mif"
                    #create_mif(dram0_content, segment.content[0::2])
                    #create_mif(dram1_content, segment.content[1::2])
        else:
            rom_content = self.rom_content
            dram0_content = self.dram0_content
            dram1_content = self.dram1_content

        system = FpgaSystem(rom_content=rom_content, dram0_content=dram0_content, dram1_content=dram1_content, dram_size=128*1024, rom_size=8*1024)

        system.clk <<= self.clk
        system.clk2 <<= self.clk2
        system.rst <<= rst

        system.is_sim <<= self.is_sim

        system.brew_if <<= ext_bus

        self.output_pins <<= system.output_pins
        self.output_pins2 <<= system.output_pins2
        system.input_pins <<= self.input_pins

        brew.n_int <- system.n_int

def counter_demo():
    """
    Setting up initial segments, jump to DRAM and output a counter on GPIO
    """

    create_segment("code", 0)
    create_segment("code_dram", 0x8000_0000)
    set_active_segment("code_dram")
    place_symbol("_start")
    set_active_segment("code")

    pc_eq_I("_start")

    set_active_segment("code_dram")

    r_eq_i("$r5", 0)
    place_symbol("loop")
    r_eq_r_shr_i("$r6", "$r5", 10)
    mem8_I_eq_r(FpgaSystem.gpio_base, "$r6")
    r_eq_r_plus_i("$r5", "$r5", 1)
    pc_eq_I("loop")

def sim(
    *,
    program_generator: Callable = None,
    rom_content: str = None,
    dram0_content: str = None,
    dram1_content: str = None
):
    class top(Module):
        clk               = ClkPort()
        clk2              = ClkPort()
        n_rst             = Input(logic)

        output_pins = Output(BrewByte)
        input_pins = Input(BrewByte)

        def body(self):
            top = FpgaTop(
                program_generator=program_generator,
                rom_content=rom_content,
                dram0_content=dram0_content,
                dram1_content=dram1_content
            )
            top.clk <<= self.clk
            top.clk2 <<= self.clk2
            top.n_rst <<= self.n_rst
            top.input_pins <<= self.input_pins
            self.output_pins <<= top.output_pins

        def simulate(self, simulator: Simulator) -> TSimEvent:
            clk_period = 100
            clk_ratio = 5

            clk_wait = clk_period // 2
            clk2_wait = clk_wait // clk_ratio

            def clk() -> int:
                self.clk <<= 1
                self.clk2 <<= 1
                for _ in range(clk_ratio):
                    yield clk2_wait
                    self.clk2 <<= ~self.clk2
                self.clk <<= ~self.clk
                for _ in range(clk_ratio):
                    yield clk2_wait
                    self.clk2 <<= ~self.clk2

            #self.program()
            simulator.log("Simulation started")

            self.n_rst <<= 0
            self.clk <<= 1
            self.clk2 <<= 1
            for i in range(5):
                yield from clk()
            self.n_rst <<= 1

            for i in range(1000):
                yield from clk()
            yield 10
            simulator.log("Done")

    top_class = top
    vcd_filename = "fpga_top.vcd"
    if vcd_filename is None:
        vcd_filename = top_class.__name__.lower()
    with Netlist().elaborate() as netlist:
        top_inst = top_class()
    netlist.simulate(vcd_filename, add_unnamed_scopes=False)

def gen(
    *,
    program_generator: Callable = None,
    rom_content: str = None,
    dram0_content: str = None,
    dram1_content: str = None
):
    target_dir = "q_fpga_top"

    from os import makedirs

    makedirs(target_dir, exist_ok=True)

    def copy_file(source: str) -> str:
        """
        Copies the file 'source' to the destination folder and returns it's name
        """
        from shutil import copyfile
        dst_name = str(Path(target_dir) / Path(source).name)
        copyfile(source, dst_name)
        return dst_name

    if rom_content is not None: rom_content = copy_file(rom_content)
    if dram0_content is not None: dram0_content = copy_file(dram0_content)
    if dram1_content is not None: dram1_content = copy_file(dram1_content)

    def top():
        return FpgaTop(
            program_generator=program_generator,
            rom_content=rom_content,
            dram0_content=dram0_content,
            dram1_content=dram1_content
        )

    back_end = SystemVerilog()
    back_end.support_unique_case = False
    netlist = Build.generate_rtl(top, "fpga_top.sv", back_end=back_end)
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(
        target_dir=target_dir,
        top_level=top_level_name,
        source_files=("fpga_top.sv",),
        clocks=(("clk", 10), ("clk2", 50)),
        project_name="fpga_top",
        device="10M50DAF484C6G" # Device on the DECA board
        #device="10M50DA" # Device on the DECA board
    )

    flow.add_custom_setting("#============================================================")
    flow.add_custom_setting("# disable config pin so bank8 can use 1.2V ")
    flow.add_custom_setting("#============================================================")
    flow.add_custom_setting("set_global_assignment -name AUTO_RESTART_CONFIGURATION ON")
    flow.add_custom_setting("set_global_assignment -name ENABLE_CONFIGURATION_PINS OFF")
    flow.add_custom_setting("set_global_assignment -name ENABLE_BOOT_SEL_PIN OFF")

    # Clocks
    flow.add_pin_assignment("clk",  "PIN_M9", "2.5 V") # 10MHz clock
    flow.add_pin_assignment("clk2", "PIN_M8", "2.5 V") # 50MHz clock
    #flow.add_pin_assignment("MAX10_CLK2_50", "PIN_P11", "3.3-V LVTTL") # 50MHz clock

    # Push buttons
    flow.add_pin_assignment("n_rst",         "PIN_H21", "1.5 V Schmitt Trigger")
    flow.add_pin_assignment("input_pins[0]", "PIN_H22", "1.5 V Schmitt Trigger")

    # Switches
    flow.add_pin_assignment("input_pins[1]", "PIN_J21", "1.5 V Schmitt Trigger")
    flow.add_pin_assignment("input_pins[2]", "PIN_J22", "1.5 V Schmitt Trigger")

    flow.add_pin_assignment("input_pins[3]", "PIN_W18",   "3.3-V LVTTL")
    flow.add_pin_assignment("input_pins[4]", "PIN_Y18",   "3.3-V LVTTL")
    flow.add_pin_assignment("input_pins[5]", "PIN_Y19",   "3.3-V LVTTL")
    flow.add_pin_assignment("input_pins[6]", "PIN_AA17",  "3.3-V LVTTL")
    flow.add_pin_assignment("input_pins[7]", "PIN_AA20",  "3.3-V LVTTL")

    # LEDs
    flow.add_pin_assignment("output_pins[0]", "PIN_C7", "1.2 V")
    flow.add_pin_assignment("output_pins[1]", "PIN_C8", "1.2 V")
    flow.add_pin_assignment("output_pins[2]", "PIN_A6", "1.2 V")
    flow.add_pin_assignment("output_pins[3]", "PIN_B7", "1.2 V")
    flow.add_pin_assignment("output_pins[4]", "PIN_C4", "1.2 V")
    flow.add_pin_assignment("output_pins[5]", "PIN_A5", "1.2 V")
    flow.add_pin_assignment("output_pins[6]", "PIN_B4", "1.2 V")
    flow.add_pin_assignment("output_pins[7]", "PIN_C5", "1.2 V")

    #flow.add_pin_assignment("GPIO0_D[0]",      "PIN_W18",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[1]",      "PIN_Y18",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[2]",      "PIN_Y19",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[3]",      "PIN_AA17",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[4]",      "PIN_AA20",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[5]",      "PIN_AA19",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[6]",      "PIN_AB21",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[7]",      "PIN_AB20",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[8]",      "PIN_AB19",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[9]",      "PIN_Y16",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[10]",     "PIN_V16",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[11]",     "PIN_AB18",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[12]",     "PIN_V15",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[13]",     "PIN_W17",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[14]",     "PIN_AB17",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[15]",     "PIN_AA16",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[16]",     "PIN_AB16",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[17]",     "PIN_W16",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[18]",     "PIN_AB15",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[19]",     "PIN_W15",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[20]",     "PIN_Y14",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[21]",     "PIN_AA15",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[22]",     "PIN_AB14",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[23]",     "PIN_AA14",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[24]",     "PIN_AB13",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[25]",     "PIN_AA13",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[26]",     "PIN_AB12",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[27]",     "PIN_AA12",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[28]",     "PIN_AB11",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[29]",     "PIN_AA11",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[30]",     "PIN_AB10",  "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[31]",     "PIN_Y13",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[32]",     "PIN_Y11",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[33]",     "PIN_W13",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[34]",     "PIN_W12",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[35]",     "PIN_W11",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[36]",     "PIN_V12",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[37]",     "PIN_V11",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[38]",     "PIN_V13",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[39]",     "PIN_V14",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[40]",     "PIN_Y17",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[41]",     "PIN_W14",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[42]",     "PIN_U15",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO0_D[43]",     "PIN_R13",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[0]",      "PIN_Y5",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[1]",      "PIN_Y6",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[2]",      "PIN_W6",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[3]",      "PIN_W7",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[4]",      "PIN_W8",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[5]",      "PIN_V8",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[6]",      "PIN_AB8",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[7]",      "PIN_V7",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[8]",      "PIN_R11",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[9]",      "PIN_AB7",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[10]",     "PIN_AB6",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[11]",     "PIN_AA7",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[12]",     "PIN_AA6",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[13]",     "PIN_Y7",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[14]",     "PIN_V10",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[15]",     "PIN_U7",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[16]",     "PIN_W9",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[17]",     "PIN_W5",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[18]",     "PIN_R9",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[19]",     "PIN_W4",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[20]",     "PIN_P9",    "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[21]",     "PIN_V17",   "3.3-V LVTTL")
    #flow.add_pin_assignment("GPIO1_D[22]",     "PIN_W3",    "3.3-V LVTTL")
    #flow.add_pin_assignment("BBB_PWR_BUT",     "PIN_U6",    "3.3-V LVTTL")
    #flow.add_pin_assignment("BBB_SYS_RESET_n", "PIN_AA2",   "3.3-V LVTTL")

    flow.generate()
    flow.run()

if __name__ == "__main__":
    #gen(program_generator=counter_demo)
    gen(
        rom_content="../../sw/blinky/rom.rom_mef",
        dram0_content="../../sw/blinky/blinky.dram0_mef",
        dram1_content="../../sw/blinky/blinky.dram1_mef"
    )
    #sim(
    #    rom_content="../../sw/blinky/rom.rom_mef",
    #    dram0_content="../../sw/blinky/blinky.dram0_mef",
    #    dram1_content="../../sw/blinky/blinky.dram1_mef"
    #)

