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

class ScanChain(Module):
    clk = ClkPort()
    rst = RstPort()

    idin = Input(logic)
    idout = Output(logic)
    load = Input(logic)
    odin = Input(logic)
    odout = Output(logic)

    def construct(self):
        self.inputs = []
        self.outputs = []
        self.seen_ports = set()

    def add_input(self, input_port: Junction):
        if input_port in self.seen_ports:
            raise SyntaxErrorException(f"Junction {input_port} has already been added to the serializer. Duplications are not supported.")
        my_port = self.create_named_port(f"input_port_{len(self.inputs)+1}", port_type=Input)
        my_port <<= input_port
        self.inputs.append(my_port)
        self.seen_ports.add(input_port)

    def add_output(self, output_port: Junction):
        if output_port in self.seen_ports:
            raise SyntaxErrorException(f"Junction {output_port} has already been added to the serializer. Duplications are not supported.")
        net_type = output_port.get_net_type()
        if net_type is None:
            raise SyntaxErrorException(f"Can't create serializer output without a type")
        my_port = self.create_named_port(f"output_port_{len(self.outputs)+1}", port_type=Output)
        my_port.set_net_type(net_type)
        output_port <<= my_port
        self.outputs.append(my_port)
        self.seen_ports.add(output_port)

    def body(self):
        # Collect all inputs and outputs. This is a bit tricky due to composites, and reverse members
        inputs = []
        outputs = []
        for input in self.inputs:
            for names, (input_member, reversed) in input.get_all_member_junctions_with_names(add_self = True).items():
                if input_member.is_composite():
                    continue
                if reversed:
                    outputs.append(input_member)
                else:
                    inputs.append(input_member)
        for output in self.outputs:
            for names, (output_member, reversed) in output.get_all_member_junctions_with_names(add_self = True).items():
                if output_member.is_composite():
                    continue
                if reversed:
                    inputs.append(output_member)
                else:
                    outputs.append(output_member)
        # Compute the size of the two shift-registers needed
        input_len = sum(i.get_num_bits() for i in inputs)
        output_len = sum(o.get_num_bits() for o in outputs)

        # Generate the shift registers and hook them up
        input_reg = Wire(Unsigned(input_len))
        output_reg = Wire(Unsigned(output_len))
        load_wire = Wire(Unsigned(input_len))
        load_wire <<= Unsigned(input_len)(concat(*inputs)) # concat's signed-ness depends on the type of the first element in inputs.
        input_reg <<= Reg(Select(self.load, concat(input_reg[input_len-2:0], self.idin), load_wire))
        self.idout <<= input_reg[input_len-1]
        output_reg <<= Reg(concat(output_reg[output_len-2:0], self.odin))
        self.odout <<= output_reg[output_len-1]
        o_ofs = 0
        for o in outputs:
            o_type = o.get_net_type()
            o_len = o.get_num_bits()
            o_w = Wire(Unsigned(o_len))
            o_w <<= Reg(output_reg[o_len+o_ofs-1:o_ofs], clock_en=self.load)
            o <<= o_type(o_w)
            o_ofs += o_len
        del o_w
        del o
        del input_member
        del output_member
        del output
        del input


def test_serializer():
    class RGB(Struct):
        r = Unsigned(8)
        g = Unsigned(8)
        b = Unsigned(8)

    class If1(Interface):
        fwd = Unsigned(8)
        rev = Reverse(Signed(12))

    class top(Module):
        clk = ClkPort()
        rst = RstPort()

        idin = Input(logic)
        idout = Output(logic)
        load = Input(logic)
        odin = Input(logic)
        odout = Output(logic)

        i1 = Input(Unsigned(3))
        i2 = Input(RGB)
        i3 = Input(If1)
        o1 = Output(Unsigned(5))
        o2 = Output(RGB)
        o3 = Output(If1)

        def body(self):
            ser = ScanChain()
            ser.add_input(self.i1)
            ser.add_input(self.i2)
            ser.add_input(self.i3)
            ser.add_output(self.o1)
            ser.add_output(self.o2)
            ser.add_output(self.o3)

    Build.generate_rtl(top)

