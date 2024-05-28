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




class MultInputIf(Interface):
    valid = logic
    op_a = BrewData
    op_b = BrewData

#class MultOutputIf(Interface):
#   result = BrewData

class MultUnit(Module):
    clk = ClkPort()
    rst = RstPort()

    input_port = Input(MultInputIf)
    output_port = Output(BrewData)

    OPTIMIZED = True
    def body(self):
        if self.OPTIMIZED:
            partial_11 = (self.input_port.op_a[15: 0] * self.input_port.op_b[15: 0])
            partial_12 = (self.input_port.op_a[31:16] * self.input_port.op_b[15: 0])[15:0]
            partial_21 = (self.input_port.op_a[15: 0] * self.input_port.op_b[31:16])[15:0]
            s1_partial_11 = Reg(partial_11, clock_en = self.input_port.valid)
            s1_partial_12 = Reg(partial_12, clock_en = self.input_port.valid)
            s1_partial_21 = Reg(partial_21, clock_en = self.input_port.valid)
            mult_result = (s1_partial_11 + concat(s1_partial_12+s1_partial_21, "16'b0"))[31:0]
        else:
            op_a = Select(self.input_port.valid, Reg(self.input_port.op_a, clock_en = self.input_port.valid), self.input_port.op_a)
            op_b = Select(self.input_port.valid, Reg(self.input_port.op_b, clock_en = self.input_port.valid), self.input_port.op_b)
            mult_result_large = op_a * op_b
            mult_result = mult_result_large[31:0]

        self.output_port <<= mult_result


def gen():
    def top():
        #return ScanWrapper(ExecuteStage, {"clk", "rst"}, has_multiply=True, has_shift=True)
        return MultUnit()

    #back_end = SystemVerilog()
    #back_end.yosys_fix = True
    netlist = Build.generate_rtl(top, "mult.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(
        target_dir="q_mult",
        top_level=top_level_name,
        source_files=("mult.sv",),
        clocks=(),
        project_name="mult",
        family="MAX 10",
        device="10M50DAF672C7G" # Something large with a ton of pins
    )
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()

