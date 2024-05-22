from typing import Optional
from dataclasses import dataclass, fields
import inspect

try:
    from .brew_types import *
except ImportError:
    from brew_types import *

def fn_name():
    return inspect.currentframe().f_back.f_code.co_name


@dataclass
class ExecExp(object):
    fn_name: str
    exec_unit: Optional[op_class] = None
    alu_op: Optional[alu_ops] = None
    shifter_op: Optional[shifter_ops] = None
    branch_op: Optional[branch_ops] = None
    ldst_op: Optional[ldst_ops] = None
    op_a: Optional[int] = None
    op_b: Optional[int] = None
    op_c: Optional[int] = None
    mem_access_len: Optional[int] = None
    inst_len: Optional[int] = None
    do_bse: Optional[bool] = None
    do_wse: Optional[bool] = None
    do_bze: Optional[bool] = None
    do_wze: Optional[bool] = None
    result_reg_addr: Optional[int] = None
    result_reg_addr_valid: Optional[bool] = None
    fetch_av: Optional[bool] = None

    def check_member(self, actual: Wire, element_name: str, simulator: Simulator):
        ref_elem = getattr(self, element_name)
        act_elem = getattr(actual, element_name)
        simulator.sim_assert(ref_elem is None or ref_elem == act_elem, f"expected {element_name}: {ref_elem}, actual: {act_elem}")

    def check(self, actual: Wire, simulator: Simulator):
        for field in fields(self):
            if field.name not in {"fn_name",}:
                self.check_member(actual, field.name, simulator)

class DecodeExpectations(object):
    def swi(self, swi = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def stm(self): ExecExp(fn_name(), exec_unit=op_class.branch)
    def woi(self): ExecExp(fn_name(), exec_unit=op_class.alu)
    def sii(self): ExecExp(fn_name(), exec_unit=op_class.branch)
    def r_eq_r_xor_r(self,     rD = None, rA = None,  rB = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_r_or_r(self,      rD = None, rA = None,  rB = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_r_and_r(self,     rD = None, rA = None,  rB = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_r_plus_r(self,    rD = None, rA = None,  rB = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_r_minus_r(self,   rD = None, rA = None,  rB = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_r_shl_r(self,     rD = None, rA = None,  rB = None): return ExecExp(fn_name(), exec_unit=op_class.shift)
    def r_eq_r_shr_r(self,     rD = None, rA = None,  rB = None): return ExecExp(fn_name(), exec_unit=op_class.shift)
    def r_eq_r_sar_r(self,     rD = None, rA = None,  rB = None): return ExecExp(fn_name(), exec_unit=op_class.shift)
    def r_eq_r_mul_r(self,     rD = None, rA = None,  rB = None): return ExecExp(fn_name(), exec_unit=op_class.mult)
    def r_eq_r_plus_t(self,    rD = None, rB = None,  imm = None): return ExecExp(fn_name(), exec_unit=op_class.alu)

    def r_eq_I_xor_r(self,   rD = None, imm = None, rB = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_I_or_r(self,    rD = None, imm = None, rB = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_I_and_r(self,   rD = None, imm = None, rB = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_I_plus_r(self,  rD = None, imm = None, rB = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_I_minus_r(self, rD = None, imm = None, rB = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_I_shl_r(self,   rD = None, imm = None, rB = None): return ExecExp(fn_name(), exec_unit=op_class.shift)
    def r_eq_I_shr_r(self,   rD = None, imm = None, rB = None): return ExecExp(fn_name(), exec_unit=op_class.shift)
    def r_eq_I_sar_r(self,   rD = None, imm = None, rB = None): return ExecExp(fn_name(), exec_unit=op_class.shift)
    def r_eq_I_mul_r(self,   rD = None, imm = None, rB = None): return ExecExp(fn_name(), exec_unit=op_class.mult)

    def r_eq_i_xor_r(self,   rD = None, imm = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_i_or_r(self,    rD = None, imm = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_i_and_r(self,   rD = None, imm = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_i_plus_r(self,  rD = None, imm = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_i_minus_r(self, rD = None, imm = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_i_shl_r(self,   rD = None, imm = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.shift)
    def r_eq_i_shr_r(self,   rD = None, imm = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.shift)
    def r_eq_i_sar_r(self,   rD = None, imm = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.shift)
    def r_eq_i_mul_r(self,   rD = None, imm = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.mult)

    def fence(self): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def pc_eq_r(self, rD = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def tpc_eq_r(self, rD = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def r_eq_pc(self, rD = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_tpc(self, rD = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_t(self, rD = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_pc_plus_t(self, rD = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_neg_r(self, rD = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_not_r(self, rD = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_bse_r(self, rD = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def r_eq_wse_r(self, rD = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.alu)

    def r_eq_I(self, rD = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def pc_eq_I(self, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def tpc_eq_I(self, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def r_eq_i(self, rD = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.alu)
    def pc_eq_i(self, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def tpc_eq_i(self, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_eq_z(self,  rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_ne_z(self,  rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_lts_z(self, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_ges_z(self, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_gts_z(self, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_les_z(self, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_eq_r(self,  rB = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_ne_r(self,  rB = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_lts_r(self, rB = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_ges_r(self, rB = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_lt_r(self,  rB = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_ge_r(self,  rB = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_setb(self,  rA = None, bit = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)
    def if_r_clrb(self,  rB = None, bit = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.branch)

    def mem32_r_plus_t_eq_r(self, rA = None, imm = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_mem32_r_plus_t(self, rD = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_mem8_r(self, rD = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_mem16_r(self, rD = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_mem32_r(self, rD = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_memll32_r(self, rD = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def mem8_r_eq_r(self, rA = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def mem16_r_eq_r(self, rA = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def mem32_r_eq_r(self, rA = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def memsr32_r_eq_r(self, rA = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_smem8_r(self, rD = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_smem16_r(self, rD = None, rA = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)

    def r_eq_mem8_r_plus_i(self, rD = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_mem16_r_plus_i(self, rD = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_mem32_r_plus_i(self, rD = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_memll32_r_plus_i(self, rD = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def mem8_r_plus_i_eq_r(self, rA = None, imm = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def mem16_r_plus_i_eq_r(self, rA = None, imm = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def mem32_r_plus_i_eq_r(self, rA = None, imm = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def memsr32_r_plus_i_eq_r(self, rA = None, imm = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_smem8_r_plus_i(self, rD = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_smem16_r_plus_i(self, rD = None, rA = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)

    def r_eq_mem8_I(self, rD = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_mem16_I(self, rD = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_mem32_I(self, rD = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_memll32_I(self, rD = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def mem8_I_eq_r(self, imm = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def mem16_I_eq_r(self, imm = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def mem32_I_eq_r(self, imm = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def memsr32_I_eq_r(self, imm = None, rD = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_smem8_I(self, rD = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
    def r_eq_smem16_I(self, rD = None, imm = None): return ExecExp(fn_name(), exec_unit=op_class.ld_st)
