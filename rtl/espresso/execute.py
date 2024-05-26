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

    +-----------+ +-----------+
    |    ALU    | |   Branch  |
    +-----------+ |           |
    +-----------+ |           |
    | Br. Trgt. | |           |
    +-----------+ +-----------+
    +-----------+ +-----------+
    |    LDST   | |   Memory  |
    +-----------+ +-----------+
    +-------------------------+
    |         Shifter         |
    +-------------------------+
    +-------------------------+
    |        Multilper        |
    +-------------------------+

PC is cycle-1 relative. If there was a branch, that will be determined in cycle-2,
though the branch target address is calculated in cycle-1. This means that cycle-1
executes the instruction in a branch-shadow, if there were no bubbles in the pipeline.
There is logic in cycle-2 to remember a branch from the previous cycle and cancel
any instruction that leaks through from cycle-1.
"""

#TIMING_CLOSURE_REG = Reg
TIMING_CLOSURE_REG = lambda x:x



class BranchUnitInputIf(Interface):
    opcode          = EnumNet(branch_ops)
    op_a            = BrewData
    op_b            = BrewData
    #pc              = BrewInstAddr
    spc             = BrewInstAddr
    tpc             = BrewInstAddr
    #op_c            = BrewData
    task_mode       = logic
    branch_addr     = BrewInstAddr
    interrupt       = logic
    fetch_av        = logic # Coming all the way from fetch: if the instruction gotten this far, we should raise the exception
    mem_av          = logic # Coming from the load-store unit if that figures out an exception
    mem_unaligned   = logic # Coming from the load-store unit if an unaligned access was attempted
    f_zero          = logic
    f_sign          = logic
    f_carry         = logic
    f_overflow      = logic
    is_branch_insn  = logic
    woi             = logic

class BranchUnitOutputIf(Interface):
    spc                       = BrewInstAddr
    spc_changed               = logic
    tpc                       = BrewInstAddr
    tpc_changed               = logic
    task_mode                 = logic
    task_mode_changed         = logic
    ecause                    = EnumNet(exceptions)
    is_exception              = logic
    is_exception_or_interrupt = logic
    do_branch                 = logic

class BranchUnit(Module):

    input_port = Input(BranchUnitInputIf)
    output_port = Output(BranchUnitOutputIf)

    def body(self):
        @module(1)
        def bb_get_bit(word, bit_code):
            return SelectOne(
                bit_code == 0,  word[0],
                bit_code == 1,  word[1],
                bit_code == 2,  word[2],
                bit_code == 3,  word[3],
                bit_code == 4,  word[4],
                bit_code == 5,  word[5],
                bit_code == 6,  word[6],
                bit_code == 7,  word[7],
                bit_code == 8,  word[8],
                bit_code == 9,  word[9],
                bit_code == 10, word[14],
                bit_code == 11, word[15],
                bit_code == 12, word[16],
                bit_code == 13, word[30],
                bit_code == 14, word[31],
            )

        # Branch codes:
        #  eq: f_zero = 1
        #  ne: f_zero = 0
        #  lt: f_carry = 1
        #  ge: f_carry = 0
        #  lts: f_sign != f_overflow
        #  ges: f_sign == f_overflow
        condition_result = self.input_port.is_branch_insn & SelectOne(
            self.input_port.opcode == branch_ops.cb_eq,   self.input_port.f_zero,
            self.input_port.opcode == branch_ops.cb_ne,   ~self.input_port.f_zero,
            self.input_port.opcode == branch_ops.cb_lts,  self.input_port.f_sign != self.input_port.f_overflow,
            self.input_port.opcode == branch_ops.cb_ges,  self.input_port.f_sign == self.input_port.f_overflow,
            self.input_port.opcode == branch_ops.cb_lt,   self.input_port.f_carry,
            self.input_port.opcode == branch_ops.cb_ge,   ~self.input_port.f_carry,
            self.input_port.opcode == branch_ops.bb_one,  bb_get_bit(self.input_port.op_a, self.input_port.op_b),
            self.input_port.opcode == branch_ops.bb_zero, ~bb_get_bit(self.input_port.op_a, self.input_port.op_b),
        )

        # Set if we have an exception: in task mode this results in a switch to scheduler mode, in scheduler mode, it's a reset
        is_exception = (self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.swi)) | self.input_port.mem_av | self.input_port.mem_unaligned | self.input_port.fetch_av

        # Set whenever we branch without a mode change
        in_mode_branch = SelectOne(
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.pc_w),        1,
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.pc_w_ind),    1,
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.tpc_w),       self.input_port.task_mode,
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.tpc_w_ind),   self.input_port.task_mode,
            is_exception,                                                                        ~self.input_port.task_mode,
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.stm),         0,
            default_port =                                                                       condition_result,
        )

        branch_target = SelectOne(
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.pc_w),                                 self.input_port.op_a[31:1],
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.tpc_w),                                self.input_port.op_a[31:1],
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.pc_w_ind),                             self.input_port.branch_addr,
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.tpc_w_ind),                            self.input_port.branch_addr,
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.stm),                                  self.input_port.tpc,
            default_port =                                                                                                Select(is_exception | self.input_port.interrupt, self.input_port.branch_addr, self.input_port.tpc),
        )
        spc_branch_target = Select(
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.pc_w),
            self.input_port.branch_addr,
            self.input_port.op_a[31:1],
        )

        self.output_port.spc            <<= Select(is_exception, spc_branch_target, 0)
        self.output_port.spc_changed    <<= ~self.input_port.task_mode & (is_exception | (in_mode_branch & (~self.input_port.woi | ~self.input_port.interrupt)))
        self.output_port.tpc            <<= branch_target
        self.output_port.tpc_changed    <<= Select(
            self.input_port.task_mode,
            # In Scheduler mode: TPC can only change through TCP manipulation instructions. For those, the value comes through op_c
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.tpc_w),
            # In task mode, all branches count, but so do exceptions which, while don't change TPC, they don't update TPC either.
            in_mode_branch | is_exception | self.input_port.interrupt
        )
        self.output_port.task_mode_changed <<= Select(
            self.input_port.task_mode,
            # In scheduler mode: exit to ask mode, if STM instruction is executed
            (self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.stm)),
            # In task mode: we enter scheduler mode in case of an exception or interrupt
            is_exception | self.input_port.interrupt
        )
        self.output_port.task_mode  <<= self.input_port.task_mode ^ self.output_port.task_mode_changed

        self.output_port.do_branch  <<= in_mode_branch | self.output_port.task_mode_changed

        swi_exception = self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.swi)

        # We set the ECAUSE bits even in scheduler mode: this allows for interrupt polling and,
        # after a reset, we can check it to determine the reason for the reset
        # NOTE: we *have* to do the type-cast outside the switch: the terms are always evaluated
        #       in simulation, and thus, if op_a is an invalid exception, the simulator would
        #       blow up trying to do the type-conversion, even if swi_exception isn't set.
        self.output_port.ecause <<= EnumNet(exceptions)(SelectFirst(
            self.input_port.interrupt,      exceptions.exc_hwi,
            self.input_port.fetch_av,       exceptions.exc_inst_av,
            self.input_port.mem_unaligned,  exceptions.exc_unaligned,
            self.input_port.mem_av,         exceptions.exc_mem_av,
            swi_exception,                  self.input_port.op_a[6:0],
        ))
        self.output_port.is_exception <<= is_exception
        self.output_port.is_exception_or_interrupt  <<= is_exception | (self.input_port.task_mode & self.input_port.interrupt)





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
        # We have two stages in one, really here
        pc = Select(self.task_mode_in, self.spc_in, self.tpc_in)

        # this signal is high for one cycle *after* a branch. It's used in stage 2 to cancel any instruction that leaked through stage 1
        s1_was_branch = Reg(self.do_branch)
        s2_was_branch = Reg(s1_was_branch)

        # Stege 1
        ########################################
        # Ready-valid FSM
        stage_1_valid = Wire(logic)
        stage_2_ready = Wire(logic)

        multi_cycle_exec_lockout = Reg(self.input_port.ready & self.input_port.valid & (self.input_port.exec_unit == op_class.mult) & ~self.input_port.fetch_av)

        stage_1_fsm = ForwardBufLogic()
        stage_1_fsm.clear <<= self.do_branch
        stage_1_fsm.input_valid <<= ~multi_cycle_exec_lockout & ~s1_was_branch & ~self.do_branch & self.input_port.valid
        # we 'bite out' a cycle for two-cycle units, such as multiply
        self.input_port.ready <<= ~multi_cycle_exec_lockout & ~s1_was_branch  & stage_1_fsm.input_ready
        stage_1_valid <<= stage_1_fsm.output_valid
        stage_1_fsm.output_ready <<= stage_2_ready

        stage_1_reg_en = Wire(logic)
        stage_1_reg_en <<= ~multi_cycle_exec_lockout & ~s1_was_branch  & stage_1_fsm.out_reg_en

        # ALU
        alu_output = Wire(AluOutputIf)
        alu_unit = AluUnit()
        alu_unit.input_port.opcode <<= self.input_port.alu_op
        alu_unit.input_port.op_a   <<= self.input_port.op_a
        alu_unit.input_port.op_b   <<= self.input_port.op_b
        alu_unit.input_port.pc     <<= pc
        alu_unit.input_port.tpc    <<= self.tpc_in
        alu_output <<= alu_unit.output_port
        s1_alu_output = Wire(AluOutputIf)
        s1_alu_output <<= Reg(alu_output, clock_en = stage_1_reg_en)


        # Load-store
        ldst_output = Wire(AddrCalcOutputIf)
        ldst_unit = AddrCalcUnit()
        ldst_unit.input_port.is_ldst        <<= (self.input_port.exec_unit == op_class.ld_st) | (self.input_port.exec_unit == op_class.branch_ind)
        ldst_unit.input_port.is_csr         <<= (self.input_port.ldst_op == ldst_ops.csr_load) | (self.input_port.ldst_op == ldst_ops.csr_store)
        ldst_unit.input_port.op_b           <<= self.input_port.op_b
        ldst_unit.input_port.op_c           <<= self.input_port.op_c
        ldst_unit.input_port.mem_base       <<= self.mem_base
        ldst_unit.input_port.mem_limit      <<= self.mem_limit
        ldst_unit.input_port.task_mode      <<= self.task_mode_in
        ldst_unit.input_port.mem_access_len <<= self.input_port.mem_access_len
        ldst_output <<= ldst_unit.output_port
        s1_ldst_output = Wire(AddrCalcOutputIf)
        s1_ldst_output <<= Reg(ldst_output, clock_en = stage_1_reg_en)


        # Branch-target
        branch_target_output = Wire(BranchTargetUnitOutputIf)
        branch_target_unit = BranchTargetUnit()
        branch_target_unit.input_port.op_c       <<= self.input_port.op_c
        branch_target_unit.input_port.pc         <<= pc
        branch_target_unit.input_port.inst_len   <<= self.input_port.inst_len
        branch_target_output <<= branch_target_unit.output_port
        s1_branch_target_output = Wire(BranchTargetUnitOutputIf)
        s1_branch_target_output <<= Reg(branch_target_output, clock_en = stage_1_reg_en)

        # Shifter
        if self.has_shift:
            shifter_output = Wire(ShifterOutputIf)
            shifter_unit = ShifterUnit()
            shifter_unit.input_port.opcode <<= self.input_port.shifter_op
            shifter_unit.input_port.op_a   <<= self.input_port.op_a
            shifter_unit.input_port.op_b   <<= self.input_port.op_b
            shifter_output <<= shifter_unit.output_port
            s1_shifter_output = Wire(ShifterOutputIf)
            s1_shifter_output <<= Reg(shifter_output, clock_en = stage_1_reg_en)

        # Multiplier (this unit has internal pipelining)
        if self.has_multiply:
            mult_output = Wire(MultOutputIf)
            mult_unit = MultUnit()
            mult_unit.input_port.valid  <<= stage_1_reg_en
            mult_unit.input_port.op_a   <<= self.input_port.op_a
            mult_unit.input_port.op_b   <<= self.input_port.op_b
            mult_output <<= mult_unit.output_port

        # Delay inputs that we will need later
        s1_exec_unit = Reg(self.input_port.exec_unit, clock_en = stage_1_reg_en)
        s1_branch_op = Reg(self.input_port.branch_op, clock_en = stage_1_reg_en)
        s1_ldst_op = Reg(self.input_port.ldst_op, clock_en = stage_1_reg_en)
        s1_op_a = Reg(self.input_port.op_a, clock_en = stage_1_reg_en)
        s1_op_b = Reg(self.input_port.op_b, clock_en = stage_1_reg_en)
        s1_op_c = Reg(self.input_port.op_c, clock_en = stage_1_reg_en)
        s1_do_bse = Reg(self.input_port.do_bse, clock_en = stage_1_reg_en)
        s1_do_wse = Reg(self.input_port.do_wse, clock_en = stage_1_reg_en)
        s1_do_bze = Reg(self.input_port.do_bze, clock_en = stage_1_reg_en)
        s1_do_wze = Reg(self.input_port.do_wze, clock_en = stage_1_reg_en)
        s1_woi = Reg(self.input_port.woi, clock_en = stage_1_reg_en)
        s1_result_reg_addr = Reg(self.input_port.result_reg_addr, clock_en = stage_1_reg_en)
        s1_result_reg_addr_valid = Reg(self.input_port.result_reg_addr_valid, clock_en = stage_1_reg_en)
        s1_fetch_av = Reg(self.input_port.fetch_av, clock_en = stage_1_reg_en)
        s1_tpc = Reg(self.tpc_in, clock_en = stage_1_reg_en)
        s1_spc = Reg(self.spc_in, clock_en = stage_1_reg_en)
        s1_task_mode = Reg(self.task_mode_in, clock_en = stage_1_reg_en)
        s1_mem_access_len = Reg(self.input_port.mem_access_len, clock_en = stage_1_reg_en)
        s1_eff_addr = Reg(ldst_unit.output_port.eff_addr, clock_en = stage_1_reg_en)
        s1_pc = Select(s1_task_mode, s1_spc, s1_tpc)

        # Stage 2
        ########################################
        # Ready-valid FSM
        branch_input = Wire(BranchUnitInputIf)
        branch_output = Wire(BranchUnitOutputIf)

        mem_input = Wire(MemInputIf)
        s2_mem_output = Wire(MemOutputIf)

        s2_pc = Select(s1_task_mode, s1_spc, s1_tpc)

        stage_2_valid = Wire(logic)
        s2_exec_unit = Wire(EnumNet(op_class))
        s2_ldst_op = Wire()
        s2_result_reg_addr_valid = Wire()

        # NOTE: The use of s1_exec_unit here is not exactly nice: we depend on it being static independent of stage_2_ready.
        # It's correct, but it's not nice.
        # NOTE: since we're going out to the RF write port, self.output_port.ready doesn't exist. That in turn means
        #       that stage_2_fsm.input_ready is constant '1'. So, really the only reason we would apply back-pressure
        #       is if there's a pending bus operation.
        stage_2_fsm = ForwardBufLogic()
        stage_2_fsm.input_valid <<= stage_1_valid
        # We cancel stage-2 of an instruction, if there was an exception or an interrupt.
        # This is different from stage-1, where we want to cancel all instructions in a branch-shadow.
        # The distinction is only relevant for CALL-s, which do branch, yet have side-effects as well.
        stage_2_fsm.clear <<= branch_output.is_exception_or_interrupt
        block_mem = s1_ldst_output.mem_av | s1_ldst_output.mem_unaligned | s1_fetch_av
        s1_is_ld_st = (s1_exec_unit == op_class.ld_st) | (s1_exec_unit == op_class.branch_ind)
        s2_is_ld_st = (s2_exec_unit == op_class.ld_st) | (s2_exec_unit == op_class.branch_ind)
        mem_input.valid <<= stage_1_valid & ~block_mem & s1_is_ld_st
        stage_2_ready <<= Select(s1_is_ld_st & ~block_mem, stage_2_fsm.input_ready,  mem_input.ready)
        stage_2_valid <<= Select(s2_is_ld_st & ~block_mem, stage_2_fsm.output_valid, s2_mem_output.valid | (s2_result_reg_addr_valid & (s2_ldst_op == ldst_ops.store))) & ~s2_was_branch
        stage_2_fsm.output_ready <<= Select(s2_is_ld_st & ((s2_ldst_op == ldst_ops.load) | (s2_ldst_op == ldst_ops.csr_load)) & ~block_mem, 1, s2_mem_output.valid)

        stage_2_reg_en = Wire(logic)
        stage_2_reg_en <<= stage_1_valid & stage_2_ready & ~Reg(self.do_branch)

        # PC handling:
        # We are upgrading TPC/SPC in the first cycle of execute, as if for straight execution.
        # In the second stage, we use the pre-computed branch target and exception flags to handle branches.
        # These means that there are two possible sources for xPC updates in every cycle:
        # - Current instruction in 'execute 1'
        # - Previous instruction in case of a branch, in 'execute 2'
        # To make things right, 'execute 2' has priority updating xPC

        # Branch unit
        branch_unit = BranchUnit()
        branch_input.opcode          <<= s1_branch_op
        #branch_input.pc              <<= s2_pc
        branch_input.spc             <<= s1_spc
        branch_input.tpc             <<= s1_tpc
        branch_input.task_mode       <<= s1_task_mode
        branch_input.branch_addr     <<= Select(
            (s1_exec_unit == op_class.branch_ind),
            s1_branch_target_output.branch_addr,
            concat(s2_mem_output.data_h, s2_mem_output.data_l)[31:1]
        )
        branch_input.interrupt       <<= self.interrupt
        branch_input.fetch_av        <<= s1_fetch_av
        branch_input.mem_av          <<= s1_ldst_output.mem_av
        branch_input.mem_unaligned   <<= s1_ldst_output.mem_unaligned
        branch_input.op_a            <<= s1_op_a
        branch_input.op_b            <<= s1_op_b
        #branch_input.op_c            <<= s1_op_c
        branch_input.f_zero          <<= s1_alu_output.f_zero
        branch_input.f_sign          <<= s1_alu_output.f_sign
        branch_input.f_carry         <<= s1_alu_output.f_carry
        branch_input.f_overflow      <<= s1_alu_output.f_overflow
        branch_input.is_branch_insn  <<= (s1_exec_unit == op_class.branch) | (s1_exec_unit == op_class.branch_ind)
        branch_input.woi             <<= s1_woi

        branch_unit.input_port <<= branch_input
        branch_output <<= branch_unit.output_port
        #spc
        #spc_changed
        #tpc
        #tpc_changed
        #task_mode
        #task_mode_changed
        #ecause
        #do_branch

        # Memory unit
        memory_unit = MemoryStage()


        mem_input.read_not_write <<= s1_is_ld_st & ((s1_ldst_op == ldst_ops.load) | (s1_ldst_op == ldst_ops.csr_load))
        mem_input.data <<= s1_op_a
        mem_input.addr <<= s1_ldst_output.phy_addr
        mem_input.is_csr <<= s1_ldst_output.is_csr
        mem_input.access_len <<= s1_mem_access_len
        memory_unit.input_port <<= mem_input
        self.bus_req_if <<= memory_unit.bus_req_if
        memory_unit.bus_rsp_if <<= self.bus_rsp_if
        self.csr_if <<= memory_unit.csr_if
        s2_mem_output <<= memory_unit.output_port
        #data_l
        #data_h

        # Combine all outputs into a single output register, mux-in memory results
        selector_choices = [s1_exec_unit == op_class.alu, s1_alu_output.result]
        if self.has_multiply:
            selector_choices += [s1_exec_unit == op_class.mult, mult_output.result]
        if self.has_shift:
            selector_choices += [s1_exec_unit == op_class.shift, s1_shifter_output.result]
        selector_choices += [(s1_exec_unit == op_class.branch) | (s1_exec_unit == op_class.branch_ind), concat(s1_branch_target_output.straight_addr, "1'b0")]
        result = SelectOne(*selector_choices)

        s2_result_reg_addr_valid <<= Reg(s1_result_reg_addr_valid, clock_en = stage_2_reg_en)
        self.output_port.valid <<= stage_2_valid & s2_result_reg_addr_valid & (Reg(stage_2_reg_en) | (s2_mem_output.valid & s2_is_ld_st))
        # TODO: I'm not sure if we need these delayed versions for write-back
        #s2_result_reg_addr = Reg(s1_result_reg_addr, clock_en = stage_2_reg_en)
        #ldst_result_reg_addr = Reg(s1_result_reg_addr, clock_en = mem_input.ready)

        # When we have a branch, we have to clear the exec unit from s2; otherwise it will potentially prevent 'sideband_strobe' from firing when we resume from the target.
        # The test for this is:
        #   $pc <- mem[some_table] # jumps to xxx
        # xxx:
        #   $pc <- yyy
        # These back-to-back jumps would fail without the intervention
        s2_exec_unit <<= Reg(Select(self.do_branch, Select(stage_2_reg_en, s2_exec_unit, s1_exec_unit), op_class.invalid))
        s2_ldst_op <<= Reg(s1_ldst_op, clock_en = stage_2_reg_en)

        self.output_port.data_l <<= Select(s2_exec_unit == op_class.ld_st, Reg(result[15: 0], clock_en = stage_2_reg_en), Select(s2_ldst_op == ldst_ops.store, s2_mem_output.data_l, 0))
        self.output_port.data_h <<= Select(s2_exec_unit == op_class.ld_st, Reg(result[31:16], clock_en = stage_2_reg_en), Select(s2_ldst_op == ldst_ops.store, s2_mem_output.data_h, 0))
        self.output_port.data_en <<= 1
        #self.output_port.addr <<= Select(s2_exec_unit == op_class.ld_st, s2_result_reg_addr, ldst_result_reg_addr)
        self.output_port.addr <<= Reg(s1_result_reg_addr, clock_en = stage_2_reg_en)
        self.output_port.do_bse <<= Reg(s1_do_bse, clock_en = stage_2_reg_en)
        self.output_port.do_wse <<= Reg(s1_do_wse, clock_en = stage_2_reg_en)
        self.output_port.do_bze <<= Reg(s1_do_bze, clock_en = stage_2_reg_en)
        self.output_port.do_wze <<= Reg(s1_do_wze, clock_en = stage_2_reg_en)

        # Set sideband outputs as needed
        sideband_strobe = Select(
            s2_exec_unit == op_class.branch_ind,
            (s1_exec_unit != op_class.branch_ind) & stage_2_reg_en,
            s2_mem_output.valid
        )
        self.do_branch <<= branch_output.do_branch & sideband_strobe

        straight_tpc_out = Select(stage_1_reg_en, self.tpc_in, Select(self.task_mode_in, self.tpc_in, branch_target_output.straight_addr))
        self.tpc_out <<= Select(
            s1_was_branch,
            Select(
                sideband_strobe & branch_output.tpc_changed,
                straight_tpc_out,
                branch_output.tpc,
            ),
            self.tpc_in
        )
        straight_spc_out = Select(stage_1_reg_en, self.spc_in, Select(~(self.task_mode_out | self.task_mode_in), self.spc_in, branch_target_output.straight_addr))
        self.spc_out <<= Select(
            s1_was_branch,
            Select(
                sideband_strobe & branch_output.spc_changed,
                straight_spc_out,
                branch_output.spc,
            ),
            self.spc_in
        )
        self.task_mode_out <<= Select(
            s1_was_branch,
            Select(
                sideband_strobe & branch_output.task_mode_changed,
                self.task_mode_in,
                branch_output.task_mode,
            ),
            self.task_mode_in
        )
        self.ecause_out <<= Select(
            sideband_strobe & ~s1_was_branch,
            self.ecause_in,
            Select(
                branch_output.is_exception_or_interrupt,
                self.ecause_in,
                branch_output.ecause
            )
        )
        # We mask eaddr_out updates in the shadow of a branch: do_branch is one cycle delayed, so if that fires, the current instruction
        # should be cancelled and have no side-effects. That goes for eaddr_out as well.
        self.eaddr_out <<= Reg(Select(
            s1_fetch_av | ((s1_exec_unit == op_class.branch) & (s1_branch_op == branch_ops.swi)),
            s1_eff_addr,
            concat(s1_pc, "1'b0"),
        ), clock_en=branch_output.is_exception)

        #self.complete <<= stage_2_reg_en
        self.complete <<= stage_2_valid



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

