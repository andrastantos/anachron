#!/usr/bin/python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon"))
sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon" / "unit_tests"))

try:
    from .brew_types import *
    from .brew_utils import *

    from .bus_if import BusIf
    from .fetch import FetchStage
    from .decode import DecodeStage
    from .execute import ExecuteStage
    from .memory import MemoryStage
    from .sign_zero_extend import ResultExtendStage
    from .reg_file import RegFile
    from .synth import *
except ImportError:
    from brew_types import *
    from brew_utils import *

    from bus_if import BusIf
    from fetch import FetchStage
    from decode import DecodeStage
    from execute import ExecuteStage
    from memory import MemoryStage
    from sign_zero_extend import ResultExtendStage
    from reg_file import RegFile
    from synth import *

"""
TODO: Should we change mem_limit to something that's measured in logical addresses instead of physical ones?

Area notes: pretty much all the area is spent on Execute and quite a bit on Decode. All the rest is more or less rounding error.
            Execute has a *lot* of fluff in it still, decode... maybe, but not as much, I don't think.
"""

class Pipeline(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    # Memory interfaces
    fetch_to_bus = Output(BusIfRequestIf)
    bus_to_fetch = Input(BusIfResponseIf)
    mem_to_bus = Output(BusIfRequestIf)
    bus_to_mem = Input(BusIfResponseIf)
    csr_if = Output(ApbIf)

    # Things that need CSR access
    ecause_write_pulse = Input(logic)
    ecause_write_data = Input(Unsigned(12))
    ecause    = Output(Unsigned(12))
    eaddr     = Output(BrewAddr)
    pmem_base  = Input(BrewMemBase)
    pmem_limit = Input(BrewMemBase)
    dmem_base  = Input(BrewMemBase)
    dmem_limit = Input(BrewMemBase)

    interrupt         = Input(logic)

    # Events
    event_fetch_wait_on_bus = Output(logic)
    event_decode_wait_on_rf = Output(logic)
    event_mem_wait_on_bus   = Output(logic)
    event_branch_taken      = Output(logic)
    event_branch            = Output(logic)
    event_load              = Output(logic)
    event_store             = Output(logic)
    event_execute           = Output(logic)
    event_fetch             = Output(logic)
    event_fetch_drop        = Output()
    event_inst_word         = Output()

    def construct(self, csr_base: int, has_multiply: bool = True, has_shift: bool = True, page_bits: int = 7):
        self.csr_base = csr_base
        self.has_multiply = has_multiply
        self.has_shift = has_shift
        self.page_bits = page_bits

    def body(self):
        # Instruction pointers
        spc  = Wire(BrewInstAddr)
        tpc  = Wire(BrewInstAddr)
        task_mode  = Wire(logic)

        # Connecting tissue
        fetch_to_decode = Wire(FetchDecodeIf)
        decode_to_exec = Wire(DecodeExecIf)
        do_branch = Wire(logic)
        exec_to_extend = Wire(ResultExtendIf)
        rf_req = Wire(RegFileReadRequestIf)
        rf_rsp = Wire(RegFileReadResponseIf)
        rf_write = Wire(RegFileWriteBackIf)

        # Stages
        fetch_stage = FetchStage(page_bits=self.page_bits)
        decode_stage = DecodeStage(has_multiply=self.has_multiply, has_shift=self.has_multiply)
        execute_stage = ExecuteStage(csr_base=self.csr_base, has_multiply=self.has_multiply, has_shift=self.has_multiply)
        result_extend_stage = ResultExtendStage()
        reg_file = RegFile()

        # FETCH STAGE
        ############################
        self.fetch_to_bus <<= fetch_stage.bus_if_request
        fetch_stage.bus_if_response <<= self.bus_to_fetch

        fetch_to_decode <<= fetch_stage.decode

        fetch_stage.mem_base <<= self.pmem_base
        fetch_stage.mem_limit <<= self.pmem_limit
        fetch_stage.spc <<= spc
        fetch_stage.tpc <<= tpc
        fetch_stage.task_mode <<= task_mode
        fetch_stage.do_branch <<= do_branch
        fetch_stage.break_burst <<= decode_stage.break_fetch_burst

        self.event_fetch <<= fetch_stage.event_fetch
        self.event_fetch_drop <<= fetch_stage.event_dropped

        self.event_fetch_wait_on_bus <<= self.fetch_to_bus.valid & ~self.fetch_to_bus.ready

        # DECODE STAGE
        ############################
        decode_stage.fetch           <<= fetch_to_decode
        decode_to_exec               <<= decode_stage.output_port

        rf_req <<= decode_stage.reg_file_req
        decode_stage.reg_file_rsp <<= rf_rsp

        decode_stage.do_branch <<= do_branch

        self.event_decode_wait_on_rf <<= rf_req.valid & ~rf_req.ready

        # EXECUTE STAGE
        #############################
        execute_stage.input_port <<= decode_to_exec
        exec_to_extend           <<= execute_stage.output_port

        self.mem_to_bus <<= execute_stage.bus_req_if
        execute_stage.bus_rsp_if <<= self.bus_to_mem

        self.csr_if <<= execute_stage.csr_if

        execute_stage.mem_base      <<= self.dmem_base
        execute_stage.mem_limit     <<= self.dmem_limit
        execute_stage.spc_in        <<= spc
        execute_stage.tpc_in        <<= tpc
        execute_stage.task_mode_in  <<= task_mode
        execute_stage.ecause_in     <<= Select(
            self.ecause_write_pulse,
            self.ecause,
            ~self.ecause_write_data & self.ecause
        )

        execute_stage.interrupt     <<= self.interrupt

        will_execute = decode_to_exec.ready & decode_to_exec.valid & ~decode_to_exec.fetch_av & ~execute_stage.do_branch
        self.event_branch     <<= will_execute & (decode_to_exec.exec_unit == op_class.branch)
        self.event_load       <<= will_execute & (decode_to_exec.exec_unit == op_class.ld_st) & (decode_to_exec.ldst_op == ldst_ops.load)
        self.event_store      <<= will_execute & (decode_to_exec.exec_unit == op_class.ld_st) & (decode_to_exec.ldst_op == ldst_ops.store)
        self.event_execute    <<= will_execute
        self.event_inst_word  <<= Select(will_execute, 0, decode_to_exec.inst_len+1)

        spc          <<= Reg(execute_stage.spc_out)
        tpc          <<= Reg(execute_stage.tpc_out)
        task_mode    <<= Reg(execute_stage.task_mode_out)
        self.ecause  <<= Reg(execute_stage.ecause_out)
        do_branch    <<= Reg(execute_stage.do_branch)
        self.eaddr   <<= execute_stage.eaddr_out

        self.event_mem_wait_on_bus <<= self.mem_to_bus.valid & ~self.mem_to_bus.ready
        self.event_branch_taken <<= do_branch

        # RESULT EXTEND STAGE
        ######################
        result_extend_stage.input_port <<= exec_to_extend
        rf_write <<= result_extend_stage.output_port

        # REG FILE
        ####################
        reg_file.read_req <<= rf_req
        rf_rsp <<= reg_file.read_rsp
        reg_file.write <<= rf_write

        reg_file.do_branch <<= do_branch


def gen():
    def top():
        return Pipeline(csr_base=0x1, has_multiply=False, has_shift=False)

    back_end = SystemVerilog()
    back_end.yosys_fix = True
    netlist = Build.generate_rtl(top, "pipeline.sv", back_end)
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(target_dir="q_pipeline", top_level=top_level_name, source_files=("pipeline.sv",), clocks=(("clk", 100),), project_name="pipeline")
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()
    #sim()


