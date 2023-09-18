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
except ImportError:
    from brew_types import *
    from brew_utils import *
    from memory import MemoryStage
    from scan import ScanWrapper
    from synth import *

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

class ExecUnitResultIf(Interface):
    result = BrewData


class AluInputIf(Interface):
    opcode = EnumNet(alu_ops)
    op_a = BrewData
    op_b = BrewData
    pc = BrewInstAddr
    tpc = BrewInstAddr

class AluOutputIf(Interface):
    result = BrewData
    f_zero = logic
    f_sign  = logic
    f_carry = logic
    f_overflow = logic

class AluUnit(Module):
    clk = ClkPort()
    rst = RstPort()

    input_port = Input(AluInputIf)
    output_port = Output(AluOutputIf)

    OPTIMIZED = True
    def body(self):
        if self.OPTIMIZED:
            c_in = Wire(logic)
            c_in <<= (self.input_port.opcode == alu_ops.a_minus_b)
            xor_b = Wire(BrewData)
            xor_b <<= Select((self.input_port.opcode == alu_ops.a_minus_b), 0, 0xffffffff)
            b = xor_b ^ self.input_port.op_b
            a = Select((self.input_port.opcode == alu_ops.pc_plus_b), self.input_port.op_a, concat(self.input_port.pc, "1'b0"))
            sum = a + b + c_in
            and_result = a & b
            xor_result = self.input_port.op_a ^ self.input_port.op_b

            use_adder = (self.input_port.opcode == alu_ops.a_plus_b) | (self.input_port.opcode == alu_ops.a_minus_b)
            use_and = (self.input_port.opcode == alu_ops.a_and_b)
            adder_result = Wire(Unsigned(33))
            adder_result <<= SelectOne(
                use_adder,                                      sum,
                self.input_port.opcode == alu_ops.a_or_b,       self.input_port.op_a | self.input_port.op_b,
                use_and,                                        and_result,
                self.input_port.opcode == alu_ops.a_xor_b,      xor_result,
                self.input_port.opcode == alu_ops.tpc,          concat(self.input_port.tpc, "1'b0"),
                self.input_port.opcode == alu_ops.pc_plus_b,    sum,
            )

            self.output_port.result <<= adder_result[31:0]
            #self.output_port.f_zero <<= adder_result[31:0] == 0
            self.output_port.f_zero <<= xor_result == 0
            self.output_port.f_sign <<= adder_result[31]
            self.output_port.f_carry <<= adder_result[32] ^ (self.input_port.opcode == alu_ops.a_minus_b)
            # overflow for now is only valid for a_minus_b
            # See https://en.wikipedia.org/wiki/Overflow_flag for details
            self.output_port.f_overflow <<= (self.input_port.op_a[31] != self.input_port.op_b[31]) & (self.input_port.op_a[31] != adder_result[31])
        else:
            adder_result = Wire(Unsigned(33))
            adder_result <<= SelectOne(
                self.input_port.opcode == alu_ops.a_plus_b,     (self.input_port.op_a + self.input_port.op_b),
                self.input_port.opcode == alu_ops.a_minus_b,    Unsigned(33)(self.input_port.op_a - self.input_port.op_b),
                self.input_port.opcode == alu_ops.a_or_b,       self.input_port.op_a | self.input_port.op_b,
                self.input_port.opcode == alu_ops.a_and_b,      self.input_port.op_a & self.input_port.op_b,
                self.input_port.opcode == alu_ops.a_xor_b,      self.input_port.op_a ^ self.input_port.op_b,
                self.input_port.opcode == alu_ops.tpc,          concat(self.input_port.tpc, "1'b0"),
                self.input_port.opcode == alu_ops.pc_plus_b,    concat(self.input_port.pc, "1'b0") + self.input_port.op_b,
            )

            self.output_port.result <<= adder_result[31:0]
            self.output_port.f_zero <<= adder_result[31:0] == 0
            self.output_port.f_sign <<= adder_result[31]
            self.output_port.f_carry <<= adder_result[32]
            # overflow for now is only valid for a_minus_b
            # See https://en.wikipedia.org/wiki/Overflow_flag for details
            self.output_port.f_overflow <<= (self.input_port.op_a[31] != self.input_port.op_b[31]) & (self.input_port.op_a[31] != adder_result[31])


class ShifterInputIf(Interface):
    opcode = EnumNet(shifter_ops)
    op_a = BrewData
    op_b = BrewData

class ShifterOutputIf(Interface):
    result = BrewData

class ShifterUnit(Module):
    clk = ClkPort()
    rst = RstPort()

    input_port = Input(ShifterInputIf)
    output_port = Output(ShifterOutputIf)

    def body(self):
        # TODO: this can be optimized quite a bit. As of now, we instantiate 3 barrel shifters
        self.signed_a = Signed(32)(self.input_port.op_a)
        shifter_result = SelectOne(
            self.input_port.opcode == shifter_ops.shll, self.input_port.op_a << self.input_port.op_b[4:0],
            self.input_port.opcode == shifter_ops.shlr, self.input_port.op_a >> self.input_port.op_b[4:0],
            self.input_port.opcode == shifter_ops.shar, self.signed_a >> self.input_port.op_b[4:0],
        )[31:0]

        self.output_port.result <<= shifter_result


class MultInputIf(Interface):
    valid = logic
    op_a = BrewData
    op_b = BrewData

class MultOutputIf(Interface):
    result = BrewData

class MultUnit(Module):
    clk = ClkPort()
    rst = RstPort()

    input_port = Input(MultInputIf)
    output_port = Output(MultOutputIf)

    OPTIMIZED = True
    def body(self):
        if self.OPTIMIZED:
            partial_11 = (self.input_port.op_a[15: 0] * self.input_port.op_b[15: 0])
            partial_12 = (self.input_port.op_a[31:16] * self.input_port.op_b[15: 0])[15:0]
            partial_21 = (self.input_port.op_a[15: 0] * self.input_port.op_b[31:16])[15:0]
            s1_partial_11 = Reg(partial_11, clock_en = self.input_port.valid)
            s1_partial_12 = Reg(partial_12, clock_en = self.input_port.valid)
            s1_partial_21 = Reg(partial_21, clock_en = self.input_port.valid)
            mult_result = (s1_partial_11 + concat(s1_partial_12+s1_partial_21, "16'b0"))[31:0]
        else:
            op_a = Select(self.input_port.valid, Reg(self.input_port.op_a, clock_en = self.input_port.valid), self.input_port.op_a)
            op_b = Select(self.input_port.valid, Reg(self.input_port.op_b, clock_en = self.input_port.valid), self.input_port.op_b)
            mult_result_large = op_a * op_b
            mult_result = mult_result_large[31:0]

        self.output_port.result <<= mult_result


