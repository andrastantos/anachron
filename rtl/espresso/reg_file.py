#!/usr/bin/python3
from random import *
from typing import *
try:
    from silicon import *
    from silicon.memory import SimpleDualPortMemory
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str((Path() / ".." / ".." / ".." / "silicon").absolute()))
    from silicon import *
    from silicon.memory import SimpleDualPortMemory
try:
    from .brew_types import *
    from .brew_utils import *
    from .scan import ScanWrapper
    from .synth import *
except ImportError:
    from brew_types import *
    from brew_utils import *
    from scan import ScanWrapper
    from synth import *


#TIMING_CLOSURE_REG = Reg
TIMING_CLOSURE_REG = lambda a: a
"""
The register file for Brew consists of a single write and two read ports.

The V1 version doesn't implement types, so only values are provided.

For FPGAs, BRAMs can be used to implement the register file.

The register file also implements the score-board for the rest of the pipeline to handle reservations
"""

class RegFile(Module):
    clk = ClkPort()
    rst = RstPort()

    # Interface towards decode
    read_req = Input(RegFileReadRequestIf)
    read_rsp = Output(RegFileReadResponseIf)

    # Interface towards the write-back of the pipeline
    write = Input(RegFileWriteBackIf)

    do_branch = Input(logic)

    '''
    CLK                    /^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__
    write.valid            ______/^^^^^\_______________________/^^^^^\_______________________________________________/^^^^^\___________
    write.addr             ------<=====>-----------------------<=====>-----------------------------------------------<=====>-----------
    write.data             ------<=====>-----------------------<=====>-----------------------------------------------<=====>-----------
    CLK                    /^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__
    score_clr              ______/^^^^^\_______________________/^^^^^\_______________________________________________/^^^^^\___________
    score_set              ______/^^^^^\_______________________/^^^^^\___________/^^^^^\_____/^^^^^^^^^^^\_____/^^^^^^^^^^^\___________
    score_value            ^^^^^^^^^^^^\_____________ ^^^^^^^^^^^^^^^\______________________________________________ ^^^^^^\___________
    CLK                    /^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__
    read_req.valid         ______/^^^^^\_________________/^^^^^\_________________/^^^^^\_____/^^^^^^^^^^^\_____/^^^^^^^^^^^\___________
    read_req.ready         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    read_req.readX_valid   ______/^^^^^\_________________/^^^^^\_________________/^^^^^\_____/^^^^^^^^^^^\_____/^^^^^^^^^^^\___________
    read_req.readX_addr    ------<=====>-----------------<=====>-----------------<=====>-----<=====X=====>-----<=====X=====>-----------
    read_rsp.valid         ____________/^^^^^\_______________________/^^^^^\___________/^^^^^\_____/^^^^^^^^^^^\_____/^^^^^^^^^^^\_____
    read_rsp.readX_data    ------------<=====>-----------------------<=====>-----------<=====>-----<=====X=====>-----<=====X=====>-----
                                 bypass behavior           bypass behavior       simple read   back-to-back read  back-to-back read w bypass
    '''


    #read1_rsv_bit = Output(logic)
    #read2_rsv_bit = Output(logic)
    #rsv_rsv_bit = Output(logic)

    def body(self):
        req_advance = self.read_req.ready & self.read_req.valid
        rsp_advance = self.read_rsp.ready & self.read_rsp.valid

        outstanding_req = Wire(logic)
        outstanding_req <<= req_advance | (~rsp_advance & Reg(Select(
            req_advance,
            Select(
                rsp_advance,
                outstanding_req,
                0
            ),
            1
        )))

        def remember(thing: Junction):
            return Select(req_advance, Reg(thing, clock_en=req_advance), thing)

        def remember2(thing: Junction):
            out_val = Wire(thing.get_net_type())
            out_val <<= Select(req_advance, Reg(Select(self.do_branch, Select(req_advance, out_val, thing), 0)), thing)
            return out_val

        read1_valid = remember2(self.read_req.read1_valid)
        read1_addr  = remember(self.read_req.read1_addr)
        read2_valid = remember2(self.read_req.read2_valid)
        read2_addr  = remember(self.read_req.read2_addr)
        rsv_valid   = remember2(self.read_req.rsv_valid)
        rsv_addr    = remember(self.read_req.rsv_addr)

        # We have two memory instances, one for each read port. The write ports of
        # these instances are connected together so they get written the same data
        # NOTE: disabling read-new-data behavior for Quartus-es sake.
        #mem1 = SimpleDualPortMemory(registered_input_a=False, registered_output_a=True, registered_input_b=True, registered_output_b=False, addr_type=BrewRegAddr, data_type=BrewData)
        #mem2 = SimpleDualPortMemory(registered_input_a=False, registered_output_a=True, registered_input_b=True, registered_output_b=False, addr_type=BrewRegAddr, data_type=BrewData)
        mem1 = SimpleDualPortMemory(registered_input_a=False, registered_output_a=True, registered_input_b=False, registered_output_b=True, addr_type=BrewRegAddr, data_type=BrewData)
        mem2 = SimpleDualPortMemory(registered_input_a=False, registered_output_a=True, registered_input_b=False, registered_output_b=True, addr_type=BrewRegAddr, data_type=BrewData)

        # We disable forwarding and writing to the RF if write.data_en is not asserted.
        # This allows for clearing a reservation without touching the data
        # during (branch/exception recovery).
        mem1.port1_write_en <<= self.write.valid & self.write.data_en
        mem1.port1_data_in <<= self.write.data
        mem1.port1_addr <<= self.write.addr
        mem2.port1_write_en <<= self.write.valid & self.write.data_en
        mem2.port1_data_in <<= self.write.data
        mem2.port1_addr <<= self.write.addr

        write_data_d = Wire()
        write_data_d <<= Reg(self.write.data)

        # Read ports have bypass logic, but with the same latency as normal register reads
        # NOTE: Since we are configuring the underlying memories as 'read new data', this
        #       bypass logic is not necessary. I'll leave it here though since some targets
        #       might not support such an arrangement. Quartus for instance complains, but
        #       complies.
        # NOTE: There are some problems with the bypass: we only accept the request on the
        #       same cycle the response comes back, so we can't present the right address to
        #       the underlying memory before. That is to say, the read address could change
        #       *on the same cycle* when the write occurs. It's nice that the memory is
        #       configured as 'read new data', but the address inputs are registered on the
        #       read port; as such, we still incur a one-cycle latency.
        # NOTE: Quartus at least has a really hard time with 'read new data' configuration of
        #       the memories. It outputs a note that it generates bypass logic, but the gate
        #       level simulation shows bad behavior for not even conflicting, but adjacent
        #       writes. The issue appears to be that write is double-registered and adjacent
        #       read of the same address conflicts with the write, generating X-es. Not sure
        #       if this is a simulation issue or a true problem in the operation of the RAMs
        #       but since we have the bypass logic here anyway, let's not depend on the RAMS.
        mem1.port2_addr <<= read1_addr
        #self.read_rsp.read1_data <<= mem1.port2_data_out
        self.read_rsp.read1_data <<= Select(
            Reg((self.write.addr == read1_addr) & self.write.valid & self.write.data_en),
            mem1.port2_data_out,
            write_data_d
        )

        mem2.port2_addr <<= read2_addr
        #self.read_rsp.read2_data <<= mem2.port2_data_out
        self.read_rsp.read2_data <<= Select(
            Reg((self.write.addr == read2_addr) & self.write.valid & self.write.data_en),
            mem2.port2_data_out,
            write_data_d
        )

        rsv_set_valid = Wire(logic)

        '''
        The problem is the following:

        We set 'wait_for_write' whenever there's a new request (which is not immediately satisfied) or whenever there's a write that does't
        clear all hazards. The problem is this: we set the 'reservation' even when we have read hazards, thus we're going to wait for a write.
        However, after that point, it will appear that we have a write-after-write hazard so we'll continue to wait for a write that clears that
        which will never come.

        There are three solutions to this problem:
        1. Remember that we set the write reservation so we don't have to wait for a write for that.
        2. Set the write reservation only when we serve the response.
            This later approach has the problem that, if at the same cycle where we serve the response, we also
            has a read-after-write hazard (that is we accept a new request which tries to read) we will miss it
            because the reservation bit is set only in the following cycle.
        3. We can try to set the reservation on the cycle when all the hazards are cleared. This ought to work
           because we only accept a request in the following cycle.
            This does't work because we don't actually realize the fact that we registered our reservation and in the next cycle
            still treat it as an outstanding write.

        So #1 it is.
        '''
        rsv_registered = Wire(logic)
        wait_for_rsv_raw = Wire(logic)
        rsv_registered <<= ~req_advance & Reg(Select(
            rsv_set_valid & ~rsv_registered,
            Select(
                req_advance,
                rsv_registered,
                0
            ),
            ~wait_for_rsv_raw # We might have an actual legitimate reason to wait for a write in case of a write-after-write hazard.
        ))



        # Score-board for reservations
        rsv_board = Wire(Unsigned(BrewRegCnt))

        def get_rsv_bit(addr):
            return Select(addr, *rsv_board)

        def wait(read_valid, read_addr):
            return outstanding_req & read_valid & get_rsv_bit(read_addr) & ~((self.write.addr == read_addr) & self.write.valid)

        #rsv_board_as_bits = tuple(rsv_board)
        #self.read1_rsv_bit <<= Select(read1_addr, *rsv_board_as_bits)
        #self.read2_rsv_bit <<= Select(read2_addr, *rsv_board_as_bits)
        #self.rsv_rsv_bit   <<= Select(rsv_addr,   *rsv_board_as_bits)

        # If we've registered our reservation and we also have a read of the same register, let's not wait: no one will clear the reservation
        wait_for_read1 = TIMING_CLOSURE_REG(wait(read1_valid, read1_addr) & ((read1_addr != rsv_addr) | ~rsv_registered))
        wait_for_read2 = TIMING_CLOSURE_REG(wait(read2_valid, read2_addr) & ((read2_addr != rsv_addr) | ~rsv_registered))
        wait_for_rsv_raw <<= wait(rsv_valid,   rsv_addr)
        wait_for_rsv   = TIMING_CLOSURE_REG(wait_for_rsv_raw & ~rsv_registered)
        wait_for_some = wait_for_read1 | wait_for_read2 | wait_for_rsv
        wait_for_write = Wire(logic)
        #wait_for_write <<= Select(
        #    req_advance | self.write.valid,
        #    Reg(wait_for_some, clock_en = req_advance | self.write.valid),
        #    wait_for_some
        #)
        wait_for_write <<= Select(
            req_advance | self.write.valid,
            Reg(Select(
                self.do_branch,
                Select(
                    req_advance | self.write.valid,
                    wait_for_write,
                    wait_for_some
                ),
                0
            )),
            wait_for_some
        )

        # Setting and clearing reservation bits (if we set and clear at the same cycle, set takes priority)
        rsv_set_valid <<= rsv_valid & ~wait_for_write & outstanding_req
        #rsv_valid_d = Reg(rsv_valid)
        #rsv_addr_d = Reg(rsv_addr)
        #rsv_set_valid = self.read_rsp.valid & self.read_rsp.ready & rsv_valid_d # We only set the reservation bit when we give our response. This way, if we get back-pressured.
        rsv_clr_valid = self.write.valid & (~wait_for_rsv | (rsv_addr != self.write.addr))
        for i in range(BrewRegCnt):
            rsv_board[i] <<= Reg(
                Select(
                    self.do_branch,
                    Select(
                        rsv_set_valid & (rsv_addr == i),
                        #rsv_set_valid & (rsv_addr_d == i),
                        Select(
                            rsv_clr_valid & (self.write.addr == i),
                            rsv_board[i],
                            0
                        ),
                        1
                    ),
                    0
                )
            )


        wait_for_write_d = Reg(Select(self.do_branch, wait_for_write, 0))
        out_buf_full = Wire(logic)
        out_buf_full <<= Reg(Select(self.do_branch, Select(req_advance, Select(rsp_advance, out_buf_full, 0), 1), 0))

        self.read_req.ready <<= ~wait_for_write_d & (self.read_rsp.ready | ~out_buf_full)
        self.read_rsp.valid <<= ~wait_for_write_d & out_buf_full




