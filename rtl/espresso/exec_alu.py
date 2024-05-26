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




class AluInputIf(Interface):
    opcode = EnumNet(alu_ops)
    op_a = BrewData
    op_b = BrewData
    pc = BrewInstAddr
    tpc = BrewInstAddr

class AluOutputIf(Interface):
    result = BrewData
    f_zero = logic
    f_sign  = logic
    f_carry = logic
    f_overflow = logic

class AluUnit(GenericModule):
    input_port = Input(AluInputIf)
    output_port = Output(AluOutputIf)

    def construct(self, use_optimized_logic: bool = True):
        self.use_optimized_logic = use_optimized_logic

    def body(self):
        # Optimized logic is about 50 LUTs (20%) smaller
        if self.use_optimized_logic:
            c_in = Wire(logic)
            c_in <<= (self.input_port.opcode == alu_ops.a_minus_b)
            xor_b = Wire(BrewData)
            xor_b <<= Select((self.input_port.opcode == alu_ops.a_minus_b), 0, 0xffffffff)
            b = xor_b ^ self.input_port.op_b
            a = Select((self.input_port.opcode == alu_ops.pc_plus_b), self.input_port.op_a, concat(self.input_port.pc, "1'b0"))
            sum = a + b + c_in
            and_result = a & b
            xor_result = self.input_port.op_a ^ self.input_port.op_b

            use_adder = (self.input_port.opcode == alu_ops.a_plus_b) | (self.input_port.opcode == alu_ops.a_minus_b)
            use_and = (self.input_port.opcode == alu_ops.a_and_b)
            adder_result = Wire(Unsigned(33))
            adder_result <<= SelectOne(
                use_adder,                                      sum,
                self.input_port.opcode == alu_ops.a_or_b,       self.input_port.op_a | self.input_port.op_b,
                use_and,                                        and_result,
                self.input_port.opcode == alu_ops.a_xor_b,      xor_result,
                self.input_port.opcode == alu_ops.tpc,          concat(self.input_port.tpc, "1'b0"),
                self.input_port.opcode == alu_ops.pc_plus_b,    sum,
            )

            self.output_port.result <<= adder_result[31:0]
            #self.output_port.f_zero <<= adder_result[31:0] == 0
            self.output_port.f_zero <<= xor_result == 0
            self.output_port.f_sign <<= adder_result[31]
            self.output_port.f_carry <<= adder_result[32] ^ (self.input_port.opcode == alu_ops.a_minus_b)
            # overflow for now is only valid for a_minus_b
            # See https://en.wikipedia.org/wiki/Overflow_flag for details
            self.output_port.f_overflow <<= (self.input_port.op_a[31] != self.input_port.op_b[31]) & (self.input_port.op_a[31] != adder_result[31])
        else:
            adder_result = Wire(Unsigned(33))
            adder_result <<= SelectOne(
                self.input_port.opcode == alu_ops.a_plus_b,     (self.input_port.op_a + self.input_port.op_b),
                self.input_port.opcode == alu_ops.a_minus_b,    Unsigned(33)(self.input_port.op_a - self.input_port.op_b),
                self.input_port.opcode == alu_ops.a_or_b,       self.input_port.op_a | self.input_port.op_b,
                self.input_port.opcode == alu_ops.a_and_b,      self.input_port.op_a & self.input_port.op_b,
                self.input_port.opcode == alu_ops.a_xor_b,      self.input_port.op_a ^ self.input_port.op_b,
                self.input_port.opcode == alu_ops.tpc,          concat(self.input_port.tpc, "1'b0"),
                self.input_port.opcode == alu_ops.pc_plus_b,    concat(self.input_port.pc, "1'b0") + self.input_port.op_b,
            )

            self.output_port.result <<= adder_result[31:0]
            self.output_port.f_zero <<= adder_result[31:0] == 0
            self.output_port.f_sign <<= adder_result[31]
            self.output_port.f_carry <<= adder_result[32]
            # overflow for now is only valid for a_minus_b
            # See https://en.wikipedia.org/wiki/Overflow_flag for details
            self.output_port.f_overflow <<= (self.input_port.op_a[31] != self.input_port.op_b[31]) & (self.input_port.op_a[31] != adder_result[31])




def gen():
    def top():
        #return ScanWrapper(ExecuteStage, {"clk", "rst"}, has_multiply=True, has_shift=True)
        return AluUnit(use_optimized_logic=True)

    #back_end = SystemVerilog()
    #back_end.yosys_fix = True
    netlist = Build.generate_rtl(top, "alu.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(
        target_dir="q_alu",
        top_level=top_level_name,
        source_files=("alu.sv",),
        clocks=(),
        project_name="alu",
        family="MAX 10",
        device="10M50DAF672C7G" # Something large with a ton of pins
    )
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()

