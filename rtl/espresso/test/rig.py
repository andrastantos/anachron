from brew_v1 import BrewV1Top
from brew_types import *
from assembler import *
from silicon import *

con_base = 0x0001_0000

class RegFileLeech(Module):
    clk = ClkPort()
    rst = RstPort()

    def set_reg_file(self, reg_file: 'RegFile'):
        self.reg_file = reg_file
        self.wb_if = reg_file.write
    def simulate(self, simulator: Simulator):
        def wait_clk():
            yield self.clk
            while self.clk.get_sim_edge() != EdgeType.Positive:
                yield self.clk

        while True:
            yield from wait_clk()
            if self.wb_if.valid == 1 and self.wb_if.data_en == 1:
                reg_name = f"$r{self.wb_if.addr}"
                reg_value = f"{self.wb_if.data:08x} ({self.wb_if.data})"
                simulator.log(f"                          <<<<<<<<<< {reg_name} <= {reg_value}")

class ExecLeech(Module):
    clk = ClkPort()
    rst = RstPort()

    def set_execute(self, execute: 'ExecuteStage'):
        self.execute = execute
        self.do_branch = execute.do_branch
        self.tpc = execute.tpc_in
        self.spc = execute.spc_in
        self.task_mode = execute.task_mode_in
        self.exec_input = execute.input_port
    def simulate(self, simulator: Simulator):
        def wait_clk():
            yield self.clk
            while self.clk.get_sim_edge() != EdgeType.Positive:
                yield self.clk

        while True:
            yield from wait_clk()
            if (self.exec_input.valid & self.exec_input.ready) == 1:
                b = "SKIP" if self.do_branch == 1 else "Exec"
                if self.task_mode == 0:
                    prefix = "S"
                    pc = self.spc
                else:
                    prefix = "T"
                    pc = self.tpc
                if self.do_branch == 0:
                    simulator.log(f"{b}: {prefix}{(pc << 1):08x}")

class LdStLeech(Module):
    clk = ClkPort()
    rst = RstPort()

    def set_execute(self, execute: 'ExecuteStage'):
        self.execute = execute
        self.bus_req_if = execute.bus_req_if
        self.bus_rsp_if = execute.bus_rsp_if
    def simulate(self, simulator: Simulator):
        def wait_clk():
            yield self.clk
            while self.clk.get_sim_edge() != EdgeType.Positive:
                yield self.clk

        while True:
            yield from wait_clk()
            if (self.bus_req_if.valid & self.bus_req_if.ready) == 1:
                simulator.sim_assert(self.bus_req_if.byte_en != 0)
                if self.bus_req_if.byte_en == 1:
                    addr = self.bus_req_if.addr*2
                    access_size = 8
                if self.bus_req_if.byte_en == 2:
                    addr = self.bus_req_if.addr*2 + 1
                    access_size = 8
                if self.bus_req_if.byte_en == 3:
                    addr = self.bus_req_if.addr*2
                    access_size = 16
                if self.bus_req_if.read_not_write == 1:
                    mode = "reading"
                    value = ""
                elif self.bus_req_if.read_not_write == 0:
                    mode = "writing"
                    value = f" with value {self.bus_req_if.data:04x} ({self.bus_req_if.data})"
                else:
                    mode = "NONE"
                simulator.log(f"                          ---------- {mode} {access_size}-bit memory addr {addr:08x}{value}")