class ScanWrapper(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    idin = Input(logic)
    idout = Output(logic)
    load = Input(logic)
    odin = Input(logic)
    odout = Output(logic)

    def construct(self, Top:Callable, black_list:Sequence[str] = None, clk_port_name: str="clk", *args, **kwargs):
        self.Top = Top
        self.black_list = black_list
        self.clk_port_name = clk_port_name

        self.top = self.Top(*args, **kwargs)
        for name, port in self.top.get_inputs().items():
            if self.black_list is not None and name in self.black_list:
                my_port = self.create_named_port(f"top_{name}", port_type=Input)
                net_type = port.get_net_type()
                if net_type is None:
                    raise SyntaxErrorException("Cant wrap module that has input ports with no types")
                my_port.set_net_type(net_type)
        for name, port in self.top.get_outputs().items():
            if self.black_list is not None and name in self.black_list:
                self.create_named_port(f"top_{name}", port_type=Output)


    def body(self):
        ser = ScanChain()
        ser.idin <<= self.idin
        self.idout <<= ser.idout
        ser.odin <<= self.odin
        self.odout <<= ser.odout
        ser.load <<= self.load

        def get_name(prefix, name, names):
            n = f"{name}_{first(names)}" if len(names) > 0 else name
            return f"{prefix}_{n}"

        top_clk = None
        for name, port in self.top.get_inputs().items():
            if name == self.clk_port_name:
                top_clk = port
        for name, port in self.top.get_inputs().items():
            if self.black_list is not None and name in self.black_list:
                my_port = getattr(self, f"top_{name}")
                port <<= my_port
            else:
                for names, (member, reversed) in port.get_all_member_junctions_with_names(add_self = True).items():
                    if member.is_composite():
                        continue
                    if reversed:
                        if top_clk is not None:
                            reg_member = Reg(member, clock_port=top_clk)
                            setattr(self, get_name("oreg", name, names), reg_member)
                            ser.add_input(reg_member)
                            del reg_member
                        else:
                            ser.add_input(member)
                    else:
                        if top_clk is not None:
                            wire = Wire(member.get_net_type())
                            reg_member = Reg(wire, clock_port=top_clk)
                            member <<= reg_member
                            setattr(self, get_name("ireg", name, names), reg_member)
                            setattr(self, get_name("ser", name, names), wire)
                            ser.add_output(wire)
                            del wire
                            del reg_member
                        else:
                            ser.add_output(member)

        for name, port in self.top.get_outputs().items():
            if self.black_list is not None and name in self.black_list:
                my_port = getattr(self, f"top_{name}")
                my_port <<= port
            else:
                for names, (member, reversed) in port.get_all_member_junctions_with_names(add_self = True).items():
                    if member.is_composite():
                        continue
                    if not reversed:
                        if top_clk is not None:
                            member = Reg(member, clock_port=top_clk)
                            setattr(self, get_name("oreg", name, names), member)
                        ser.add_input(member)
                    else:
                        if top_clk is not None:
                            wire = Wire(member.get_net_type())
                            reg_member = Reg(wire, clock_port=top_clk)
                            member <<= reg_member
                            setattr(self, get_name("ireg", name, names), reg_member)
                            setattr(self, get_name("ser", name, names), wire)
                            ser.add_output(wire)
                            del wire
                            del reg_member
                        else:
                            ser.add_output(member)


def gen():
    class RGB(Struct):
        r = Unsigned(8)
        g = Unsigned(8)
        b = Unsigned(8)

    class If1(Interface):
        fwd = Unsigned(8)
        rev = Reverse(Signed(12))

    class inner_top(Module):
        clk = ClkPort()
        rst = RstPort()

        exclude = Input(Unsigned(5))
        i1 = Input(Unsigned(3))
        i2 = Input(RGB)
        i3 = Input(If1)
        o1 = Output(Unsigned(5))
        o2 = Output(RGB)
        o3 = Output(If1)

        def body(self):
            self.o1 <<= self.i2.r[1]
            self.o2 <<= self.i2
            self.o3.fwd <<= self.i1
            self.i3.rev <<= Reg(self.o3.rev)

    def top():
        return ScanWrapper(inner_top, {"clk", "rst", "exclude"})

    Build.generate_rtl(top)

if __name__ == "__main__":
    gen()
    #sim()

