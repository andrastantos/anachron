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


class BranchUnitInputIf(Interface):
    opcode          = EnumNet(branch_ops)
    op_a            = BrewData # Can we move this to stage 1? For now let's keep it here...
    bit_test_bit    = logic
    spc             = BrewInstAddr
    tpc             = BrewInstAddr
    task_mode       = logic
    branch_addr     = BrewInstAddr
    straight_addr   = BrewInstAddr
    interrupt       = logic
    fetch_av        = logic # Coming all the way from fetch: if the instruction gotten this far, we should raise the exception
    mem_av          = logic # Coming from the load-store unit if that figures out an exception
    mem_unaligned   = logic # Coming from the load-store unit if an unaligned access was attempted
    f_zero          = logic
    f_sign          = logic
    f_carry         = logic
    f_overflow      = logic
    is_branch_insn  = logic
    is_exception    = logic
    is_interrupt    = logic
    woi             = logic

class BranchUnitOutputIf(Interface):
    spc                       = BrewInstAddr
    spc_changed               = logic
    tpc                       = BrewInstAddr
    tpc_changed               = logic
    task_mode                 = logic
    task_mode_changed         = logic
    ecause                    = EnumNet(exceptions)
    ecause_changed            = logic
    do_branch                 = logic


class BranchUnit(Module):

    input_port = Input(BranchUnitInputIf)
    output_port = Output(BranchUnitOutputIf)

    def body(self):
        # Set whenever we branch without a mode change
        # Branch codes:
        #  eq: f_zero = 1
        #  ne: f_zero = 0
        #  lt: f_carry = 1
        #  ge: f_carry = 0
        #  lts: f_sign != f_overflow
        #  ges: f_sign == f_overflow
        # Some explanation: WOI is decoded into a branch_eq that's always true to the same address as the instruction. So we should branch, unless there's an interrupt and we're in a WOI
        # Exceptions in SCHEUDLER mode result in jump to 0, which is technically an in-mode branch
        in_mode_branch = Select(
            self.input_port.is_exception,
            self.input_port.is_branch_insn & SelectOne(
                self.input_port.opcode == branch_ops.pc_w,        1,
                self.input_port.opcode == branch_ops.pc_w_ind,    1,
                self.input_port.opcode == branch_ops.tpc_w,       self.input_port.task_mode,
                self.input_port.opcode == branch_ops.tpc_w_ind,   self.input_port.task_mode,
                self.input_port.opcode == branch_ops.cb_eq,       self.input_port.f_zero & ~(self.input_port.woi & self.input_port.is_interrupt),
                self.input_port.opcode == branch_ops.cb_ne,      ~self.input_port.f_zero,
                self.input_port.opcode == branch_ops.cb_lts,      self.input_port.f_sign != self.input_port.f_overflow,
                self.input_port.opcode == branch_ops.cb_ges,      self.input_port.f_sign == self.input_port.f_overflow,
                self.input_port.opcode == branch_ops.cb_lt,       self.input_port.f_carry,
                self.input_port.opcode == branch_ops.cb_ge,      ~self.input_port.f_carry,
                self.input_port.opcode == branch_ops.bb_one,      self.input_port.bit_test_bit,
                self.input_port.opcode == branch_ops.bb_zero,    ~self.input_port.bit_test_bit,
                self.input_port.opcode == branch_ops.stm,         0,
            ),
            ~self.input_port.task_mode
        )

        is_exception_or_interrupt = self.input_port.is_exception | (self.input_port.task_mode & self.input_port.is_interrupt)

        self.output_port.tpc <<= Select(
            is_exception_or_interrupt,
            SelectOne(
                self.input_port.opcode == branch_ops.pc_w,      self.input_port.op_a[31:1],
                self.input_port.opcode == branch_ops.tpc_w,     self.input_port.op_a[31:1],
                #self.input_port.opcode == branch_ops.pc_w_ind,  self.input_port.branch_addr,
                #self.input_port.opcode == branch_ops.tpc_w_ind, self.input_port.branch_addr,
                default_port =                                  self.input_port.branch_addr,
            ),
            self.input_port.tpc
        )
        self.output_port.tpc_changed <<= Select(
            self.input_port.task_mode,
            # In Scheduler mode: TPC can only change through TCP manipulation instructions. For those, the value comes through op_c
            self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.tpc_w),
            # In task mode, all branches count, but so do exceptions and interrupts: stage1 already updated TPC
            # to the next address, we'll have to correct for it here
            in_mode_branch | is_exception_or_interrupt
        )

        self.output_port.spc <<= Select(self.input_port.is_exception,
            Select(
                self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.pc_w),
                self.input_port.branch_addr,
                self.input_port.op_a[31:1],
            ),
            0
        )
        self.output_port.spc_changed <<= ~self.input_port.task_mode & (self.input_port.is_exception | in_mode_branch)

        self.output_port.task_mode_changed <<= Select(
            self.input_port.task_mode,
            # In scheduler mode: exit to ask mode, if STM instruction is executed
            (self.input_port.is_branch_insn & (self.input_port.opcode == branch_ops.stm)),
            # In task mode: we enter scheduler mode in case of an exception or interrupt
            is_exception_or_interrupt
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
        self.output_port.ecause_changed <<= is_exception_or_interrupt


def gen():
    def top():
        #return ScanWrapper(ExecuteStage, {"clk", "rst"}, has_multiply=True, has_shift=True)
        return BranchUnit()

    #back_end = SystemVerilog()
    #back_end.yosys_fix = True
    netlist = Build.generate_rtl(top, "exec_branch.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(
        target_dir="q_branch",
        top_level=top_level_name,
        source_files=("exec_branch.sv",),
        clocks=(),
        project_name="branch",
        family="MAX 10",
        device="10M50DAF672C7G" # Something large with a ton of pins
    )
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()

