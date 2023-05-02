import sys
from pathlib import Path
import itertools

sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon"))
sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon" / "unit_tests"))

# System emulator for FPGA. Includes:
# - DRAM emulation
# - ROM emulation
# - SRAM emulation
# - GPIO
#
# Requires at least twice the CPU clock rate for operation.
# We are going to use a 10MHz clock for the processor and a 50MHz clock for the system
# as these clocks are available on the DECA board without an internal PLL.

try:
    from .brew_types import *
    from .scan import *
    from .synth import *
except ImportError:
    from brew_types import *
    from scan import *
    from synth import *

from silicon import *
from math import log2


class Dram(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    addr = Input()
    data_in = Input()
    data_out = Output()

    n_ras = Input(logic)
    n_cas = Input(logic)
    n_we =  Input(logic)

    def construct(self, inv_clock: bool, reset_content: Optional[str] = None):
        self.inv_clock = inv_clock
        self.reset_content = reset_content

    def body(self):
        self.data_out.set_net_type(self.data_in.get_net_type())


        #def edge_detect(signal: Junction, edge: EdgeType):
        #    prev_signal = Reg(signal)
        #    is_edge = prev_signal ^ signal
        #    if edge == EdgeType.Positive:
        #        return is_edge & ~prev_signal
        #    elif edge == EdgeType.Negative:
        #        return is_edge & prev_signal
        #    elif edge == EdgeType.Undefined:
        #        return is_edge
        #    else:
        #        assert False

        #n_ras_neg_edge = edge_detect(self.n_ras, EdgeType.Negative)
        #n_cas_neg_edge = edge_detect(self.n_cas, EdgeType.Negative)

        #row_addr = Reg(self.addr, clock_en=n_ras_neg_edge)
        #col_addr = Reg(self.addr, clock_en=n_cas_neg_edge)
        #read_not_write = Reg(self.n_we, clock_en=n_cas_neg_edge)


        """
            CLK             \___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\__
            CLK2            \_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/
            DRAM_nRAS       ^^^^^^^^^^^^\_______________________________________/^^^^^^^\_______________/^^^^^^
            DRAM_nCAS_A     ^^^^^^^^^^^^^^^^\___/^^^\___/^^^\___/^^^\___/^^^^^^^^^^^^^^^^^^^\___/^^^^^^^^^^^^^^
            DRAM_nCAS_B     ^^^^^^^^^^^^^^^^^^^^\___/^^^\___/^^^\___/^^^\___/^^^^^^^^^^^^^^^^^^^\___/^^^^^^^^^^
            DRAM_ADDR       ------------<===X=======X=======X=======X=======>-----------<===X=======>----------
            DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            DRAM_DATA       -------------------<>--<>--<>--<>--<>--<>--<>--<>------------------<>--<>----------
            DRAM_nWE        ^^^^^^^^^^^^\_______________________________________/^^^^^^^\_______________/^^^^^^
            DRAM_DATA       ----------------<===X===X===X===X===X===X===X===>---------------<===X===>----------
            CLK             \___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\__
        """

        prev_n_ras = Reg(self.n_ras)
        row_addr = Reg(self.addr, clock_en=~self.n_ras & prev_n_ras)
        if self.inv_clock:
            ram_clk = ~self.clk
        else:
            ram_clk = self.clk

        with ram_clk as clk:
            mem = Memory(MemoryConfig(
                (
                    MemoryPortConfig(addr_type=Unsigned(self.addr.get_num_bits()*2), data_type=self.data_in.get_net_type(), registered_input=True, registered_output=False),
                ),
                self.reset_content
            ))

            mem.addr <<= concat(row_addr, self.addr)
            mem.data_in <<= self.data_in
            self.data_out <<= mem.data_out
            mem.write_en <<= ~self.n_cas & ~self.n_we

class Sram(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    addr = Input()
    data_in = Input(BrewByte)
    data_out = Output(BrewByte)

    n_ce = Input(logic)
    n_we =  Input(logic)

    def construct(self, reset_content: Optional[str] = None):
        self.reset_content = reset_content

    def body(self):
        #self.data_out.set_net_type(self.data_in.get_net_type())

        mem = Memory(MemoryConfig(
            (
                MemoryPortConfig(addr_type=self.addr.get_net_type(), data_type=self.data_in.get_net_type(), registered_input=False, registered_output=True),
            ),
            self.reset_content
        ))

        mem.addr <<= self.addr
        mem.data_in <<= self.data_in
        self.data_out <<= mem.data_out
        mem.write_en <<= ~self.n_ce & ~self.n_we


class Gpio(Module):
    clk = ClkPort()
    rst = RstPort()

    #addr = Input()
    data_in = Input()
    data_out = Output()

    n_ce = Input(logic)
    n_we =  Input(logic)

    output_pins = Output()
    input_pins = Input()

    def construct(self, reset_content: Optional[str] = None):
        self.reset_content = reset_content

    def body(self):
        self.data_out.set_net_type(self.data_in.get_net_type())
        self.output_pins.set_net_type(self.data_in.get_net_type())
        #self.input_pins.set_net_type(self.data_in.get_net_type())

        self.output_pins <<= Reg(self.data_in, clock_en= ~self.n_ce & ~self.n_we)
        self.data_out <<= Reg(Reg(self.input_pins))


class Rom(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    addr = Input()
    data_out = Output(BrewByte)

    n_ce = Input(logic)

    def construct(self, reset_content: Optional[str]):
        self.reset_content = reset_content

    def body(self):
        mem = Memory(MemoryConfig(
            (
                MemoryPortConfig(addr_type=self.addr.get_net_type(), data_type=self.data_in.get_net_type(), registered_input=False, registered_output=True),
            ),
            self.reset_content
        ))

        mem.addr <<= self.addr
        self.data_out <<= mem.data_out


class AddrDecode(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    brew_if = Input(ExternalBusIf)
    addr = Output()

    def construct(self, decoder_map: Sequence[Tuple[str, int, int]]):
        self.enables = []
        for (name, base_addr, size) in decoder_map:
            if (size & (size-1)) != 0:
                raise SyntaxErrorException(f"Decoder for {name} must have a size that's a power of two. It is 0x{size:x}")
            if (base_addr & (size-1) != 0):
                raise SyntaxErrorException(f"Decoder for {name} must have a base address that's a multiple of it's size")
            # TODO: we should check for non-overlapping regions but that's hard(er), so I'm just going to leave it out for now
            port = Output(logic)
            setattr(self, name, port)
            data_port = Input()
            setattr(self, f"{name}_data_in", data_port)
            n_wait_port = Input(default_value=1)
            setattr(self, f"{name}_data_in", data_port)
            setattr(self, f"{name}_n_wait", n_wait_port)
            self.enables.append((port, data_port, n_wait_port, base_addr >> int(log2(size)), int(log2(size))))

    def body(self):
        prev_n_nren = Reg(self.brew_if.n_nren)

        row_addr = Reg(self.brew_if.addr, clock_en=~self.brew_if.n_nren & prev_n_nren)
        self.addr.set_net_type(Unsigned(self.brew_if.addr.get_num_bits()*2+1))
        self.addr <<= concat(row_addr, self.brew_if.addr, self.brew_if.n_cas_0)
        n_cas = self.brew_if.n_cas_0 & self.brew_if.n_cas_1

        data_mux_selectors = []
        n_wait_selectors = []
        for (port, data_port, n_wait_port, base_addr, size) in self.enables:
            # TODO: fix this syntax:
            #enable = (self.addr[:size] != base_addr) | (n_cas) | ~self.brew_if.bus_en
            enable = (self.addr[self.addr.get_num_bits()-1:size] != base_addr) | (n_cas) | ~self.brew_if.bus_en | self.brew_if.n_nren
            port <<= enable
            data_mux_selectors.append(~enable)
            data_mux_selectors.append(data_port)
            n_wait_selectors.append(~enable)
            n_wait_selectors.append(n_wait_port)
        del port
        del data_port
        del n_wait_port
        self.brew_if.data_in <<= SelectOne(*data_mux_selectors)
        self.brew_if.n_wait <<= SelectOne(*n_wait_selectors)





class FpgaSystem(GenericModule):
    clk = ClkPort()
    clk2 = ClkPort()
    rst = RstPort()

    brew_if = Input(ExternalBusIf)

    output_pins = Output(BrewByte)
    input_pins = Input(BrewByte)

    def construct(self, rom_content: str, dram0_content: str = None, dram1_content: str = None):
        self.rom_content = rom_content
        self.dram0_content = dram0_content
        self.dram1_content = dram1_content

    def body(self):
        dram0 = Dram(reset_content=self.dram0_content, inv_clock=True)
        dram1 = Dram(reset_content=self.dram1_content, inv_clock=False)
        rom = Sram(reset_content=self.rom_content)
        gpio = Gpio()

        decode_input = Wire(ExternalBusIf)
        decode = AddrDecode(
            (
                ("rom",  0x0000_0000, 0x0001_0000),
                ("gpio", 0x0001_0000, 0x0000_1000)
            )
        )

        self.brew_if.data_in <<= SelectOne(
            ~self.brew_if.n_ras_a & ~self.brew_if.n_cas_0, dram0.data_out,
            ~self.brew_if.n_ras_a & ~self.brew_if.n_cas_1, dram1.data_out,
            default_port = decode_input.data_in
        )

        # TODO: This should have blown up as both decode and the select above drives brew_if.data_in...
        #decode.brew_if <<= self.brew_if
        decode_input.n_ras_a       <<= self.brew_if.n_ras_a
        decode_input.n_ras_b       <<= self.brew_if.n_ras_b
        decode_input.n_cas_0       <<= self.brew_if.n_cas_0
        decode_input.n_cas_1       <<= self.brew_if.n_cas_1
        decode_input.addr          <<= self.brew_if.addr
        decode_input.n_we          <<= self.brew_if.n_we
        decode_input.data_out      <<= self.brew_if.data_out
        decode_input.data_out_en   <<= self.brew_if.data_out_en
        decode_input.n_nren        <<= self.brew_if.n_nren
        decode_input.n_dack        <<= self.brew_if.n_dack
        decode_input.tc            <<= self.brew_if.tc
        decode_input.bus_en        <<= self.brew_if.bus_en

        self.brew_if.n_wait        <<= decode_input.n_wait

        decode.clk <<= self.clk2
        decode.brew_if <<= decode_input

        dram0.clk     <<= self.clk2
        dram0.addr    <<= self.brew_if.addr
        dram0.data_in <<= self.brew_if.data_out
        dram0.n_ras   <<= self.brew_if.n_ras_a
        dram0.n_cas   <<= self.brew_if.n_cas_0
        dram0.n_we    <<= self.brew_if.n_we

        dram1.clk     <<= self.clk2
        dram1.addr    <<= self.brew_if.addr
        dram1.data_in <<= self.brew_if.data_out
        dram1.n_ras   <<= self.brew_if.n_ras_a
        dram1.n_cas   <<= self.brew_if.n_cas_1
        dram1.n_we    <<= self.brew_if.n_we

        rom.clk <<= self.clk2
        rom.addr <<= decode.addr
        rom.n_ce <<= decode.rom
        rom.data_in <<= self.brew_if.data_out
        rom.n_we <<= self.brew_if.n_we
        decode.rom_data_in <<= rom.data_out

        gpio.n_ce <<= decode.gpio
        gpio.n_we <<= self.brew_if.n_we
        gpio.data_in <<= self.brew_if.data_out
        decode.gpio_data_in <<= gpio.data_out

        gpio.input_pins <<= self.input_pins
        self.output_pins <<= gpio.output_pins


def sim():

    class test_top(Module):
        clk               = ClkPort()
        clk2              = ClkPort()
        rst               = RstPort()

        brew_if = Input(ExternalBusIf)

        output_pins = Output(BrewByte)
        input_pins = Input(BrewByte)

        def body(self):
            dut = FpgaSystem(rom_content=None)
            dut.clk <<= self.clk
            dut.clk2 <<= self.clk2
            dut.brew_if <<= self.brew_if
            dut.input_pins <<= self.input_pins
            self.output_pins <<= dut.output_pins

        def simulate(self, simulator: Simulator):
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_neg_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Negative:
                    yield (self.clk, )

            def wait_rst():
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()

            """
                CLK             \___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\__
                CLK2            \_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/^\_/
                DRAM_nRAS       ^^^^^^^^^^^^\_______________________________________/^^^^^^^\_______________/^^^^^^
                DRAM_nCAS_A     ^^^^^^^^^^^^^^^^\___/^^^\___/^^^\___/^^^\___/^^^^^^^^^^^^^^^^^^^\___/^^^^^^^^^^^^^^
                DRAM_nCAS_B     ^^^^^^^^^^^^^^^^^^^^\___/^^^\___/^^^\___/^^^\___/^^^^^^^^^^^^^^^^^^^\___/^^^^^^^^^^
                DRAM_ADDR       ------------<===X=======X=======X=======X=======>-----------<===X=======>----------
                DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                DRAM_DATA       -------------------<>--<>--<>--<>--<>--<>--<>--<>------------------<>--<>----------
                DRAM_nWE        ^^^^^^^^^^^^\_______________________________________/^^^^^^^\_______________/^^^^^^
                DRAM_DATA       ----------------<===X===X===X===X===X===X===X===>---------------<===X===>----------
                CLK             \___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\___/^^^\__
            """

            def write_dram(addr, values):
                self.brew_if.n_nren <<= 1
                self.brew_if.n_ras_a <<= 1
                self.brew_if.n_ras_b <<= 1
                self.brew_if.n_cas_0 <<= 1
                self.brew_if.n_cas_1 <<= 1
                self.brew_if.n_we <<= 1
                self.brew_if.data_out <<= None
                self.brew_if.addr <<= None
                row_addr = (addr >> 12) & ((1 <<11) - 1)
                col_addr = (addr >>  0) & ((1 <<12) - 1) # col_addr contains the byte-select in it's LSB
                yield from wait_clk()
                self.brew_if.n_ras_a <<= 0
                self.brew_if.addr <<= row_addr
                self.brew_if.n_we <<= 0
                for value in values:
                    if (col_addr & 1) == 0:
                        yield from wait_neg_clk()
                        self.brew_if.n_cas_0 <<= 0
                        self.brew_if.n_cas_1 <<= 1
                    else:
                        yield from wait_clk()
                        self.brew_if.n_cas_0 <<= 1
                        self.brew_if.n_cas_1 <<= 0
                    self.brew_if.data_out <<= value
                    self.brew_if.addr <<= col_addr >> 1
                    col_addr += 1
                if (col_addr & 1) == 0:
                    yield from wait_neg_clk()
                else:
                    yield from wait_clk()
                self.brew_if.n_cas_0 <<= 1
                self.brew_if.n_cas_1 <<= 1
                yield from wait_clk()
                self.brew_if.n_ras_a <<= 1
                self.brew_if.n_we <<= 1
                yield from wait_clk()

            def read_dram(addr, length):
                self.brew_if.n_nren <<= 1
                self.brew_if.n_ras_a <<= 1
                self.brew_if.n_ras_b <<= 1
                self.brew_if.n_cas_0 <<= 1
                self.brew_if.n_cas_1 <<= 1
                self.brew_if.n_we <<= 1
                self.brew_if.data_out <<= None
                self.brew_if.addr <<= None
                row_addr = (addr >> 12) & ((1 <<11) - 1)
                col_addr = (addr >>  0) & ((1 <<12) - 1) # col_addr contains the byte-select in it's LSB
                yield from wait_clk()
                self.brew_if.n_ras_a <<= 0
                self.brew_if.addr <<= row_addr
                ret_val = bytearray(b"")
                first = True
                for _ in range(length):
                    if (col_addr & 1) == 0:
                        yield from wait_neg_clk()
                        self.brew_if.n_cas_0 <<= 0
                        self.brew_if.n_cas_1 <<= 1
                    else:
                        yield from wait_clk()
                        self.brew_if.n_cas_0 <<= 1
                        self.brew_if.n_cas_1 <<= 0
                    self.brew_if.addr <<= col_addr >> 1
                    col_addr += 1
                    if not first:
                        simulator.log(f"returning {self.brew_if.data_in}")
                        ret_val.append(int(self.brew_if.data_in.sim_value.value))
                        pass
                    first = False
                if (col_addr & 1) == 0:
                    yield from wait_neg_clk()
                else:
                    yield from wait_clk()
                simulator.log(f"returning {self.brew_if.data_in}")
                ret_val.append(int(self.brew_if.data_in.sim_value.value))
                self.brew_if.n_cas_0 <<= 1
                self.brew_if.n_cas_1 <<= 1
                yield from wait_clk()
                self.brew_if.n_ras_a <<= 1
                self.brew_if.n_we <<= 1
                yield from wait_clk()
                return ret_val


            def write_nram(addr, values):
                self.brew_if.n_nren <<= 1
                self.brew_if.n_ras_a <<= 1
                self.brew_if.n_ras_b <<= 1
                self.brew_if.n_cas_0 <<= 1
                self.brew_if.n_cas_1 <<= 1
                self.brew_if.n_we <<= 1
                self.brew_if.data_out <<= None
                self.brew_if.addr <<= None
                row_addr = (addr >> 12) & ((1 <<11) - 1)
                col_addr = (addr >>  0) & ((1 <<12) - 1) # col_addr contains the byte-select in it's LSB
                yield from wait_clk()
                self.brew_if.n_nren <<= 0
                self.brew_if.addr <<= row_addr
                self.brew_if.n_we <<= 0
                for value in values:
                    if (col_addr & 1) == 0:
                        yield from wait_clk()
                        self.brew_if.n_cas_0 <<= 0
                        self.brew_if.n_cas_1 <<= 1
                    else:
                        yield from wait_clk()
                        self.brew_if.n_cas_0 <<= 1
                        self.brew_if.n_cas_1 <<= 0
                    self.brew_if.data_out <<= value
                    self.brew_if.addr <<= col_addr >> 1
                    col_addr += 1
                if (col_addr & 1) == 0:
                    yield from wait_clk()
                else:
                    yield from wait_clk()
                self.brew_if.n_cas_0 <<= 1
                self.brew_if.n_cas_1 <<= 1
                yield from wait_clk()
                self.brew_if.n_nren <<= 1
                self.brew_if.n_we <<= 1
                yield from wait_clk()

            def read_nram(addr, length):
                self.brew_if.n_nren <<= 1
                self.brew_if.n_ras_a <<= 1
                self.brew_if.n_ras_b <<= 1
                self.brew_if.n_cas_0 <<= 1
                self.brew_if.n_cas_1 <<= 1
                self.brew_if.n_we <<= 1
                self.brew_if.data_out <<= None
                self.brew_if.addr <<= None
                row_addr = (addr >> 12) & ((1 <<11) - 1)
                col_addr = (addr >>  0) & ((1 <<12) - 1) # col_addr contains the byte-select in it's LSB
                yield from wait_clk()
                self.brew_if.n_nren <<= 0
                self.brew_if.addr <<= row_addr
                ret_val = bytearray(b"")
                first = True
                for _ in range(length):
                    if (col_addr & 1) == 0:
                        yield from wait_clk()
                        self.brew_if.n_cas_0 <<= 0
                        self.brew_if.n_cas_1 <<= 1
                    else:
                        yield from wait_clk()
                        self.brew_if.n_cas_0 <<= 1
                        self.brew_if.n_cas_1 <<= 0
                    self.brew_if.addr <<= col_addr >> 1
                    col_addr += 1
                    if not first:
                        simulator.log(f"returning {self.brew_if.data_in}")
                        ret_val.append(int(self.brew_if.data_in.sim_value.value))
                        pass
                    first = False
                if (col_addr & 1) == 0:
                    yield from wait_clk()
                else:
                    yield from wait_clk()
                simulator.log(f"returning {self.brew_if.data_in}")
                ret_val.append(int(self.brew_if.data_in.sim_value.value))
                self.brew_if.n_cas_0 <<= 1
                self.brew_if.n_cas_1 <<= 1
                yield from wait_clk()
                self.brew_if.n_nren <<= 1
                self.brew_if.n_we <<= 1
                yield from wait_clk()
                return ret_val

            self.brew_if.bus_en <<= 1
            self.brew_if.n_nren <<= 1
            self.brew_if.n_ras_a <<= 1
            self.brew_if.n_ras_b <<= 1
            self.brew_if.n_cas_0 <<= 1
            self.brew_if.n_cas_1 <<= 1
            self.brew_if.n_we <<= 1
            self.brew_if.data_out <<= None
            self.brew_if.addr <<= None

            yield from wait_rst()
            for _ in range(3):
                yield from wait_clk()
            # Set up both UARTs to the same config
            yield from write_dram(0x0000_1020, b"\01\02\03\04")
            for _ in range(10):
                yield from wait_clk()
            readback = yield from read_dram(0x0000_1020, 4)
            assert readback == b"\01\02\03\04"
            for _ in range(10):
                yield from wait_clk()
            yield from write_nram(0x0000_1020, b"\11\12\13\14")
            for _ in range(10):
                yield from wait_clk()
            readback = yield from read_nram(0x0000_1020, 4)
            assert readback == b"\11\12\13\14"

            for _ in range(10):
                yield from wait_clk()

            yield from write_nram(0x0001_0000, b"\xaa")
            yield from wait_clk()
            assert self.output_pins == 0xaa
            self.input_pins <<= 0xf0
            readback = yield from read_nram(0x0001_0000, 1)
            assert readback == b"\xf0"


    class top(Module):
        clk               = ClkPort()
        clk2              = ClkPort()
        rst               = RstPort()

        def body(self):
            local_top = test_top()
            local_top.clk <<= self.clk
            local_top.clk2 <<= self.clk2


        def simulate(self, simulator: Simulator) -> TSimEvent:
            clk_period = 100
            clk_ratio = 5

            clk_wait = clk_period // 2
            clk2_wait = clk_wait // clk_ratio

            def clk() -> int:
                self.clk <<= 1
                self.clk2 <<= 1
                for _ in range(clk_ratio):
                    yield clk2_wait
                    self.clk2 <<= ~self.clk2
                self.clk <<= ~self.clk
                for _ in range(clk_ratio):
                    yield clk2_wait
                    self.clk2 <<= ~self.clk2

            #self.program()
            simulator.log("Simulation started")

            self.rst <<= 1
            self.clk <<= 1
            yield 10
            for i in range(5):
                yield from clk()
            self.rst <<= 0

            for i in range(150):
                yield from clk()
            yield 10
            simulator.log("Done")

    top_class = top
    vcd_filename = "fpga_system.vcd"
    if vcd_filename is None:
        vcd_filename = top_class.__name__.lower()
    with Netlist().elaborate() as netlist:
        top_inst = top_class()
    netlist.simulate(vcd_filename, add_unnamed_scopes=False)

def gen():
    def top():
        return FpgaSystem

    netlist = Build.generate_rtl(top, "fpga_system.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(target_dir="q_fpga_system", top_level=top_level_name, source_files=("fpga_system.sv",), clocks=(("clk", 10), ("clk2", 50)), project_name="fpga_system")
    flow.generate()
    flow.run()


if __name__ == "__main__":
    #gen()
    sim()