class BranchTargetUnitInputIf(Interface):
    op_c       = BrewData
    pc         = BrewInstAddr
    inst_len   = Unsigned(2) # 0: single-beat, 1: two-beat, 3: 4-beat

class BranchTargetUnitOutputIf(Interface):
    branch_addr = BrewInstAddr
    straight_addr = BrewInstAddr

class BranchTargetUnit(Module):

    input_port = Input(BranchTargetUnitInputIf)
    output_port = Output(BranchTargetUnitOutputIf)

    def body(self):
        def unmunge_offset(offset):
            return concat(
                offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0],
                offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0],
                offset[15:1]
            )
        offset = unmunge_offset(self.input_port.op_c)
        self.output_port.branch_addr   <<= (self.input_port.pc + offset)[30:0]
        self.output_port.straight_addr <<= (self.input_port.pc + self.input_port.inst_len + 1)[30:0]


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
        self.output_port.spc_changed    <<= ~self.input_port.task_mode & (is_exception | in_mode_branch)
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
        unknown_inst_exception = self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.unknown)

        # We set the ECAUSE bits even in scheduler mode: this allows for interrupt polling and,
        # after a reset, we can check it to determine the reason for the reset
        self.output_port.ecause <<= SelectFirst(
            unknown_inst_exception,         exceptions.exc_unknown_inst,
            self.input_port.interrupt,      exceptions.exc_hwi,
            self.input_port.fetch_av,       exceptions.exc_inst_av,
            self.input_port.mem_unaligned,  exceptions.exc_unaligned,
            self.input_port.mem_av,         exceptions.exc_mem_av,
            swi_exception,                  EnumNet(exceptions)(0x20 | self.input_port.op_a[2:0]),
        )
        self.output_port.is_exception <<= is_exception
        self.output_port.is_exception_or_interrupt  <<= is_exception | (self.input_port.task_mode & self.input_port.interrupt)







class LoadStoreInputIf(Interface):
    is_ldst = logic
    op_b = BrewData
    op_c = BrewData
    mem_base = BrewMemBase
    mem_limit = BrewMemBase
    task_mode = logic
    mem_access_len = Unsigned(2) # 0: 8-bit, 1: 16-bit, 2: 32-bit
    is_csr = logic

class LoadStoreOutputIf(Interface):
    phy_addr = BrewAddr
    eff_addr = BrewAddr
    mem_av = logic
    mem_unaligned = logic
    is_csr = logic

class LoadStoreUnit(Module):
    clk = ClkPort()
    rst = RstPort()

    input_port = Input(LoadStoreInputIf)
    output_port = Output(LoadStoreOutputIf)

    def body(self):
        eff_addr = TIMING_CLOSURE_REG((self.input_port.op_b + self.input_port.op_c)[31:0])
        phy_addr = Select(
            self.input_port.is_csr,
            (eff_addr + Select(self.input_port.task_mode, 0, (self.input_port.mem_base << BrewMemShift)))[31:0],
            concat(self.input_port.op_c[15:0], "2'b00") | Select(self.input_port.task_mode, 0, 0x20000),
        )

        mem_av = self.input_port.task_mode & self.input_port.is_ldst & (eff_addr[31:BrewMemShift] > self.input_port.mem_limit) & ~self.input_port.is_csr
        mem_unaligned = ~self.input_port.is_csr & self.input_port.is_ldst & Select(self.input_port.mem_access_len,
            0, # 8-bit access is always aligned
            eff_addr[0], # 16-bit access is unaligned if LSB is non-0
            eff_addr[0] | eff_addr[1], # 32-bit access is unaligned if lower two bits are non-0
            1 # This is an invalid length
        )

        self.output_port.phy_addr <<= phy_addr
        self.output_port.eff_addr <<= eff_addr
        self.output_port.mem_av <<= mem_av
        self.output_port.mem_unaligned <<= mem_unaligned
        self.output_port.is_csr <<= self.input_port.is_csr

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
        ldst_output = Wire(LoadStoreOutputIf)
        ldst_unit = LoadStoreUnit()
        ldst_unit.input_port.is_ldst        <<= (self.input_port.exec_unit == op_class.ld_st) | (self.input_port.exec_unit == op_class.branch_ind)
        ldst_unit.input_port.is_csr         <<= (self.input_port.ldst_op == ldst_ops.csr_load) | (self.input_port.ldst_op == ldst_ops.csr_store)
        ldst_unit.input_port.op_b           <<= self.input_port.op_b
        ldst_unit.input_port.op_c           <<= self.input_port.op_c
        ldst_unit.input_port.mem_base       <<= self.mem_base
        ldst_unit.input_port.mem_limit      <<= self.mem_limit
        ldst_unit.input_port.task_mode      <<= self.task_mode_in
        ldst_unit.input_port.mem_access_len <<= self.input_port.mem_access_len
        ldst_output <<= ldst_unit.output_port
        s1_ldst_output = Wire(LoadStoreOutputIf)
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
        mem_input = Wire(MemInputIf)
        s2_mem_output = Wire(MemOutputIf)

        s2_pc = Select(s1_task_mode, s1_spc, s1_tpc)

        stage_2_valid = Wire(logic)
        s2_exec_unit = Wire(EnumNet(op_class))
        s2_ldst_op = Wire()

        # NOTE: The use of s1_exec_unit here is not exactly nice: we depend on it being static independent of stage_2_ready.
        # It's correct, but it's not nice.
        # NOTE: since we're going out to the RF write port, self.output_port.ready doesn't exist. That in turn means
        #       that stage_2_fsm.input_ready is constant '1'. So, really the only reason we would apply back-pressure
        #       is if there's a pending bus operation.
        stage_2_fsm = ForwardBufLogic()
        stage_2_fsm.input_valid <<= stage_1_valid
        stage_2_fsm.clear <<= self.do_branch
        block_mem = s1_ldst_output.mem_av | s1_ldst_output.mem_unaligned | s1_fetch_av
        s1_is_ld_st = (s1_exec_unit == op_class.ld_st) | (s1_exec_unit == op_class.branch_ind)
        s2_is_ld_st = (s2_exec_unit == op_class.ld_st) | (s2_exec_unit == op_class.branch_ind)
        mem_input.valid <<= stage_1_valid & ~block_mem & s1_is_ld_st
        stage_2_ready <<= Select(s1_is_ld_st & ~block_mem, stage_2_fsm.input_ready,  mem_input.ready)
        stage_2_valid <<= Select(s2_is_ld_st & ~block_mem, stage_2_fsm.output_valid, s2_mem_output.valid) & ~s2_was_branch
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
        branch_input = Wire(BranchUnitInputIf)
        branch_output = Wire(BranchUnitOutputIf)
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
        if self.has_multiply | self.has_shift:
            selector_choices = [s1_exec_unit == op_class.alu, s1_alu_output.result]
            if self.has_multiply:
                selector_choices += [s1_exec_unit == op_class.mult, mult_output.result]
            if self.has_shift:
                selector_choices += [s1_exec_unit == op_class.shift, s1_shifter_output.result]
            result = SelectOne(*selector_choices)
        else:
            result = s1_alu_output.result

        s2_result_reg_addr_valid = Reg(s1_result_reg_addr_valid, clock_en = stage_2_reg_en)
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

        self.output_port.data_l <<= Select(s2_exec_unit == op_class.ld_st, Reg(result[15: 0], clock_en = stage_2_reg_en), s2_mem_output.data_l)
        self.output_port.data_h <<= Select(s2_exec_unit == op_class.ld_st, Reg(result[31:16], clock_en = stage_2_reg_en), s2_mem_output.data_h)
        self.output_port.data_en <<= Reg(~branch_output.do_branch, clock_en = stage_2_reg_en)
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






