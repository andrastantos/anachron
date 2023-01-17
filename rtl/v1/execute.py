#!/usr/bin/python3
from random import *
from typing import *
from silicon import *
try:
    from .brew_types import *
    from .brew_utils import *
except ImportError:
    from brew_types import *
    from brew_utils import *

"""
Execute stage of the V1 pipeline.

This stage is sandwiched between 'decode' and 'memory'.

It does the following:
- Computes the result from source operands
- Computes effective address for memory
- Checks for all exceptions
- Tests for branches

"""

class ExecuteStage(Module):
    clk = ClkPort()
    rst = RstPort()

    # Pipeline input
    decode = Input(DecodeExecIf)

    # Pipeline output
    mem = Output(ExecMemIf)

    # side-band interfaces
    mem_base = Input(BrewMemBase)
    mem_limit = Input(BrewMemBase)
    spc_in  = Input(BrewInstAddr)
    spc_out = Output(BrewInstAddr)
    tpc_in  = Input(BrewInstAddr)
    tpc_out = Output(BrewInstAddr)
    task_mode_in  = Input(logic)
    task_mode_out = Output(logic)
    ecause_in = Input(Unsigned(12))
    ecause_out = Output(Unsigned(12))
    rcause_in = Input(Unsigned(12))
    rcause_out = Output(Unsigned(12))
    do_branch = Output(logic)
    interrupt = Input(logic)

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

        pc = Select(self.task_mode_in, self.spc_in, self.tpc_in)

        adder_result = SelectOne(
            self.decode.opcode == op.add,      (self.decode.op_a + self.decode.op_b)[31:0],
            self.decode.opcode == op.a_sub_b,  (self.decode.op_a + self.decode.op_b)[31:0],
            self.decode.opcode == op.b_sub_a,  (self.decode.op_b - self.decode.op_a)[31:0],
            self.decode.opcode == op.addr,     (self.decode.op_b + self.decode.op_imm + (self.mem_base << BrewMemShift))[31:0],
            self.decode.opcode == op.pc_add,   (pc + concat(self.decode.op_a, "1'b0"))[31:0],
        )[31:0]
        shifter_result = SelectOne(
            self.decode.opcode == op.shll, self.decode.op_a << self.decode.op_b[5:0],
            self.decode.opcode == op.shlr, self.decode.op_a >> self.decode.op_b[5:0],
            self.decode.opcode == op.shar, Signed(32)(self.decode.op_a) >> self.decode.op_b[5:0],
        )[31:0]
        logic_result = SelectOne(
            self.decode.opcode == op.b_or,    self.decode.op_a | self.decode.op_b,
            self.decode.opcode == op.b_and,   self.decode.op_a & self.decode.op_b,
            self.decode.opcode == op.b_nand, ~self.decode.op_a & self.decode.op_b,
            self.decode.opcode == op.b_xor,   self.decode.op_a ^ self.decode.op_b,
        )
        cbranch_result = SelectOne(
            self.decode.opcode == op.cb_eq,   self.decode.op_a == self.decode.op_b,
            self.decode.opcode == op.cb_ne,   self.decode.op_a != self.decode.op_b,
            self.decode.opcode == op.cb_lts,  Signed(32)(self.decode.op_a) <  Signed(32)(self.decode.op_b),
            self.decode.opcode == op.cb_ges,  Signed(32)(self.decode.op_a) >= Signed(32)(self.decode.op_b),
            self.decode.opcode == op.cb_lt,   self.decode.op_a <  self.decode.op_b,
            self.decode.opcode == op.cb_ge,   self.decode.op_a >= self.decode.op_b,
        )
        bbranch_result = SelectOne(
            self.decode.opcode == op.bb_one,  bb_get_bit(self.decode.op_a, self.decode.op_b),
            self.decode.opcode == op.bb_zero, bb_get_bit(self.decode.op_b, self.decode.op_a),
        )

        mem_av = (self.decode.exec_unit == exec.adder) & (self.decode.opcode == op.addr) & (adder_result[31:BrewMemShift] > self.mem_limit)
        mem_unaligned = (self.decode.exec_unit == exec.adder) & (self.decode.opcode == op.addr) & \
            Select(self.decode.mem_access_len,
                0, # 8-bit access is always aligned
                adder_result[0], # 16-bit access is unaligned if LSB is non-0
                adder_result[0] | adder_result[1], # 32-bit access is unaligned if lower two bits are non-0
                1 # This is an invalid length
            )

        def unmunge_offset(offset):
            return concat(
                offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0],
                offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0], offset[0],
                offset[15:1], 0
            )

        next_inst_addr = SelectOne(
            (self.decode.exec_unit == exec.cbranch) | (self.decode.exec_unit == exec.bbranch), (pc + unmunge_offset(self.decode.op_imm))[30:0],
            (self.decode.exec_unit == exec.misc) & (self.decode.opcode == op.misc_pc_w), self.decode.op_imm[31:1],
            (self.decode.exec_unit == exec.misc) & (self.decode.opcode == op.misc_tpc_w) & self.task_mode_in, self.decode.op_imm[31:1],
            default_port = Select(
                self.task_mode_in,
                (self.spc_in + self.decode.inst_len + 1)[30:0], # Inst len is 0=16-bit, 1=32-bit, 2=48-bit
                (self.tpc_in + self.decode.inst_len + 1)[30:0]  # Inst len is 0=16-bit, 1=32-bit, 2=48-bit
            )
        )

        mult_result_large = self.decode.op_a * self.decode.op_b
        mult_result = mult_result_large[31:0]
        exec_result = SelectOne(
            self.decode.exec_unit == exec.adder, adder_result,
            self.decode.exec_unit == exec.shift, shifter_result,
            self.decode.exec_unit == exec.mult, mult_result,
            self.decode.exec_unit == exec.bitwise, logic_result,
            self.decode.exec_unit == exec.misc, SelectOne(
                self.decode.opcode == op.misc_swi,   None,
                self.decode.opcode == op.misc_stm,   None,
                self.decode.opcode == op.misc_pc_r,  pc,
                self.decode.opcode == op.misc_tpc_r, self.tpc_in,
                self.decode.opcode == op.misc_pc_w,  None,
                self.decode.opcode == op.misc_tpc_w, None,
            )
        )
        is_branch = SelectOne(
            self.decode.exec_unit == exec.adder, mem_av,
            self.decode.exec_unit == exec.shift, 0,
            self.decode.exec_unit == exec.mult,  0,
            self.decode.exec_unit == exec.bitwise, 0,
            self.decode.exec_unit == exec.cbranch, cbranch_result,
            self.decode.exec_unit == exec.bbranch, bbranch_result,
            self.decode.exec_unit == exec.misc, SelectOne(
                self.decode.opcode == op.misc_swi,   1,
                self.decode.opcode == op.misc_stm,   1,
                self.decode.opcode == op.misc_pc_r,  0,
                self.decode.opcode == op.misc_tpc_r, 0,
                self.decode.opcode == op.misc_pc_w,  1,
                self.decode.opcode == op.misc_tpc_w, self.task_mode_in,

            )
        )

        is_exception = self.decode.fetch_av | SelectOne(
            self.decode.exec_unit == exec.adder, mem_av | mem_unaligned,
            self.decode.exec_unit == exec.shift, 0,
            self.decode.exec_unit == exec.mult,  0,
            self.decode.exec_unit == exec.bitwise, 0,
            self.decode.exec_unit == exec.cbranch, 0,
            self.decode.exec_unit == exec.bbranch, 0,
            self.decode.exec_unit == exec.misc, SelectOne(
                self.decode.opcode == op.misc_swi,   1,
                self.decode.opcode == op.misc_stm,   0,
                self.decode.opcode == op.misc_pc_r,  0,
                self.decode.opcode == op.misc_tpc_r, 0,
                self.decode.opcode == op.misc_pc_w,  0,
                self.decode.opcode == op.misc_tpc_w, 0,
            )
        )

        # TODO:: This can probably be optimized as many of the options can't really happen at the same time.
        #        With some caution in fetch, it can even be the case that all of these are exclusive conditions.
        #        Because of that, a simple concatenation of the bit-fields could probably work. But for now,
        #        let's leave it this way and optimize later.
        ecause_mask = Select(
            self.decode.fetch_av,
            Select(
                mem_unaligned,
                Select(
                    mem_av,
                    0,
                    Select(
                        (self.decode.exec_unit == exec.misc) & (self.decode.opcode == op.misc_swi),
                        0,
                        1 << ((self.decode.op_a & 7)[2:0])
                    ),
                    1 << exc_mdp
                ),
                1 << exc_cua
            ),
            1 << exc_mip
        )
        ecause_mask = 0

        reg_en = Wire(logic) # output of handshake_fsm

        self.do_branch <<= is_branch & reg_en

        handshake_fsm = ForwardBufLogic()

        handshake_fsm.input_valid <<= self.decode.valid
        self.decode.ready <<= handshake_fsm.input_ready
        self.mem.valid <<= handshake_fsm.output_valid
        handshake_fsm.output_ready <<= self.mem.ready
        reg_en <<= handshake_fsm.out_reg_en


        self.mem.mem_access_len  <<= Reg(self.decode.mem_access_len, clock_en=reg_en)
        self.mem.result          <<= Reg(exec_result, clock_en=reg_en)
        self.mem.result_reg_addr <<= Reg(self.decode.result_reg_addr, clock_en=reg_en)
        self.mem.mem_addr        <<= Reg(adder_result, clock_en=reg_en)
        self.mem.is_load         <<= Reg(self.decode.is_load, clock_en=reg_en)
        self.mem.is_store        <<= Reg(self.decode.is_store, clock_en=reg_en)
        self.mem.do_bse          <<= Reg(self.decode.do_bse, clock_en=reg_en)
        self.mem.do_wse          <<= Reg(self.decode.do_wse, clock_en=reg_en)
        self.mem.do_bze          <<= Reg(self.decode.do_bze, clock_en=reg_en)
        self.mem.do_wze          <<= Reg(self.decode.do_wze, clock_en=reg_en)

        # Side-band info output
        self.spc_out <<= Select(reg_en,
            self.spc_in,
            Select(
                self.task_mode_in,
                # In Scheduler mode
                Select(is_exception, next_inst_addr, 0), # Exception in scheduler mode is reset
                # In Task mode
                self.spc_in
            )
        )
        self.tpc_out <<= Select(reg_en,
            self.tpc_in,
            Select(
                self.task_mode_in,
                # In Scheduler mode: TPC can only change through TCP manipulation instructions
                Select(
                    (self.decode.exec_unit == exec.misc) & (self.decode.opcode == op.misc_tpc_w),
                    self.tpc_in,
                    self.decode.op_imm[31:1]
                ),
                # In Task mode: TPC changes through branches, or through normal execution
                Select(is_exception, next_inst_addr, self.tpc_in) # Exception in task mode: no TPC update
            )
        )
        # Still needs assignment
        self.task_mode_out <<= Select(reg_en,
            self.task_mode_in,
            Select(
                self.task_mode_in,
                # In scheduler mode: exit to ask mode, if STM instruction is executed
                ~((self.decode.exec_unit == exec.misc) & (self.decode.opcode == op.misc_stm)),
                # In task mode: we enter scheduler mode in case of an exception
                ~is_exception
            )
        )

        # We set the HWI ECAUSE bit even in scheduler mode: this allows for interrupt polling at least.
        # The interrupt will not get serviced of course until we're in TASK mode.
        hwi_mask =  Select(self.interrupt, 0, 1 << exc_hwi)
        self.ecause_out <<= Select(reg_en,
            self.ecause_in,
            Select(
                is_exception,
                self.ecause_in | hwi_mask,
                self.ecause_in | ecause_mask | hwi_mask
            )
        )
        self.rcause_out <<= Select(reg_en,
            self.rcause_in,
            Select(
                is_exception & ~self.task_mode_in,
                self.rcause_in,
                self.rcause_in | ecause_mask
            )
        )

def gen():
    Build.generate_rtl(ExecuteStage)

#gen()
#sim()
