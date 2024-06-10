#!/usr/bin/python3

import sys
from pathlib import Path
from random import *
from typing import *
from silicon import *

sys.path.append(str(Path(__file__).parent / ".." ))

from brew_types import *
from brew_utils import *
from scan import ScanWrapper
from synth import *
from bus_if import *
from copy import copy

def get_ws(addr: int) -> int:
    return ((addr >> 27) - 1) & 0xf

def get_region(addr: int) -> int:
    return (addr >> 25) & 3

def get_region_name(addr: int, add_nren_idx: bool = False) -> str:
    if not add_nren_idx:
        return ("NREN", "NREN", "DRAM0", "DRAM1")[get_region(addr)]
    return ("NREN0", "NREN1", "DRAM0", "DRAM1")[get_region(addr)]

def get_bus_addr(addr: int) -> int:
    return addr & ((1 << 25) - 1)

def interpret_addr(addr: int) -> str:
    ws = get_ws(addr)
    ofs = get_bus_addr(addr)
    return f"{get_region_name(addr, True)}:{ofs:#08x}-{ws:01x}"

@dataclass
class ExpectedTransaction(object):
    kind: str # This would be things like 'DMA' or 'REFRESH', but not sure how to use it at the moment
    region: str # This is the same as Region.name below
    addr: int # Full transaction address, or row address for refresh
    data: int # Expected data (8 bits)
    is_write: bool
    burst_beat: int # 0-based burst index
    byte_idx: int # 0 for low, 1 for high byte

expected_transactions: Sequence[ExpectedTransaction] = []

