#!/usr/bin/python3
from random import *
from typing import *
from silicon import *
from silicon.memory import SimpleDualPortMemory

try:
    from .brew_types import *
    from .brew_utils import *
    from .scan import ScanWrapper
    from .synth import *
    from .reg_file import *
except ImportError:
    from brew_types import *
    from brew_utils import *
    from scan import ScanWrapper
    from synth import *
    from reg_file import *



from dataclasses import dataclass

def sim():
    sim_regs = list(i << 16 for i in range(15))

    write_queue: List['WriteQueueItem'] = []

    expect_queue: List['ExpectQueueItem'] = []

    done = False
    checker_idle = True

    def next_val(idx):
        return ((sim_regs[idx] & 0xffff) + 1) | (idx << 16)
    class WriteQueueItem(object):
        def __init__(self, rsv, delay):
            self.value = next_val(rsv)
            self.idx = rsv
            self.delay = delay

    class ExpectQueueItem(object):
        def __init__(self, rd1, rd2, delay):
            self.read1_data = sim_regs[rd1] if rd1 is not None else None
            self.read2_data = sim_regs[rd2] if rd2 is not None else None
            self.read1_addr = rd1
            self.read2_addr = rd2
            self.delay = delay

        def check(self, data1, data2):
            assert self.read1_data is None or self.read1_data == data1
            assert self.read2_data is None or self.read2_data == data2
            pass

    # Generates both read and write requests to the register file.
    # Each request contains up to 2 reads, a reservation and a delayed write to clear the reservation.
    # Note: if a reservation is set, it must be cleared.
    class Requestor(Module):
        clk = ClkPort()
        rst = RstPort()

        read_req = Output(RegFileReadRequestIf)

        def simulate(self, simulator: Simulator) -> TSimEvent:
            nonlocal done

            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def request(rd1, rd2, rsv, wr_delay: int = 2, rsp_delay: int = 0):
                self.read_req.read1_addr <<= rd1
                self.read_req.read1_valid <<= rd1 is not None
                self.read_req.read2_addr <<= rd2
                self.read_req.read2_valid <<= rd2 is not None
                self.read_req.rsv_addr <<= rsv
                self.read_req.rsv_valid <<= rsv is not None
                expect_queue.append(ExpectQueueItem(rd1, rd2, rsp_delay))
                if rsv is not None:
                    write_queue.append(WriteQueueItem(rsv, wr_delay))
                    sim_regs[rsv] = next_val(rsv)
                self.read_req.valid <<= 1
                yield from wait_clk()
                while self.read_req.ready != 1:
                    yield from wait_clk()
                self.read_req.valid <<= 0

            self.read_req.valid <<= 0
            def wait_rst():
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()

            def init():
                for idx, _ in enumerate(sim_regs):
                    write_queue.append(WriteQueueItem(idx, 0))
                    sim_regs[idx] = next_val(idx)
                while len(write_queue) > 0:
                    yield from wait_clk()
                for _ in range(10):
                    yield from wait_clk()

            yield from wait_rst()
            yield from init()
            yield from request(0, 0, None)
            yield from request(1, None, None)
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from request(None, None, 3, wr_delay=3)
            yield from wait_clk()
            yield from wait_clk()
            yield from request(None, None, 4, wr_delay=2)
            yield from request(4, 3, 5)
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from request(None, None, 0xd, rsp_delay=4, wr_delay=10)
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from request(None, None, 0xe, rsp_delay=2, wr_delay=4)
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from request(0xd, 0xe, None)
            yield from wait_clk()
            yield from wait_clk()

            while len(write_queue) > 0 or len(expect_queue) > 0 or not checker_idle:
                yield from wait_clk()
            for _ in range(10):
                yield from wait_clk()
            done = True

    # Pops items from the write queue and executes the write after the designated number of delays
    class Writer(Module):
        clk = ClkPort()
        rst = RstPort()

        write = Output(RegFileWriteBackIf)

        def simulate(self, simulator: Simulator) -> TSimEvent:
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            self.write.data_en <<= 1
            self.write.valid <<= 0
            while True:
                yield from wait_clk()
                self.write.valid <<= 0
                if len(write_queue) > 0:
                    if write_queue[0].delay == 0:
                        item = write_queue.pop(0)
                        self.write.valid <<= 1
                        self.write.data <<= int(item.value)
                        self.write.addr <<= int(item.idx)
                    else:
                        write_queue[0].delay -= 1

    class Checker(Module):
        clk = ClkPort()
        rst = RstPort()

        read_rsp = Input(RegFileReadResponseIf)

        def simulate(self, simulator: Simulator) -> TSimEvent:
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            self.read_rsp.ready <<= 0
            item = None
            while True:
                yield from wait_clk()
                if self.read_rsp.ready == 1 and self.read_rsp.valid == 1:
                    item.check(self.read_rsp.read1_data, self.read_rsp.read2_data)
                    self.read_rsp.ready <<= 0
                    item = None
                if len(expect_queue) > 0 and item is None:
                    if expect_queue[0].delay == 0:
                        item = expect_queue.pop(0)
                        self.read_rsp.ready <<= 1
                    else:
                        expect_queue[0].delay -= 1
                nonlocal checker_idle
                checker_idle = item == None


    class top(Module):
        clk = ClkPort()
        rst = RstPort()

        def body(self):
            seed(0)

            self.requestor = Requestor()
            self.writer = Writer()
            self.chker = Checker()
            self.dut = RegFile()

            self.dut.do_branch <<= 0
            self.dut.read_req <<= self.requestor.read_req
            self.dut.write <<= self.writer.write
            self.chker.read_rsp <<= self.dut.read_rsp


        def simulate(self) -> TSimEvent:
            nonlocal done

            def clk():
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

            for i in range(500):
                yield from clk()
                if done: break
            now = yield 10
            print(f"Done at {now}")
            assert done

    Build.simulation(top, "reg_file.vcd", add_unnamed_scopes=False)

if __name__ == "__main__":
    sim()
