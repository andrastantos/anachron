
#!/usr/bin/python3
from random import *
from typing import *
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

from dataclasses import dataclass
import itertools
from copy import copy

"""
    DMA core integrated into the CPU

    For DMA accesses we generate I/O-style bus-cycles (which happen to be valid DRAM cycles as well).
    The only difference is that we assert DRAM_nRAS and nDACKx instead of nREN. This generates a memory cycle.

    DRAM_nWE is asserted to writes (from I/O to memory) and de-asserted for reads.
    THIS IS OPPOSITE OF nIOR/nIOW DECODING ON THE ISA BUS. EXTERNAL LOGIC IS NEEDED!!!

    In other words,

    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^
    DRAM_nRAS       ^^^^^^^^^\___________/^^^^^\___________/^^^^^^^^^^^\___________/^^^^^\_________________/^^
    DRAM_nCAS_A     ^^^^^^^^^^^^\________/^^^^^^^^\________/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_nCAS_B     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\________/^^^^^^^^\______________/^^
    DRAM_ADDR       ---------<==X========>-----<==X========>-----------<==X========>-----<==X==============>--
    DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\_________________/^^
    DRAM_DATA       --------------<======>----------------------------------<======>--------------------------
    DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\_________________/^^
    DRAM_DATA       ----------------------------------<====>------------------------------------------<====>--
    DRQ             ___/^^^^^\-----------/^^^^^\---------\_____/^^^^^^^\-----------/^^^^^\---------------\____
    nDACK           ^^^^^^^^^\___________/^^^^^\___________/^^^^^^^^^^^\___________/^^^^^\_________________/^^
    TC              ---------<==========>------<===========>-----------<===========>-----<=================>--
    nWAIT           ---------------/^^^^^\-----------/^^^^^\-----------------/^^^^^\-----------\_____/^^^^^\--
    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^

    DRQ is sampled every clock cycle when nDACK is high, but is ignored when nDACK is low. There is a one
    clock-cycle delay in assertion of nDACK from the detection of DRQ (in other words nDACK is registered).

    For ISA-compatible devices, the following logic can be used:

        nIOR = (nREN | ~DRAM_nWE) & (&nDACK |  DRAM_nWE)
        nIOW = (nREN |  DRAM_nWE) & (&nDACK | ~DRAM_nWE)

        nWAIT = IOCHRDY

        TC = TC

Since DRAM_nCAS_x is asserted for 1.5 cycles, it's minimum pulse length is 150ns. That's much much shorter
then the ISA bus spec of 700ns (http://www.bitsavers.org/pdf/intel/_busSpec/Intel_ISA_Spec2.01_Sep89.pdf).

That means that we have to insert many many wait-states, not just one as with I/O cycles. The bus interface
will use the high-order bits of the target address (even if it's in DRAM) to generate the right number of
wait-states, in other words, wait-state programming is done through some of the top address bits, the same
was as for I/Os.

All in all that the DMA interface is somewhat special.
"""

