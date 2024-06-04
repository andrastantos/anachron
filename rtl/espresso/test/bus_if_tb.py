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

def sim():
    inst_stream = []


    class DRAM_sim(Module):
        addr_bus_len = 12
        addr_bus_mask = (1 << addr_bus_len) - 1

        bus_if = Input(ExternalBusIf)

        def simulate(self, simulator) -> TSimEvent:
            full_addr = 0
            self.bus_if.data_in <<= None
            self.bus_if.n_wait <<= 1
            while True:
                yield (self.bus_if.n_ras_a, self.bus_if.n_nren, self.bus_if.n_cas_0, self.bus_if.n_cas_1)
                data_assigned = False
                for (byte, cas) in (("low", self.bus_if.n_cas_0), ("high", self.bus_if.n_cas_1)):
                    if (self.bus_if.n_ras_a.get_sim_edge() == EdgeType.Negative) or (self.bus_if.n_nren.get_sim_edge() == EdgeType.Negative):
                        #assert self.dram_n_cas_0.get_sim_edge() == EdgeType.NoEdge
                        #assert self.dram_n_cas_1.get_sim_edge() == EdgeType.NoEdge
                        #assert self.dram_n_cas_0 == 1
                        #assert self.dram_n_cas_1 == 1
                        # Falling edge or nRAS: capture row address
                        if full_addr is None:
                            full_addr = 0
                        full_addr = full_addr & self.addr_bus_mask | (self.bus_if.addr << self.addr_bus_len)
                        simulator.log("Capturing raw address {self.bus_if.addr:03x} into full address {full_addr:08x}")
                    else:
                        if cas.get_sim_edge() == EdgeType.Negative:
                            #assert self.DRAM_nRAS.get_sim_edge() == EdgeType.NoEdge
                            #assert self.DRAM_nRAS == 0
                            # Falling edge of nCAS
                            full_addr = full_addr & (self.addr_bus_mask << self.addr_bus_len) | self.bus_if.addr
                            if self.bus_if.n_we == 0:
                                # Write to the address
                                data = f"{self.bus_if.data_out:04x}"
                                simulator.log(f"Writing byte {byte} to address {full_addr:08x} {data}")
                            else:
                                shift = 8 if byte == "high" else 0
                                data = (full_addr >> shift) & 0xff
                                if data_assigned:
                                    simulator.log(f"Driving both bytes at the same time")
                                simulator.log(f"Reading byte {byte} from address {full_addr:08x} {data:04x}")
                                self.bus_if.data_in <<= data
                                data_assigned = True
                if not data_assigned:
                    self.bus_if.data_in <<= None

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

        def construct(self, nram_base: int = 0) -> None:
            self.mode = None
            self.nram_base = nram_base
            self.dram_base = 2 if nram_base == 0 else 0

        def set_mode(self, mode):
            self.mode = mode

        #read_not_write  = logic
        #byte_en         = Unsigned(2)
        #addr            = BrewBusAddr
        #data            = BrewBusData
        #last            = logic

        def simulate(self) -> TSimEvent:
            self.burst_cnt = None
            self.burst_addr = None
            self.is_dram = None

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
                    self.is_dram = is_dram
                    self.wait_states = wait_states
                else:
                    assert addr is None
                    assert is_dram is None
                    self.burst_addr += 1
                    self.burst_cnt -= 1
                assert self.burst_cnt >= 0

                self.request_port.valid <<= 1
                self.request_port.read_not_write <<= not do_write
                self.request_port.byte_en <<= byte_en
                self.request_port.addr <<= self.burst_addr | ((self.dram_base if self.is_dram else self.nram_base) << (29-4)) | ((self.wait_states + 1) << (29))
                self.request_port.data <<= data

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
                yield from wait_clk()
                while not (self.request_port.ready & self.request_port.valid):
                    yield from wait_clk()

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

        def construct(self, nram_base: int = 0) -> None:
            self.mode = None
            self.nram_base = nram_base
            self.dram_base = 2 if nram_base == 0 else 0

        def body(self):
            self.request_port.one_hot_channel.set_net_type(Unsigned(4))

        def set_mode(self, mode):
            self.mode = mode

        #read_not_write  = logic
        #byte_en         = Unsigned(2)
        #addr            = BrewBusAddr
        #data            = BrewBusData
        #last            = logic

        def simulate(self) -> TSimEvent:
            def reset():
                self.request_port.valid <<= 0
                self.request_port.read_not_write <<= None
                self.request_port.byte_en <<= None
                self.request_port.addr <<= None
                self.request_port.one_hot_channel <<= None
                self.request_port.terminal_count <<= None

            def read_or_write(addr, is_dram, byte_en, channel, terminal_count, wait_states, do_write, is_master):
                assert addr is not None or is_master
                assert is_dram is not None or is_master

                self.request_port.valid <<= 1
                self.request_port.read_not_write <<= not do_write
                self.request_port.byte_en <<= byte_en
                self.request_port.addr <<= None if is_master else addr | ((self.dram_base if is_dram else self.nram_base) << (29-4)) | ((wait_states + 1) << (29))
                self.request_port.one_hot_channel <<= 1 << channel
                self.request_port.terminal_count <<= terminal_count
                self.request_port.is_master <<= is_master

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
                yield from wait_clk()
                while not (self.request_port.ready & self.request_port.valid):
                    yield from wait_clk()

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
            #if self.mode == "fetch":
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

