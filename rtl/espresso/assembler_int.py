"""
Internals for a better assembler
"""

from typing import Optional
from random import randint
from dataclasses import dataclass, fields

try:
    from .brew_types import *
except ImportError:
    from brew_types import *


def _r(reg):
    if reg is None: reg = randint(0,14)
    assert reg >= 0 and reg <= 14
    return reg

def _i(imm):
    if imm is None: imm = randint(0, 0xffff)
    return (imm, )

def _I(imm):
    if imm is None: imm = randint(0, 0xffffffff)
    return (imm & 0xffff, (imm >> 16) & 0xffff)

def _t(imm):
    if imm is None: imm = randint(-7, 7)
    if imm < 0: imm -= 1
    return imm & 0xf

def _inst(field_d, field_c, field_b, field_a):
    for f in (field_d, field_c, field_b, field_a): assert f >= 0 and f <= 0xf
    return (field_d << 12) | (field_c << 8) | (field_b << 4) | field_a

def _b(bit):
    if bit is None: return randint(0,14)
    return {
         0: 0x0,
         1: 0x1,
         2: 0x2,
         3: 0x3,
         4: 0x4,
         5: 0x5,
         6: 0x6,
         7: 0x7,
         8: 0x8,
         9: 0x9,
        14: 0xa,
        15: 0xb,
        16: 0xc,
        30: 0xd,
        31: 0xe,
    }[bit]

def _T(imm):
    if imm is None: imm = randint(-64, 63) << 2
    assert imm <= 63*4 and imm >= -64*4
    assert imm & 3 == 0
    return imm >> 2


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

import inspect

def fn_name():
    return inspect.currentframe().f_back.f_code.co_name

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

