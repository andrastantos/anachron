#!/usr/bin/python3

# This is the top-level BREW V1 CPU

import sys
from pathlib import Path
import itertools

sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon"))
sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon" / "unit_tests"))

try:
    from .brew_types import *
    from .brew_utils import *

    from .pipeline import Pipeline
    from .bus_if import BusIf
    from .cpu_dma import CpuDma
    from .synth import *
    from .assembler import *
    from .apb_timer import ApbSimpleTimer

except ImportError:
    from brew_types import *
    from brew_utils import *

    from pipeline import Pipeline
    from bus_if import BusIf
    from cpu_dma import CpuDma
    from synth import *
    from assembler import *
    from apb_timer import ApbSimpleTimer

class BrewV1Top(GenericModule):
    clk               = ClkPort()
    rst               = RstPort()

    # DRAM interface
    dram              = Output(ExternalBusIf)

    # External dma-request
    drq               = Input(Unsigned(4))

    n_int             = Input(logic)

    def construct(self, nram_base: int = 0x0, has_multiply: bool = True, has_shift: bool = True, page_bits: int = 7):
        self.nram_base = nram_base
        self.has_multiply = has_multiply
        self.has_shift = has_shift
        self.page_bits = page_bits

        self.csr_cpu_task_mode_page      = 0x8000
        self.csr_cpu_scheduler_mode_page = 0x0000

        self.csr_mach_arch      = 0x00
        self.csr_capability     = 0x01
        self.csr_pmem_base_ofs  = 0x80
        self.csr_pmem_limit_ofs = 0x81
        self.csr_dmem_base_ofs  = 0x82
        self.csr_dmem_limit_ofs = 0x83
        self.csr_ecause_ofs     = 0x00
        self.csr_eaddr_ofs      = 0x01

        self.csr_mach_arch_reg  = self.csr_cpu_task_mode_page + self.csr_mach_arch
        self.csr_capability_reg = self.csr_cpu_task_mode_page + self.csr_capability
        self.csr_pmem_base_reg  = self.csr_cpu_scheduler_mode_page + self.csr_pmem_base_ofs
        self.csr_pmem_limit_reg = self.csr_cpu_scheduler_mode_page + self.csr_pmem_limit_ofs
        self.csr_dmem_base_reg  = self.csr_cpu_scheduler_mode_page + self.csr_dmem_base_ofs
        self.csr_dmem_limit_reg = self.csr_cpu_scheduler_mode_page + self.csr_dmem_limit_ofs
        self.csr_ecause_reg     = self.csr_cpu_scheduler_mode_page + self.csr_ecause_ofs
        self.csr_eaddr_reg      = self.csr_cpu_scheduler_mode_page + self.csr_eaddr_ofs

    def body(self):
        bus_if = BusIf(nram_base=self.nram_base)
        pipeline = Pipeline(has_multiply=self.has_multiply, has_shift=self.has_shift, page_bits=self.page_bits)
        dma = CpuDma()
        timer = ApbSimpleTimer()

        # Things that need CSR access
        ecause     = Wire(EnumNet(exceptions))
        ecause_clear_pulse = Wire()
        eaddr      = Wire(BrewAddr)
        pmem_base  = Wire(BrewMemBase)
        pmem_limit = Wire(BrewMemBase)
        dmem_base  = Wire(BrewMemBase)
        dmem_limit = Wire(BrewMemBase)

        self.csrs_cpu_task_mode = {
            self.csr_mach_arch:  RegMapEntry("csr_mach_arch",  (RegField("32'b0",access="R"),), "Machine architecture register"),
            self.csr_capability: RegMapEntry("csr_capability", (RegField("32'b0",access="R"),), "Machine capability register")
        }

        self.csrs_cpu_scheduler_mode = {
            self.csr_ecause_ofs:     RegMapEntry("csr_ecause",     (RegField(ecause,access="R"),), "Exception cause register", read_pulse=ecause_clear_pulse),
            self.csr_eaddr_ofs:      RegMapEntry("csr_eaddr",      (RegField(eaddr,access="R"),), "Exception address register"),

            self.csr_pmem_base_ofs:  RegMapEntry("csr_pmem_base",  (RegField(pmem_base,  start_bit=10),), "Program memory base register"),
            self.csr_pmem_limit_ofs: RegMapEntry("csr_pmem_limit", (RegField(pmem_limit, start_bit=10),), "Program memory limit register"),
            self.csr_dmem_base_ofs:  RegMapEntry("csr_dmem_base",  (RegField(dmem_base,  start_bit=10),), "Data memory base register"),
            self.csr_dmem_limit_ofs: RegMapEntry("csr_dmem_limit", (RegField(dmem_limit, start_bit=10),), "Data memory limit register"),
        }


        fetch_to_bus = Wire(BusIfRequestIf)
        bus_to_fetch = Wire(BusIfResponseIf)
        mem_to_bus = Wire(BusIfRequestIf)
        bus_to_mem = Wire(BusIfResponseIf)
        dma_to_bus = Wire(BusIfDmaRequestIf)
        bus_to_dma = Wire(BusIfDmaResponseIf)
        csr_if = Wire(CsrIf)
        self.cpu_task_mode_csr_if = Wire(CsrIf)
        self.cpu_scheduler_mode_csr_if = Wire(CsrIf)
        bus_if_reg_if = Wire(CsrIf)
        dma_reg_if = Wire(CsrIf)
        timer_reg_if = Wire(CsrIf)

        # BUS INTERFACE
        ###########################
        bus_if.fetch_request <<= fetch_to_bus
        bus_to_fetch <<= bus_if.fetch_response
        bus_if.mem_request <<= mem_to_bus
        bus_to_mem <<= bus_if.mem_response
        bus_if.dma_request <<= dma_to_bus
        bus_to_dma <<= bus_if.dma_response

        self.dram <<= bus_if.dram

        bus_if.reg_if <<= bus_if_reg_if

        # DMA
        ###########################
        dma_to_bus <<= dma.bus_req_if
        dma.bus_rsp_if <<= bus_to_dma

        dma.drq <<= self.drq

        dma.reg_if <<= dma_reg_if

        # Timer
        ############################
        timer.bus_if <<= timer_reg_if

        # PIPELINE
        ############################
        fetch_to_bus <<= pipeline.fetch_to_bus
        pipeline.bus_to_fetch <<= bus_to_fetch
        mem_to_bus <<= pipeline.mem_to_bus
        pipeline.bus_to_mem <<= bus_to_mem
        csr_if <<= pipeline.csr_if

        pipeline.ecause_clear_pulse <<= ecause_clear_pulse
        ecause <<= pipeline.ecause
        eaddr  <<= pipeline.eaddr
        pipeline.pmem_base  <<= pmem_base
        pipeline.pmem_limit <<= pmem_limit
        pipeline.dmem_base  <<= dmem_base
        pipeline.dmem_limit <<= dmem_limit

        pipeline.interrupt <<= ~self.n_int | ~timer.n_int

        event_fetch_wait_on_bus = pipeline.event_fetch_wait_on_bus
        event_decode_wait_on_rf = pipeline.event_decode_wait_on_rf
        event_mem_wait_on_bus   = pipeline.event_mem_wait_on_bus
        event_branch_taken      = pipeline.event_branch_taken
        event_branch            = pipeline.event_branch
        event_load              = pipeline.event_load
        event_store             = pipeline.event_store
        event_execute           = pipeline.event_execute
        event_bus_idle          = bus_if.event_bus_idle
        event_fetch             = pipeline.event_fetch
        event_fetch_drop        = pipeline.event_fetch_drop
        event_inst_word         = pipeline.event_inst_word

        # CSR address decode
        #############################
        csr_cpu_task_mode_psel      = csr_if.psel & (csr_if.paddr[15:8] == 0x80)
        csr_cpu_scheduler_mode_psel = csr_if.psel & (csr_if.paddr[15:8] == 0x00)
        csr_event_psel              = csr_if.psel & (csr_if.paddr[15:8] == 0x81)
        csr_bus_if_psel             = csr_if.psel & (csr_if.paddr[15:8] == 0x02)
        csr_dma_psel                = csr_if.psel & (csr_if.paddr[15:8] == 0x03)
        csr_timer_psel              = csr_if.psel & (csr_if.paddr[15:8] == 0x04)

        top_level_prdata = Wire(Unsigned(32))
        top_level_pready = Wire(logic)

        # CSR bus routing
        #############################
        dma_reg_if.pwrite  <<= csr_if.pwrite
        dma_reg_if.psel    <<= csr_dma_psel
        dma_reg_if.penable <<= csr_if.penable
        dma_reg_if.paddr   <<= csr_if.paddr[4:0] # FIXME: This used to be 3:0 which generated a silent error: There are actually 17 decoded registers, yet we happily generated the decoder logic with a 4-bit address
        dma_reg_if.pwdata  <<= csr_if.pwdata

        bus_if_reg_if.pwrite  <<= csr_if.pwrite
        bus_if_reg_if.psel    <<= csr_bus_if_psel
        bus_if_reg_if.penable <<= csr_if.penable
        bus_if_reg_if.paddr   <<= csr_if.paddr[3:0]
        bus_if_reg_if.pwdata  <<= csr_if.pwdata

        timer_reg_if.pwrite  <<= csr_if.pwrite
        timer_reg_if.psel    <<= csr_timer_psel
        timer_reg_if.penable <<= csr_if.penable
        timer_reg_if.paddr   <<= csr_if.paddr[1:0]
        timer_reg_if.pwdata  <<= csr_if.pwdata

        self.cpu_task_mode_csr_if.pwrite  <<= csr_if.pwrite
        self.cpu_task_mode_csr_if.psel    <<= csr_cpu_task_mode_psel
        self.cpu_task_mode_csr_if.penable <<= csr_if.penable
        self.cpu_task_mode_csr_if.paddr   <<= csr_if.paddr[3:0]
        self.cpu_task_mode_csr_if.pwdata  <<= csr_if.pwdata

        self.cpu_scheduler_mode_csr_if.pwrite  <<= csr_if.pwrite
        self.cpu_scheduler_mode_csr_if.psel    <<= csr_cpu_scheduler_mode_psel
        self.cpu_scheduler_mode_csr_if.penable <<= csr_if.penable
        self.cpu_scheduler_mode_csr_if.paddr   <<= csr_if.paddr[7:0]
        self.cpu_scheduler_mode_csr_if.pwdata  <<= csr_if.pwdata

        event_prdata = Wire(BrewData)

        csr_if.prdata <<= SelectOne(
            csr_dma_psel,                dma_reg_if.prdata,
            csr_timer_psel,              timer_reg_if.prdata,
            csr_bus_if_psel,             bus_if_reg_if.prdata,
            csr_event_psel,              event_prdata,
            csr_cpu_task_mode_psel,      self.cpu_task_mode_csr_if.prdata,
            csr_cpu_scheduler_mode_psel, self.cpu_scheduler_mode_csr_if.prdata
        )
        csr_if.pready <<= SelectOne(
            csr_dma_psel,                dma_reg_if.pready,
            csr_timer_psel,              timer_reg_if.pready,
            csr_bus_if_psel,             bus_if_reg_if.pready,
            csr_event_psel,              1,
            csr_cpu_task_mode_psel,      self.cpu_task_mode_csr_if.pready,
            csr_cpu_scheduler_mode_psel, self.cpu_scheduler_mode_csr_if.pready
        )

        # EVENT COUNTERS
        #############################

        event_counter_size = 32
        event_counter_cnt = 8

        event_cnts = []
        event_selects = []
        event_regs = []
        event_enabled = Wire(logic)
        event_write_strobe = csr_event_psel &  csr_if.pwrite & csr_if.penable

        for i in range(event_counter_cnt):
            event_cnt = Wire(Unsigned(event_counter_size))
            event_select = Wire(Unsigned(5))
            event = Select(event_select,
                1,
                event_fetch_wait_on_bus,
                event_decode_wait_on_rf,
                event_mem_wait_on_bus,
                event_branch_taken,
                event_branch,
                event_load,
                event_store,
                event_load | event_store,
                event_execute,
                event_bus_idle,
                event_fetch,
                event_fetch_drop,
                event_inst_word
            )
            event_cnt <<= Reg((event_cnt + event)[event_cnt.get_num_bits()-1:0], clock_en=event_enabled)
            setattr(self, f"event_cnt_{i}", event_cnt)
            setattr(self, f"event_select_{i}", event_select)
            event_cnts.append(event_cnt)
            event_selects.append(event_select)
            event_regs.append(event_select)
            event_regs.append(event_cnt)
            del event
            del event_cnt
            del event_select

        event_addr = csr_if.paddr[4:0]
        event_prdata <<= Reg(Select(
            event_addr,
            event_enabled, # Global enable register
            0,             # Reserved
            *event_regs,   # Pairs of selector/counter registers
        ))
        event_enabled <<= Reg(csr_if.pwdata[0], clock_en=(event_addr == 0) & event_write_strobe) # Global enable register
        for i, (event_cnt, event_select) in enumerate(zip(event_cnts, event_selects)):
            event_select <<= Reg(csr_if.pwdata[event_select.get_num_bits()-1:0], clock_en=(event_addr == i*2+2) & event_write_strobe) # Selector registers
            # Counters are read-only.
        del event_cnt
        del event_select

        # CSRs
        #####################

        '''
        APB signalling

                        <-- read -->      <-- write ->
            CLK     \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/
            psel    ___/^^^^^^^^^^^\_____/^^^^^^^^^^^\______
            penable _________/^^^^^\___________/^^^^^\______
            pready  ---------/^^^^^\-----------/^^^^^\------
            pwrite  ---/^^^^^^^^^^^\-----\___________/------
            paddr   ---<===========>-----<===========>------
            prdata  ---------<=====>------------------------
            pwdata  ---------------------<===========>------
            csr_rs  ___/^^^^^^^^^^^\________________________
            csr_wr  ___________________________/^^^^^\______
        '''

        create_apb_reg_map(self.csrs_cpu_task_mode,      self.cpu_task_mode_csr_if)
        create_apb_reg_map(self.csrs_cpu_scheduler_mode, self.cpu_scheduler_mode_csr_if)



def gen():
    def top():
        return BrewV1Top(nram_base=0x0, has_multiply=True, has_shift=True, page_bits=7)

    back_end = SystemVerilog()
    back_end.yosys_fix = True
    back_end.support_cast = False
    netlist = Build.generate_rtl(top, "brew_v1_top.sv", back_end=back_end)
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    cyclone_v_device = "5CEBA4U15C7"
    max_10_device = "10M04SAE144C7G"
    flow = QuartusFlow(
        target_dir="q_brew_v1_top",
        top_level="brew_v1",
        source_files=("brew_v1.sv", "brew_v1_top.sv"),
        constraint_files=("brew_v1.sdc",),
        clocks=(("clk", 100),),
        device=max_10_device,
        project_name="BREW_V1"
    )
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()

