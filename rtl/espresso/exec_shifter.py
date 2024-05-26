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




class ShifterInputIf(Interface):
    opcode = EnumNet(shifter_ops)
    op_a = BrewData
    op_b = BrewData

class ShifterOutputIf(Interface):
    result = BrewData

class ShifterUnit(Module):
    input_port = Input(ShifterInputIf)
    output_port = Output(ShifterOutputIf)

    def body(self):
        # TODO: this can be optimized quite a bit. As of now, we instantiate 3 barrel shifters
        self.signed_a = Signed(32)(self.input_port.op_a)
        shifter_result = SelectOne(
            self.input_port.opcode == shifter_ops.shll, self.input_port.op_a << self.input_port.op_b[4:0],
            self.input_port.opcode == shifter_ops.shlr, self.input_port.op_a >> self.input_port.op_b[4:0],
            self.input_port.opcode == shifter_ops.shar, self.signed_a >> self.input_port.op_b[4:0],
        )[31:0]

        self.output_port.result <<= shifter_result




def gen():
    def top():
        #return ScanWrapper(ExecuteStage, {"clk", "rst"}, has_multiply=True, has_shift=True)
        return ShifterUnit()

    #back_end = SystemVerilog()
    #back_end.yosys_fix = True
    netlist = Build.generate_rtl(top, "shifter.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(
        target_dir="q_shifter",
        top_level=top_level_name,
        source_files=("shifter.sv",),
        clocks=(),
        project_name="shifter",
        family="MAX 10",
        device="10M50DAF672C7G" # Something large with a ton of pins
    )
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()