class BrewAssembler(object):
    def swi(self, swi = None): return (_inst(swi & 7 if swi is not None else randint(0,7), 0x0, 0x0, 0x0),)
    def stm(self): return (0x8000,)
    def woi(self): return (0x9000,)
    def sii(self): return (0xa000,)
    def r_eq_r_xor_r(self,     rD = None, rA = None,  rB = None): return (_inst(_r(rD), 0x1, _r(rB), _r(rA)), )
    def r_eq_r_or_r(self,      rD = None, rA = None,  rB = None): return (_inst(_r(rD), 0x2, _r(rB), _r(rA)), )
    def r_eq_r_and_r(self,     rD = None, rA = None,  rB = None): return (_inst(_r(rD), 0x3, _r(rB), _r(rA)), )
    def r_eq_r_plus_r(self,    rD = None, rA = None,  rB = None): return (_inst(_r(rD), 0x4, _r(rB), _r(rA)), )
    def r_eq_r_minus_r(self,   rD = None, rA = None,  rB = None): return (_inst(_r(rD), 0x5, _r(rB), _r(rA)), )
    def r_eq_r_shl_r(self,     rD = None, rA = None,  rB = None): return (_inst(_r(rD), 0x6, _r(rB), _r(rA)), )
    def r_eq_r_shr_r(self,     rD = None, rA = None,  rB = None): return (_inst(_r(rD), 0x7, _r(rB), _r(rA)), )
    def r_eq_r_sar_r(self,     rD = None, rA = None,  rB = None): return (_inst(_r(rD), 0x8, _r(rB), _r(rA)), )
    def r_eq_r_mul_r(self,     rD = None, rA = None,  rB = None): return (_inst(_r(rD), 0x9, _r(rB), _r(rA)), )
    def r_eq_r_plus_t(self,    rD = None, rB = None,  imm = None): return (_inst(_r(rD), 0xb, _r(rB), _t(imm)), )

    def r_eq_I_xor_r(self,   rD = None, imm = None, rB = None): return (_inst(_r(rD), 0x1, _r(rB), 0xf), *_I(imm),)
    def r_eq_I_or_r(self,    rD = None, imm = None, rB = None): return (_inst(_r(rD), 0x2, _r(rB), 0xf), *_I(imm),)
    def r_eq_I_and_r(self,   rD = None, imm = None, rB = None): return (_inst(_r(rD), 0x3, _r(rB), 0xf), *_I(imm),)
    def r_eq_I_plus_r(self,  rD = None, imm = None, rB = None): return (_inst(_r(rD), 0x4, _r(rB), 0xf), *_I(imm),)
    def r_eq_I_minus_r(self, rD = None, imm = None, rB = None): return (_inst(_r(rD), 0x5, _r(rB), 0xf), *_I(imm),)
    def r_eq_I_shl_r(self,   rD = None, imm = None, rB = None): return (_inst(_r(rD), 0x6, _r(rB), 0xf), *_I(imm),)
    def r_eq_I_shr_r(self,   rD = None, imm = None, rB = None): return (_inst(_r(rD), 0x7, _r(rB), 0xf), *_I(imm),)
    def r_eq_I_sar_r(self,   rD = None, imm = None, rB = None): return (_inst(_r(rD), 0x8, _r(rB), 0xf), *_I(imm),)
    def r_eq_I_mul_r(self,   rD = None, imm = None, rB = None): return (_inst(_r(rD), 0x9, _r(rB), 0xf), *_I(imm),)

    def r_eq_i_xor_r(self,   rD = None, imm = None, rA = None): return (_inst(_r(rD), 0x1, 0xf, _r(rA)), *_i(imm),)
    def r_eq_i_or_r(self,    rD = None, imm = None, rA = None): return (_inst(_r(rD), 0x2, 0xf, _r(rA)), *_i(imm),)
    def r_eq_i_and_r(self,   rD = None, imm = None, rA = None): return (_inst(_r(rD), 0x3, 0xf, _r(rA)), *_i(imm),)
    def r_eq_i_plus_r(self,  rD = None, imm = None, rA = None): return (_inst(_r(rD), 0x4, 0xf, _r(rA)), *_i(imm),)
    def r_eq_i_minus_r(self, rD = None, imm = None, rA = None): return (_inst(_r(rD), 0x5, 0xf, _r(rA)), *_i(imm),)
    def r_eq_r_shl_i(self,   rD = None, rA = None, imm = None): return (_inst(_r(rD), 0x6, 0xf, _r(rA)), *_i(imm),)
    def r_eq_r_shr_i(self,   rD = None, rA = None, imm = None): return (_inst(_r(rD), 0x7, 0xf, _r(rA)), *_i(imm),)
    def r_eq_r_sar_i(self,   rD = None, rA = None, imm = None): return (_inst(_r(rD), 0x8, 0xf, _r(rA)), *_i(imm),)
    def r_eq_i_mul_r(self,   rD = None, imm = None, rA = None): return (_inst(_r(rD), 0x9, 0xf, _r(rA)), *_i(imm),)

    def fence(self): return (0x0001,)
    def pc_eq_r(self, rD = None): return (_inst(_r(rD), 0x0, 0x0, 0x2),)
    def tpc_eq_r(self, rD = None): return (_inst(_r(rD), 0x0, 0x0, 0x3),)
    def r_eq_pc(self, rD = None): return (_inst(_r(rD), 0x0, 0x0, 0x4),)
    def r_eq_tpc(self, rD = None): return (_inst(_r(rD), 0x0, 0x0, 0x5),)
    def r_eq_t(self, rD = None, imm = None): return (_inst(_r(rD), 0x0, 0x1, _t(imm)),)
    def r_eq_pc_plus_t(self, rD = None, imm = None): return (_inst(_r(rD), 0x0, 0x2, _t(imm)),)
    def r_eq_neg_r(self, rD = None, rA = None): return (_inst(_r(rD), 0x0, 0x3, _r(rA)),)
    def r_eq_not_r(self, rD = None, rA = None): return (_inst(_r(rD), 0x0, 0x4, _r(rA)),)
    def r_eq_bse_r(self, rD = None, rA = None): return (_inst(_r(rD), 0x0, 0x5, _r(rA)),)
    def r_eq_wse_r(self, rD = None, rA = None): return (_inst(_r(rD), 0x0, 0x6, _r(rA)),)

    def r_eq_I(self, rD = None, imm = None): return (_inst(_r(rD), 0x0, 0x0, 0xf), *_I(imm))
    def pc_eq_I(self, imm = None): return (_inst(0x2, 0x0, 0xe, 0xf), *_I(imm))
    def tpc_eq_I(self, imm = None): return (_inst(0x3, 0x0, 0xe, 0xf), *_I(imm))
    def r_eq_i(self, rD = None, imm = None): return (_inst(_r(rD), 0x0, 0xf, 0x0), *_i(imm))
    def pc_eq_i(self, imm = None): return (_inst(0x2, 0x0, 0xf, 0xe), *_i(imm))
    def tpc_eq_i(self, imm = None): return (_inst(0x3, 0x0, 0xf, 0xe), *_i(imm))
    def if_r_eq_z(self,  rA = None, imm = None): return (_inst(0xf, 0x0, 0x0, _r(rA)), *_i(imm))
    def if_r_ne_z(self,  rA = None, imm = None): return (_inst(0xf, 0x0, 0x1, _r(rA)), *_i(imm))
    def if_r_lts_z(self, rA = None, imm = None): return (_inst(0xf, 0x0, 0x2, _r(rA)), *_i(imm))
    def if_r_ges_z(self, rA = None, imm = None): return (_inst(0xf, 0x0, 0x3, _r(rA)), *_i(imm))
    def if_r_gts_z(self, rA = None, imm = None): return (_inst(0xf, 0x0, 0x4, _r(rA)), *_i(imm))
    def if_r_les_z(self, rA = None, imm = None): return (_inst(0xf, 0x0, 0x5, _r(rA)), *_i(imm))
    def if_r_eq_r(self,  rB = None, rA = None, imm = None): return (_inst(0xf, 0x1, _r(rB), _r(rA)), *_i(imm))
    def if_r_ne_r(self,  rB = None, rA = None, imm = None): return (_inst(0xf, 0x2, _r(rB), _r(rA)), *_i(imm))
    def if_r_lts_r(self, rB = None, rA = None, imm = None): return (_inst(0xf, 0x3, _r(rB), _r(rA)), *_i(imm))
    def if_r_ges_r(self, rB = None, rA = None, imm = None): return (_inst(0xf, 0x4, _r(rB), _r(rA)), *_i(imm))
    def if_r_lt_r(self,  rB = None, rA = None, imm = None): return (_inst(0xf, 0x5, _r(rB), _r(rA)), *_i(imm))
    def if_r_ge_r(self,  rB = None, rA = None, imm = None): return (_inst(0xf, 0x6, _r(rB), _r(rA)), *_i(imm))
    def if_r_setb(self,  rA = None, bit = None, imm = None): return (_inst(0xf, _b(bit), 0xf, _r(rA)), *_i(imm))
    def if_r_clrb(self,  rB = None, bit = None, imm = None): return (_inst(0xf, _b(bit), _r(rB), 0xf), *_i(imm))

    def mem32_r_plus_t_eq_r(self, rA = None, imm = None, rD = None):
        if rA is None: rA = randint(0,1) + 12
        assert rA in (12,13)
        field_ba = (_T(imm) << 1 | (rA & 1)) & 0xff
        return (_inst(_r(rD), 0xc, (field_ba >> 4) & 0xf, field_ba & 0xf),)
    def r_eq_mem32_r_plus_t(self, rD = None, rA = None, imm = None):
        if rA is None: rA = randint(0,1) + 12
        assert rA in (12,13)
        field_ba = (_T(imm) << 1 | (rA & 1)) & 0xff
        return (_inst(_r(rD), 0xd, (field_ba >> 4) & 0xf, field_ba & 0xf),)
    def r_eq_mem8_r(self, rD = None, rA = None): return (_inst(_r(rD), 0xe, 0x4, _r(rA)),)
    def r_eq_mem16_r(self, rD = None, rA = None): return (_inst(_r(rD), 0xe, 0x5, _r(rA)),)
    def r_eq_mem32_r(self, rD = None, rA = None): return (_inst(_r(rD), 0xe, 0x6, _r(rA)),)
    def r_eq_memll32_r(self, rD = None, rA = None): return (_inst(_r(rD), 0xe, 0x7, _r(rA)),)
    def mem8_r_eq_r(self, rA = None, rD = None): return (_inst(_r(rD), 0xe, 0x8, _r(rA)),)
    def mem16_r_eq_r(self, rA = None, rD = None): return (_inst(_r(rD), 0xe, 0x9, _r(rA)),)
    def mem32_r_eq_r(self, rA = None, rD = None): return (_inst(_r(rD), 0xe, 0xa, _r(rA)),)
    def memsr32_r_eq_r(self, rA = None, rD = None): return (_inst(_r(rD), 0xe, 0xb, _r(rA)),)
    def r_eq_smem8_r(self, rD = None, rA = None): return (_inst(_r(rD), 0xe, 0xc, _r(rA)),)
    def r_eq_smem16_r(self, rD = None, rA = None): return (_inst(_r(rD), 0xe, 0xd, _r(rA)),)

    def r_eq_mem8_r_plus_i(self, rD = None, rA = None, imm = None): return (_inst(_r(rD), 0xf, 0x4, _r(rA)), *_i(imm))
    def r_eq_mem16_r_plus_i(self, rD = None, rA = None, imm = None): return (_inst(_r(rD), 0xf, 0x5, _r(rA)), *_i(imm))
    def r_eq_mem32_r_plus_i(self, rD = None, rA = None, imm = None): return (_inst(_r(rD), 0xf, 0x6, _r(rA)), *_i(imm))
    def r_eq_memll32_r_plus_i(self, rD = None, rA = None, imm = None): return (_inst(_r(rD), 0xf, 0x7, _r(rA)), *_i(imm))
    def mem8_r_plus_i_eq_r(self, rA = None, imm = None, rD = None): return (_inst(_r(rD), 0xf, 0x8, _r(rA)), *_i(imm))
    def mem16_r_plus_i_eq_r(self, rA = None, imm = None, rD = None): return (_inst(_r(rD), 0xf, 0x9, _r(rA)), *_i(imm))
    def mem32_r_plus_i_eq_r(self, rA = None, imm = None, rD = None): return (_inst(_r(rD), 0xf, 0xa, _r(rA)), *_i(imm))
    def memsr32_r_plus_i_eq_r(self, rA = None, imm = None, rD = None): return (_inst(_r(rD), 0xf, 0xb, _r(rA)), *_i(imm))
    def r_eq_smem8_r_plus_i(self, rD = None, rA = None, imm = None): return (_inst(_r(rD), 0xf, 0xc, _r(rA)), *_i(imm))
    def r_eq_smem16_r_plus_i(self, rD = None, rA = None, imm = None): return (_inst(_r(rD), 0xf, 0xd, _r(rA)), *_i(imm))

    def r_eq_mem8_I(self, rD = None, imm = None): return (_inst(_r(rD), 0xf, 0x4, 0xf), *_I(imm))
    def r_eq_mem16_I(self, rD = None, imm = None): return (_inst(_r(rD), 0xf, 0x5, 0xf), *_I(imm))
    def r_eq_mem32_I(self, rD = None, imm = None): return (_inst(_r(rD), 0xf, 0x6, 0xf), *_I(imm))
    def r_eq_memll32_I(self, rD = None, imm = None): return (_inst(_r(rD), 0xf, 0x7, 0xf), *_I(imm))
    def mem8_I_eq_r(self, imm = None, rD = None): return (_inst(_r(rD), 0xf, 0x8, 0xf), *_I(imm))
    def mem16_I_eq_r(self, imm = None, rD = None): return (_inst(_r(rD), 0xf, 0x9, 0xf), *_I(imm))
    def mem32_I_eq_r(self, imm = None, rD = None): return (_inst(_r(rD), 0xf, 0xa, 0xf), *_I(imm))
    def memsr32_I_eq_r(self, imm = None, rD = None): return (_inst(_r(rD), 0xf, 0xb, 0xf), *_I(imm))
    def r_eq_smem8_I(self, rD = None, imm = None): return (_inst(_r(rD), 0xf, 0xc, 0xf), *_I(imm))
    def r_eq_smem16_I(self, rD = None, imm = None): return (_inst(_r(rD), 0xf, 0xd, 0xf), *_I(imm))


    def r_eq_csr(self, rD = None, imm = None): return (_inst(_r(rD), 0x0, 0xf, 0x8), *_i(imm))
    def csr_eq_r(self, imm = None, rD = None): return (_inst(_r(rD), 0x0, 0xf, 0x9), *_i(imm))