from copy import copy
class Dram(GenericModule):
    n_ras         = Input(logic)
    n_cas         = Input(logic)
    addr          = Input()
    n_we          = Input(logic)
    data_out      = Output(BrewByte)
    data_out_en   = Output(logic)
    data_in       = Input(BrewByte)
    data_in_en    = Input(logic)

    def construct(self, name:str, latency: int = 30, hold_time: int = 20):
        self.latency = latency
        self.hold_time = hold_time
        self.content = {}
        self.name = name

    def clear(self):
        self.content = {}

    def set_mem(self, addr: int, data: ByteString):
        for ofs, byte in enumerate(data):
            print(f"-------- programming DRAM {self.name} at address {addr+ofs:08x} with {byte:02x}")
            self.content[ofs+addr] = byte

    def get_mem(self, addr: int) -> Optional[int]:
        return self.content.get(addr, None)

    def simulate(self, simulator: Simulator):
        self.data_out <<= None
        self.data_out_en <<= 0
        while True:
            yield self.n_ras
            if self.n_ras.get_sim_edge() == EdgeType.Positive:
                # Get got deselected
                self.data_out <<= None
                self.data_out_en <<= 0
            elif self.n_ras.get_sim_edge() == EdgeType.Negative:
                simulator.sim_assert(self.n_cas == 1, f"DRAM {self.name}: n_ras should not assert while n_cas is low")
                row_addr = copy(self.addr.sim_value)
                while True:
                    yield self.n_cas, self.n_ras
                    if self.n_ras.get_sim_edge() == EdgeType.Positive:
                        # End of burst
                        break
                    simulator.sim_assert(self.n_ras.get_sim_edge() == EdgeType.NoEdge)
                    if self.n_cas.get_sim_edge() == EdgeType.Negative:
                        yield 0
                        yield 0
                        col_addr = copy(self.addr.sim_value)
                        addr = row_addr << self.addr.get_num_bits() | col_addr
                        if self.n_we == 1:
                            try:
                                value = self.content[addr]
                            except KeyError:
                                value = None
                            val_str = "--" if value is None else f"{value:02x}"
                            #simulator.log(f"                                              DRAM {self.name} Reading address {addr:08x}, returning {val_str}")
                            yield self.latency
                            self.data_out <<= value
                            self.data_out_en <<= 1
                        elif self.n_we == 0:
                            value = None if self.data_in_en != 1 else self.data_in
                            self.content[addr] = int(value)
                            val_str = "--" if value is None else f"{value:02x}"
                            #simulator.log(f"                                              DRAM {self.name} Writing address {addr:08x} with value {val_str}")
                            self.data_out <<= None
                            self.data_out_en <<= 0
                    elif self.n_cas.get_sim_edge() == EdgeType.Positive:
                        if self.n_we == 1:
                            yield self.hold_time
                            self.data_out <<= None
                            self.data_out_en <<= 0
                    else:
                        simulator.sim_assert(f"Unexpected n_cas edge: {self.n_cas.get_sim_edge()}")

class AddressDecode(Module):
    n_nren        = Input(logic)
    n_cas_0       = Input(logic)
    n_cas_1       = Input(logic)
    addr          = Input(Unsigned(11))
    full_addr     = Output(Unsigned(23))
    rom_en        = Output(logic)
    con_en        = Output(logic)

    def body(self):
        self.n_cas = Wire(logic)
        self.n_cas <<= self.n_cas_0 & self.n_cas_1

    def simulate(self, simulator: Simulator):
        global con_base
        self.rom_base = 0x0000_0000
        self.con_base = con_base
        self.decode_mask = 0xffff_0000
        self.rom_en <<= 0
        self.con_en <<= 0
        while True:
            yield self.n_nren
            if self.n_nren.get_sim_edge() == EdgeType.Negative:
                simulator.sim_assert(self.n_cas == 1, "n_nren should not assert while n_cas is low")
                row_addr = copy(self.addr.sim_value)
                while True:
                    yield self.n_cas, self.n_nren
                    if self.n_nren.get_sim_edge() == EdgeType.Positive:
                        # End of burst
                        self.rom_en <<= 0
                        self.con_en <<= 0
                        break
                    simulator.sim_assert(self.n_nren.get_sim_edge() == EdgeType.NoEdge)
                    if self.n_cas.get_sim_edge() == EdgeType.Negative:
                        col_addr = copy(self.addr.sim_value)
                        addr = (row_addr << self.addr.get_num_bits() | col_addr) << 1 | self.n_cas_0
                        self.full_addr <<= addr
                        if (addr & self.decode_mask) == self.con_base:
                            self.con_en <<= 1
                            self.rom_en <<= 0
                        elif (addr & self.decode_mask) == self.rom_base:
                            self.con_en <<= 0
                            self.rom_en <<= 1
                        else:
                            self.con_en <<= 0
                            self.rom_en <<= 0
                    elif self.n_cas.get_sim_edge() == EdgeType.Positive:
                        self.rom_en <<= 0
                        self.con_en <<= 0
                    else:
                        simulator.sim_assert(f"Unexpected n_cas edge: {self.n_cas.get_sim_edge()}")