def sim():

    def test(name, ref, act, fmt = None):
        if ref is not None and ref != act:
            if fmt is not None:
                print(f"mismatch {name}: expected={ref:{fmt}} actual={act:{fmt}}")
            else:
                print(f"mismatch {name}: expected={ref} actual={act}")
            assert ref is None or ref == act

    class Result(object):
        def __init__(
            self,
            data_l,
            data_h,
            data_en,
            addr,
            result_valid = None,
            do_bse = None,
            do_wse = None,
            do_bze = None,
            do_wze = None,
        ):
            self.data_l = data_l
            self.data_h = data_h
            self.data_en = int(data_en) if data_en is not None else None
            self.addr = addr
            self.result_valid = int(result_valid) if result_valid is not None else None
            self.do_bse = int(do_bse) if do_bse is not None else None
            self.do_wse = int(do_wse) if do_wse is not None else None
            self.do_bze = int(do_bze) if do_bze is not None else None
            self.do_wze = int(do_wze) if do_wze is not None else None

        def compare(
            self,
            result: Junction,
        ):
            test("data_l",        self.data_l,        result.data_l,   "04x")
            test("data_h",        self.data_h,        result.data_h,   "04x")
            test("data_en",       self.data_en,       result.data_en)
            test("addr",          self.addr,          result.addr,     "1x")
            test("result_valid",  self.result_valid,  result.valid)
            test("do_bse",        self.do_bse,        result.do_bse)
            test("do_wse",        self.do_wse,        result.do_wse)
            test("do_bze",        self.do_bze,        result.do_bze)
            test("do_wze",        self.do_wze,        result.do_wze)

            return True

    class PCResult(object):
        def __init__(
            self,
            spc_out = None,
            tpc_out = None,
            task_mode_out = None,
            ecause_out = None,
            do_branch = None,
        ):
            self.spc_out = spc_out
            self.tpc_out = tpc_out
            self.task_mode_out = task_mode_out
            self.ecause_out = ecause_out
            self.do_branch = do_branch

        def compare(
            self,
            spc_out: Junction,
            tpc_out: Junction,
            task_mode_out: Junction,
            ecause_out: Junction,
            do_branch: Junction,
        ):
            test("spc_out",       self.spc_out,       spc_out,         "08x")
            test("tpc_out",       self.tpc_out,       tpc_out,         "08x")
            test("task_mode_out", self.task_mode_out, task_mode_out)
            test("ecause_out",    self.ecause_out,    ecause_out,      "016b")
            test("do_branch",     self.do_branch,     do_branch)

            return True


    class DecodeEmulator(GenericModule):
        class JumpType(Enum):
            Straight = 0
            InModeJump = 1
            Exception = 2
            Reset = 3

        clk = ClkPort()
        rst = RstPort()

        output_port = Output(DecodeExecIf)

        mem_base      = Output(BrewMemBase)
        mem_limit     = Output(BrewMemBase)
        spc_in        = Output(BrewInstAddr)
        spc_out       = Input(BrewInstAddr)
        tpc_in        = Output(BrewInstAddr)
        tpc_out       = Input(BrewInstAddr)
        task_mode_in  = Output(logic)
        task_mode_out = Input(logic)
        ecause_in     = Output(Unsigned(12))
        interrupt     = Output(logic)
        last_jump_type_wire = Output(EnumNet(JumpType))
        this_jump_type_wire = Output(EnumNet(JumpType))
        last_jump_type_input = Input(EnumNet(JumpType))
        this_jump_type_input = Input(EnumNet(JumpType))

        def construct(self, result_queue, pc_result_queue, sideband_state, bus_req_queue):
            self.result_queue = result_queue
            self.pc_result_queue = pc_result_queue
            self.sideband_state = sideband_state
            self.bus_req_queue = bus_req_queue

        def simulate(self, simulator) -> TSimEvent:
            self.last_jump_type = DecodeEmulator.JumpType.Straight
            self.this_jump_type = DecodeEmulator.JumpType.Straight

            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )
                self.spc_in <<= self.spc_out
                self.tpc_in <<= self.tpc_out
                self.task_mode_in <<= self.task_mode_out
                self.sideband_state.tpc = self.tpc_out
                self.sideband_state.spc = self.spc_out
                self.sideband_state.task_mode = self.task_mode_out
                self.last_jump_type = self.this_jump_type
                self.this_jump_type = DecodeEmulator.JumpType.Straight
                self.last_jump_type_wire <<= self.last_jump_type
                self.this_jump_type_wire <<= self.this_jump_type

            def wait_for_transfer():
                if len(self.pc_result_queue) > 0 and self.pc_result_queue[-1].do_branch:
                    if self.pc_result_queue[-1].ecause_out != 0:
                        if self.last_jump_type == DecodeEmulator.JumpType.Exception or self.sideband_state.task_mode == 0:
                            # Exception in scheduler mode
                            self.this_jump_type = DecodeEmulator.JumpType.Reset
                        else:
                            self.this_jump_type = DecodeEmulator.JumpType.Exception
                    else:
                        self.this_jump_type = DecodeEmulator.JumpType.InModeJump
                else:
                    self.this_jump_type = DecodeEmulator.JumpType.Straight
                self.this_jump_type_wire <<= self.this_jump_type
                print(f"{simulator.now:4d} input transfer started")
                self.output_port.valid <<= 1
                yield from wait_clk()
                assert self.output_port.ready.sim_value is not None
                while self.output_port.ready != 1:
                    print(f"{simulator.now:4d} input transfer waiting")
                    yield from wait_clk()
                self.output_port.valid <<= 0
                print(f"{simulator.now:4d} input transfer accepted")


            def set_side_band(*, tpc = None, spc = None, task_mode = True, mem_base = None, mem_limit = None, interrupt = False, ecause = 0):
                self.sideband_state.mem_base = randint(0,0x3fff) if mem_base is None else mem_base
                self.sideband_state.mem_limit = randint(0,0x3fff) if mem_limit is None else mem_limit
                self.sideband_state.tpc = randint(0,0x3fff) | 0x10000000 if tpc is None else tpc
                self.sideband_state.spc = randint(0,0x3fff) | 0x50000000 if spc is None else spc
                self.sideband_state.task_mode = 1 if task_mode else 0
                self.sideband_state.ecause = ecause
                self.sideband_state.interrupt = 1 if interrupt else 0

                self.mem_base <<= self.sideband_state.mem_base
                self.mem_limit <<= self.sideband_state.mem_limit
                self.tpc_in <<= self.sideband_state.tpc
                self.spc_in <<= self.sideband_state.spc
                self.task_mode_in <<= self.sideband_state.task_mode
                self.ecause_in <<= self.sideband_state.ecause
                self.interrupt <<= self.sideband_state.interrupt

            def safe_fmt(what, fmt = None):
                if what is None:
                    return "NONE"
                elif fmt is None:
                    return f"{what}"
                else:
                    return f"{what:{fmt}}"


            def send_rr_op(unit: op_class, op: alu_ops, op_a: int, op_b: int, op_c: int = None, *, result_reg = 0, result_reg_valid = True, fetch_av = False, inst_len = inst_len_16):
                self.output_port.exec_unit <<= unit
                self.output_port.alu_op <<= op if unit == op_class.alu else None
                self.output_port.shifter_op <<= op if unit == op_class.shift else None
                self.output_port.branch_op <<= None
                self.output_port.ldst_op <<= None
                self.output_port.op_a <<= op_a
                self.output_port.op_b <<= op_b
                self.output_port.op_c <<= op_c
                self.output_port.mem_access_len <<= None
                self.output_port.inst_len <<= inst_len
                self.output_port.do_bse <<= 0
                self.output_port.do_wse <<= 0
                self.output_port.do_bze <<= 0
                self.output_port.do_wze <<= 0
                self.output_port.result_reg_addr <<= result_reg
                self.output_port.result_reg_addr_valid <<= 1 if result_reg_valid and not fetch_av else 0
                self.output_port.fetch_av <<= 1 if fetch_av else 0

                mask = 0xffffffff
                if unit == op_class.alu:
                    if op == alu_ops.a_plus_b:
                        result = (op_a + op_b) & mask
                    elif op == alu_ops.a_minus_b:
                        result = (op_a - op_b) & mask
                    elif op == alu_ops.a_and_b:
                        result = op_a & op_b
                    elif op == alu_ops.a_or_b:
                        result = op_a | op_b
                    elif op == alu_ops.a_xor_b:
                        result = op_a ^ op_b
                    elif op == alu_ops.tpc:
                        result = self.sideband_state.tpc << 1
                    elif op == alu_ops.pc_plus_b:
                        result = ((self.sideband_state.tpc << 1 if self.sideband_state.task_mode else self.sideband_state.spc << 1) + op_b) & mask
                elif unit == op_class.shift:
                    if op == shifter_ops.shll:
                        result = (op_a << (op_b & 31)) & mask
                    elif op == shifter_ops.shlr:
                        result = (op_a >> (op_b & 31)) & mask
                    elif op == shifter_ops.shar:
                        msb = (op_a >> 31) & 1
                        upper = (msb << 32) - msb
                        extended_op_a = (upper << 32) | op_a
                        result = (extended_op_a >> (op_b & 31)) & mask
                elif unit == op_class.mult:
                    result = (op_a * op_b) & mask

                next_spc = self.sideband_state.spc
                next_tpc = self.sideband_state.tpc
                next_task_mode = self.sideband_state.task_mode
                ecause_mask = 0
                next_do_branch = 0
                if not self.sideband_state.task_mode:
                    if fetch_av:
                        next_spc = 0
                        ecause_mask |= 1 << exc_mip
                        next_do_branch = 1
                    else:
                        next_spc += inst_len + 1
                else:
                    if fetch_av:
                        next_task_mode = 0
                        ecause_mask |= 1 << exc_mip
                        next_do_branch = 1
                    else:
                        next_tpc += inst_len +1

                if self.last_jump_type == DecodeEmulator.JumpType.Straight:
                    # If the previous instruction somehow generated a branch, this instruction should be cancelled and so no side-effects should be observable
                    print(f"{simulator.now:4d} Sending {unit} {op} {safe_fmt(op_a, '08x')} {safe_fmt(op_b, '08x')}")
                    if not fetch_av:
                        self.result_queue.append(Result(
                            data_l = result & 0xffff,
                            data_h = result >> 16,
                            data_en = 1,
                            addr = result_reg,
                            result_valid = 1,
                            do_bse = 0,
                            do_wse = 0,
                            do_bze = 0,
                            do_wze = 0
                        ))
                    self.pc_result_queue.append(PCResult(
                        spc_out = next_spc,
                        tpc_out = next_tpc,
                        task_mode_out = next_task_mode,
                        ecause_out = self.sideband_state.ecause | ecause_mask,
                        do_branch = next_do_branch
                    ))
                else:
                    print(f"{simulator.now:4d} Sending CANCELLED {unit} {op} {safe_fmt(op_a, '08x')} {safe_fmt(op_b, '08x')}")
                    self.pc_result_queue.append(PCResult())
                yield from wait_for_transfer()

            def send_alu_op(op: alu_ops, op_a: int, op_b: int, op_c: int = None, *, result_reg = 0, result_reg_valid = True, fetch_av = False, inst_len = inst_len_16):
                yield from send_rr_op(op_class.alu, op, op_a, op_b, op_c, result_reg=result_reg, result_reg_valid=result_reg_valid, fetch_av=fetch_av, inst_len=inst_len)
            def send_shifter_op(op: shifter_ops, op_a: int, op_b: int, op_c: int = None, *, result_reg = 0, result_reg_valid = True, fetch_av = False, inst_len = inst_len_16):
                yield from send_rr_op(op_class.shift, op, op_a, op_b, op_c, result_reg=result_reg, result_reg_valid=result_reg_valid, fetch_av=fetch_av, inst_len=inst_len)
            def send_mult_op(op_a: int, op_b: int, op_c: int = None, *, result_reg = 0, result_reg_valid = True, fetch_av = False, inst_len = inst_len_16):
                yield from send_rr_op(op_class.mult, None, op_a, op_b, op_c, result_reg=result_reg, result_reg_valid=result_reg_valid, fetch_av=fetch_av, inst_len=inst_len)
            def send_bubble():
                self.output_port.exec_unit <<= None
                self.output_port.alu_op <<= None
                self.output_port.shifter_op <<= None
                self.output_port.branch_op <<= None
                self.output_port.ldst_op <<= None
                self.output_port.op_a <<= None
                self.output_port.op_b <<= None
                self.output_port.op_c <<= None
                self.output_port.mem_access_len <<= None
                self.output_port.inst_len <<= None
                self.output_port.do_bse <<= None
                self.output_port.do_wse <<= None
                self.output_port.do_bze <<= None
                self.output_port.do_wze <<= None
                self.output_port.result_reg_addr <<= None
                self.output_port.result_reg_addr_valid <<= None
                self.output_port.fetch_av <<= None
                self.output_port.valid <<= 0
                yield from wait_clk()

            def send_cbranch_op(op: branch_ops, op_a: int, op_b: int, op_c: int = None, *, fetch_av = False, inst_len = inst_len_16):
                self.output_port.exec_unit <<= op_class.branch
                self.output_port.alu_op <<= alu_ops.a_minus_b
                self.output_port.shifter_op <<= None
                self.output_port.branch_op <<= op
                self.output_port.ldst_op <<= None
                self.output_port.op_a <<= op_a
                self.output_port.op_b <<= op_b
                self.output_port.op_c <<= op_c
                self.output_port.mem_access_len <<= None
                self.output_port.inst_len <<= inst_len
                self.output_port.do_bse <<= 0
                self.output_port.do_wse <<= 0
                self.output_port.do_bze <<= 0
                self.output_port.do_wze <<= 0
                self.output_port.result_reg_addr <<= None
                self.output_port.result_reg_addr_valid <<= 0
                self.output_port.fetch_av <<= 1 if fetch_av else 0

                pc = self.sideband_state.tpc if self.sideband_state.task_mode else self.sideband_state.spc

                def to_signed(i: int, length: int = 32) -> int:
                    mask = (1 << length) - 1
                    msb = 1 << (length-1)
                    i = i & mask
                    if i & msb == 0:
                        return i
                    return i - mask - 1

                def bit_idx(i: int) -> int:
                    if i == 0x0: return 0
                    if i == 0x1: return 1
                    if i == 0x2: return 2
                    if i == 0x3: return 3
                    if i == 0x4: return 4
                    if i == 0x5: return 5
                    if i == 0x6: return 6
                    if i == 0x7: return 7
                    if i == 0x8: return 8
                    if i == 0x9: return 9
                    if i == 0xa: return 14
                    if i == 0xb: return 15
                    if i == 0xc: return 16
                    if i == 0xd: return 30
                    if i == 0xe: return 31
                    assert False, f"Invalid bit index value: {i}"

                ecause_mask = 0
                is_exception = fetch_av
                if fetch_av:
                    ecause_mask |= 1 << exc_mip

                if op_c is not None:
                    offset_msb = op_c & 1
                    if offset_msb != 0:
                        offset_msb = 0xffff0000
                    offset = offset_msb | ((op_c & 0xfffe) >> 1)
                if op == branch_ops.cb_eq:
                    branch = op_a == op_b
                    branch_target = (pc + offset) & 0x7fffffff
                elif op == branch_ops.cb_ne:
                    branch = op_a != op_b
                    branch_target = (pc + offset) & 0x7fffffff
                elif op == branch_ops.cb_lts:
                    branch = to_signed(op_a) < to_signed(op_b)
                    branch_target = (pc + offset) & 0x7fffffff
                elif op == branch_ops.cb_ges:
                    branch = to_signed(op_a) >= to_signed(op_b)
                    branch_target = (pc + offset) & 0x7fffffff
                elif op == branch_ops.cb_lt:
                    branch = op_a < op_b
                    branch_target = (pc + offset) & 0x7fffffff
                elif op == branch_ops.cb_ge:
                    branch = op_a >= op_b
                    branch_target = (pc + offset) & 0x7fffffff
                elif op == branch_ops.bb_one:
                    branch = (op_a & (1 << bit_idx(op_b))) != 0
                    branch_target = (pc + offset) & 0x7fffffff
                elif op == branch_ops.bb_zero:
                    branch = (op_a & (1 << bit_idx(op_b))) == 0
                    branch_target = (pc + offset) & 0x7fffffff
                elif op == branch_ops.swi:
                    if not fetch_av:
                        ecause_mask |= 1 << (op_a & 7)
                    is_exception = True
                    branch = True
                    branch_target = None
                elif op == branch_ops.stm:
                    if not self.sideband_state.task_mode:
                        branch_target = pc + inst_len + 1
                        branch = True
                    else:
                        branch = False
                elif op == branch_ops.pc_w:
                    branch = True
                    branch_target = op_a >> 1
                elif op == branch_ops.tpc_w:
                    if self.sideband_state.task_mode:
                        branch = True
                        branch_target = None
                    else:
                        branch = False

                next_pc = pc + inst_len + 1 if not branch else branch_target
                if not is_exception:
                    next_spc = self.sideband_state.spc if     self.sideband_state.task_mode else next_pc
                    next_tpc = self.sideband_state.tpc if not self.sideband_state.task_mode else next_pc
                    next_task_mode = self.sideband_state.task_mode
                    if op == branch_ops.stm: next_task_mode = 1
                    if op == branch_ops.tpc_w: next_tpc = op_a >> 1
                else:
                    if self.sideband_state.task_mode:
                        next_tpc = self.sideband_state.tpc
                        next_spc = self.sideband_state.spc
                    else:
                        next_tpc = self.sideband_state.tpc
                        next_spc = 0
                    next_task_mode = 0

                if self.last_jump_type == DecodeEmulator.JumpType.Straight:
                    # If the previous instruction somehow generated a branch, this instruction should be cancelled and so no side-effects should be observable
                    print(f"{simulator.now:4d} Sending branch {op} {safe_fmt(op_a, '08x')} {safe_fmt(op_b, '08x')} {safe_fmt(op_c, '08x')} should {'branch' if branch else 'NOT branch'}")
                    self.pc_result_queue.append(PCResult(
                        spc_out = next_spc,
                        tpc_out = next_tpc,
                        task_mode_out = next_task_mode,
                        ecause_out = self.sideband_state.ecause | ecause_mask,
                        do_branch = branch
                    ))
                else:
                    print(f"{simulator.now:4d} Sending CANCELLED branch {op} {safe_fmt(op_a, '08x')} {safe_fmt(op_b, '08x')} {safe_fmt(op_c, '08x')}")
                    self.pc_result_queue.append(PCResult())
                yield from wait_for_transfer()


            def send_ldst_op(op: ldst_ops, op_a: int, op_b: int, op_c: int, mem_access_len = access_len_32, *, result_reg = 0, result_reg_valid = True, fetch_av = False, inst_len = inst_len_16, do_bse = False, do_wse = False, do_bze = False, do_wze = False):
                self.output_port.exec_unit <<= op_class.ld_st
                self.output_port.alu_op <<= None
                self.output_port.shifter_op <<= None
                self.output_port.branch_op <<= None
                self.output_port.ldst_op <<= op
                self.output_port.op_a <<= op_a
                self.output_port.op_b <<= op_b
                self.output_port.op_c <<= op_c
                self.output_port.mem_access_len <<= mem_access_len
                self.output_port.inst_len <<= inst_len
                self.output_port.do_bse <<= 1 if do_bse else 0
                self.output_port.do_wse <<= 1 if do_wse else 0
                self.output_port.do_bze <<= 1 if do_bze else 0
                self.output_port.do_wze <<= 1 if do_wze else 0
                self.output_port.result_reg_addr <<= result_reg
                self.output_port.result_reg_addr_valid <<= result_reg_valid
                self.output_port.fetch_av <<= 1 if fetch_av else 0

                eff_addr = op_b + op_c
                phy_addr = eff_addr + (self.sideband_state.mem_base << 10)
                mem_av = (eff_addr[BrewAddr.get_length()-1:BrewMemShift] > self.sideband_state.mem_limit) and not fetch_av
                if not fetch_av:
                    if mem_access_len == access_len_8:
                        mem_unaligned = False
                        byte_en = phy_addr & 1
                    elif mem_access_len == access_len_16:
                        mem_unaligned = (eff_addr & 1) != 0
                        byte_en = 3
                    elif mem_access_len == access_len_32:
                        mem_unaligned = (eff_addr & 3) != 0
                        byte_en = 3
                else:
                    byte_en = 3
                    mem_unaligned = False

                # We know what the memory behavior is, so we can predict the returned data for loads
                expected_result_l = (phy_addr >> 1) & 0xffff
                if mem_access_len == access_len_32:
                    expected_result_h = ((phy_addr >> 1) & 0xffff) + 1
                else:
                    expected_result_h = None

                ecause_mask = 0
                is_exception = fetch_av | mem_av | mem_unaligned
                if fetch_av: ecause_mask |= 1 << exc_mip
                if mem_av: ecause_mask |= 1 << exc_cua
                if mem_unaligned: ecause_mask |= 1 << exc_mdp

                pc = self.sideband_state.tpc if self.sideband_state.task_mode else self.sideband_state.spc
                next_pc = pc + inst_len + 1
                if not is_exception:
                    next_spc = self.sideband_state.spc if     self.sideband_state.task_mode else next_pc
                    next_tpc = self.sideband_state.tpc if not self.sideband_state.task_mode else next_pc
                    next_task_mode = self.sideband_state.task_mode
                else:
                    if self.sideband_state.task_mode:
                        next_tpc = self.sideband_state.tpc
                        next_spc = self.sideband_state.spc
                    else:
                        next_tpc = self.sideband_state.tpc
                        next_spc = 0
                    next_task_mode = 0

                if self.last_jump_type == DecodeEmulator.JumpType.Straight:
                    # If the previous instruction somehow generated a branch, this instruction should be cancelled and so no side-effects should be observable
                    print(f"{simulator.now:4d} Sending ldst {op} {safe_fmt(op_a, '08x')} {safe_fmt(op_b, '08x')} {safe_fmt(op_c, '08x')}")
                    self.result_queue.append(Result(
                        data_l = expected_result_l if op == ldst_ops.load else None,
                        data_h = expected_result_h if op == ldst_ops.load else None,
                        data_en = None,
                        addr = result_reg if op == ldst_ops.load else None,
                        result_valid = result_reg_valid if op == ldst_ops.load else None,
                        do_bse = do_bse,
                        do_wse = do_wse,
                        do_bze = do_bze,
                        do_wze = do_wze
                    ))
                    self.pc_result_queue.append(PCResult(
                        spc_out = next_spc,
                        tpc_out = next_tpc,
                        task_mode_out = next_task_mode,
                        ecause_out = self.sideband_state.ecause | ecause_mask,
                        do_branch = is_exception
                    ))

                    if not is_exception:
                        self.bus_req_queue.append(BusIfQueueItem(
                            read_not_write = op == ldst_ops.load,
                            byte_en = byte_en,
                            addr = phy_addr >> 1,
                            data = None if op == ldst_ops.load else (op_a >> 0) & 0xffff
                        ))
                        if mem_access_len == access_len_32:
                            self.bus_req_queue.append(BusIfQueueItem(
                                read_not_write = op == ldst_ops.load,
                                byte_en = byte_en,
                                addr = (phy_addr >> 1) + 1,
                                data = None if op == ldst_ops.load else (op_a >> 16) & 0xffff
                            ))
                else:
                    print(f"{simulator.now:4d} Sending CANCELLED ldst {op} {safe_fmt(op_a, '08x')} {safe_fmt(op_b, '08x')} {safe_fmt(op_c, '08x')}")
                    self.pc_result_queue.append(PCResult())

                yield from wait_for_transfer()


            self.output_port.valid <<= 0
            yield from wait_clk()
            while self.rst:
                yield from wait_clk()
            for i in range(5): yield from wait_clk()
            set_side_band()



            yield from send_ldst_op(ldst_ops.load, op_a = 4, op_b = 8, op_c = 16, mem_access_len = access_len_32)

            for i in range(5):
                yield from send_bubble()



            yield from send_mult_op(41,100)
            for i in range(5):
                yield from send_bubble()
            yield from send_mult_op(42,101)
            yield from send_mult_op(43,102)
            yield from send_mult_op(44,103)
            for i in range(5):
                yield from send_bubble()
            yield from send_alu_op(alu_ops.a_plus_b, 4, 3)
            yield from send_alu_op(alu_ops.a_minus_b, 7, 9)
            yield from send_alu_op(alu_ops.a_and_b, 4, 3)
            yield from send_alu_op(alu_ops.a_or_b, 12, 43)
            yield from send_alu_op(alu_ops.a_xor_b, 23, 12)
            set_side_band()
            yield from send_alu_op(alu_ops.a_plus_b, 4, 3, fetch_av=True)
            yield from send_mult_op(41,43)
            yield from send_shifter_op(shifter_ops.shll,0xf0000001,2)
            yield from send_shifter_op(shifter_ops.shll,0xf0000001,31)
            yield from send_shifter_op(shifter_ops.shll,0xf0000001,32)
            yield from send_shifter_op(shifter_ops.shlr,0xff00ff00,0)
            yield from send_shifter_op(shifter_ops.shlr,0xff00ff00,1)
            yield from send_shifter_op(shifter_ops.shlr,0xff00ff00,8)
            yield from send_shifter_op(shifter_ops.shar,0xff00ff00,0)
            yield from send_shifter_op(shifter_ops.shar,0xff00ff00,1)
            yield from send_shifter_op(shifter_ops.shar,0xff00ff00,8)
            set_side_band(tpc=0xddccbba, spc=0x2233445, task_mode=True)
            yield from send_alu_op(alu_ops.tpc, 3, 2, 1)
            yield from send_alu_op(alu_ops.pc_plus_b, 3, 2, 1)
            yield from send_bubble()
            yield from send_bubble()
            yield from send_bubble()
            set_side_band(tpc=0xddccbba, spc=0x2233445, task_mode=False)
            yield from send_alu_op(alu_ops.tpc, 3, 2, 1)
            yield from send_alu_op(alu_ops.pc_plus_b, 3, 2, 1)
            ### branch tests
            for i in range(5):
                yield from send_bubble()
            yield from send_cbranch_op(branch_ops.cb_eq, 3, 4, 0x1000)
            yield from send_cbranch_op(branch_ops.cb_eq, 15, 15, 0x2000)
            yield from send_cbranch_op(branch_ops.cb_ne, 3, 4, 0x1000)
            yield from send_cbranch_op(branch_ops.cb_ne, 15, 15, 0x2000)
            yield from send_cbranch_op(branch_ops.cb_lt, 3, 4, 0x1000)
            yield from send_cbranch_op(branch_ops.cb_lt, 15, 15, 0x2000)
            yield from send_cbranch_op(branch_ops.cb_lt, 4, 3, 0x3000)
            yield from send_cbranch_op(branch_ops.cb_lts, 3, 4, 0x1000)
            yield from send_cbranch_op(branch_ops.cb_lts, 15, 15, 0x2000)
            yield from send_cbranch_op(branch_ops.cb_lts, 4, 3, 0x3000)
            yield from send_cbranch_op(branch_ops.cb_ge, 3, 4, 0x1000)
            yield from send_cbranch_op(branch_ops.cb_ge, 15, 15, 0x2000)
            yield from send_cbranch_op(branch_ops.cb_ge, 4, 3, 0x3000)
            yield from send_cbranch_op(branch_ops.cb_ges, 3, 4, 0x1000)
            yield from send_cbranch_op(branch_ops.cb_ges, 15, 15, 0x2000)
            yield from send_cbranch_op(branch_ops.cb_ges, 4, 3, 0x3000)
            yield from send_cbranch_op(branch_ops.bb_one, 15, 3, 0x1000)
            yield from send_cbranch_op(branch_ops.bb_one, 15, 6, 0x2000)
            yield from send_cbranch_op(branch_ops.bb_zero, 15, 3, 0x1000)
            yield from send_cbranch_op(branch_ops.bb_zero, 15, 6, 0x2000)
            yield from send_cbranch_op(branch_ops.swi, 1, None, None)
            yield from send_bubble()
            yield from send_bubble()
            set_side_band(tpc=0xddccbba, spc=0x2233445, task_mode=True)
            yield from send_cbranch_op(branch_ops.swi, 2, None, None)
            yield from send_cbranch_op(branch_ops.swi, 3, None, None, fetch_av=True)
            yield from send_cbranch_op(branch_ops.pc_w, 0x2222, None, None)
            yield from send_cbranch_op(branch_ops.tpc_w, 0x4444, None, None)
            yield from send_bubble()
            yield from send_bubble()
            set_side_band(tpc=0xddccbba, spc=0x2233445, task_mode=False)
            yield from send_cbranch_op(branch_ops.pc_w, 0x2222, None, None)
            yield from send_cbranch_op(branch_ops.tpc_w, 0x4444, None, None)
            yield from send_cbranch_op(branch_ops.stm, None, None, None)
            yield from send_bubble()
            yield from send_bubble()
            set_side_band(tpc=0xddccbba, spc=0x2233445, task_mode=True)
            yield from send_cbranch_op(branch_ops.stm, None, None, None)
            ### random ALU tests
            for i in range(5):
                yield from send_bubble()
            for i in range(100):
                op_a = randint(0, 0xffffffff)
                op_b = randint(0, 0xffffffff)
                yield from send_alu_op(alu_ops.a_plus_b,    op_a, op_b)
                yield from send_alu_op(alu_ops.a_minus_b,   op_a, op_b)
                yield from send_alu_op(alu_ops.a_and_b,     op_a, op_b)
                yield from send_alu_op(alu_ops.a_or_b,      op_a, op_b)
                yield from send_alu_op(alu_ops.a_xor_b,     op_a, op_b)

    class PCChecker(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        # We have to be very careful with branch testing:
        # If no branch supposed to happen in this instruction, the PC gets updated on the same cycle the instruction is accepted
        # If a branch is supposed to happen, the PC gets updated *again* the cycle after the instruction is accepted

        trigger_port = Input(logic)
        spc_out = Input(BrewInstAddr)
        tpc_out = Input(BrewInstAddr)
        task_mode_out = Input(logic)
        ecause_out = Input(Unsigned(12))
        do_branch = Input(logic)

        def construct(self, result_queue: Array):
            self.result_queue = result_queue

        #def body(self):
        #    self.spc = Wire()
        #    self.spc <<= Reg(self.spc_out)
        #    self.tpc = Wire()
        #    self.tpc <<= Reg(self.tpc_out)
        #    self.task_mode = Wire()
        #    self.task_mode <<= Reg(self.task_mode_out)
        #    self.ecause = Wire()
        #    self.ecause <<= Reg(self.ecause_out)

        def simulate(self) -> TSimEvent:
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            while True:
                yield from wait_clk()
                if self.trigger_port:
                    expected: PCResult = self.result_queue[0]
                    if expected.do_branch:
                        yield from wait_clk()
                        if self.trigger_port:
                            # We are accepting an instruction right after a jump. This should be cancelled
                            self.result_queue.pop(0)
                            cancelled: PCResult = self.result_queue[0]
                            pass
                    self.result_queue.pop(0)
                    assert expected.compare(self.spc_out, self.tpc_out, self.task_mode_out, self.ecause_out, self.do_branch)

    class ResultChecker(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        input_port = Input(ResultExtendIf)
        complete = Input(logic)

        def construct(self, result_queue: Array):
            self.result_queue = result_queue

        def simulate(self, simulator) -> TSimEvent:
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            while True:
                yield from wait_clk()
                #if self.complete == 1:
                if self.input_port.valid == 1:
                    expected: Result = self.result_queue.pop(0)
                    if expected.result_valid:
                        print(f"{simulator.now:4d} Writing REG $r{self.input_port.addr:x} with value {self.input_port.data_h:04x}{self.input_port.data_l:04x} (expected: {expected.data_h:04x}{expected.data_l:04x}) enable: {self.input_port.data_en}")
                    assert expected.compare(self.input_port)

    class CsrQueueItem(object):
        def __init__(self, req: ApbBaseIf = None, *, pwrite = None, paddr = None, pwdata = None):
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

        input_port = Input(ApbIf(BrewCsrAddr))

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
                    self.input_port.ready <<= 1
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

    class top(Module):
        clk = ClkPort()
        rst = RstPort()

        def body(self):
            seed(0)
            bus_queue = BusIfQueue(3)
            bus_req_queue = []
            csr_queue = []
            result_queue = []
            pc_result_queue = []


            class SidebandState(object): pass
            sideband_state = SidebandState()

            decode_emulator = DecodeEmulator(result_queue, pc_result_queue, sideband_state, bus_req_queue)


            last_jump_type_wire = decode_emulator.last_jump_type_wire
            this_jump_type_wire = decode_emulator.this_jump_type_wire
            decode_emulator.last_jump_type_input <<= decode_emulator.last_jump_type_wire
            decode_emulator.this_jump_type_input <<= decode_emulator.this_jump_type_wire


            csr_emulator = CsrEmulator(csr_queue)
            bus_req_emulator = BusIfReqEmulator(bus_queue, bus_req_queue)
            bus_rsp_emulator = BusIfRspEmulator(bus_queue)
            result_checker = ResultChecker(result_queue)
            pc_checker = PCChecker(pc_result_queue)

            dut = ExecuteStage()

            dut.input_port <<= decode_emulator.output_port
            result_checker.input_port <<= dut.output_port
            result_checker.complete <<= dut.complete

            csr_emulator.input_port <<= dut.csr_if
            bus_req_emulator.input_port <<= dut.bus_req_if
            dut.bus_rsp_if <<= bus_rsp_emulator.output_port

            # side-band interfaces
            dut.mem_base <<= decode_emulator.mem_base
            dut.mem_limit <<= decode_emulator.mem_limit
            dut.spc_in <<= decode_emulator.spc_in
            decode_emulator.spc_out <<= dut.spc_out
            dut.tpc_in  <<= decode_emulator.tpc_in
            decode_emulator.tpc_out <<= dut.tpc_out
            dut.task_mode_in <<= decode_emulator.task_mode_in
            decode_emulator.task_mode_out <<= dut.task_mode_out
            dut.ecause_in <<= decode_emulator.ecause_in
            dut.interrupt <<= decode_emulator.interrupt

            pc_checker.trigger_port <<= decode_emulator.output_port.ready & decode_emulator.output_port.valid
            pc_checker.spc_out <<= dut.spc_out
            pc_checker.tpc_out <<= dut.tpc_out
            pc_checker.task_mode_out <<= dut.task_mode_out
            pc_checker.ecause_out <<= dut.ecause_out
            pc_checker.do_branch <<= dut.do_branch

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

            for i in range(1000):
                yield from clk()
            now = yield 10
            print(f"Done at {now}")

    Build.simulation(top, "execute.vcd", add_unnamed_scopes=True)


def gen():
    def top():
        return ScanWrapper(ExecuteStage, {"clk", "rst"}, has_multiply=True, has_shift=True)

    back_end = SystemVerilog()
    back_end.yosys_fix = True
    netlist = Build.generate_rtl(top, "execute.sv", back_end)
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(target_dir="q_execute", top_level=top_level_name, source_files=("execute.sv",), clocks=(("clk", 10), ("top_clk", 100)), project_name="execute")
    flow.generate()
    flow.run()

if __name__ == "__main__":
    #gen()
    sim()