from dataclasses import dataclass

def sim2():
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

            for i in range(500):
                yield from clk()
                if done: break
            now = yield 10
            print(f"Done at {now}")
            assert done

    Build.simulation(top, "reg_file2.vcd", add_unnamed_scopes=False)

def sim():

    class Excerciser(Module):
        clk = ClkPort()
        rst = RstPort()

        # Interface towards decode
        read_req = Output(RegFileReadRequestIf)
        read_rsp = Input(RegFileReadResponseIf)

        # Interface towards the write-back of the pipeline
        write = Output(RegFileWriteBackIf)

        def simulate(self) -> TSimEvent:

            self.sim_write_state = "idle"

            def write_reg(addr, data, enable = 1):
                self.sim_write_state = "write"
                self.write.valid <<= 1
                self.write.addr <<= addr
                self.write.data <<= data
                self.write.data_en <<= enable

            def write_sm():
                if self.rst == 1:
                    self.write.valid <<= 0
                    self.write.data <<= None
                    self.write.data_en <<= None
                    self.write.addr <<= None
                    self.sim_write_state = "idle"
                elif self.sim_write_state == "idle":
                    pass
                elif self.sim_write_state == "write":
                    self.write.valid <<= 0
                    self.sim_write_state = "idle"

            self.sim_req_state = "idle"

            def start_req(read1, read2, rsv):
                assert self.sim_req_state == "idle"
                self.read_req.read1_addr <<= read1
                self.read_req.read1_valid <<= read1 is not None
                self.read_req.read2_addr <<= read2
                self.read_req.read2_valid <<= read2 is not None
                self.read_req.rsv_addr <<= rsv
                self.read_req.rsv_valid <<= rsv is not None
                self.read_req.valid <<= 1
                self.sim_req_state = "request"

            def req_sm():
                if self.rst == 1:
                    self.read_req.read1_addr <<= None
                    self.read_req.read1_valid <<= None
                    self.read_req.read2_addr <<= None
                    self.read_req.read2_valid <<= None
                    self.read_req.rsv_addr <<= None
                    self.read_req.rsv_valid <<= None
                    self.read_req.valid <<= 0
                    self.sim_req_state = "idle"
                elif self.sim_req_state == "idle":
                    pass
                elif self.sim_req_state == "request":
                    if self.read_req.valid == 1:
                        self.read_req.read1_addr <<= None
                        self.read_req.read1_valid <<= None
                        self.read_req.read2_addr <<= None
                        self.read_req.read2_valid <<= None
                        self.read_req.rsv_addr <<= None
                        self.read_req.rsv_valid <<= None
                        self.read_req.valid <<= 0
                        self.sim_req_state = "idle"

            self.block_rsp_cnt = 0
            def block_rsp(clock_cnt):
                self.block_rsp_cnt = clock_cnt
                self.read_rsp.ready <<= 0

            def rsp_sm():
                if self.rst == 1:
                    self.read_rsp.ready <<= 1
                elif self.block_rsp_cnt > 0:
                    self.block_rsp_cnt -= 1
                    self.read_rsp.ready <<= self.block_rsp_cnt == 0

            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )
                    req_sm()
                    write_sm()
                    rsp_sm()


            def wait_rst():
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()

            self.read_req.valid <<= 0
            self.write.valid <<= 0
            yield from wait_rst()
            for i in range(4):
                yield from wait_clk()

            write_reg(0,100)
            yield from wait_clk()
            yield from wait_clk()
            write_reg(1,101)
            yield from wait_clk()
            yield from wait_clk()
            write_reg(2,102)
            yield from wait_clk()
            write_reg(3,103)
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            start_req(1,2,3)
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            start_req(3,0,None)
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            write_reg(3,203)
            yield from wait_clk()
            start_req(1,2,3)
            yield from wait_clk()
            yield from wait_clk()
            yield from wait_clk()
            write_reg(3,303)
            yield from wait_clk()
            start_req(1,2,3)
            write_reg(3,403)
            yield from wait_clk()
            yield from wait_clk()
            start_req(0,1,None)
            yield from wait_clk()
            start_req(3,3,None)
            yield from wait_clk()
            yield from wait_clk()
            write_reg(3,503)
            yield from wait_clk()
            yield from wait_clk()



    class top(Module):
        clk = ClkPort()
        rst = RstPort()

        def body(self):
            seed(0)

            self.excericeser = Excerciser()
            self.dut = RegFile()

            self.dut.do_branch <<= 0
            self.dut.read_req <<= self.excericeser.read_req
            self.excericeser.read_rsp <<= self.dut.read_rsp

            self.dut.write <<= self.excericeser.write


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

            for i in range(50):
                yield from clk()
            now = yield 10
            print(f"Done at {now}")

    Build.simulation(top, "reg_file.vcd", add_unnamed_scopes=True)

def gen():
    def top():
        return ScanWrapper(RegFile, {"clk", "rst"})

    netlist = Build.generate_rtl(top, "reg_file.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(target_dir="q_reg_file", top_level=top_level_name, source_files=("reg_file.sv",), clocks=(("clk", 10), ("top_clk", 100)), project_name="reg_file")
    flow.generate()
    flow.run()

if __name__ == "__main__":
    #gen()
    #sim()
    sim2()