class CpuDma(Module):
    clk = ClkPort()
    rst = RstPort()

    bus_req_if = Output(BusIfDmaRequestIf)
    bus_rsp_if = Input(BusIfDmaResponseIf)
    reg_if = Input(ApbIf)

    drq = Input()

    interrupt = Output(logic)

    def body(self):
        self.ch_count = self.drq.get_num_bits()

        ### Register offsets
        ################################
        ch_addr_ofs = 0
        ch_limit_ofs = 1
        ch_config_ofs = 2
        #ch_stat_ofs = 3 Read-only, so offset constant is not directly used

        ch_reg_bank_size = 4

        int_reg_ofs = self.ch_count*ch_reg_bank_size+0
        # status register bits
        #stat_active_bit = 0
        #stat_req_pending_bit = 1
        #stat_int_pending_bit = 2
        # config register bits
        cfg_single_bit         = 0
        cfg_read_not_write_bit = 1
        cfg_int_enable_bit     = 2
        cfg_is_master_bit      = 3
        cfg_high_priority_bit  = 4
        cfg_req_polarity_bit   = 5 # 0 for active low, 1 for active high request
        cfg_req_no_cdc_bit     = 6 # 0 for async requestors (that need CDC), 1 for synchronous requestors (no CDC needed)

        next_addr = Wire(BrewAddr)
        tc = Wire(logic)
        tc_reg = Reg(tc, clock_en=self.bus_req_if.ready & self.bus_req_if.valid)

        class ChInfo():
            def __init__(self):
                # Basic registers
                self.addr = Wire(BrewAddr)
                self.limit = Wire(BrewAddr)
                # Configuration bits
                self.single = Wire(logic)
                self.read_not_write = Wire(logic)
                self.int_enable = Wire(logic)
                self.is_master = Wire(logic)
                self.high_priority = Wire(logic)
                self.req_polarity = Wire(logic)
                self.req_no_cdc = Wire(logic)
                # Status bits
                self.active = Wire(logic)
                self.int_pending = Wire(logic)
                self.req_pending = Wire(logic)


        ch_infos = tuple(ChInfo() for _ in range(self.ch_count))

        reg_write_strobe = self.reg_if.psel & self.reg_if.pwrite & self.reg_if.penable
        self.reg_if.pready <<= 1

        reg_addr = self.reg_if.paddr

        selected_dma_channel = Wire(Unsigned(self.ch_count)) # one-hot encoded channel selector, based on arbitration

        served_dma_channel = Reg(selected_dma_channel, clock_en=self.bus_req_if.ready & self.bus_req_if.valid)

        drq = Wire(Unsigned(self.ch_count))
        for idx in range(self.ch_count):
            drq[idx] <<= ch_infos[idx].req_polarity ^ Select(ch_infos[idx].req_no_cdc, Reg(Reg(self.drq[idx])), self.drq[idx])
        prev_drq = Reg(drq)

        for idx, ch_info in enumerate(ch_infos):
            ch_base = idx*ch_reg_bank_size
            ch_served = served_dma_channel[idx] & self.bus_rsp_if.valid

            ch_info.addr <<= Reg(
                Select(
                    (reg_addr == ch_base + ch_addr_ofs) & reg_write_strobe,
                    Select(
                        ch_served,
                        ch_info.addr,
                        next_addr
                    ),
                    self.reg_if.pwdata
                )
            )
            ch_info.limit <<= Reg(self.reg_if.pwdata, clock_en = (reg_addr == ch_base + ch_limit_ofs) & reg_write_strobe)

            ch_info.single         <<= Reg(self.reg_if.pwdata[cfg_single_bit        ], clock_en = (reg_addr == ch_base + ch_config_ofs) & reg_write_strobe)
            ch_info.read_not_write <<= Reg(self.reg_if.pwdata[cfg_read_not_write_bit], clock_en = (reg_addr == ch_base + ch_config_ofs) & reg_write_strobe)
            ch_info.int_enable     <<= Reg(self.reg_if.pwdata[cfg_int_enable_bit    ], clock_en = (reg_addr == ch_base + ch_config_ofs) & reg_write_strobe)
            ch_info.is_master      <<= Reg(self.reg_if.pwdata[cfg_is_master_bit     ], clock_en = (reg_addr == ch_base + ch_config_ofs) & reg_write_strobe)
            ch_info.high_priority  <<= Reg(self.reg_if.pwdata[cfg_high_priority_bit ], clock_en = (reg_addr == ch_base + ch_config_ofs) & reg_write_strobe)
            ch_info.req_polarity   <<= Reg(self.reg_if.pwdata[cfg_req_polarity_bit  ], clock_en = (reg_addr == ch_base + ch_config_ofs) & reg_write_strobe)
            ch_info.req_no_cdc     <<= Reg(self.reg_if.pwdata[cfg_req_no_cdc_bit    ], clock_en = (reg_addr == ch_base + ch_config_ofs) & reg_write_strobe)

            ch_info.active <<= Reg(
                Select(
                    (reg_addr == ch_base + ch_addr_ofs) & reg_write_strobe,
                    Select(
                        ch_served,
                        ch_info.active,
                        ~tc_reg
                    ),
                    1
                )
            )
            ch_info.int_pending <<= Reg(
                Select(
                    tc_reg & ch_served & ch_info.int_enable,
                    Select(
                        (reg_addr == int_reg_ofs) & reg_write_strobe & self.reg_if.pwdata[idx],
                        ch_info.int_pending,
                        0
                    ),
                    1
                )
            )
            ch_info.req_pending <<= ch_info.active & Select(
                ch_info.single & ~ch_info.is_master,
                # Single mode: create edge-sensitive requests (with an extra cycle latency)
                Reg(
                    Select(drq[idx] & ~prev_drq[idx],
                        Select(
                            ch_served,
                            ch_info.req_pending,
                            0
                        ),
                        1
                    )
                ),
                # Burst mode: level-sensitive requests
                drq[idx]
            )

            # Export all ch_info members into a wire that can be dumped into a VCD file
            for name, member in vars(ch_info).items():
                if is_wire(member):
                    setattr(self, f"ch_{idx}_{name}", member)
            setattr(self, f"ch_{idx}_served", ch_served)
        del ch_served

        ch_read_not_writes = concat(*(ch_info.read_not_write for ch_info in reversed(ch_infos)))

        self.reg_if.prdata <<= Reg(Select(
            reg_addr,
            *(itertools.chain.from_iterable((
                # offset 0: channel address
                ch_info.addr,
                # offset 1: channel limit
                ch_info.limit,
                # offset 2: channel config
                concat(
                    ch_info.req_polarity,
                    ch_info.req_no_cdc,
                    ch_info.is_master,
                    ch_info.high_priority,
                    ch_info.read_not_write,
                    ch_info.single
                ),
                # offset 3: channel status
                concat(
                    ch_info.int_pending,
                    ch_info.req_pending,
                    ch_info.active
                )
            ) for ch_info in ch_infos)),
            # int_reg_ofs
            concat(*(ch_info.int_pending for ch_info in reversed(ch_infos))),
        ))

        self.interrupt <<= or_gate(*(ch_info.int_pending for ch_info in reversed(ch_infos)))

        # Arbitration logic (we have a high-priority and a low-priority arbiter, each implementing their own round-robin)
        # NOTE: We step both arbiters at the same time, independent of whether they were the ones providing the requestor.
        #       This might be slightly sub-optimal, but I doubt it would cause trouble in real life.
        priority_change = Wire(logic)
        high_pri_selected_dma_channel = Wire(Unsigned(self.ch_count))
        low_pri_selected_dma_channel = Wire(Unsigned(self.ch_count))
        high_pri_req_pending = Wire(Unsigned(self.ch_count))
        low_pri_req_pending  = Wire(Unsigned(self.ch_count))
        high_pri_selected = Wire()

        priority_change <<= self.bus_rsp_if.valid
        req_pendig = or_gate(*(ch_info.req_pending for ch_info in ch_infos))
        high_pri_req_pending <<= concat(*(ch_info.req_pending &  ch_info.high_priority for ch_info in reversed(ch_infos)))
        low_pri_req_pending  <<= concat(*(ch_info.req_pending & ~ch_info.high_priority for ch_info in reversed(ch_infos)))
        high_pri_arbiter = RoundRobinArbiter()
        low_pri_arbiter = RoundRobinArbiter()
        high_pri_selected_dma_channel <<= high_pri_arbiter(high_pri_req_pending, advance=priority_change &  high_pri_selected)
        low_pri_selected_dma_channel  <<= low_pri_arbiter(low_pri_req_pending,  advance=priority_change & ~high_pri_selected)
        high_pri_selected <<= high_pri_req_pending != 0
        selected_dma_channel <<= Select(
            high_pri_selected,
            low_pri_selected_dma_channel,
            high_pri_selected_dma_channel
        )

        def byte_en_from_lsb(addr):
            return concat(addr[0], ~addr[0])

        def select_for_ch(one_hot_channel, per_channel_values):
            return SelectOne(
                *itertools.chain.from_iterable(
                    (selector, value) for selector, value in zip(one_hot_channel, per_channel_values)
                ),
                default_port = 0
            )

        selected_addr = select_for_ch(selected_dma_channel, (ch_info.addr for ch_info in ch_infos))
        selected_limit = select_for_ch(selected_dma_channel, (ch_info.limit for ch_info in ch_infos))
        tc <<= ~(selected_addr < selected_limit)
        next_addr <<= Reg((selected_addr + 1)[31:0], clock_en=self.bus_req_if.ready & self.bus_req_if.valid)

        # Bus interface
        self.bus_req_if.valid           <<= req_pendig
        read_not_writes = Wire(Unsigned(self.ch_count))
        read_not_writes <<= ch_read_not_writes & selected_dma_channel
        self.bus_req_if.read_not_write  <<= or_gate(*read_not_writes) # reduction or; only a single DMA channel is enabled, so all other channels are masked out
        self.bus_req_if.one_hot_channel <<= selected_dma_channel
        self.bus_req_if.byte_en         <<= select_for_ch(selected_dma_channel, (byte_en_from_lsb(ch_info.addr) for ch_info in ch_infos))
        self.bus_req_if.addr            <<= selected_addr[31:1]
        self.bus_req_if.is_master       <<= select_for_ch(selected_dma_channel, (ch_info.is_master for ch_info in ch_infos))
        self.bus_req_if.terminal_count  <<= tc


