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

    def construct(self, init_content: Optional[str] = None):
        self.init_content = init_content

    def body(self):
        self.data_out.set_net_type(self.data_in.get_net_type())

        # A read will happen in every clock cycle when both n_ras and n_cas asserted
        # A write however will only happen on the falling edge of all three control signals
        #
        # Both row and column addresses are latched on the respective edges of the control signals

        def fall_edge_detect(signal):
            was = Reg(signal)
            return was & ~signal

        n_is_write = self.n_cas | self.n_ras | self.n_we

        do_write =  fall_edge_detect(Reg(n_is_write, reset_value_port = 1))
        latch_row = fall_edge_detect(Reg(self.n_ras, reset_value_port = 1))
        latch_col = fall_edge_detect(Reg(self.n_cas, reset_value_port = 1))

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

        row_addr = Reg(self.addr, clock_en=latch_row)
        col_addr = Select(latch_col, Reg(self.addr, clock_en=latch_col), self.addr)

        mem = Memory(MemoryConfig(
            (
                MemoryPortConfig(addr_type=Unsigned(self.addr.get_num_bits()*2), data_type=self.data_in.get_net_type(), registered_input=True, registered_output=False),
            ),
            self.init_content
        ))

        mem.addr <<= concat(row_addr, col_addr)
        mem.data_in <<= self.data_in
        self.data_out <<= mem.data_out
        mem.write_en <<= do_write

