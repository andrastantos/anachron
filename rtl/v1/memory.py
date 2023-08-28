#!/usr/bin/python3
from random import *
from typing import *
from copy import copy
from typing import List

try:
    from silicon import *
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str((Path() / ".." / ".." / ".." / "silicon").absolute()))
    from silicon import *

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

"""
Memory stage of the V1 pipeline.

This stage is part of 'execute'.

It does the following:
- Handles handshaking with the bus interface
- Issues loads/stores
- Stalls the pipeline until memory responses come back

NOTE:
- Memory interface consumes physical addresses
- Memory interface assumes that accesses are valid
In other words, AV and unaligned exceptions are generated in a previous stage.

"""

class MemoryStage(Module):
    clk = ClkPort()
    rst = RstPort()


    # Pipeline input from execute
    input_port = Input(MemInputIf)
    # Pipeline output to register file
    output_port = Output(MemOutputIf)

    # Interface to the bus interface
    bus_req_if = Output(BusIfRequestIf)
    bus_rsp_if = Input(BusIfResponseIf)

    # Interface to the CSR registers
    csr_if = Output(ApbIf)

    def body(self):

        '''
                                      +--- 32-bit DRAM read          +--- 16-bit DRAM read   +--- 32-bit I/O read
                                      |                              |                       |
            CLK                 /^^\__/^^\__/^^\__/^^\_~_/^^\__/^^\__/^^\__/^^\__/^~^\__/^^\__/^^\__/^^\__/^~^\__/^^\__/^^\_~_/^^\__/^^\__
            IN_valid            ______/^^^^^\__________~_____________/^^^^^\_______~__________/^^^^^\_______~_______________~_____________
            IN_ready            ^^^^^^^^^^^^\__________~_______/^^^^^^^^^^^\_______~____/^^^^^^^^^^^\_______~_______________~_/^^^^^^^^^^^
            IN_read_not_write   ------/^^^^^\----------~-------------/^^^^^\-------~----------/^^^^^\-------~---------------~-------------
            IN_data_l           -----------------------~---------------------------~------------------------~---------------~-------------
            IN_data_h           -----------------------~---------------------------~------------------------~---------------~-------------
            IN_addr             ------<=====>----------~-------------<=====>-------~----------<=====>-------~---------------~-------------
            IN_access_len       ------<  2  >----------~-------------<  1  >-------~----------<  2  >-------~---------------~-------------

            ACTIVE              ____________/^^^^^\____~___________________________~________________/^^^^^^^~^^^^^^^^^^\____~_____________

            BRQ_valid           ______/^^^^^^^^^^^\____~_____________/^^^^^\_______~__________/^^^^^^^^^^^^^~^^^^^^^^^^\____~_____________
            BRQ_ready           ^^^^^^^^^^^^^^^^^^\____~_______/^^^^^^^^^^^\_______~____/^^^^^^^^^^^\_______~____/^^^^^\____~_/^^^^^^^^^^^
            BRQ_read_not_write  ------/^^^^^^^^^^^\----~-------------/^^^^^\-------~----------/^^^^^^^^^^^^^~^^^^^^^^^^\----~-------------
            BRQ_byte_en         ------<     3     >----~-------------<  3  >-------~----------<           3 ~          >----~-------------
            BRQ_addr            ------<=====X=====>----~-------------<=====>-------~----------<=====X=======~==========>----~-------------
            BRQ_data            -----------------------~---------------------------~------------------------~---------------~-------------
                                /^^\__/^^\__/^^\__/^^\_~_/^^\__/^^\__/^^\__/^^\__/^~^\__/^^\__/^^\__/^^\__/^~^\__/^^\__/^^\_~_/^^\__/^^\__
            BRSP_valid          _______________________~_/^^^^^^^^^^^\_____________~____/^^^^^\_____________~____/^^^^^\____~_/^^^^^\_____
            BRSP_data           -----------------------~-<=====X=====>-------------~----<=====>-------------~----<=====>----~-<=====>-----

            PENDING             ____________/^^^^^^^^^^~^^^^^^^\___________________~________________/^^^^^^^~^^^^^^^^^^\____~_____________

            OUT_valid           _______________________~_______/^^^^^\_____________~____/^^^^^\_____________~_______________~_/^^^^^\_____
            OUT_data_l          -----------------------~-------<=====>-------------~----<=====>-------------~---------------~-<=====>-----
            OUT_data_h          -----------------------~-------<=====>-------------~------------------------~---------------~-<=====>-----

            ACTIVE:    goes high when transaction is accepted  IN
                       goes low when last transfer of the burst is accepted on BRQ
                       (this could happen in the same cycle, in which case ACTIVE stays low)
            IN_ready:  goes low when a transaction is accepted on IN
                       goes high *with* BRQ_ready going high
                       (in other words, it's low if ACTIVE is high, otherwise, it's a pass-through of BRQ_ready)
            BRQ_ready: goes high *with* IN_valid
                       goes low when the last transfer of the burst is accepted on BRQ
            PENDING:   goes high when the first transfer of of a multi-transfer burst on BRQ
                       goes low on the first transfer of a multi-transfer burst response on BRSP
            OUT_valid: goes high *with* the last transfer of the burst on BRSP
                       (i.e. it is BRSP_valid, except when the first transaction is received for a multi-beat burst)

            NOTE: writes have no corresponding response. The only thing that happens is that IN_ready goes inactive for a while.

            CSRs only support full 32-bit reads and writes

            CLK                 /^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^~^\__/^^\__/^^\__
            IN_valid            ______/^^^^^\___________/^^^^^\_______~________________
            IN_ready            ^^^^^^^^^^^^\_____/^^^^^^^^^^^\_______~___/^^^^^^^^^^^^
            IN_read_not_write   ------<=====>-----------<=====>-------~----------------
            IN_data_l           ------<=====>-----------<=====>-------~----------------
            IN_data_h           ------<=====>-----------<=====>-------~----------------
            IN_addr             ------<=====>-----------<=====>-------~----------------
            IN_access_len       ------<  2  >-----------<  2  >-------~----------------

            CSR_psel            ______/^^^^^^^^^^^\_____/^^^^^^^^^^^^^~^^^^^^^^^\______
            CSR_penable         ____________/^^^^^\___________/^^^^^^^~^^^^^^^^^\______
            CSR_pready          ------------/^^^^^\-----------\_______~___/^^^^^\------
            CSR_pwrite          ------<===========>-----<=============~=========>------
            CSR_paddr           ------<===========>-----<=============~=========>------
            CSR_prdata          ------------<=====>-------------------~---<=====>------
            CSR_pwdata          ------<===========>-----<=============~=========>------

            OUT_valid           ____________/^^^^^\___________________~___/^^^^^\______
            OUT_ready           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^~^^^^^^^^^^^^^^^^
            OUT_data_l          ------------<=====>-------------------~---<=====>------
            OUT_data_h          ------------<=====>-------------------~---<=====>------

        '''
        def remember(interface, signal):
            return Select(interface.ready & interface.valid, Reg(signal, clock_en=interface.ready & interface.valid), signal)

        csr_pen = Wire(logic)

        is_csr = Wire(logic)

        input_advance = (self.input_port.ready & self.input_port.valid)
        bus_request_advance = (self.bus_req_if.ready & self.bus_req_if.valid)
        bus_response_advance = self.bus_rsp_if.valid
        output_advance = self.output_port.valid

        multi_cycle = Wire(logic)
        multi_cycle <<= Reg((self.input_port.access_len == access_len_32) & ~is_csr, clock_en = input_advance)
        # Active is set for 32-bit transfers, until all requests are sent
        active = Wire(logic)
        next_active = Wire(logic)
        next_active <<= Select((self.input_port.access_len == access_len_32) & ~is_csr & input_advance, Select(bus_request_advance, active, 0), 1)
        active <<= Reg(next_active)
        # Pending is set for 32-bit transfers, until the first response is back
        pending = Wire(logic)
        pending <<= Reg(Select((self.input_port.access_len == access_len_32) & ~is_csr & input_advance & self.input_port.read_not_write, Select(bus_response_advance, pending, 0), 1))
        ##### # We need to delay pending by one cycle after the input is accepted due to the following reason:
        ##### # Response comes back a cycle *after* bus_if accepts the subsequent request. Because of that,
        ##### # if there are back-to-back reads, where the first is 8- or 16-bit long and the next one is 32-bit long,
        ##### # we would think that the response to the first read is the first response for the 32-bit read and would
        ##### # not issue the result towards the register-file
        ##### #
        ##### # !!!IMPORTANT!!!
        ##### # This logic of course only applies if bus_if has at least two cycles of latency. This is true
        ##### # now, but will it be forever? Maybe not once caches are involved.
        ##### pending = Wire(logic)
        ##### pending_set = Reg((self.input_port.access_len == access_len_32) & ~is_csr & input_advance & self.input_port.read_not_write)
        ##### pending_clr = bus_response_advance
        ##### pending <<= Reg(Select(pending_set, Select(pending_clr, pending, 0),1))
        # Gap goes active for one cycle after all requests are sent to ensure proper burst termination between back-to-back requests
        gap = Wire(logic)
        gap <<= Reg(
            Select(
                ((self.input_port.access_len != access_len_32) & ~is_csr & input_advance) | (active & ~next_active),
                0,
                1
            )
        )
        csr_select = self.input_port.is_csr
        is_csr <<= Select(
            input_advance,
            Reg(
                Select(
                    input_advance,
                    Select(output_advance, is_csr, 0),
                    csr_select
                )
            ),
            csr_select
        )

        csr_active = Wire()
        self.input_port.ready <<= (self.bus_req_if.ready & ~active & ~gap) | (csr_select & self.input_port.valid & ~csr_active) # this is not ideal: we won't accept a CSR access if the bus is occupied. Yet, I don't think we should depend on is_dram here.
        self.bus_req_if.valid <<= ((self.input_port.valid & ~csr_select) | active) & ~gap
        self.output_port.valid <<= (self.bus_rsp_if.valid & ~pending) | (csr_pen & self.csr_if.pready & ~self.csr_if.pwrite)

        first_addr = self.input_port.addr[BrewBusAddr.length:1]
        # We already have aligned addresses. As a result, LSB should be 0 for 32-bit accesses, so incrementing it is the same as setting LSB to 1.
        next_addr = Reg(first_addr | 1, clock_en=input_advance)

        byte_en = Wire(Unsigned(2))
        byte_en[0] <<= (self.input_port.access_len != 0) | ~self.input_port.addr[0]
        byte_en[1] <<= (self.input_port.access_len != 0) |  self.input_port.addr[0]

        data_store = Wire(Unsigned(16)) # Stores high-word for writes, low-word reads
        data_store <<= Reg(
            Select(
                input_advance,
                Select(
                    bus_response_advance & pending,
                    data_store,
                    self.bus_rsp_if.data
                ),
                self.input_port.data[31:16]
            )
        )

        self.bus_req_if.read_not_write  <<= remember(self.input_port, self.input_port.read_not_write)
        self.bus_req_if.byte_en         <<= remember(self.input_port, byte_en)
        self.bus_req_if.addr            <<= Select(input_advance, next_addr, first_addr)
        self.bus_req_if.data            <<= Select(input_advance, data_store, self.input_port.data[15:0])

        self.output_port.data_l <<= Select(csr_pen, Select(multi_cycle, self.bus_rsp_if.data, data_store), self.csr_if.prdata[15: 0])
        self.output_port.data_h <<= Select(csr_pen, self.bus_rsp_if.data,                                  self.csr_if.prdata[31:16])

        csr_pen <<= Reg(Select(input_advance, Select(self.csr_if.pready & is_csr, csr_pen, 0), is_csr))
        csr_active <<= Reg(self.csr_if.psel) # Active for an extra cycle, to allow the bus to return to idle
        self.csr_if.psel <<= input_advance & is_csr | csr_pen
        self.csr_if.penable <<= csr_pen
        self.csr_if.pwrite <<= remember(self.input_port, ~self.input_port.read_not_write)
        # We maintain the LSB csr bit to retain the ability to define SCHEDULER-mode only CSRs
        self.csr_if.paddr <<= remember(self.input_port, concat(self.input_port.addr[17], self.input_port.addr[BrewCsrAddrWidth:2]))
        self.csr_if.pwdata <<= remember(self.input_port, self.input_port.data)