def sim():
    class BusIfSim(Module):
        clk = ClkPort()
        rst = RstPort()

        req_port = Input(BusIfDmaRequestIf)
        rsp_port = Output(BusIfDmaResponseIf)

        dack = Output(Unsigned(4))
        tc = Output(logic)

        def simulate(self, simulator: Simulator):
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_rst():
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()

            self.req_port.ready <<= 0
            self.rsp_port.valid <<= 0
            yield from wait_rst()

            self.req_port.ready <<= 1
            while True:
                yield from wait_clk()
                if self.req_port.ready & self.req_port.valid:
                    self.dack <<= self.req_port.one_hot_channel
                    self.tc <<= self.req_port.terminal_count
                    yield from wait_clk()
                    yield from wait_clk()
                    self.rsp_port.valid <<= 1
                    self.dack <<= 0
                    yield from wait_clk()
                    self.rsp_port.valid <<= 0

    class Driver(Module):
        clk = ClkPort()
        rst = RstPort()

        drq = Output(Unsigned(4))
        dack = Input(Unsigned(4))
        tc = Input(logic)
        reg_if = Output(ApbIf)

        def construct(self):
            self.reg_if.paddr.set_net_type(Unsigned(4))

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

            def start_transfer(ch, base, limit, read_not_write, *, master=False, single=False, high_pri=False):
                conf_val = (
                    (1 << 0) & (-single) |
                    (1 << 1) & (-read_not_write) |
                    (1 << 2) & (-master) |
                    (1 << 3) & (-high_pri)
                )
                yield from write_reg(4*2+2, conf_val << (4*ch))
                yield from write_reg(ch*2+1, limit)
                yield from write_reg(ch*2+0, base) # Write base last as that activates the channel

            self.drq <<= 0
            self.reg_if.psel <<= 0
            yield from wait_rst()
            yield from start_transfer(0, 100, 110, False)
            while True:
                for _ in range(randint(0,3)):
                    yield from wait_clk()
                simulator.log(f"CH {0} drq sent")
                self.drq <<= 1 << 0
                yield from wait_clk()
                while (self.dack & (1 << 0)) != 1:
                    yield from wait_clk()
                tc = copy(self.tc)
                if tc:
                    simulator.log(f"CH {0} TERMINAL dack received")
                else:
                    simulator.log(f"CH {0} dack received")
                self.drq <<= 0
                while (self.dack & (1 << 0)) != 0:
                    yield from wait_clk()
                if tc:
                    break

            self.drq <<= 0
            self.reg_if.psel <<= 0
            for _ in range(10): yield from wait_clk()
            yield from start_transfer(0, 100, 110, False, single=True)
            while True:
                for _ in range(randint(0,3)):
                    yield from wait_clk()
                simulator.log(f"CH {0} drq sent")
                self.drq <<= 1 << 0
                yield from wait_clk()
                while (self.dack & (1 << 0)) != 1:
                    yield from wait_clk()
                tc = copy(self.tc)
                if tc:
                    simulator.log(f"CH {0} TERMINAL dack received")
                else:
                    simulator.log(f"CH {0} dack received")
                self.drq <<= 0
                while (self.dack & (1 << 0)) != 0:
                    yield from wait_clk()
                if tc:
                    break



    class top(Module):
        clk = ClkPort()
        rst = RstPort()

        def body(self):
            dut = CpuDma()
            bus_if_sim = BusIfSim()
            driver = Driver()

            bus_if_sim.req_port <<= dut.bus_req_if
            dut.bus_rsp_if <<= bus_if_sim.rsp_port
            dut.reg_if <<= driver.reg_if
            dut.drq <<= driver.drq
            driver.dack <<= bus_if_sim.dack
            driver.tc <<= bus_if_sim.tc

        def simulate(self, simulator: Simulator):
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

            for i in range(300):
                yield from clk()
            now = yield 10
            print(f"Done at {now}")

    Build.simulation(top, "cpu_dma.vcd", add_unnamed_scopes=True)


