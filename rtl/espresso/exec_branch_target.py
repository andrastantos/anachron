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



class BranchTargetUnitInputIf(Interface):
    op_c       = BrewData
    pc         = BrewInstAddr
    inst_len   = Unsigned(2) # 0: single-beat, 1: two-beat, 3: 4-beat

class BranchTargetUnitOutputIf(Interface):
    branch_addr = BrewInstAddr
    straight_addr = BrewInstAddr

class BranchTargetUnit(Module):
    input_port = Input(BranchTargetUnitInputIf)
    output_port = Output(BranchTargetUnitOutputIf)

    def body(self):
        def unmunge_offset(offset):
            return concat(
                offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0],
                offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0],
                offset[15:1]
            )
        offset = unmunge_offset(self.input_port.op_c)
        self.output_port.branch_addr   <<= (self.input_port.pc + offset)[30:0]
        self.output_port.straight_addr <<= (self.input_port.pc + self.input_port.inst_len + 1)[30:0]


def gen():
    def top():
        #return ScanWrapper(ExecuteStage, {"clk", "rst"}, has_multiply=True, has_shift=True)
        return BranchTargetUnit()

    #back_end = SystemVerilog()
    #back_end.yosys_fix = True
    netlist = Build.generate_rtl(top, "br_target.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(
        target_dir="q_br_target",
        top_level=top_level_name,
        source_files=("br_target.sv",),
        clocks=(),
        project_name="br_target",
        family="MAX 10",
        device="10M50DAF672C7G" # Something large with a ton of pins
    )
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()