def sim():

    class CsrQueueItem(object):
        def __init__(self, req: ApbIf = None, *, pwrite = None, paddr = None, pwdata = None):
            if req is not None:
                self.pwrite = req.pwrite
                self.paddr  = req.paddr
                self.pwdata = req.pwdata
            else:
                self.pwrite = int(pwrite) if pwrite is not None else None
                self.paddr  = paddr
                self.pwdata = pwdata
        def report(self,prefix):
            if not self.pwrite:
                print(f"{prefix} reading CSR {self.paddr:03x}")
            else:
                data_str = f"{self.pwdata:08x}" if self.pwdata is not None else "--------"
                print(f"{prefix} writing CSR {self.paddr:03x} data:{data_str}")
        def compare(self, actual: Union[BusIfRequestIf, 'BusIfQueueItem']):
            assert self.pwrite is None or actual.pwrite == self.pwrite
            assert self.paddr is None or actual.paddr == self.paddr
            assert self.pwdata is None or actual.pwdata == self.pwdata


    class CsrEmulator(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        input_port = Input(ApbIf)

        def construct(self, queue: List[CsrQueueItem]):
            self.queue = queue

        def simulate(self, simulator) -> TSimEvent:
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            self.input_port.pready <<= None
            self.input_port.prdata <<= None
            while True:
                yield from wait_clk()

                if self.rst == 1:
                    self.input_port.pready <<= None
                    self.input_port.prdata <<= None
                else:
                    if (self.input_port.psel == 1):
                        self.input_port.pready <<= 1
                        if self.input_port.pwrite == 0:
                            # Read request
                            actual = CsrQueueItem(self.input_port)
                            actual.report(f"{simulator.now:4d}")
                            if(self.input_port.penable == 0):
                                expected = self.queue.pop(0)
                            expected.compare(actual)
                            self.input_port.prdata <<= self.input_port.paddr | ((self.input_port.paddr+1) << 16)
                        if(self.input_port.penable == 1):
                            if self.input_port.pwrite == 1:
                                # Write request
                                actual = CsrQueueItem(self.input_port)
                                actual.report(f"{simulator.now:4d}")
                                expected = self.queue.pop(0)
                                expected.compare(actual)
                                self.input_port.prdata <<= None
                    else:
                        self.input_port.pready <<= None
                        self.input_port.prdata <<= None

    class BusIfQueueItem(object):
        def __init__(self, req: BusIfRequestIf = None, *, read_not_write = None, byte_en = None, addr = None, data = None):
            if req is not None:
                self.read_not_write  = req.read_not_write.sim_value.value
                self.byte_en         = req.byte_en.sim_value.value
                self.addr            = req.addr.sim_value.value
                self.data            = req.data.sim_value.value if req.data.sim_value is not None else None
            else:
                self.read_not_write  = int(read_not_write) if read_not_write is not None else None
                self.byte_en         = byte_en
                self.addr            = addr
                self.data            = data
        def report(self,prefix):
            assert self.addr is not None
            assert self.byte_en is not None
            access_type = 'BUS'
            if self.read_not_write == 1:
                print(f"{prefix} reading {access_type} {self.addr:08x} byte_en:{self.byte_en:02b}")
            else:
                data_str = f"{self.data:04x}" if self.data is not None else "NONE"
                print(f"{prefix} writing {access_type} {self.addr:08x} byte_en:{self.byte_en:02b} data:{data_str}")
        def compare(self, actual: Union[BusIfRequestIf, 'BusIfQueueItem']):
            assert self.read_not_write is None or actual.read_not_write == self.read_not_write
            assert self.byte_en is None or actual.byte_en == self.byte_en
            assert self.addr is None or actual.addr == self.addr
            assert self.data is None or actual.data == self.data

    class BusIfQueue(object):
        def __init__(self, depth):
            self._queue = [None,]*depth
            self._head = None
        def push(self, item):
            self._queue.append(item)
            self._head = self._queue.pop(0)
        def head(self):
            return self._head
        def __len__(self):
            return sum(1 for i in self._queue if i is not None)

    class BusIfReqEmulator(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        input_port = Input(BusIfRequestIf)

        def construct(self, queue: BusIfQueue, expect_queue: List[BusIfQueueItem]):
            self.queue = queue
            self.expect_queue = expect_queue

        def simulate(self, simulator: 'Simulator') -> TSimEvent:
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_clk_copy_valid():
                yield (self.clk, self.input_port.valid)
                self.input_port.ready <<= self.input_port.valid
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, self.input_port.valid)
                    self.input_port.ready <<= self.input_port.valid

            self.input_port.ready <<= 0

            while True:
                yield from wait_clk()

                if self.rst == 1:
                    self.input_port.ready <<= 0
                else:
                    self.input_port.ready <<= 0
                    if self.input_port.valid == 1:
                        self.input_port.ready <<= 1
                        yield from wait_clk()
                    if self.input_port.valid == 1 and self.input_port.ready == 1:
                        # Start of burst, record signals so we can check further beats
                        first_beat = BusIfQueueItem(self.input_port)
                        first_beat.report(f"{simulator.now:4d} REQUEST first")
                        expected: BusIfQueueItem = self.expect_queue.pop(0)
                        expected.compare(first_beat)
                        self.queue.push(first_beat)
                        yield from wait_clk_copy_valid()
                        beat_cnt = 1
                        while self.input_port.valid == 1:
                            next_beat = BusIfQueueItem(self.input_port)
                            next_beat.report(f"{simulator.now:4d} REQUEST {beat_cnt:5d} ")
                            assert first_beat.read_not_write == next_beat.read_not_write
                            assert first_beat.addr & ~255 == next_beat.addr & ~255
                            assert first_beat.byte_en == 3
                            assert next_beat.byte_en == 3
                            expected: BusIfQueueItem = self.expect_queue.pop(0)
                            expected.compare(next_beat)
                            self.queue.push(next_beat)
                            yield from wait_clk_copy_valid()
                            beat_cnt+=1
                        self.input_port.ready <<= 0
                        while len(self.queue) > 0:
                            self.queue.push(None)
                            yield from wait_clk()
                        print(f"{simulator.now:4d} done waiting")
                        self.queue.push(None)
                    else:
                        self.queue.push(None)


    class BusIfRspEmulator(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        output_port = Input(BusIfResponseIf)

        def construct(self, queue: BusIfQueue):
            self.queue = queue

        def simulate(self, simulator: 'Simulator') -> TSimEvent:
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            self.output_port.valid <<= 0

            while True:
                yield from wait_clk()

                if self.rst == 1:
                    self.output_port.valid <<= 0
                else:
                    item: BusIfQueueItem = self.queue.head()
                    if item is not None:
                        item.report(f"{simulator.now:4d} SERVICING ")
                        if item.read_not_write:
                            data = item.addr & 0xffff
                            self.output_port.data <<= data
                            self.output_port.valid <<= 1
                        else:
                            self.output_port.data <<= None
                            self.output_port.valid <<= 0
                    else:
                        print(f"{simulator.now:4d} SERVICING nothing")
                        self.output_port.data <<= None
                        self.output_port.valid <<= 0


    class ResponseQueueItem(object):
        def __init__(self, rsp:MemOutputIf = None, *, data_l = None, data_h = None):
            if rsp is not None:
                self.data_l    = rsp.data_l.sim_value.value if rsp.data_l.sim_value is not None else None
                self.data_h    = rsp.data_h.sim_value.value if rsp.data_h.sim_value is not None else None
            else:
                self.data_l    = data_l
                self.data_h    = data_h
        def report(self,prefix):
            data_l_str = f"{self.data_l:04x}" if self.data_l is not None else "----"
            data_h_str = f"{self.data_h:04x}" if self.data_h is not None else "----"
            print(f"{prefix} response {data_h_str}{data_l_str}")
        def compare(self, actual: Union[MemOutputIf, 'ResponseQueueItem']):
            assert self.data_l is None or actual.data_l == self.data_l
            assert self.data_h is None or actual.data_h == self.data_h

    class ResponseChecker(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        input_port = Input(MemOutputIf)

        def construct(self, queue: List[ResponseQueueItem]) -> None:
            self.queue = queue

        def simulate(self, simulator) -> TSimEvent:
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            while True:
                yield from wait_clk()
                if self.input_port.valid == 1:
                    expected = self.queue.pop(0)
                    actual = ResponseQueueItem(self.input_port)
                    actual.report(f"{simulator.now:4d} Received")
                    expected.compare(actual)




    class Stimulator(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        output_port = Output(MemInputIf)

        def construct(self, req_queue: List[BusIfQueueItem], rsp_queue: List[ResponseQueueItem], csr_queue: List[CsrQueueItem]) -> None:
            self.req_queue = req_queue
            self.rsp_queue = rsp_queue
            self.csr_queue = csr_queue

        def simulate(self) -> TSimEvent:
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_rst():
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()

            def wait_transfer():
                self.output_port.valid <<= 1
                yield from wait_clk()
                while (self.output_port.valid & self.output_port.ready) != 1:
                    yield from wait_clk()
                self.output_port.valid <<= 0

            def munge_addr(addr, offs=0):
                addr = addr // 2 + offs
                return addr

            def do_load(addr: int, access_len: int, is_csr: bool = False):
                self.output_port.read_not_write <<= 1
                self.output_port.data <<= None
                self.output_port.addr <<= addr
                self.output_port.access_len <<= access_len
                if not is_csr:
                    if access_len == access_len_32:
                        self.req_queue.append(BusIfQueueItem(read_not_write=1, byte_en=3, addr=munge_addr(addr,0), data=None))
                        self.req_queue.append(BusIfQueueItem(read_not_write=1, byte_en=3, addr=munge_addr(addr,1), data=None))
                    elif access_len == access_len_16:
                        self.req_queue.append(BusIfQueueItem(read_not_write=1, byte_en=3, addr=munge_addr(addr), data=None))
                    elif access_len == access_len_8:
                        self.req_queue.append(BusIfQueueItem(read_not_write=1, byte_en=1 << (addr & 1), addr=munge_addr(addr), data=None))
                    else:
                        assert False
                    self.rsp_queue.append(ResponseQueueItem(
                        data_l=(addr//2+0) & 0xffff,
                        data_h=(addr//2+1) & 0xffff if access_len == access_len_32 else None
                    ))
                else:
                    self.csr_queue.append(CsrQueueItem(
                        pwrite=0,
                        paddr=addr//4 & 1023,
                    ))
                    self.rsp_queue.append(ResponseQueueItem(
                        data_l=(addr//4+0) & 1023,
                        data_h=(addr//4+1) & 1023
                    ))

                yield from wait_transfer()

            def do_store(addr: int, data: int, access_len: int, is_csr: bool = False):
                self.output_port.read_not_write <<= 0
                self.output_port.data <<= data
                self.output_port.addr <<= addr
                self.output_port.access_len <<= access_len
                if not is_csr:
                    if access_len == access_len_32:
                        self.req_queue.append(BusIfQueueItem(read_not_write=0, byte_en=3, addr=munge_addr(addr,0), data=(data >>  0) & 0xffff))
                        self.req_queue.append(BusIfQueueItem(read_not_write=0, byte_en=3, addr=munge_addr(addr,1), data=(data >> 16) & 0xffff))
                    elif access_len == access_len_16:
                        self.req_queue.append(BusIfQueueItem(read_not_write=0, byte_en=3, addr=munge_addr(addr), data=data & 0xffff))
                    elif access_len == access_len_8:
                        self.req_queue.append(BusIfQueueItem(read_not_write=0, byte_en=1 << (addr & 1), addr=munge_addr(addr), data=data & 0xffff))
                    else:
                        assert False
                else:
                    self.csr_queue.append(CsrQueueItem(
                        pwrite=1,
                        paddr=addr//4 & 1023,
                        pwdata=data
                    ))
                yield from wait_transfer()

            self.output_port.valid <<= 0
            yield from wait_rst()
            for i in range(4):
                yield from wait_clk()

            yield from do_load(addr=0x140, access_len=access_len_32)
            yield from do_load(addr=0x240, access_len=access_len_16)
            yield from do_load(addr=0x244, access_len=access_len_8)
            yield from do_load(addr=0x245, access_len=access_len_8)
            for i in range(4):
                yield from wait_clk()
            yield from do_store(addr=0xadd0e55, data=0x12345678, access_len=access_len_32)
            yield from do_store(addr=0x0002000, data=0x23456789, access_len=access_len_16)
            yield from do_store(addr=0x0004000, data=0x3456789a, access_len=access_len_8)
            yield from do_store(addr=0x0005001, data=0x456789ab, access_len=access_len_8)
            for i in range(4):
                yield from wait_clk()
            yield from do_load(addr=0x140, access_len=access_len_32, is_csr=True)
            for i in range(4):
                yield from wait_clk()
            yield from do_store(addr=0x240, data=0xdeadbeef, access_len=access_len_32, is_csr=True)



    class top(Module):
        clk = ClkPort()
        rst = RstPort()

        def body(self):
            bus_queue = BusIfQueue(3)
            req_queue = []
            rsp_queue = []
            csr_queue = []

            seed(0)
            stimulator = Stimulator(req_queue=req_queue, rsp_queue=rsp_queue, csr_queue=csr_queue)
            csr_emulator = CsrEmulator(csr_queue)
            bus_req_emulator = BusIfReqEmulator(bus_queue, expect_queue=req_queue)
            bus_rsp_emulator = BusIfRspEmulator(bus_queue)
            response_checker = ResponseChecker(queue=rsp_queue)

            dut = MemoryStage()

            dut.input_port <<= stimulator.output_port
            response_checker.input_port <<= dut.output_port
            bus_req_emulator.input_port <<= dut.bus_req_if
            dut.bus_rsp_if <<= bus_rsp_emulator.output_port

            csr_emulator.input_port <<= dut.csr_if

        def simulate(self) -> TSimEvent:
            def clk() -> int:
                yield 5
                self.clk <<= ~self.clk & self.clk
                yield 5
                self.clk <<= ~self.clk
                yield 0

            print("Simulation started")

            self.rst <<= 1
            self.clk <<= 1
            yield 10
            for i in range(5):
                yield from clk()
            self.rst <<= 0

            for i in range(100):
                yield from clk()
            now = yield 10
            print(f"Done at {now}")

    Build.simulation(top, "memory.vcd", add_unnamed_scopes=True)

def gen():
    def top():
        return ScanWrapper(MemoryStage, {"clk", "rst"})

    netlist = Build.generate_rtl(top, "memory.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(target_dir="q_memory", top_level=top_level_name, source_files=("memory.sv",), clocks=(("clk", 10), ("top_clk", 100)), project_name="memory")
    flow.generate()
    flow.run()

if __name__ == "__main__":
    #gen()
    sim()
