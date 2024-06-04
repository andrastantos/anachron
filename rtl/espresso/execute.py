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
    +-----------+
    | Multilper |
    +-----------+


PC management:
--------------

$pc is stage1 relative. That is to say, TPC and SPC (the registers) contain the
current instruction address when read by exec1 units.

Exec1 outputs updated TPC and SPC with straight-line execution assumed.

Exec2 consideres interrupt, exceptions and branches. It then, if needs to,
outputs a change to TPC/SPC and TASK_MODE with a corresponding 'changed' signal.

The exec1 and exec2 outputs are combined into a single output inside execute,
the outer module.

Let's consider the following isntruction sequence:

    $r0 <- $r0 + $r1
    $pc <- SOME_ROUTINE
    $r1 <- $r1 & $r1
    $r2 <- $r2 | $r2

Here, when the addition is in exec2, the branch is in exec1. In this cycle
exec2 sees no reason to update TPC, so it doesn't set TPC_CHANGED. As a result,
execute writes back the value supplied by exec1 into TPC.

In the subsequent cycle, the branch enters exec2, and the target address is
finally recognized. TPC_CHANGED is asserted, so TPC is updated to the branch
target. In this same cycle the AND instruction is in exec1.

In cycle 3, do_branch gets asserted, which blocks any TPC/SPC update (i.e. they
will not change from the branch-target address that was captured in cycle 2).
In the same time, the AND instruction when was captured in exec2 and the OR
instruction in exec1; both of which are cancelled. Cancelling in this case means
that side-effects won't take affect, including the start of memory transactions
or register write-backs.

This all means that in case of a branch execution (for instance) TPC gets first
updated to the first branch-shadow instruction address, then corrected for the
correct target. Same for exceptions and interrupts: first TPC gets to skip
forward, then adjusted back when at the same time, TASK_MODE changes.

TEST_BENCH PROBLEMS:
--------------------
The current TB doesn't quite know how to deal with this in-the-middle-of-execute
reference point for TPC/SPC and it gets really confused by the potential double-
update during branches as well. This needs to be corrected, but how?


No other stage should care about the reference point for TPC/SPC. The only other
stage that is even aware of these values is FETCH and that has it's own counter:
it just needs the values for a branch, i.e. when do_branch goes active.

Problem with multiply:
----------------------
Stage1 accepts a new operation while stage 2 is busy handling a read for
instance. If, during that time, a multiply comes by, it'll be accepted. But
multiply is multi-stage and will continue advancing on *that* pipeline; worse,
multiply doesn't have back-pressure so it'll just assume that stage2 is ready to
catch the result as it pops out.

For now, I simplified multiply (at east in the OPTIMIZED mode) to be
single-stage. We'll see if this causes timing-closure problems. If it does,
the stage will get broken into two different modules and incorporated into
'exec1' and 'exec2' as any other module.

Further optimizations:
----------------------
I think there's a lot of stuff that gets unnecessarily registered between
'exec1' and 'exec2'. This should be reviewed and see if the computation
can be front-loaded to 'exec1' or if values can be collapsed into muxed
registers if the use is mutually exclusive.

