from typing import *
from silicon import *
try:
    from .brew_types import *
    from .brew_utils import *
    from .scan import ScanWrapper
    from .synth import *
except ImportError:
    from brew_types import *
    from brew_utils import *
    from scan import ScanWrapper
    from synth import *






class AddrCalcInputIf(Interface):
    is_ldst = logic
    op_b = BrewData
    op_c = BrewData
    mem_base = BrewMemBase
    mem_limit = BrewMemBase
    task_mode = logic
    mem_access_len = Unsigned(2) # 0: 8-bit, 1: 16-bit, 2: 32-bit
    is_csr = logic

class AddrCalcOutputIf(Interface):
    phy_addr = BrewAddr
    eff_addr = BrewAddr
    mem_av = logic
    mem_unaligned = logic
    is_csr = logic

class AddrCalcUnit(Module):
    input_port = Input(AddrCalcInputIf)
    output_port = Output(AddrCalcOutputIf)

    def body(self):
        eff_addr = (self.input_port.op_b + self.input_port.op_c)[31:0]
        phy_addr = Select(
            self.input_port.is_csr,
            get_phy_addr(eff_addr, Select(self.input_port.task_mode, 0, self.input_port.mem_base)),
            concat(self.input_port.op_c[15:0], "2'b00") | Select(self.input_port.task_mode, 0, 0x20000),
        )

        mem_av = self.input_port.task_mode & self.input_port.is_ldst & is_over_limit(eff_addr, self.input_port.mem_limit) & ~self.input_port.is_csr
        mem_unaligned = ~self.input_port.is_csr & self.input_port.is_ldst & Select(self.input_port.mem_access_len,
            0, # 8-bit access is always aligned
            eff_addr[0], # 16-bit access is unaligned if LSB is non-0
            eff_addr[0] | eff_addr[1], # 32-bit access is unaligned if lower two bits are non-0
            None # This is an invalid length
        )

        self.output_port.phy_addr <<= phy_addr
        self.output_port.eff_addr <<= eff_addr
        self.output_port.mem_av <<= mem_av
        self.output_port.mem_unaligned <<= mem_unaligned
        self.output_port.is_csr <<= self.input_port.is_csr



def gen():
    def top():
        #return ScanWrapper(ExecuteStage, {"clk", "rst"}, has_multiply=True, has_shift=True)
        return AddrCalcUnit()

    #back_end = SystemVerilog()
    #back_end.yosys_fix = True
    netlist = Build.generate_rtl(top, "addr_calc.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(
        target_dir="q_addr_calc",
        top_level=top_level_name,
        source_files=("addr_calc.sv",),
        clocks=(),
        project_name="addr_calc",
        family="MAX 10",
        device="10M50DAF672C7G" # Something large with a ton of pins
    )
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()