def gen():
    def top():
        class CpuDmaWrapper(Module):
            clk = ClkPort()
            rst = RstPort()

            bus_req_if = Output(BusIfDmaRequestIf)
            bus_rsp_if = Input(BusIfDmaResponseIf)
            reg_if_pwrite = Input(logic)
            reg_if_psel = Input(logic)
            reg_if_penable = Input(logic)
            reg_if_pready = Output(logic)
            reg_if_paddr = Input(Unsigned(4))
            reg_if_pwdata = Input(BrewCsrData)
            reg_if_prdata = Output(BrewCsrData)
            drq = Input(Unsigned(4))

            def body(self) -> None:
                dma = CpuDma()
                self.bus_req_if <<= dma.bus_req_if
                dma.bus_rsp_if <<= self.bus_rsp_if
                self.reg_if_pready <<= dma.reg_if.pready
                self.reg_if_prdata <<= dma.reg_if.prdata
                dma.reg_if.pwrite <<= self.reg_if_pwrite
                dma.reg_if.psel <<= self.reg_if_psel
                dma.reg_if.penable <<= self.reg_if_penable
                dma.reg_if.paddr <<= self.reg_if_paddr
                dma.reg_if.pwdata <<= self.reg_if_pwdata
                dma.drq <<= self.drq

        return ScanWrapper(CpuDmaWrapper, {"clk", "rst"})

    netlist = Build.generate_rtl(top, "cpu_dma.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(target_dir="q_cpu_dma", top_level=top_level_name, source_files=("cpu_dma.sv",), clocks=(("clk", 10), ("top_clk", 100)), project_name="cpu_dma")
    flow.generate()
    flow.run()

if __name__ == "__main__":
    #gen()
    sim()
