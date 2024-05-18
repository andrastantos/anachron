import sys
from pathlib import Path

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


class ApbSimpleTimer(Module):
    """
    A very simple timer to generate periodic pulses (a.k.a. interrupts)
    """

    clk = ClkPort()
    rst = RstPort()

    bus_if = Input(CsrIf)

    tick = Output(logic)
    n_int = Output(logic)

    def body(self):
        timer_val = Wire(Unsigned(32))
        timer_limit = Wire(Unsigned(32))
        timer_limit_write = Wire(logic)
        int_pending = Wire(logic)
        enabled = Wire(logic)

        self.reg_map = {
            0:     RegMapEntry("timer_cnt_limit",     (RegField(read_wire = timer_val, write_wire = timer_limit,access="RW"),), "Timer count and limit register", write_pulse=timer_limit_write),
            1:     RegMapEntry("timer_int_stat",      (RegField(wire = int_pending, set_wire = self.tick, access="RW1C"),), "Timer interrupt status register"),
            2:     RegMapEntry("timer_ctrl",          (RegField(wire = enabled, access="RW"),), "Timer control register")
        }

        limit_reached = timer_val == timer_limit

        timer_val <<= Reg(Select(
            timer_limit_write | limit_reached,
            increment(timer_val),
            0,
        ))

        self.tick <<= limit_reached & enabled
        self.n_int <<= ~int_pending

        create_apb_reg_map(self.reg_map, self.bus_if)

