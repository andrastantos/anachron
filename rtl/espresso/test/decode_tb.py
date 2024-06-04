#!/usr/bin/python3
from random import *
from typing import *
from copy import copy
import sys
from pathlib import Path

from silicon import *
from silicon.utils import TSimEvent


sys.path.append(str(Path(__file__).parent / ".." ))

try:
    from .brew_types import *
    from .brew_utils import *
    from .scan import ScanWrapper
    from .synth import *
    from .assembler import *
    from .decode import *
except ImportError:
    from brew_types import *
    from brew_utils import *
    from scan import ScanWrapper
    from synth import *
    from assembler import *
    from decode import *

from expectations import *

def sim():
    class RegFileEmulator(Module):
        clk = ClkPort()
        rst = RstPort()

        # Interface to the register file
        reg_file_req = Input(RegFileReadRequestIf)
        reg_file_rsp = Output(RegFileReadResponseIf)

        def construct(self):
            self.wait_range = 0

        def set_wait_range(self, wait_range):
            self.wait_range = wait_range

        def simulate(self, simulator: Simulator) -> TSimEvent:
            self.out_buf_full = False

            def wait_clk():
                yield (self.clk, self.reg_file_rsp.ready, self.reg_file_rsp.valid)
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    if not self.out_buf_full or (self.reg_file_rsp.ready and self.reg_file_rsp.valid):
                        self.reg_file_req.ready <<= 1
                    else:
                        self.reg_file_req.ready <<= 0
                    yield (self.clk, self.reg_file_rsp.ready, self.reg_file_rsp.valid)


            self.reg_file_rsp.valid <<= 0
            self.reg_file_req.ready <<= 1

            while True:
                yield from wait_clk()

                if (self.reg_file_rsp.valid & self.reg_file_rsp.ready) == 1:
                    self.out_buf_full = False
                    self.reg_file_rsp.read1_data <<= None
                    self.reg_file_rsp.read2_data <<= None
                    self.reg_file_rsp.valid <<= 0

                if (self.reg_file_req.valid & self.reg_file_req.ready) == 1:
                    self.reg_file_rsp.read1_data <<= None
                    self.reg_file_rsp.read2_data <<= None
                    self.reg_file_rsp.valid <<= 0

                    rd_addr1 = copy(self.reg_file_req.read1_addr.sim_value) if self.reg_file_req.read1_valid == 1 else None
                    rd_addr2 = copy(self.reg_file_req.read2_addr.sim_value) if self.reg_file_req.read2_valid == 1 else None
                    rsv_addr = copy(self.reg_file_req.rsv_addr.sim_value  ) if self.reg_file_req.rsv_valid == 1   else None

                    if rd_addr1 is not None:
                        rd_data1 = 0x100+rd_addr1
                        simulator.log(f"RF reading $r{rd_addr1:x} with value {rd_data1}")
                    else:
                        rd_data1 = None
                    if rd_addr2 is not None:
                        rd_data2 = 0x100+rd_addr2
                        simulator.log(f"RF reading $r{rd_addr2:x} with value {rd_data2}")
                    else:
                        rd_data2 = None
                    if rsv_addr is not None:
                        simulator.log(f"RF reserving $r{rsv_addr:x}")
                    self.out_buf_full = True
                    for _ in range(randint(0,self.wait_range)):
                        self.reg_file_req.ready <<= 0
                        self.reg_file_rsp.valid <<= 0
                        simulator.log("RF waiting")
                        yield from wait_clk()
                    self.reg_file_rsp.read1_data <<= rd_data1
                    self.reg_file_rsp.read2_data <<= rd_data2
                    self.reg_file_rsp.valid <<= 1
                #else:
                #    self.reg_file_rsp.read1_data <<= None
                #    self.reg_file_rsp.read2_data <<= None
                #    self.reg_file_rsp.valid <<= 0


    class FetchEmulator(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        fetch = Output(FetchDecodeIf)

        def construct(self, exp_queue: List['DecodeExpectations'], set_exec_wait_range: Callable, set_reg_file_wait_range: Callable):
            self.exp_queue = exp_queue
            self.set_exec_wait_range = set_exec_wait_range
            self.set_reg_file_wait_range = set_reg_file_wait_range

        def simulate(self, simulator) -> TSimEvent:
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_rst():
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()

            def wait_transfer():
                self.fetch.valid <<= 1
                yield from wait_clk()
                while (self.fetch.valid & self.fetch.ready) != 1:
                    yield from wait_clk()
                self.fetch.valid <<= 0

            def issue(inst, exp: DecodeExpectations, av = False, ):
                if len(inst) == 1:
                    self.fetch.inst_0 <<= inst[0]
                    self.fetch.inst_1 <<= None
                    self.fetch.inst_2 <<= None
                elif len(inst) == 2:
                    self.fetch.inst_0 <<= inst[0]
                    self.fetch.inst_1 <<= inst[1]
                    self.fetch.inst_2 <<= None
                elif len(inst) == 3:
                    self.fetch.inst_0 <<= inst[0]
                    self.fetch.inst_1 <<= inst[1]
                    self.fetch.inst_2 <<= inst[2]
                else:
                    assert False
                exp.fetch_av = av
                self.exp_queue.append(exp)
                self.fetch.inst_len <<= len(inst) - 1
                self.fetch.av <<= av
                yield from wait_transfer()

            self.fetch.valid <<= 0
            yield from wait_rst()
            for i in range(4):
                yield from wait_clk()


            """
            $<8000: SWI
            $ .002: $pc <- $rD
            $ .004: $rD <- $pc
            $ .01.: $rD <- tiny FIELD_A
            $ .04.: $rD <- ~$rA
            $ .2..: $rD <- $rA | $rB
            $ .00f: $rD <- VALUE
            $ .3.f: $rD <- FIELD_E & $rB
            $ .0f0: $rD <- short VALUE
            $ .4f.: $rD <- FIELD_E + $rA
            $ .c**: MEM[$rA+tiny OFS*4] <- $rD
            $ .d**: $rD <- MEM[$rA+tiny OFS*4]
            $ .e4.: $rD <- MEM8[$rA]
            $ .e8.: MEM8[$rA] <- $rD
            """
            test_inst_table = [
                "swi",
                "pc_eq_r",
                "r_eq_pc",
                "r_eq_t",
                "r_eq_not_r",
                "r_eq_r_or_r",
                "r_eq_I",
                "r_eq_I_and_r",
                "r_eq_i",
                "r_eq_i_plus_r",
                "mem32_r_plus_t_eq_r",
                "r_eq_mem32_r_plus_t",
                "r_eq_mem8_r",
                "mem8_r_eq_r"
            ]
            a = BrewAssembler()
            de = DecodeExpectations()
            def _i(method, *args, **kwargs):
                nonlocal a, de, simulator
                asm_fn = getattr(a, method)
                decode_fn = getattr(de, method)
                words = asm_fn(*args, **kwargs)
                words_str = ":".join(f"{i:04x}" for i in words)
                simulator.log(f"ISSUING {method} {words_str}")
                return words, decode_fn(*args, **kwargs)

            yield from issue(*_i("r_eq_r_or_r", 0,2,3), av=True)
            #yield from issue(a.r_eq_I(4, 0xdeadbeef))
            #yield from issue(a.mem8_r_eq_r(4,5))
            for i in range(4):
                yield from wait_clk()
            pass

            def test_cycle(cycle_count, exec_wait, reg_file_wait):
                simulator.log(f"====== {'NO' if exec_wait == 0 else f'random {exec_wait}'} exec wait, {'NO' if reg_file_wait == 0 else f'random {reg_file_wait}'} reg file wait")
                self.set_exec_wait_range(exec_wait)
                self.set_reg_file_wait_range(reg_file_wait)
                for i in range(cycle_count):
                    inst = test_inst_table[randint(0,len(test_inst_table)-1)]
                    yield from issue(*_i(inst))

                for i in range(4):
                    yield from wait_clk()

            cycle_count = 50
            yield from test_cycle(cycle_count, 0, 0)
            yield from test_cycle(cycle_count, 0, 4)
            yield from test_cycle(cycle_count, 4, 0)
            yield from test_cycle(cycle_count, 4, 4)


    class ExecEmulator(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        input_port = Input(DecodeExecIf)

        def set_wait_range(self, wait_range):
            self.wait_range = wait_range

        def construct(self, exp_queue: List[DecodeExpectations]):
            self.exp_queue = exp_queue
            self.wait_range = 0

        def simulate(self, simulator) -> TSimEvent:
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_rst():
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()

            def wait_transfer():
                self.input_port.ready <<= 1
                yield from wait_clk()
                while (self.input_port.valid & self.input_port.ready) != 1:
                    yield from wait_clk()
                self.input_port.ready <<= 0


            self.input_port.ready <<= 0
            yield from wait_rst()
            while True:
                yield from wait_transfer()
                exp = self.exp_queue.pop(0)
                simulator.log(f"EXEC got something {exp.fn_name}")
                exp.check(self.input_port, simulator)
                for _ in range(randint(0,self.wait_range)):
                    simulator.log("EXEC waiting")
                    yield from wait_clk()



    class top(Module):
        clk = ClkPort()
        rst = RstPort()

        def body(self):
            exec_exp_queue = []
            self.reg_file_emulator = RegFileEmulator()
            self.exec_emulator = ExecEmulator(exec_exp_queue)
            self.fetch_emulator = FetchEmulator(exec_exp_queue, self.exec_emulator.set_wait_range, self.reg_file_emulator.set_wait_range)

            self.dut = DecodeStage(use_mini_table=False, support_exc_unknown_inst=True)

            self.dut.fetch <<= self.fetch_emulator.fetch

            self.exec_emulator.input_port <<= self.dut.output_port

            self.dut.do_branch <<= 0

            self.reg_file_emulator.reg_file_req <<= self.dut.reg_file_req
            self.dut.reg_file_rsp <<= self.reg_file_emulator.reg_file_rsp




        def simulate(self) -> TSimEvent:
            seed(0)

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

            for i in range(1000):
                yield from clk()
            now = yield 10
            print(f"Done at {now}")

    Build.simulation(top, "decode_tb.vcd", add_unnamed_scopes=True)

if __name__ == "__main__":
    sim()
