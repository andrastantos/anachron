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



# We have a tiny module to select bits from operands. This is used in BranchUnit, but we can pre-load the logic and save a ton of pipeline registers
class BitExtractInputIf(Interface):
    op_a            = BrewData
    op_b            = BrewData

class BitExtractOutputIf(Interface):
    bit             = logic

class BitExtract(Module):
    input_port = Input(BitExtractInputIf)
    output_port = Output(BitExtractOutputIf)

    def body(self):
        @module(1)
        def bb_get_bit(word, bit_code):
            return SelectOne(
                bit_code == 0,  word[0],
                bit_code == 1,  word[1],
                bit_code == 2,  word[2],
                bit_code == 3,  word[3],
                bit_code == 4,  word[4],
                bit_code == 5,  word[5],
                bit_code == 6,  word[6],
                bit_code == 7,  word[7],
                bit_code == 8,  word[8],
                bit_code == 9,  word[9],
                bit_code == 10, word[14],
                bit_code == 11, word[15],
                bit_code == 12, word[16],
                bit_code == 13, word[30],
                bit_code == 14, word[31],
            )
        self.output_port.bit <<= bb_get_bit(self.input_port.op_a, self.input_port.op_b)


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

