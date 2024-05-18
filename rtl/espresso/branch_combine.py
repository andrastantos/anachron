#!/usr/bin/python3
from random import *
from typing import *
from silicon import *
try:
    from .brew_types import *
    from .brew_utils import *
except ImportError:
    from brew_types import *
    from brew_utils import *

"""
Branch and Combine helpers for the V1 pipeline.

These two little modules help with distributing
issued instructions to their rightful execution
unit, then collecting the results for write-back.
"""

class RvBranch(Module):
    #clk = ClkPort()
    #rst = RstPort()

    # Pipeline input
    input_port = Input()
    output_port1 = Output()
    output_port2 = Output()

    def body(self):
        self.output_port1.set_net_type(self.input_port.get_net_type())
        self.output_port2.set_net_type(self.input_port.get_net_type())

        data = self.input_port.get_data_members()

        self.input_port.ready <<= self.output_port1.ready & self.output_port2.ready
        self.output_port1.valid <<= self.input_port.valid & self.output_port2.ready
        self.output_port2.valid <<= self.input_port.valid & self.output_port1.ready
        self.output_port1.set_data_members(data)
        self.output_port2.set_data_members(data)

class RvCombine(Module):
    #clk = ClkPort()
    #rst = RstPort()

    # Pipeline input
    input_port1 = Input()
    input_port2 = Input()
    output_port = Output()

    def body(self):
        if self.input_port1.get_net_type() is not self.input_port2.get_net_type():
            raise SyntaxErrorException(f"RvCombine input ports must have the same type. They are {self.input_port1.get_net_type()} and {self.input_port2.get_net_type()} for {self}")

        self.output_port.set_net_type(self.input_port1.get_net_type())

        data1 = self.input_port1.get_data_members()
        data2 = self.input_port2.get_data_members()

        # For now, trivial arbitration: port1 always wins
        port_select = Wire(logic)
        port_select <<= ~self.input_port1.valid

        #self.input_port1.ready <<= (port_select == 0) & self.output_port.ready
        #self.input_port2.ready <<= (port_select == 1) & self.output_port.ready
        self.input_port1.ready <<= self.output_port.ready
        self.input_port2.ready <<= port_select & self.output_port.ready

        self.output_port.valid <<= Select(port_select, self.input_port1.valid, self.input_port2.valid)
        data_members = Wire(data1.get_net_type())
        data_members <<= Select(port_select, data1, data2)
        self.output_port.set_data_members(data_members)

def gen():
    class Bus(ReadyValid):
        data            = Unsigned(32)

    class top(Module):
        in1 = Input(Bus)
        in2 = Input(Bus)
        out1 = Output(Bus)
        out2 = Output(Bus)

        def body(self):
            internal = RvCombine(input_port1 = self.in1, input_port2 = self.in2)
            brancher = RvBranch()
            brancher.input_port <<= internal
            self.out1 <<= brancher.output_port1
            self.out2 <<= brancher.output_port2

    Build.generate_rtl(top)

if __name__ == "__main__":
    gen()
    #sim()
    pass