class Sram(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    addr = Input()
    data_in = Input(BrewByte)
    data_out = Output(BrewByte)

    n_ce = Input(logic)
    n_we =  Input(logic)

    def construct(self, init_content: Optional[str] = None):
        self.init_content = init_content

    def body(self):
        #self.data_out.set_net_type(self.data_in.get_net_type())

        mem = Memory(MemoryConfig(
            (
                MemoryPortConfig(addr_type=self.addr.get_net_type(), data_type=self.data_in.get_net_type(), registered_input=False, registered_output=True),
            ),
            self.init_content
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

    def construct(self, init_content: Optional[str] = None):
        self.init_content = init_content

    def body(self):
        self.data_out.set_net_type(self.data_in.get_net_type())
        self.output_pins.set_net_type(self.data_in.get_net_type())
        #self.input_pins.set_net_type(self.data_in.get_net_type())

        self.output_pins <<= Reg(self.data_in, clock_en= ~self.n_ce & ~self.n_we)
        self.data_out <<= Reg(Reg(self.input_pins))


class ApbBridge(Module):
    clk = ClkPort()
    rst = RstPort()

    apb_out = Output(Apb8If)

    n_ce = Input(logic)
    n_we = Input(logic)
    n_wait = Output(logic)

    addr = Input()
    data_in = Input(BrewByte)
    data_out = Output(BrewByte)

    def body(self):
        self.apb_out.paddr <<= Reg(self.addr, clock_en=~self.n_ce)
        self.apb_out.pwdata <<= Reg(self.data_in, clock_en=~self.n_ce)
        self.apb_out.pwrite <<= Reg(~self.n_we, clock_en=~self.n_ce)
        apb_done = (self.apb_out.penable & self.apb_out.pready)
        served = Wire(logic)
        served <<= Reg(Select(
            self.n_ce,
            apb_done | served,
            0
        ))
        self.apb_out.psel <<= Reg(Select(
            self.apb_out.psel,
            ~self.n_ce & ~served,
            ~apb_done
        ))
        self.apb_out.penable <<= Reg(Select(
            self.apb_out.penable,
            self.apb_out.psel & ~served,
            ~apb_done
        ))
        self.data_out <<= Select(apb_done, Reg(self.apb_out.prdata, clock_en=apb_done), self.apb_out.prdata)
        self.n_wait <<= apb_done | self.n_ce | served


class Rom(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    addr = Input()
    data_out = Output(BrewByte)

    n_ce = Input(logic)

    def construct(self, init_content: Optional[str]):
        self.init_content = init_content

    def body(self):
        mem = Memory(MemoryConfig(
            (
                MemoryPortConfig(addr_type=self.addr.get_net_type(), data_type=self.data_in.get_net_type(), registered_input=False, registered_output=True),
            ),
            self.init_content
        ))

        mem.addr <<= self.addr
        self.data_out <<= mem.data_out


class AddrDecode(GenericModule):
    clk = ClkPort()
    #rst = RstPort()

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
            n_enable = (self.addr[self.addr.get_num_bits()-1:size] != base_addr) | (n_cas) | ~self.brew_if.bus_en | self.brew_if.n_nren #| self.rst
            port <<= Reg(n_enable)
            data_mux_selectors.append(~n_enable)
            data_mux_selectors.append(data_port)
            n_wait_selectors.append(~n_enable)
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

    io_apb_if = Output(Apb8If)
    #io_interrupt = Input(logic)

    output_pins = Output(BrewByte)
    input_pins = Input(BrewByte)

    output_pins2 = Output(BrewByte)
    input_pins2 = Input(BrewByte)

    n_int = Output(logic)
    is_sim = Input(logic)

    rom_base =      0x0000_0000
    gpio_base =     0x0001_0000
    gpio2_base =    0x0001_1000
    gpio_int_base = 0x0001_2000
    io_apb_base =   0x0002_0000
    io_apb_size =   4096*16
    gpio_size =     4096
    dram_base =     0x8000_0000

    def construct(self, rom_content: str, *, dram_size: int = 128*1024, rom_size: int = 8*1024, dram0_content: str = None, dram1_content: str = None):
        self.rom_content = rom_content
        self.dram0_content = dram0_content
        self.dram1_content = dram1_content
        self.dram_size = dram_size
        self.rom_size = rom_size

    def body(self):
        dram_addr_width = int(log2(self.dram_size/2))//2

        dram0 = Dram(init_content=self.dram0_content)
        dram1 = Dram(init_content=self.dram1_content)
        rom = Sram(init_content=self.rom_content)
        gpio = Gpio()
        gpio2 = Gpio()
        gpio_int = Gpio()
        apb_bridge = ApbBridge()

        ext_if_data_out_r = Reg(self.brew_if.data_out, clock_port=self.clk2)
        ext_if_data_out_0 = Reg(ext_if_data_out_r, clock_port=self.clk2)
        ext_if_n_ras_a = Reg(self.brew_if.n_ras_a, clock_port=self.clk2, reset_value_port=1)
        ext_if_n_ras_b = Reg(self.brew_if.n_ras_b, clock_port=self.clk2, reset_value_port=1)
        ext_if_n_cas_0 = Reg(self.brew_if.n_cas_0, clock_port=self.clk2, reset_value_port=1)
        ext_if_n_cas_1 = Reg(self.brew_if.n_cas_1, clock_port=self.clk2, reset_value_port=1)
        ext_if_addr = Reg(self.brew_if.addr, clock_port=self.clk2)
        ext_if_n_we = Reg(self.brew_if.n_we, clock_port=self.clk2, reset_value_port=1)
        ext_if_data_out_en = Reg(self.brew_if.data_out_en, clock_port=self.clk2)
        ext_if_n_nren = Reg(self.brew_if.n_nren, clock_port=self.clk2, reset_value_port=1)
        ext_if_n_dack = Reg(self.brew_if.n_dack, clock_port=self.clk2, reset_value_port=1)
        ext_if_bus_en = Reg(self.brew_if.bus_en, clock_port=self.clk2)
        ext_if_tc = Reg(self.brew_if.tc, clock_port=self.clk2)
        #data_in       = Reverse(BrewByte)
        #n_wait        = Reverse(logic)

        decode_input = Wire(ExternalBusIf)
        decode = AddrDecode(
            (
                ("rom",        self.rom_base,        self.rom_size),
                ("gpio",       self.gpio_base,       self.gpio_size),
                ("gpio2",      self.gpio2_base,      self.gpio_size),
                ("gpio_int",   self.gpio_int_base,   self.gpio_size),
                ("io_apb",     self.io_apb_base,     self.io_apb_size)
            )
        )

        self.brew_if.data_in <<= SelectOne(
            ~ext_if_n_ras_a & ~ext_if_n_cas_0, dram0.data_out,
            ~ext_if_n_ras_a & ~ext_if_n_cas_1, dram1.data_out,
            default_port = decode_input.data_in
        )

        # TODO: This should have blown up as both decode and the select above drives brew_if.data_in...
        #decode.brew_if <<= self.brew_if
        decode_input.n_ras_a       <<= ext_if_n_ras_a
        decode_input.n_ras_b       <<= ext_if_n_ras_b
        decode_input.n_cas_0       <<= ext_if_n_cas_0
        decode_input.n_cas_1       <<= ext_if_n_cas_1
        decode_input.addr          <<= ext_if_addr
        decode_input.n_we          <<= ext_if_n_we
        decode_input.data_out      <<= ext_if_data_out_0
        decode_input.data_out_en   <<= ext_if_data_out_en
        decode_input.n_nren        <<= ext_if_n_nren
        decode_input.n_dack        <<= ext_if_n_dack
        decode_input.tc            <<= ext_if_tc
        decode_input.bus_en        <<= ext_if_bus_en

        self.brew_if.n_wait        <<= decode_input.n_wait

        decode.clk <<= self.clk2
        decode.brew_if <<= decode_input

        # We support 128kByte of DRAM.
        dram0.clk     <<= ~self.clk2
        dram0.addr    <<= self.brew_if.addr[dram_addr_width-1:0]
        dram0.data_in <<= self.brew_if.data_out
        dram0.n_ras   <<= self.brew_if.n_ras_a
        dram0.n_cas   <<= self.brew_if.n_cas_0
        dram0.n_we    <<= self.brew_if.n_we

        dram1.clk     <<= ~self.clk2
        dram1.addr    <<= self.brew_if.addr[dram_addr_width-1:0]
        dram1.data_in <<= self.brew_if.data_out
        dram1.n_ras   <<= self.brew_if.n_ras_a
        dram1.n_cas   <<= self.brew_if.n_cas_1
        dram1.n_we    <<= self.brew_if.n_we

        # We have 8kB of ROM (SRAM really)
        rom.clk <<= self.clk2
        rom.addr <<= decode.addr[12:0]
        rom.n_ce <<= decode.rom
        rom.data_in <<= ext_if_data_out_0
        rom.n_we <<= ext_if_n_we
        decode.rom_data_in <<= rom.data_out

        gpio.n_ce <<= decode.gpio
        gpio.n_we <<= ext_if_n_we
        gpio.data_in <<= ext_if_data_out_0
        decode.gpio_data_in <<= gpio.data_out

        gpio.input_pins <<= self.input_pins
        self.output_pins <<= gpio.output_pins

        gpio2.n_ce <<= decode.gpio2
        gpio2.n_we <<= ext_if_n_we
        gpio2.data_in <<= ext_if_data_out_0
        decode.gpio2_data_in <<= gpio2.data_out

        gpio2.input_pins <<= self.input_pins2
        self.output_pins2 <<= gpio2.output_pins

        gpio_int.n_ce <<= decode.gpio_int
        gpio_int.n_we <<= ext_if_n_we
        gpio_int.data_in <<= ext_if_data_out_0
        decode.gpio_int_data_in <<= gpio_int.data_out
        self.n_int <<= ~gpio_int.output_pins[0]

        gpio_int.input_pins <<= self.is_sim

        apb_bridge.clk <<= self.clk2
        apb_bridge.addr <<= decode.addr[15:0]

        apb_bridge.n_ce <<= decode.io_apb
        apb_bridge.n_we <<= ext_if_n_we
        decode.io_apb_n_wait <<= apb_bridge.n_wait

        apb_bridge.data_in <<= ext_if_data_out_0
        decode.io_apb_data_in <<= apb_bridge.data_out

        self.io_apb_if <<= apb_bridge.apb_out

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

            dut.io_apb_if.prdata <<= Select(
                dut.io_apb_if.psel & dut.io_apb_if.penable,
                None,
                dut.io_apb_if.paddr[7:0]
            )
            dut.io_apb_if.pready <<= 1

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

            for _ in range(10):
                yield from wait_clk()

            yield from write_nram(0x0002_0000, b"\xaa")
            yield from wait_clk()
            readback = yield from read_nram(0x0002_0001, 1)
            assert readback == b"\x01"


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