def sim():

    class DRAM_sim(Module):
        addr_bus_len = 11
        addr_bus_mask = (1 << addr_bus_len) - 1

        bus_if = Input(ExternalBusIf)

        def simulate(self, simulator: Simulator) -> TSimEvent:
            def unswizzle_nren_addr(row, col):
                return (row << self.addr_bus_len) | col
            def unswizzle_dram_addr(row, col):
                row = int(row)
                col = int(col)
                return (
                    ((col & 0x0ff) << 0) |
                    ((row & 0x0ff) << 8) |
                    ((col & 0x100) << (16-8)) |
                    ((row & 0x100) << (17-8)) |
                    ((col & 0x200) << (18-9)) |
                    ((row & 0x200) << (19-9)) |
                    ((col & 0x400) << (20-10)) |
                    ((row & 0x400) << (21-10))
                )

            @dataclass
            class Region(object):
                name: str
                ras: JunctionBase
                support_refresh: bool
                unswizzler: Callable
                row_addr: int = None
                full_addr: int = None
                burst_cnts: Sequence[int] = None # One for each CAS

            regions = (Region("DRAM_A", self.bus_if.n_ras_a, True, unswizzle_dram_addr), Region("DRAM_B", self.bus_if.n_ras_b, True, unswizzle_dram_addr), Region("NREN", self.bus_if.n_nren, False, unswizzle_nren_addr))

            self.bus_if.data_in <<= None
            self.bus_if.n_wait <<= 1
            while True:
                yield (self.bus_if.n_ras_a, self.bus_if.n_ras_b, self.bus_if.n_nren, self.bus_if.n_cas_0, self.bus_if.n_cas_1, self.bus_if.bus_en)
                if self.bus_if.bus_en == 0:
                    pass
                else:
                    data_assigned = False
                    for region in regions:
                        if region.ras.get_sim_edge() == EdgeType.Negative:
                            region.row_addr = copy(self.bus_if.addr.sim_value)
                            region.burst_cnts = [0,0]
                        elif region.ras.get_sim_edge() == EdgeType.Positive:
                            if region.full_addr is None:
                                # We didn't get a CAS pulse, so treat is a refresh
                                simulator.sim_assert(region.support_refresh, f"{region.name} doesn't support refresh cycles")
                                simulator.log(f"{region.name} refresh at row {region.row_addr:#03x}")
                            region.row_addr = None
                            region.full_addr = None
                        else:
                            for idx, (byte, cas) in enumerate((("low ", self.bus_if.n_cas_0), ("high", self.bus_if.n_cas_1))):
                                if region.ras == 1: continue
                                if cas.get_sim_edge() == EdgeType.Negative:
                                    # This is needed for now to ensure address also updates
                                    yield 0
                                    # Falling edge of nCAS
                                    region.full_addr = region.unswizzler(region.row_addr, self.bus_if.addr)
                                    if self.bus_if.n_we == 0:
                                        # Write to the address
                                        data = f"{self.bus_if.data_out:#04x}"
                                        simulator.sim_assert(not data_assigned, "Multiple regions or byte-lanes are written at the same time")
                                        simulator.log(f"{region.name} writing byte {byte} in beat {region.burst_cnts[idx]} to address {region.full_addr:#08x} {data}")
                                    else:
                                        shift = idx * 8
                                        data = (region.full_addr >> shift) & 0xff
                                        simulator.sim_assert(not data_assigned, "Multiple regions or byte-lanes are read at the same time")
                                        simulator.log(f"{region.name} reading byte {byte} in beat {region.burst_cnts[idx]} from address {region.full_addr:#08x} {data:#04x}")
                                        self.bus_if.data_in <<= data
                                    data_assigned = True

                                    try:
                                        expected_transaction: ExpectedTransaction = first(expected_transactions)
                                        expected_transactions.pop(0)
                                    except:
                                        simulator.sim_assert(False, "No expectation for memory transaction")
                                    simulator.sim_assert(expected_transaction.addr is None or expected_transaction.addr == region.full_addr)
                                    simulator.sim_assert(expected_transaction.is_write is None or expected_transaction.is_write == (self.bus_if.n_we == 0))
                                    simulator.sim_assert(expected_transaction.burst_beat is None or expected_transaction.burst_beat == region.burst_cnts[idx])
                                    simulator.sim_assert(expected_transaction.byte_idx is None or expected_transaction.byte_idx == idx)
                                    region.burst_cnts[idx] += 1

    class CsrDriver(Module):
        clk = ClkPort()
        rst = RstPort()

        reg_if = Output(CsrIf)

        def construct(self):
            self.reg_if.paddr.set_net_type(Unsigned(1))

        def simulate(self, simulator: Simulator):
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_rst():
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()

            def write_reg(addr, value):
                self.reg_if.psel <<= 1
                self.reg_if.penable <<= 0
                self.reg_if.pwrite <<= 1
                self.reg_if.paddr <<= addr
                self.reg_if.pwdata <<= value
                yield from wait_clk()
                self.reg_if.penable <<= 1
                yield from wait_clk()
                while not self.reg_if.pready:
                    yield from wait_clk()
                simulator.log(f"REG {addr:02x} written with value {value:08x}")
                self.reg_if.psel <<= 0
                self.reg_if.penable <<= None
                self.reg_if.pwrite <<= None
                self.reg_if.paddr <<= None
                self.reg_if.pwdata <<= None

            def read_reg(addr):
                self.reg_if.psel <<= 1
                self.reg_if.penable <<= 0
                self.reg_if.pwrite <<= 0
                self.reg_if.paddr <<= addr
                self.reg_if.pwdata <<= None
                yield from wait_clk()
                self.reg_if.penable <<= 1
                yield from wait_clk()
                while not self.reg_if.pready:
                    yield from wait_clk()
                ret_val = copy(self.reg_if.prdata)
                simulator.log(f"REG {addr:02x} read returned value {ret_val:08x}")
                self.reg_if.psel <<= 0
                self.reg_if.penable <<= None
                self.reg_if.pwrite <<= None
                self.reg_if.paddr <<= None
                self.reg_if.pwdata <<= None
                return ret_val

            self.reg_if.psel <<= 0
            yield from wait_rst()
            for _ in range(3):
                yield from wait_clk()
            yield from write_reg(0, (1 << 8) | (10))


    # These two queues will contain the expected read-back values
    read_data_l = []
    read_data_h = []
    class Generator(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        request_port = Output(BusIfRequestIf)

        def construct(self) -> None:
            self.mode = None
            self.nram_base = 0x0000_0000
            self.dram_base = 0x0800_0000

        def set_mode(self, mode):
            self.mode = mode

        #read_not_write  = logic
        #byte_en         = Unsigned(2)
        #addr            = BrewBusAddr
        #data            = BrewBusData
        #last            = logic

        def simulate(self, simulator) -> TSimEvent:
            self.burst_beat = None
            self.burst_cnt = None
            self.burst_addr = None
            self.is_dram = None
            self.expected_transactions_prep = []

            def reset():
                self.request_port.valid <<= 0
                self.request_port.read_not_write <<= None
                self.request_port.byte_en <<= None
                self.request_port.addr <<= None
                self.request_port.data <<= None

            def read_or_write(addr, is_dram, burst_len, byte_en, data, wait_states, do_write):
                if burst_len is not None:
                    assert addr is not None
                    assert is_dram is not None
                    self.burst_cnt = burst_len
                    self.burst_addr = addr
                    self.burst_beat = 0
                    self.is_dram = is_dram
                    self.wait_states = wait_states
                else:
                    assert addr is None
                    assert is_dram is None
                    self.burst_addr += 1
                    self.burst_beat += 1
                    self.burst_cnt -= 1
                assert self.burst_cnt >= 0

                addr = self.burst_addr | ((self.dram_base if self.is_dram else self.nram_base) >> 1) | (((self.wait_states + 1) & 0xf) << 27)
                self.request_port.valid <<= 1
                self.request_port.read_not_write <<= not do_write
                self.request_port.byte_en <<= byte_en
                self.request_port.addr <<= addr
                self.request_port.data <<= data

                # We can prepare the expectation here but can only drop it in
                # the queue when it gets accepted by the BusIf. This is because
                # servicing can be out-of-order from requesting between the
                # various requestors (fetch/mem/dma)
                if byte_en & 1 != 0:
                    self.expected_transactions_prep.append(ExpectedTransaction("????", get_region_name(addr), get_bus_addr(addr), data, do_write, self.burst_beat, 0))
                if byte_en & 2 != 0:
                    self.expected_transactions_prep.append(ExpectedTransaction("????", get_region_name(addr), get_bus_addr(addr), data, do_write, self.burst_beat, 1))

                data_str = f"{data:#04x}" if data is not None else "0x----"
                simulator.log(f"{self.mode.upper()} {('reading','writing')[do_write]} address {addr:#08x} {interpret_addr(addr)} data {data_str} bytes {byte_en:02b}")

            def start_read(addr, is_dram, burst_len, byte_en, wait_states):
                if burst_len > 0:
                    byte_en = 3
                read_or_write(addr, is_dram, burst_len, byte_en, None, wait_states, do_write=False)

            def cont_read():
                read_or_write(None, None, None, 3, None, None, False)

            def start_write(addr, is_dram, burst_len, byte_en, data, wait_states):
                if burst_len > 0:
                    byte_en = 3
                read_or_write(addr, is_dram, burst_len, byte_en, data, wait_states, do_write=True)

            def cont_write(data):
                read_or_write(None, None, None, 3, data, None, False)

            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_for_advance():
                global expected_transactions
                yield from wait_clk()
                while not (self.request_port.ready & self.request_port.valid):
                    yield from wait_clk()
                assert len(self.expected_transactions_prep) > 0
                expected_transactions += self.expected_transactions_prep
                self.expected_transactions_prep.clear()

            def write(addr, is_dram, burst_len, byte_en, data, wait_states=0):
                idx = 0
                start_write(addr, is_dram, burst_len, byte_en, data[idx], wait_states)
                yield from wait_for_advance()
                while idx < burst_len:
                    idx += 1
                    cont_write(data[idx])
                    yield from wait_for_advance()
                reset()

            def read(addr, is_dram, burst_len, byte_en, wait_states=0):
                idx = 0
                start_read(addr, is_dram, burst_len, byte_en, wait_states)
                yield from wait_for_advance()
                while idx < burst_len:
                    idx += 1
                    cont_read()
                    yield from wait_for_advance()
                reset()
                yield from wait_clk()

            reset()
            if self.mode == "fetch":
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()
                yield from read(0x1234,True,0,3)
                yield from read(0x12,True,1,3)
                yield from read(0x24,True,3,3)
                yield from read(0x3,False,0,1)
                yield from read(0x4,False,0,2, wait_states=5)
                yield from wait_clk()
                yield from wait_clk()
                yield from wait_clk()
                yield from wait_clk()
                yield from read(0x34,True,0,2)
                yield from read(0x4,False,0,3)
            elif self.mode == "mem":
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()
                yield from read(0x5678,False,0,3, wait_states=2)

    class DmaGenerator(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        request_port = Output(BusIfDmaRequestIf)

        def construct(self) -> None:
            self.mode = None
            self.nram_base = 0x0000_0000
            self.dram_base = 0x8000_0000

        def body(self):
            self.request_port.one_hot_channel.set_net_type(Unsigned(4))

        def set_mode(self, mode):
            self.mode = mode

        #read_not_write  = logic
        #byte_en         = Unsigned(2)
        #addr            = BrewBusAddr
        #data            = BrewBusData
        #last            = logic

        def simulate(self, simulator: Simulator) -> TSimEvent:
            self.expected_transactions_prep = []

            def reset():
                self.request_port.valid <<= 0
                self.request_port.read_not_write <<= None
                self.request_port.byte_en <<= None
                self.request_port.addr <<= None
                self.request_port.one_hot_channel <<= None
                self.request_port.terminal_count <<= None

            def read_or_write(addr, is_dram, byte_en, channel, terminal_count, wait_states, do_write, is_master):
                assert byte_en in (1,2) or is_master
                assert addr is not None or is_master
                assert is_dram is not None or is_master

                self.request_port.valid <<= 1
                self.request_port.read_not_write <<= not do_write
                self.request_port.byte_en <<= byte_en
                self.request_port.addr <<= None if is_master else addr | ((self.dram_base if is_dram else self.nram_base) >> 1) | ((wait_states + 1) << (28))
                self.request_port.one_hot_channel <<= 1 << channel
                self.request_port.terminal_count <<= terminal_count
                self.request_port.is_master <<= is_master

                if not is_master:
                    self.expected_transactions_prep.append(ExpectedTransaction("????", get_region_name(addr), get_bus_addr(addr), None, do_write, 0, 1 if byte_en == 2 else 0))

            def start_read(addr, is_dram, byte_en, channel, terminal_count, wait_states):
                read_or_write(addr, is_dram, byte_en, channel, terminal_count, wait_states, do_write=False, is_master=False)

            def start_write(addr, is_dram, byte_en, channel, terminal_count, wait_states):
                read_or_write(addr, is_dram, byte_en, channel, terminal_count, wait_states, do_write=True, is_master=False)

            def start_master(channel):
                read_or_write(None, None, None, channel, None, None, do_write=None, is_master=True)

            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_for_advance():
                global expected_transactions
                yield from wait_clk()
                while not (self.request_port.ready & self.request_port.valid):
                    yield from wait_clk()
                #assert len(self.expected_transactions_prep) > 0
                expected_transactions += self.expected_transactions_prep
                self.expected_transactions_prep.clear()

            def write(addr, is_dram, byte_en, channel, terminal_count, wait_states=0):
                start_write(addr, is_dram, byte_en, channel, terminal_count, wait_states)
                yield from wait_for_advance()
                reset()
                yield from wait_clk()

            def read(addr, is_dram, byte_en, channel, terminal_count, wait_states=0):
                start_read(addr, is_dram, byte_en, channel, terminal_count, wait_states)
                yield from wait_for_advance()
                reset()
                yield from wait_clk()

            reset()
            yield from wait_clk()
            while self.rst == 1:
                yield from wait_clk()
            yield from read(0x1000e,True,1,0,0)
            yield from write(0x10010,True,2,0,0)
            for _ in range(20):
                yield from wait_clk()
            start_master(1)
            yield from wait_for_advance()
            for _ in range(40):
                yield from wait_clk()
            reset()
            yield from wait_clk()




            #    yield from read(0x12,True,1,3)
            #    yield from read(0x24,True,3,3)
            #    yield from read(0x3,False,0,1)
            #    yield from read(0x4,False,0,2)
            #    yield from wait_clk()
            #    yield from wait_clk()
            #    yield from wait_clk()
            #    yield from wait_clk()
            #    yield from read(0x34,True,0,2)
            #    yield from read(0x4,False,0,3)
            #elif self.mode == "mem":
            #    yield from wait_clk()
            #    while self.rst == 1:
            #        yield from wait_clk()
            #    yield from read(0x100e,False,0,3)

    '''
    class Checker(RvSimSink):
        def construct(self, max_wait_state: int = 0):
            super().construct(None, max_wait_state)
            self.cnt = 0
        def checker(self, value):
            def get_next_inst():
                inst = inst_stream.pop(0)
                print(f"  --- inst:", end="")
                for i in inst:
                    print(f" {i:04x}", end="")
                print("")
                has_prefix = inst[0] & 0x0ff0 == 0x0ff0
                if has_prefix:
                    prefix = inst[0]
                    inst = inst[1:]
                else:
                    prefix = None
                inst_len = len(inst)-1
                inst_code = 0
                for idx, word in enumerate(inst):
                    inst_code |= word << (16*idx)
                return prefix, has_prefix, inst_code, inst_len

            expected_prefix, expected_has_prefix, expected_inst_code, expected_inst_len = get_next_inst()
            print(f"Received: ", end="")
            if value.inst_bottom.has_prefix:
                print(f" [{value.inst_bottom.prefix:04x}]", end="")
            for i in range(value.inst_bottom.inst_len+1):
                print(f" {(value.inst_bottom.inst >> (16*i)) & 0xffff:04x}", end="")
            if value.has_top:
                print(f" top: {value.inst_top:04x}", end="")
            print("")

            assert expected_has_prefix == value.inst_bottom.has_prefix
            assert not expected_has_prefix or expected_prefix == value.inst_bottom.prefix
            assert expected_inst_len == value.inst_bottom.inst_len
            inst_mask = (1 << (16*(expected_inst_len+1))) - 1
            assert (expected_inst_code & inst_mask) == (value.inst_bottom.inst & inst_mask)
            if value.has_top == 1:
                expected_prefix, expected_has_prefix, expected_inst_code, expected_inst_len = get_next_inst()
                assert not expected_has_prefix
                assert expected_inst_len == 0
                assert expected_inst_code == value.inst_top
    '''

    class top(Module):
        clk = ClkPort()
        rst = RstPort()

        def body(self):
            seed(0)
            fetch_req = Wire(BusIfRequestIf)
            fetch_rsp = Wire(BusIfResponseIf)
            fetch_generator = Generator()
            fetch_generator.set_mode("fetch")
            fetch_req <<= fetch_generator.request_port

            mem_req = Wire(BusIfRequestIf)
            mem_rsp = Wire(BusIfResponseIf)
            mem_generator = Generator()
            mem_generator.set_mode("mem")
            mem_req <<= mem_generator.request_port

            dma_req = Wire(BusIfDmaRequestIf)
            dma_generator = DmaGenerator()
            dma_req <<= dma_generator.request_port

            csr_driver = CsrDriver()

            dram_if = Wire(ExternalBusIf)
            dram_sim = DRAM_sim()

            dut = BusIf()

            dut.fetch_request <<= fetch_req
            fetch_rsp <<= dut.fetch_response
            dut.mem_request <<= mem_req
            dut.dma_request <<= dma_req
            mem_rsp <<= dut.mem_response
            dram_if <<= dut.dram
            dram_sim.bus_if <<= dram_if
            dut.reg_if <<= csr_driver.reg_if


        def simulate(self) -> TSimEvent:
            def clk() -> int:
                yield 10
                self.clk <<= ~self.clk & self.clk
                yield 10
                self.clk <<= ~self.clk
                yield 0

            print("Simulation started")

            self.rst <<= 1
            self.clk <<= 1
            yield 10
            for i in range(5):
                yield from clk()
            self.rst <<= 0

            for i in range(150):
                yield from clk()
            now = yield 10
            print(f"Done at {now}")

    Build.simulation(top, "bus_if_tb.vcd", add_unnamed_scopes=True)


if __name__ == "__main__":
    sim()

