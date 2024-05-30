#!/usr/bin/python3
from random import *
from typing import *
from silicon import *
try:
    from .brew_types import *
    from .brew_utils import *
    from .memory import MemoryStage
    from .scan import ScanWrapper
    from .synth import *
    from .exec_alu import *
    from .exec_shifter import *
    from .exec_addr_calc import *
    from .exec_mult import *
    from .exec_branch_target import *
    from .exec_branch import *
except ImportError:
    from brew_types import *
    from brew_utils import *
    from memory import MemoryStage
    from scan import ScanWrapper
    from synth import *
    from exec_alu import *
    from exec_shifter import *
    from exec_addr_calc import *
    from exec_mult import *
    from exec_branch_target import *
    from exec_branch import *

'''
Problem with multiply: Stage1 accepts a new operation while stage 2 is busy handling a read for instance. If, during that time, a multiply comes by,
it'll be accepted. But multiply is multi-stage and will continue advancing on *that* pipeline; worse, multiply doesn't have back-pressure so it'll just
assume that stage2 is ready to catch the result as it pops out.

I think I'll brake multiply into two (combinational) stages and integrate them as usual building blocks. That seems the cleanest solution.
'''
"""
Execute stage of the V1 pipeline.

This stage is sandwiched between 'decode' and 'memory'.

It does the following:
- Computes the result from source operands
- Computes effective address for memory
- Checks for all exceptions
- Tests for branches

"""

"""

    <- cycle 1 -> <- cycle 2 ->

    +-----------+
    |    ALU    |
    +-----------+
    +-----------+ +-----------+
    | Br. Trgt. | |   Branch  |
    +-----------+ +-----------+
    +-----------+ +-----------+
    | addr-gen  | |   Memory  |
    +-----------+ +-----------+
    +-----------+
    |  Shifter  |
    +-----------+
    +-------------------------+
    |        Multilper        |
    +-------------------------+

PC is cycle-1 relative. If there was a branch, that will be determined in cycle-2,
though the branch target address is calculated in cycle-1. This means that cycle-1
executes the instruction in a branch-shadow, if there were no bubbles in the pipeline.
There is logic in cycle-2 to remember a branch from the previous cycle and cancel
any instruction that leaks through from cycle-1.

OK, so this is silly. What I should be doing is to build multi-cycle execution
units, just as with multiply. So, branch target and branch should be just one
unit, just like address calculation and memory.

or... maybe not. Yet, the interfaces should flow-through, no bypass info.

The counter-argument of course is stageing register reuse. This argument can
certainly be made for ALU and shifter.

OK, so address calc and branch should certainly be more integrated: a lot
of calculation for branch can be pre-loaded in which case registers could be
saved.
"""

class Exec12If(ReadyValid):
    ################ ALU/SHIFT/MULT
    result                  = BrewData
    f_zero                  = logic
    f_sign                  = logic
    f_carry                 = logic
    f_overflow              = logic
    is_mult_op              = logic
    ################ ADDR CALC
    phy_addr                = BrewAddr
    eff_addr                = BrewAddr
    mem_av                  = logic
    mem_unaligned           = logic
    is_csr                  = logic
    ################ BRANCH TARGET
    branch_addr             = BrewInstAddr
    straight_addr           = BrewInstAddr
    ################ BRANCH INPUT
    branch_op               = EnumNet(branch_ops)
    is_branch_ind           = logic
    op_a                    = BrewData # Can we move this to stage 1? For now let's keep it here...
    bit_test_bit            = logic
    spc                     = BrewInstAddr
    tpc                     = BrewInstAddr
    task_mode               = logic
    fetch_av                = logic # Coming all the way from fetch: if the instruction gotten this far, we should raise the exception
    mem_av                  = logic # Coming from the load-store unit if that figures out an exception
    mem_unaligned           = logic # Coming from the load-store unit if an unaligned access was attempted
    is_branch_insn          = logic
    woi                     = logic
    ################ MEMORY INPUT
    read_not_write          = logic
    access_len              = Unsigned(2) # 0 for 8-bit, 1 for 16-bit, 2 for 32-bit
    is_mem_op               = logic
    ################ WRITE-BACK GENERATION
    result_reg_addr         = BrewRegAddr
    result_reg_addr_valid   = logic
    do_bse                  = logic
    do_wse                  = logic
    do_bze                  = logic
    do_wze                  = logic
    ################ HELP WITH INTERRUPTS AND EXCEPTIONS
    is_interrupt            = logic
    is_exception            = logic

