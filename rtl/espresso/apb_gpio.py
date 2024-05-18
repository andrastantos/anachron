import sys
from pathlib import Path
import itertools

sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon"))
sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon" / "unit_tests"))

try:
    from .brew_types import *
    from .scan import *
    from .synth import *
except ImportError:
    from brew_types import *
    from scan import *
    from synth import *

from silicon import *

class ApbGpio(Module):
    clk = ClkPort()
    rst = RstPort()

    bus_if = Input(Apb8If)

    output_port = Output(Unsigned(8))
    output_update = Output(logic)
    input_port = Input(Unsigned(8))
    input_sampled = Output(logic)

    data_reg_ofs = 0

    def body(self):
        data_reg_wr =    (self.bus_if.psel & self.bus_if.penable &  self.bus_if.pwrite & (self.bus_if.paddr == ApbGpio.data_reg_ofs))
        data_reg_rd =    (self.bus_if.psel & self.bus_if.penable & ~self.bus_if.pwrite & (self.bus_if.paddr == ApbGpio.data_reg_ofs))

        self.bus_if.pready <<= 1
        self.bus_if.prdata <<= Reg(self.input_port, clock_en=data_reg_rd)

        self.output_port <<= Reg(self.bus_if.pwdata, clock_en=data_reg_wr)
        self.output_update <<= Reg(data_reg_wr)
        self.input_sampled <<= data_reg_rd