class Rom(GenericModule):
    enable        = Input(logic)
    addr          = Input(Unsigned(23))
    data_out      = Output(BrewByte)
    data_out_en   = Output(logic)

    def append(self, words):
        for word in words:
            self.content.append((word >> 0) & 0xff)
            self.content.append((word >> 8) & 0xff)

    def set_mem(self, addr: int, data: ByteString):
        while self.get_size() < addr:
            self.content.append(None)
        for byte in data:
            self.content.append(byte)

    def get_mem(self, addr: int) -> Optional[int]:
        try:
            return self.content[addr]
        except IndexError:
            return None

    def get_size(self):
        return len(self.content)

    def construct(self, latency: int = 80, hold_time: int = 20):
        self.latency = latency
        self.hold_time = hold_time
        self.content = []

    def clear(self):
        self.content = []

    def simulate(self, simulator: Simulator) -> TSimEvent:
        self.data_out <<= None
        self.data_out_en <<= 0
        while True:
            yield self.enable
            if self.enable.get_sim_edge() == EdgeType.Positive:
                # Got selected
                try:
                    value = self.content[int(self.addr)]
                except IndexError:
                    value = None
                val_str = "--" if value is None else f"{value:02x}"
                #simulator.log(f"ROM Reading address {self.addr:08x}, returning {val_str}")
                yield self.latency
                self.data_out <<= value
                self.data_out_en <<= 1
            elif self.enable.get_sim_edge() == EdgeType.Negative:
                yield self.hold_time
                self.data_out <<= None
                self.data_out_en <<= 0
            else:
                simulator.sim_assert(f"Unexpected ROM enable edge: {self.enable.get_sim_edge()}")

class Console(Module):
    enable        = Input(logic)
    addr          = Input(Unsigned(23))
    n_we          = Input(logic)
    data_in       = Input(BrewByte)
    data_in_en    = Input(logic)
    terminate     = Output(logic)

    def simulate(self, simulator: Simulator) -> TSimEvent:
        self.terminate <<= 0
        while True:
            yield self.enable
            if self.enable.get_sim_edge() == EdgeType.Positive:
                if self.n_we == 0:
                    value = None if self.data_in_en != 1 else self.data_in
                    val_str = "--" if value is None else f"{value:02x}"
                    addr = self.addr & 0xff
                    if addr == 0:
                        simulator.log(f"CONSOLE got value {val_str}")
                    if addr == 4:
                        simulator.log(f"SUCCESS")
                        self.terminate <<= 1
                    if addr == 8:
                        simulator.log(f"FAIL")
                        assert(False)
                        self.terminate <<= 1
            elif self.enable.get_sim_edge() == EdgeType.Negative:
                pass
            else:
                simulator.sim_assert(f"Unexpected CONSOLE enable edge: {self.enable.get_sim_edge()}")