"""

class Exec12If(ReadyValid):
    ################ ALU/SHIFT/MULT
    result                  = BrewData
    f_zero                  = logic
    f_sign                  = logic
    f_carry                 = logic
    f_overflow              = logic
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
    tpc                     = BrewInstAddr
    spc                     = BrewInstAddr
    task_mode               = logic

class ExecStage1(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    # Pipeline input
    input_port = Input(DecodeExecIf)

    # Pipeline output
    output_port = Output(Exec12If)

    # side-band interfaces
    mem_base = Input(BrewMemBase)
    mem_limit = Input(BrewMemBase)
    spc_in  = Input(BrewInstAddr)
    spc_out = Output(BrewInstAddr) # Output only straight-line updates. Branches come from stage 2
    spc_changed = Output(logic)
    tpc_in  = Input(BrewInstAddr)
    tpc_out = Output(BrewInstAddr) # Output only straight-line updates. Branches come from stage 2
    tpc_changed = Output(logic)
    task_mode_in  = Input(logic)
    interrupt = Input(logic)

    do_branch_immediate = Input(logic) # This is the unregistered version, not the one that all other stages use
    do_branch = Input(logic) # This is the regular, registered version

    output_strobe = Output(logic)

    def construct(self, has_multiply: bool = True, has_shift: bool = True):
        self.has_multiply = has_multiply
        self.has_shift = has_shift

    def body(self):
        # We have two stages in one, really here

        input_buf = ForwardBuf()
        input_buf_en = input_buf.out_reg_en

        reg_input_port = Wire(DecodeExecIf)
        reg_input_port <<= input_buf(self.input_port)

        pc = Select(self.task_mode_in, self.spc_in, self.tpc_in)

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
        alu_unit.input_port.pc     <<= pc
        alu_unit.input_port.tpc    <<= self.tpc_in
        alu_output <<= alu_unit.output_port

        result_selectors = []
        # Shifter
        if self.has_shift:
            shifter_output = Wire(ShifterOutputIf)
            shifter_unit = ShifterUnit()
            shifter_unit.input_port.opcode <<= reg_input_port.shifter_op
            shifter_unit.input_port.op_a   <<= reg_input_port.op_a
            shifter_unit.input_port.op_b   <<= reg_input_port.op_b
            shifter_output <<= shifter_unit.output_port
            result_selectors += [reg_input_port.exec_unit == op_class.shift,   shifter_output.result]

        # Multiplier (this unit has internal pipelining)
        if self.has_multiply:
            mult_unit = MultUnit()
            mult_unit.input_port.valid  <<= input_buf_en
            mult_unit.input_port.op_a   <<= reg_input_port.op_a
            mult_unit.input_port.op_b   <<= reg_input_port.op_b
            mult_result = mult_unit.output_port
            result_selectors += [reg_input_port.exec_unit == op_class.mult,   mult_result]

        # Physical and effective address calculation
        addr_calc_output = Wire(AddrCalcOutputIf)
        addr_calc_unit = AddrCalcUnit()
        addr_calc_unit.input_port.is_ldst        <<= (reg_input_port.exec_unit == op_class.ld_st) | (reg_input_port.exec_unit == op_class.branch_ind)
        addr_calc_unit.input_port.is_csr         <<= (reg_input_port.exec_unit == op_class.ld_st) & ((reg_input_port.ldst_op == ldst_ops.csr_load) | (reg_input_port.ldst_op == ldst_ops.csr_store))
        addr_calc_unit.input_port.op_b           <<= reg_input_port.op_b
        addr_calc_unit.input_port.op_c           <<= reg_input_port.op_c
        addr_calc_unit.input_port.mem_base       <<= self.mem_base # I don't think this needs registering: if this was changed by a previous instruction, we should pick it up immediately
        addr_calc_unit.input_port.mem_limit      <<= self.mem_limit # I don't think this needs registering: if this was changed by a previous instruction, we should pick it up immediately
        addr_calc_unit.input_port.task_mode      <<= self.task_mode_in
        addr_calc_unit.input_port.mem_access_len <<= reg_input_port.mem_access_len
        addr_calc_output <<= addr_calc_unit.output_port

        # Branch-target
        branch_target_output = Wire(BranchTargetUnitOutputIf)
        branch_target_unit = BranchTargetUnit()
        branch_target_unit.input_port.op_c       <<= reg_input_port.op_c
        branch_target_unit.input_port.pc         <<= pc
        #branch_target_unit.input_port.inst_len   <<= reg_input_port.inst_len
        branch_target_output <<= branch_target_unit.output_port

        # Bit-test result extractor
        bit_test_output = Wire(BitExtractOutputIf)
        bit_test_unit = BitExtract()
        bit_test_unit.input_port.op_a     <<= reg_input_port.op_a
        bit_test_unit.input_port.op_b     <<= reg_input_port.op_b
        bit_test_output <<= bit_test_unit.output_port

        is_branch_insn = (reg_input_port.exec_unit == op_class.branch) | (reg_input_port.exec_unit == op_class.branch_ind)
        is_exception = (is_branch_insn & (reg_input_port.branch_op == branch_ops.swi)) | addr_calc_output.mem_av | addr_calc_output.mem_unaligned | reg_input_port.fetch_av

        self.output_strobe <<= self.output_port.ready & self.output_port.valid
        # Side-band interface
        # If we could figure out here in this stage if there was going to be an exception,
        # we wouldn't need to pass along both TPC and SPC. We could make sure not to update
        # TPC.
        straight_addr = (pc + reg_input_port.inst_len + 1)[30:0]
        self.spc_out                           <<= straight_addr
        self.spc_changed                       <<= ~self.task_mode_in & self.output_strobe
        self.tpc_out                           <<= straight_addr
        self.tpc_changed                       <<=  self.task_mode_in & self.output_strobe
        reg_straight_addr = Reg(straight_addr, clock_en=self.input_port.ready & self.input_port.valid)

        # Combining the unit outputs into a single interface
        ################ ALU/SHIFT/MULT
        self.output_port.result                <<= SelectOne(*result_selectors, default_port = alu_output.result)
        self.output_port.f_zero                <<= alu_output.f_zero
        self.output_port.f_sign                <<= alu_output.f_sign
        self.output_port.f_carry               <<= alu_output.f_carry
        self.output_port.f_overflow            <<= alu_output.f_overflow
        ################ ADDR CALC
        self.output_port.phy_addr              <<= addr_calc_output.phy_addr
        self.output_port.eff_addr              <<= addr_calc_output.eff_addr
        self.output_port.mem_av                <<= addr_calc_output.mem_av
        self.output_port.mem_unaligned         <<= addr_calc_output.mem_unaligned
        self.output_port.is_csr                <<= addr_calc_output.is_csr
        ################ BRANCH TARGET
        self.output_port.branch_addr           <<= branch_target_output.branch_addr
        self.output_port.straight_addr         <<= reg_straight_addr
        ################ BRANCH INPUT
        self.output_port.branch_op             <<= reg_input_port.branch_op
        self.output_port.is_branch_ind         <<= (reg_input_port.exec_unit == op_class.branch_ind)
        self.output_port.op_a                  <<= reg_input_port.op_a
        self.output_port.bit_test_bit          <<= bit_test_output.bit
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
        self.output_port.is_interrupt          <<= self.interrupt
        self.output_port.spc                   <<= self.spc_in
        self.output_port.tpc                   <<= self.tpc_in
        self.output_port.task_mode             <<= self.task_mode_in


class ExecStage2(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    # Pipeline input
    input_port = Input(Exec12If)

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

    interrupt = Input(logic)
    ecause_out = Output(EnumNet(exceptions))
    ecause_changed = Output(logic)
    eaddr_out = Output(BrewAddr)
    eaddr_changed = Output(logic)
    do_branch_immediate = Output(logic) # This is the unregistered version, not the one that all other stages use
    do_branch = Output(logic) # This is the regular, registered version

    output_strobe = Output(logic) # goes high for 1 cycle when an instruction completes the stage

    def construct(self, has_multiply: bool = True, has_shift: bool = True):
        self.has_multiply = has_multiply
        self.has_shift = has_shift

    def body(self):
        # We can accept a transaction if:
        #    1. Mem unit is ready
        #    2. Write-back is ready (which is always)

        # We have a few stages here:
        #    1. the second stage of multiply (it's actually instantiated in stage-1, but the results need to be dealt with here)
        #    2. branch: this one determines if a branch/exception/interrupt happened and if so, where to jump to
        #    3. memory: which is responsible for load/stores including CSR reads/writes
        # The interesting point is that the only thing that *can* provide back-pressure here is memory. So, unless
        # we do a memory operation, we can always accept the next instruction. This makes handshaking very simple indeed.

        # TODO: do we need to feed memory with registered or unregistered signals? I think the answer to that is no.
        #       In this world, we register in the input and if memory doesn't well, it should...

        mem_output = Wire(MemOutputIf)

        mem_unit_ready = Wire()
        mem_output = Wire(MemOutputIf)

        state_fsm = ForwardBufLogic()

        reg_input_port = Wire(self.input_port.get_data_member_type())
        reg_input_port <<= Reg(self.input_port.get_data_members(), clock_en = state_fsm.out_reg_en)

        # We shouldn't depend on memory being able to accept a new request on the same cycle it provides a response. It may - should, really - be the case
        # but it is probably not always going to be the case due to arbitration further down the pike. We *are* dependent on memory having no more than a
        # single stage latency, that is, if it accepted a request, it will not accept a new one until the result is provided.
        #
        # This means that we have to split our logic here:
        # - From the sate-FSMs perspective, we are consuming the data when mem produces the output. That is, when the data is generated.
        # - After that however, we should clear a flag to indicate that the memory op held in reg_input_port is not valid anymore, unless of course we do consume a new
        #   memory operation in the same cycle
        mem_op_valid = SRReg(state_fsm.out_reg_en, mem_output.valid)

        state_fsm.output_ready <<= Select(reg_input_port.is_mem_op, 1, mem_output.valid) | self.do_branch # TODO: this is very weird to hook up 'valid' to 'ready'
        self.input_port.ready <<= mem_unit_ready # We don't have to combine in do_branch: if there was a branch, we either didn't have a mem-op, or we have waited for it already
        state_fsm.input_valid <<= self.input_port.valid & self.input_port.ready # THIS IS A GIANT HACK

        #reg_input_port_data_valid <<= Reg(Select(self.do_branch | self.do_branch_immediate, Select(input_ready & self.input_port.valid, reg_input_port_data_valid, 1), 0))

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
        mem_input.request_valid <<= ~self.do_branch_immediate
        mem_input.valid <<= self.input_port.valid & self.input_port.is_mem_op
        memory_unit.input_port <<= mem_input
        self.bus_req_if <<= memory_unit.bus_req_if
        memory_unit.bus_rsp_if <<= self.bus_rsp_if
        self.csr_if <<= memory_unit.csr_if
        mem_output <<= memory_unit.output_port
        mem_unit_ready <<= mem_input.ready

        # Write-back interface
        selector_choices = []
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
        self.output_port.valid <<= self.output_strobe & ~self.do_branch
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
        self.output_strobe <<= Select(reg_input_port.is_mem_op & mem_op_valid, state_fsm.output_valid, memory_unit.output_port.valid)

        self.do_branch_immediate <<= branch_output.do_branch & self.output_strobe & ~self.do_branch
        self.do_branch <<= Reg(self.do_branch_immediate)

        self.spc_out <<= branch_output.spc
        self.spc_changed <<= self.output_strobe & branch_output.spc_changed & ~self.do_branch
        self.tpc_out <<= branch_output.tpc
        self.tpc_changed <<= self.output_strobe & branch_output.tpc_changed & ~self.do_branch
        self.task_mode_out <<= branch_output.task_mode
        self.task_mode_changed <<= self.output_strobe & branch_output.task_mode_changed & ~self.do_branch
        self.ecause_out <<= branch_output.ecause
        self.ecause_changed <<= self.output_strobe & branch_output.ecause_changed & ~self.do_branch
        self.eaddr_out <<= Reg(
            SelectOne(
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
                default_port = concat(Select(reg_input_port.task_mode, reg_input_port.spc, reg_input_port.tpc), "1'b0")
            ),
            clock_en = reg_input_port.is_exception & self.output_strobe
        )

        self.eaddr_changed <<= self.output_strobe & branch_output.ecause_changed


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
    spc_out = Output(BrewInstAddr)
    tpc_out = Output(BrewInstAddr)
    ecause_out = Output(EnumNet(exceptions))
    ecause_clear_pulse = Input(logic)
    eaddr_out = Output(BrewAddr)
    task_mode_in  = Input(logic)
    task_mode_out = Output(logic)
    do_branch = Output(logic)
    do_branch_immediate = Output(logic)
    interrupt = Input(logic)

    stage2_complete = Output(logic) # goes high for 1 cycle when an instruction completes. Used for verification
    stage1_complete = Output(logic) # goes high for 1 cycle when an instruction transfers from stage1 to stage2. Used for verification

    def construct(self, has_multiply: bool = True, has_shift: bool = True):
        self.has_multiply = has_multiply
        self.has_shift = has_shift

    def body(self):
        exec_12_if = Wire(Exec12If)
        do_branch = Wire()

        stage1 = ExecStage1(has_multiply=self.has_multiply, has_shift=self.has_shift)
        stage1.input_port <<= self.input_port
        exec_12_if <<= stage1.output_port
        stage1.mem_base            <<= self.mem_base
        stage1.mem_limit           <<= self.mem_limit
        stage1.spc_in              <<= self.spc_out
        stage1.tpc_in              <<= self.tpc_out
        stage1.task_mode_in        <<= self.task_mode_in
        stage1.interrupt           <<= self.interrupt
        stage1.do_branch_immediate <<= self.do_branch_immediate
        stage1.do_branch           <<= do_branch

        stage2 = ExecStage2(has_multiply=self.has_multiply, has_shift=self.has_shift)
        stage2.input_port          <<= exec_12_if
        self.output_port           <<= stage2.output_port
        self.bus_req_if            <<= stage2.bus_req_if
        stage2.bus_rsp_if          <<= self.bus_rsp_if
        self.csr_if                <<= stage2.csr_if
        self.do_branch_immediate   <<= stage2.do_branch_immediate
        do_branch                  <<= stage2.do_branch

        self.stage1_complete       <<= exec_12_if.ready & exec_12_if.valid
        self.stage2_complete       <<= stage2.output_strobe

        # Generate SPC/TPC and TASK_MOD outputs
        # Stage 1 never changes TASK_MODE and always assumes straight-line execution for SPC/TPC
        # Stage 2 corrects for all these assumptions and asserts the corresponding XXX_CHANGED flags as needed

        tpc_changed = stage1.tpc_changed | stage2.tpc_changed
        spc_changed = stage1.spc_changed | stage2.spc_changed
        self.tpc_out <<= Reg(Select(stage2.tpc_changed, stage1.tpc_out, stage2.tpc_out), clock_en = tpc_changed)
        self.spc_out <<= Reg(Select(stage2.spc_changed, stage1.spc_out, stage2.spc_out), clock_en = spc_changed)
        self.eaddr_out <<= Reg(stage2.eaddr_out, clock_en = stage2.eaddr_changed)
        # TODO: this is silly: we have all of these are in/outs with external registers, except for this one, which is internal. Make up your mind!!!
        self.task_mode_out <<= Select(stage2.task_mode_changed, self.task_mode_in, stage2.task_mode_out)
        self.ecause_out <<= Reg(Select(stage2.ecause_changed, exceptions.exc_reset, stage2.ecause_out), clock_en = stage2.ecause_changed | self.ecause_clear_pulse)
        self.do_branch             <<= do_branch


def gen():
    def top():
        #return ScanWrapper(ExecuteStage, {"clk", "rst"}, has_multiply=True, has_shift=True)
        return ExecuteStage(has_multiply=True, has_shift=True)

    #back_end = SystemVerilog()
    #back_end.yosys_fix = True
    netlist = Build.generate_rtl(top, "synth/execute.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(
        target_dir="synth/q_execute",
        top_level=top_level_name,
        source_files=("synth/execute.sv",),
        clocks=(("clk", 10), ),#("top_clk", 100)),
        project_name="execute",
        family="MAX 10",
        device="10M50DAF672C7G" # Something large with a ton of pins
    )
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()