class ExecStage1(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    # Pipeline input
    input_port = Input(DecodeExecIf)

    # Pipeline output
    output_port = Output(Exec12If)

    # Multiplier output
    mult_result = Output(BrewData) # This is needed separately due to the internal pipelining of the multiplier

    # side-band interfaces
    mem_base = Input(BrewMemBase)
    mem_limit = Input(BrewMemBase)
    spc_in  = Input(BrewInstAddr)
    spc_out = Output(BrewInstAddr) # Output only straight-line updates. Branches come from stage 2
    tpc_in  = Input(BrewInstAddr)
    tpc_out = Output(BrewInstAddr) # Output only straight-line updates. Branches come from stage 2
    task_mode_in  = Input(logic)
    interrupt = Input(logic)

    do_branch_immediate = Input(logic) # This is the unregistered version, not the one that all other stages use
    do_branch = Input(logic) # This is the regular, registered version

    def construct(self, has_multiply: bool = True, has_shift: bool = True):
        self.has_multiply = has_multiply
        self.has_shift = has_shift

    def body(self):
        # We have two stages in one, really here

        input_buf = ForwardBuf()
        input_buf_en = input_buf.out_reg_en

        reg_input_port = Wire(DecodeExecIf)
        reg_input_port <<= input_buf(self.input_port)

        # Have to capture all the side-band ports that are needed in stage 2:
        # SPC/TPC all the others are stage-1 relative
        # TODO: do we? I'm not actually certain now that we register the input into stages...
        reg_tpc = Reg(self.tpc_in, clock_en=input_buf_en)
        reg_spc = Reg(self.spc_in, clock_en=input_buf_en)
        reg_task_mode = Reg(self.task_mode_in, clock_en=input_buf_en)
        reg_pc = Select(reg_task_mode, reg_spc, reg_tpc)
        reg_interrupt = Reg(self.interrupt, clock_en=input_buf_en)

        # Handshake
        # TODO: not sure about the double-clear here: we clear stage 1 for two cycles on a branch...
        reg_input_port.ready <<= self.do_branch_immediate | self.do_branch | self.output_port.ready
        self.output_port.valid <<= reg_input_port.valid & ~ self.do_branch

        # ALU
        alu_output = Wire(AluOutputIf)
        alu_unit = AluUnit()
        alu_unit.input_port.opcode <<= reg_input_port.alu_op
        alu_unit.input_port.op_a   <<= reg_input_port.op_a
        alu_unit.input_port.op_b   <<= reg_input_port.op_b
        alu_unit.input_port.pc     <<= reg_pc
        alu_unit.input_port.tpc    <<= reg_tpc
        alu_output <<= alu_unit.output_port

        # Shifter
        if self.has_shift:
            shifter_output = Wire(ShifterOutputIf)
            shifter_unit = ShifterUnit()
            shifter_unit.input_port.opcode <<= reg_input_port.shifter_op
            shifter_unit.input_port.op_a   <<= reg_input_port.op_a
            shifter_unit.input_port.op_b   <<= reg_input_port.op_b
            shifter_output <<= shifter_unit.output_port

        # Multiplier (this unit has internal pipelining)
        if self.has_multiply:
            mult_unit = MultUnit()
            mult_unit.input_port.valid  <<= input_buf_en
            mult_unit.input_port.op_a   <<= reg_input_port.op_a
            mult_unit.input_port.op_b   <<= reg_input_port.op_b
            self.mult_result <<= mult_unit.output_port

        # Physical and effective address calculation
        addr_calc_output = Wire(AddrCalcOutputIf)
        addr_calc_unit = AddrCalcUnit()
        addr_calc_unit.input_port.is_ldst        <<= (reg_input_port.exec_unit == op_class.ld_st) | (reg_input_port.exec_unit == op_class.branch_ind)
        addr_calc_unit.input_port.is_csr         <<= (reg_input_port.exec_unit == op_class.ld_st) & ((reg_input_port.ldst_op == ldst_ops.csr_load) | (reg_input_port.ldst_op == ldst_ops.csr_store))
        addr_calc_unit.input_port.op_b           <<= reg_input_port.op_b
        addr_calc_unit.input_port.op_c           <<= reg_input_port.op_c
        addr_calc_unit.input_port.mem_base       <<= self.mem_base # I don't think this needs registering: if this was changed by a previous instruction, we should pick it up immediately
        addr_calc_unit.input_port.mem_limit      <<= self.mem_limit # I don't think this needs registering: if this was changed by a previous instruction, we should pick it up immediately
        addr_calc_unit.input_port.task_mode      <<= reg_task_mode # I don't think this needs registering: if this was changed by a previous instruction, we would be branching
        addr_calc_unit.input_port.mem_access_len <<= reg_input_port.mem_access_len
        addr_calc_output <<= addr_calc_unit.output_port

        # Branch-target
        branch_target_output = Wire(BranchTargetUnitOutputIf)
        branch_target_unit = BranchTargetUnit()
        branch_target_unit.input_port.op_c       <<= reg_input_port.op_c
        branch_target_unit.input_port.pc         <<= reg_pc
        branch_target_unit.input_port.inst_len   <<= reg_input_port.inst_len
        branch_target_output <<= branch_target_unit.output_port

        # Bit-test result extractor
        bit_test_output = Wire(BitExtractOutputIf)
        bit_test_unit = BitExtract()
        bit_test_unit.input_port.op_a     <<= reg_input_port.op_a
        bit_test_unit.input_port.op_b     <<= reg_input_port.op_b
        bit_test_output <<= bit_test_unit.output_port

        is_branch_insn = (reg_input_port.exec_unit == op_class.branch) | (reg_input_port.exec_unit == op_class.branch_ind)
        is_exception = (is_branch_insn & (reg_input_port.branch_op == branch_ops.swi)) | addr_calc_output.mem_av | addr_calc_output.mem_unaligned | reg_input_port.fetch_av


        # Combining the unit outputs into a single interface
        ################ ALU/SHIFT/MULT
        self.output_port.result                <<= Select(reg_input_port.exec_unit == op_class.alu, shifter_output.result, alu_output.result)
        self.output_port.f_zero                <<= alu_output.f_zero
        self.output_port.f_sign                <<= alu_output.f_sign
        self.output_port.f_carry               <<= alu_output.f_carry
        self.output_port.f_overflow            <<= alu_output.f_overflow
        self.output_port.is_mult_op            <<= (reg_input_port.exec_unit == op_class.mult)
        ################ ADDR CALC
        self.output_port.phy_addr              <<= addr_calc_output.phy_addr
        self.output_port.eff_addr              <<= addr_calc_output.eff_addr
        self.output_port.mem_av                <<= addr_calc_output.mem_av
        self.output_port.mem_unaligned         <<= addr_calc_output.mem_unaligned
        self.output_port.is_csr                <<= addr_calc_output.is_csr
        ################ BRANCH TARGET
        self.output_port.branch_addr           <<= branch_target_output.branch_addr
        self.output_port.straight_addr         <<= branch_target_output.straight_addr
        ################ BRANCH INPUT
        self.output_port.branch_op             <<= reg_input_port.branch_op
        self.output_port.is_branch_ind         <<= (reg_input_port.exec_unit == op_class.branch_ind)
        self.output_port.op_a                  <<= reg_input_port.op_a
        self.output_port.bit_test_bit          <<= bit_test_output.bit
        self.output_port.spc                   <<= reg_spc
        self.output_port.tpc                   <<= reg_tpc
        self.output_port.task_mode             <<= reg_task_mode # TODO: Do we need to register THIS????
        self.output_port.fetch_av              <<= reg_input_port.fetch_av
        self.output_port.is_branch_insn        <<= is_branch_insn
        self.output_port.woi                   <<= reg_input_port.woi
        ################ MEMORY INPUT
        self.output_port.read_not_write        <<= ((reg_input_port.exec_unit == op_class.ld_st) & ((reg_input_port.ldst_op == ldst_ops.load) | (reg_input_port.ldst_op == ldst_ops.csr_load))) | (reg_input_port.exec_unit == op_class.branch_ind)
        self.output_port.access_len            <<= reg_input_port.mem_access_len
        self.output_port.is_mem_op             <<= (reg_input_port.exec_unit == op_class.ld_st) | (reg_input_port.exec_unit == op_class.branch_ind)
        ################ WRITE-BACK GENERATION
        self.output_port.result_reg_addr       <<= reg_input_port.result_reg_addr
        self.output_port.result_reg_addr_valid <<= reg_input_port.result_reg_addr_valid
        self.output_port.do_bse                <<= reg_input_port.do_bse
        self.output_port.do_wse                <<= reg_input_port.do_wse
        self.output_port.do_bze                <<= reg_input_port.do_bze
        self.output_port.do_wze                <<= reg_input_port.do_wze
        ################ HELP WITH INTERRUPTS AND EXCEPTIONS
        self.output_port.is_exception          <<= is_exception
        self.output_port.is_interrupt          <<= reg_interrupt

        # Side-band interface
        self.spc_out                           <<= Select(reg_task_mode, branch_target_output.straight_addr, reg_spc)
        #self.tpc_out                           <<= Select(is_exception | reg_interrupt, Select(reg_task_mode, reg_tpc, branch_target_output.straight_addr), reg_tpc)
        self.tpc_out                           <<= Select(reg_task_mode, reg_tpc, branch_target_output.straight_addr)

class ExecStage2(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    # Pipeline input
    input_port = Input(Exec12If)

    # Multiplier result
    mult_result = Input(BrewData)

    # Pipeline output
    output_port = Output(ResultExtendIf)

    # Interface to the bus interface
    bus_req_if = Output(BusIfRequestIf)
    bus_rsp_if = Input(BusIfResponseIf)

    # Interface to the CSR registers
    csr_if = Output(CsrIf)

    # side-band interfaces
    spc_out = Output(BrewInstAddr)
    spc_changed = Output(logic)
    tpc_out = Output(BrewInstAddr)
    tpc_changed = Output(logic)
    task_mode_out = Output(logic)
    task_mode_changed = Output(logic)
    ecause_out = Output(EnumNet(exceptions))
    ecause_changed = Output(logic)
    eaddr_out = Output(BrewAddr)
    eaddr_changed = Output(logic)
    do_branch_immediate = Output(logic) # This is the unregistered version, not the one that all other stages use
    do_branch = Output(logic) # This is the regular, registered version

    complete = Output(logic) # goes high for 1 cycle when an instruction completes. Used for verification

    def construct(self, has_multiply: bool = True, has_shift: bool = True):
        self.has_multiply = has_multiply
        self.has_shift = has_shift

    def body(self):
        # We have a few stages here:
        #    1. the second stage of multiply (it's actually instantiated in stage-1, but the results need to be dealt with here)
        #    2. branch: this one determines if a branch/exception/interrupt happened and if so, where to jump to
        #    3. memory: which is responsible for load/stores including CSR reads/writes
        # The interesting point is that the only thing that *can* provide back-pressure here is memory. So, unless
        # we do a memory operation, we can always accept the next instruction. This makes handshaking very simple indeed.

        # TODO: do we need to feed memory with registered or unregistered signals? I think the answer to that is no.
        #       In this world, we register in the input and if memory doesn't well, it should...

        stage_done_strobe = Wire()
        mem_output = Wire(MemOutputIf)

        input_ready = Wire(logic)
        input_reg_en = input_ready & self.input_port.valid
        mem_unit_ready = Wire()
        mem_output = Wire(MemOutputIf)

        reg_input_port = Wire(self.input_port.get_data_member_type())
        reg_input_port <<= Reg(self.input_port.get_data_members(), clock_en = input_reg_en)
        reg_input_port_data_valid = Wire(logic)
        clear_reg_input_valid = Wire(logic)
        clear_reg_input_valid <<= Select(
            reg_input_port.is_mem_op,
            # Not an indirect jump: clear every time
            1,
            # Indirect jump: clear when memory response comes back
            mem_output.valid
        )
        set_reg_input_valid = self.input_port.valid & self.input_port.ready
        reg_input_port_data_valid_next = Select(set_reg_input_valid, Select(clear_reg_input_valid, reg_input_port_data_valid, 0), 1)
        reg_input_port_data_valid <<= Reg(reg_input_port_data_valid_next)
        #reg_input_port_data_valid <<= Reg(Select(self.do_branch | self.do_branch_immediate, Select(input_ready & self.input_port.valid, reg_input_port_data_valid, 1), 0))
        reg_pc = Select(reg_input_port.task_mode, reg_input_port.spc, reg_input_port.tpc)

        # TODO: do we need to clear after a branch?
        input_ready <<= Select(reg_input_port.is_mem_op, 1, mem_unit_ready) | self.do_branch | ~reg_input_port_data_valid
        self.input_port.ready <<= input_ready

        # Branch unit
        branch_output = Wire(BranchUnitOutputIf)
        branch_unit = BranchUnit()
        branch_unit.input_port.opcode          <<= reg_input_port.branch_op
        branch_unit.input_port.spc             <<= reg_input_port.spc
        branch_unit.input_port.tpc             <<= reg_input_port.tpc
        branch_unit.input_port.task_mode       <<= reg_input_port.task_mode
        branch_unit.input_port.branch_addr     <<= Select(
            reg_input_port.is_branch_ind,
            reg_input_port.branch_addr,
            concat(mem_output.data_h, mem_output.data_l)[31:1]
        )
        branch_unit.input_port.is_interrupt    <<= reg_input_port.is_interrupt
        branch_unit.input_port.is_exception    <<= reg_input_port.is_exception
        branch_unit.input_port.fetch_av        <<= reg_input_port.fetch_av
        branch_unit.input_port.mem_av          <<= reg_input_port.mem_av
        branch_unit.input_port.mem_unaligned   <<= reg_input_port.mem_unaligned
        branch_unit.input_port.op_a            <<= reg_input_port.op_a
        branch_unit.input_port.bit_test_bit    <<= reg_input_port.bit_test_bit
        branch_unit.input_port.f_zero          <<= reg_input_port.f_zero
        branch_unit.input_port.f_sign          <<= reg_input_port.f_sign
        branch_unit.input_port.f_carry         <<= reg_input_port.f_carry
        branch_unit.input_port.f_overflow      <<= reg_input_port.f_overflow
        branch_unit.input_port.is_branch_insn  <<= reg_input_port.is_branch_insn
        branch_unit.input_port.woi             <<= reg_input_port.woi
        branch_output <<= branch_unit.output_port

        # Memory unit
        mem_input = Wire(MemInputIf)
        memory_unit = MemoryStage()
        mem_input.read_not_write <<= self.input_port.read_not_write
        mem_input.data <<= self.input_port.op_a
        mem_input.addr <<= self.input_port.phy_addr
        mem_input.is_csr <<= self.input_port.is_csr
        mem_input.access_len <<= self.input_port.access_len
        mem_input.valid <<= self.input_port.valid
        memory_unit.input_port <<= mem_input
        self.bus_req_if <<= memory_unit.bus_req_if
        memory_unit.bus_rsp_if <<= self.bus_rsp_if
        self.csr_if <<= memory_unit.csr_if
        mem_output <<= memory_unit.output_port
        mem_unit_ready <<= mem_input.ready

        # Write-back interface
        selector_choices = []
        if self.has_multiply:
            selector_choices += [reg_input_port.is_mult_op, self.mult_result]
        selector_choices += [reg_input_port.is_branch_insn, concat(reg_input_port.straight_addr, "1'b0")] # Patch through return address for calls
        result = SelectOne(*selector_choices, default_port = reg_input_port.result)
        is_ld_st = reg_input_port.is_mem_op & ~reg_input_port.is_branch_ind

        self.output_port.data_l <<= Select(is_ld_st, result[15: 0], mem_output.data_l)
        self.output_port.data_h <<= Select(is_ld_st, result[31:16], mem_output.data_h)
        self.output_port.data_en <<= reg_input_port.result_reg_addr_valid
        self.output_port.addr <<= reg_input_port.result_reg_addr
        self.output_port.do_bse <<= reg_input_port.do_bse
        self.output_port.do_wse <<= reg_input_port.do_wse
        self.output_port.do_bze <<= reg_input_port.do_bze
        self.output_port.do_wze <<= reg_input_port.do_wze
        self.output_port.valid <<= stage_done_strobe
        #self.output_port.valid <<= reg_input_port_data_valid & ~self.do_branch_immediate & ~self.do_branch # Not sure this is correct.

        # Create side-band interfaces
        #####################################

        # When we have a branch, we have to clear the exec unit from s2; otherwise it will potentially prevent 'stage_done_strobe' from firing when we resume from the target.
        # The test for this is:
        #   $pc <- mem[some_table] # jumps to xxx
        # xxx:
        #   $pc <- yyy
        # These back-to-back jumps would fail without the intervention

        # TODO: this I hope is not an issue anymore, but needs to be tested.
        stage_done_strobe <<= reg_input_port_data_valid & ~reg_input_port_data_valid_next

        self.do_branch_immediate <<= branch_output.do_branch & stage_done_strobe
        self.do_branch <<= Reg(self.do_branch_immediate)

        self.spc_out <<= branch_output.spc
        self.spc_changed <<= stage_done_strobe & branch_output.spc_changed
        self.tpc_out <<= branch_output.tpc
        self.tpc_changed <<= stage_done_strobe & branch_output.tpc_changed
        self.task_mode_out <<= branch_output.task_mode
        self.task_mode_changed <<= stage_done_strobe & branch_output.task_mode_changed
        self.ecause_out <<= branch_output.ecause
        self.ecause_changed <<= stage_done_strobe & branch_output.ecause_changed
        self.eaddr_out <<= SelectOne(
            #branch_output.ecause == exceptions.exc_reset,           0, <-- this never happens, it's just the default on POR
            #branch_output.ecause == exceptions.exc_hwi,             concat(reg_pc, "1'b0"),
            #branch_output.ecause == exceptions.exc_swi_0,           concat(reg_pc, "1'b0"),
            #branch_output.ecause == exceptions.exc_swi_1,           concat(reg_pc, "1'b0"),
            #branch_output.ecause == exceptions.exc_swi_2,           concat(reg_pc, "1'b0"),
            #branch_output.ecause == exceptions.exc_swi_3,           concat(reg_pc, "1'b0"),
            #branch_output.ecause == exceptions.exc_swi_4,           concat(reg_pc, "1'b0"),
            #branch_output.ecause == exceptions.exc_swi_5,           concat(reg_pc, "1'b0"),
            #branch_output.ecause == exceptions.exc_swi_6,           concat(reg_pc, "1'b0"),
            #branch_output.ecause == exceptions.exc_swi_7,           concat(reg_pc, "1'b0"),
            #branch_output.ecause == exceptions.exc_unknown_inst,    concat(reg_pc, "1'b0"),
            #branch_output.ecause == exceptions.exc_inst_av,         concat(reg_pc, "1'b0"),
            #branch_output.ecause == exceptions.exc_type,            ????, <-- this is complicated, but we don't have types yet, so it can never happen
            branch_output.ecause == exceptions.exc_unaligned,       reg_input_port.eff_addr,
            branch_output.ecause == exceptions.exc_mem_av,          reg_input_port.eff_addr,
            default_port = concat(reg_pc, "1'b0")
        )
        self.eaddr_changed <<= stage_done_strobe & branch_output.ecause_changed

        self.complete <<= stage_done_strobe

class ExecuteStage(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    # Pipeline input
    input_port = Input(DecodeExecIf)

    # Pipeline output
    output_port = Output(ResultExtendIf)

    # Interface to the bus interface
    bus_req_if = Output(BusIfRequestIf)
    bus_rsp_if = Input(BusIfResponseIf)

    # Interface to the CSR registers
    csr_if = Output(CsrIf)

    # side-band interfaces
    mem_base = Input(BrewMemBase)
    mem_limit = Input(BrewMemBase)
    spc_in  = Input(BrewInstAddr)
    spc_out = Output(BrewInstAddr)
    tpc_in  = Input(BrewInstAddr)
    tpc_out = Output(BrewInstAddr)
    task_mode_in  = Input(logic)
    task_mode_out = Output(logic)
    ecause_in = Input(EnumNet(exceptions))
    ecause_out = Output(EnumNet(exceptions))
    eaddr_out = Output(BrewAddr)
    do_branch = Output(logic)
    interrupt = Input(logic)

    complete = Output(logic) # goes high for 1 cycle when an instruction completes. Used for verification

    def construct(self, has_multiply: bool = True, has_shift: bool = True):
        self.has_multiply = has_multiply
        self.has_shift = has_shift

    def body(self):
        exec_12_if = Wire(Exec12If)
        mult_result = Wire(BrewData)
        do_branch = Wire()
        do_branch_immediate = Wire()

        stage1 = ExecStage1(has_multiply=self.has_multiply, has_shift=self.has_shift)
        stage1.input_port <<= self.input_port
        exec_12_if <<= stage1.output_port
        mult_result <<= stage1.mult_result
        stage1.mem_base            <<= self.mem_base
        stage1.mem_limit           <<= self.mem_limit
        stage1.spc_in              <<= self.spc_in
        stage1.tpc_in              <<= self.tpc_in
        stage1.task_mode_in        <<= self.task_mode_in
        stage1.interrupt           <<= self.interrupt
        stage1.do_branch_immediate <<= do_branch_immediate
        stage1.do_branch           <<= do_branch

        stage2 = ExecStage2(has_multiply=self.has_multiply, has_shift=self.has_shift)
        stage2.input_port          <<= exec_12_if
        self.output_port           <<= stage2.output_port
        stage2.mult_result         <<= mult_result
        self.bus_req_if            <<= stage2.bus_req_if
        stage2.bus_rsp_if          <<= self.bus_rsp_if
        self.csr_if                <<= stage2.csr_if
        do_branch_immediate        <<= stage2.do_branch_immediate
        do_branch                  <<= stage2.do_branch
        self.complete              <<= stage2.complete

        # Generate SPC/TPC and TASK_MOD outputs
        # Stage 1 never changes TASK_MODE and always assumes straight-line execution for SPC/TPC
        # Stage 2 corrects for all these assumptions and asserts the corresponding XXX_CHANGED flags as needed

        self.tpc_out <<= Select(stage2.tpc_changed, stage1.tpc_out, stage2.tpc_out)
        self.spc_out <<= Select(stage2.spc_changed, stage1.spc_out, stage2.spc_out)
        self.task_mode_out <<= Select(stage2.task_mode_changed, exec_12_if.task_mode, stage2.task_mode_out)
        self.ecause_out <<= Select(stage2.ecause_changed, self.ecause_in, stage2.ecause_out)
        # TODO: this is silly: we have all of these are in/outs with external registers, except for this one, which is internal. Make up your mind!!!
        self.eaddr_out <<= Reg(
            Select(stage2.eaddr_changed, self.eaddr_out, stage2.eaddr_out)
        )

        self.do_branch             <<= do_branch


def gen():
    def top():
        #return ScanWrapper(ExecuteStage, {"clk", "rst"}, has_multiply=True, has_shift=True)
        return ExecuteStage(has_multiply=True, has_shift=True)

    #back_end = SystemVerilog()
    #back_end.yosys_fix = True
    netlist = Build.generate_rtl(top, "execute.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(
        target_dir="q_execute",
        top_level=top_level_name,
        source_files=("execute.sv",),
        clocks=(("clk", 10), ),#("top_clk", 100)),
        project_name="execute",
        family="MAX 10",
        device="10M50DAF672C7G" # Something large with a ton of pins
    )
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()