class top(Module):
    clk               = ClkPort()
    rst               = RstPort()

    nram_base = 0x000_0000
    dram_base = 0x800_0000

    def construct(self):
        self.pc = 0
        self.asm = BrewAssembler()
        self.default_timeout = 1500
        self.timeout = self.default_timeout

    def body(self):
        self.cpu = BrewV1Top(nram_base=self.nram_base >> 26, has_multiply=True, has_shift=True, page_bits=7)
        self.dram_l = Dram(name="l")
        self.dram_h = Dram(name="h")
        self.addr_decode = AddressDecode()
        self.rom = Rom()
        self.con = Console()
        self.rf_leech = RegFileLeech()
        self.exec_leech = ExecLeech()
        self.ldst_leech = LdStLeech()

        self.dram_l.n_ras         <<= self.cpu.dram.n_ras_a
        self.dram_l.n_cas         <<= self.cpu.dram.n_cas_0
        self.dram_l.addr          <<= self.cpu.dram.addr[7:0]
        self.dram_l.n_we          <<= self.cpu.dram.n_we
        self.dram_l.data_in       <<= self.cpu.dram.data_out
        self.dram_l.data_in_en    <<= self.cpu.dram.data_out_en

        self.dram_h.n_ras         <<= self.cpu.dram.n_ras_a
        self.dram_h.n_cas         <<= self.cpu.dram.n_cas_1
        self.dram_h.addr          <<= self.cpu.dram.addr[7:0]
        self.dram_h.n_we          <<= self.cpu.dram.n_we
        self.dram_h.data_in       <<= self.cpu.dram.data_out
        self.dram_h.data_in_en    <<= self.cpu.dram.data_out_en

        self.cpu.dram.data_in     <<= SelectOne(
            self.dram_l.data_out_en, self.dram_l.data_out,
            self.dram_h.data_out_en, self.dram_h.data_out,
            self.rom.data_out_en,    self.rom.data_out,
        )

        self.addr_decode.n_nren   <<= self.cpu.dram.n_nren
        self.addr_decode.n_cas_0  <<= self.cpu.dram.n_cas_0
        self.addr_decode.n_cas_1  <<= self.cpu.dram.n_cas_1
        self.addr_decode.addr     <<= self.cpu.dram.addr

        self.rom.enable           <<= self.addr_decode.rom_en
        self.rom.addr             <<= self.addr_decode.full_addr
        self.con.enable           <<= self.addr_decode.con_en
        self.con.addr             <<= self.addr_decode.full_addr
        self.con.n_we             <<= self.cpu.dram.n_we

        self.cpu.dram.n_wait      <<= 1
        self.cpu.drq              <<= 0
        self.cpu.n_int            <<= 1

    def set_timeout(self, timeout):
        self.timeout = timeout

    def simulate(self, simulator: Simulator) -> TSimEvent:
        def get_reg_file():
            reg_file = first(first(self.cpu.get_inner_objects("pipeline")).get_inner_objects("reg_file"))
            return reg_file

        def get_exec():
            exec = first(first(self.cpu.get_inner_objects("pipeline")).get_inner_objects("execute_stage"))
            return exec

        self.rf_leech.set_reg_file(get_reg_file())
        self.exec_leech.set_execute(get_exec())
        self.ldst_leech.set_execute(get_exec())

        def clk() -> int:
            yield 50
            self.clk <<= ~self.clk & self.clk
            yield 50
            self.clk <<= ~self.clk
            yield 0

        #self.program()
        simulator.log("Simulation started")

        self.rst <<= 1
        self.clk <<= 1
        yield 10
        for i in range(5):
            yield from clk()
        self.rst <<= 0

        for i in range(self.timeout):
            if self.con.terminate == 1:
                break
            yield from clk()
        yield 10
        assert(self.con.terminate == 1)
        simulator.log("Done")

    def set_mem(self, addr: int, data: ByteString):
        section = addr & 0xc00_0000
        if section == self.nram_base:
            self.rom.set_mem(addr & 0x03ff_ffff, data)
        elif section == self.dram_base:
            for idx, byte in enumerate(data):
                dram_addr = (addr & 0x03ff_ffff) + idx
                if (dram_addr & 1) == 0:
                    self.dram_l.set_mem(dram_addr >> 1, byte.to_bytes(1,"little"))
                else:
                    self.dram_h.set_mem(dram_addr >> 1, byte.to_bytes(1,"little"))
        else:
            raise SimulationException(f"Address {addr:08x} doesn't fall into any mapped memory region")

    def clear(self):
        self.dram_h.clear()
        self.dram_l.clear()
        self.rom.clear()
        self.timeout = self.default_timeout

    def program(self, segments):
        for segment in segments:
            self.set_mem(segment.base_addr, segment.content)

