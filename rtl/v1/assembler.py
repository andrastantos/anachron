"""
Not a full-fledged assembler, but something that makes it slightly more convenient to write test-benches for BREW
"""

from typing import Sequence, Dict
from enum import Enum
from dataclasses import dataclass
from copy import copy

try:
    from .assembler_int import BrewAssembler
except ImportError:
    from assembler_int import BrewAssembler


class RelocTypes(Enum):
    I = 0
    i = 1
    t = 2
    T = 3
    pc_rel = 4

class Segment(object):
    def __init__(self, base_addr = None):
        self.base_addr = base_addr
        self.content = bytearray()

    def set_content(self, addr, value):
        assert addr <= len(self.content)
        assert value >= 0 and value <= 0xff
        if addr == len(self.content):
            self.content.append(value)
        else:
            self.content[addr] = value

    @property
    def size(self) -> int:
        return len(self.content)

@dataclass
class SegAddr(object):
    offset: int
    segment: str

    def abs_addr(self):
        seg = get_segment(self.segment)
        return seg.base_addr+self.offset
    def __add__(self, value: int):
        return SegAddr(self.offset+value, self.segment)
    def __sub__(self, value: int):
        return SegAddr(self.offset-value, self.segment)
    def __rsub__(self, value: int):
        return SegAddr(value-self.offset, self.segment)

@dataclass
class RelocEntry(object):
    symbol: str
    addr: SegAddr
    reloc_type: RelocTypes

_asm = BrewAssembler()
_sym_table = {}
_reloc_table: Sequence[RelocEntry] = []
_segments: Dict[str, Segment] = {}
_dot = None

def clear_asm():
    global _asm, _sym_table, _reloc_table, _segments, _dot
    _asm = BrewAssembler()
    _sym_table = {}
    _reloc_table = []
    _segments = {}
    _dot = None


def get_dot() -> SegAddr:
    return copy(_dot)

def set_dot(new_dot):
    global _dot
    _dot = copy(new_dot)

def get_all_segments():
    return _segments.values()

def get_segment(name):
    return _segments[name]

def create_segment(name, base_addr: int = None):
    assert name not in _segments
    _segments[name] = Segment(base_addr)

def set_active_segment(name: str):
    global _dot
    if name in _segments:
        ofs = _segments[name].size
    else:
        create_segment(name)
        ofs = 0
    _dot = SegAddr(ofs, name)

def set_segment_base(name: str, base_addr: int):
    _segments[name].base_addr = base_addr

def _prog(inst):
    segment = get_segment(_dot.segment)
    for w in inst:
        segment.set_content(_dot.offset+0, (w >> 0) & 0xff)
        segment.set_content(_dot.offset+1, (w >> 8) & 0xff)
        _dot.offset += 2
        if _dot.offset > segment.size: segment.size = _dot.offset

def create_symbol(name: str, value = None):
    assert name not in _sym_table
    _sym_table[name] = value

def set_symbol(name: str, value):
    _sym_table[name] = value

def place_symbol(name):
    if name not in _sym_table: create_symbol(name)
    set_symbol(name, get_dot())

def use_symbol(name: str, for_addr: SegAddr, ref_type: RelocTypes):
    if name not in _sym_table: create_symbol(name)
    _reloc_table.append(RelocEntry(name, for_addr, ref_type))

def reloc():
    for entry in _reloc_table:
        value = _sym_table[entry.symbol]
        if isinstance(value, int):
            abs_value = value
        else:
            abs_value = value.abs_addr()
        if entry.reloc_type == RelocTypes.I:
            #assert abs(abs_value) <= ((1 << 32)-1) and abs_value >= 0
            content = get_segment(entry.addr.segment).content
            for i in range(4):
                content[entry.addr.offset+i] = (abs_value >> (i*8)) & 0xff
        elif entry.reloc_type == RelocTypes.i:
            assert abs(abs_value) <= ((1 << 16-1)-1) or abs_value == -(1 << 16-1)
            content = get_segment(entry.addr.segment).content
            for i in range(2):
                content[entry.addr.offset+i] = (abs_value >> (i*8)) & 0xff
        elif entry.reloc_type == RelocTypes.t:
            assert abs(abs_value) <= 7
            content = get_segment(entry.addr.segment).content
            if abs_value < 0: abs_value = (abs_value&0xf)-1
            content[entry.addr.offset] = content[entry.addr.offset] & 0xf0 | abs_value
        elif entry.reloc_type == RelocTypes.T:
            assert (abs(abs_value) <= ((1 << 9-1)-1) or abs_value == -(1 << 9-1)) and ((abs_value & 3) == 0)
            content = get_segment(entry.addr.segment).content
            content[entry.addr.offset] = content[entry.addr.offset] & 0x01 | abs_value >> 2
        elif entry.reloc_type == RelocTypes.pc_rel:
            if not isinstance(value, int):
                value.segment == entry.addr.segment, "We don't support pc-relative relocations across segments"
                abs_value = value.offset - entry.addr.offset + 2
            else:
                abs_value -= entry.addr.offset + 2
            assert (abs(abs_value) <= ((1 << 17-1)-1) or abs_value == -(1 << 17-1)) and ((abs_value & 1) == 0)
            abs_value = abs_value & 0x1ffff
            # Move bit 17 to bit 0
            abs_value = (abs_value & 0xffff) | (abs_value >> 16)
            content = get_segment(entry.addr.segment).content
            for i in range(2):
                content[entry.addr.offset+i] = (abs_value >> (i*8)) & 0xff
    _reloc_table.clear()

def _t(imm):
    if isinstance(imm, str):
        use_symbol(imm, _dot, RelocTypes.t)
        return 0
    return int(imm)

def _T(imm):
    if isinstance(imm, str):
        use_symbol(imm, _dot, RelocTypes.T)
        return 0
    return int(imm)

def _i(imm):
    if isinstance(imm, str):
        use_symbol(imm, _dot+2, RelocTypes.i)
        return 0
    return int(imm)

def _I(imm):
    if isinstance(imm, str):
        use_symbol(imm, _dot+2, RelocTypes.I)
        return 0
    return int(imm)

def _pc_rel(imm):
    global _dot
    if isinstance(imm, str):
        use_symbol(imm, _dot+2, RelocTypes.pc_rel)
        return 0
    if isinstance(imm,SegAddr):
        assert imm.segment == _dot.segment
        imm = imm.offset
    rel_addr = imm-_dot.offset
    assert(abs(rel_addr) < 0xffff)
    assert(rel_addr & 1 == 0)
    bit_16 = (rel_addr >> 16) & 1
    return (rel_addr & 0xffff) | bit_16

def _r(r:str):
    assert r.startswith("$r")
    return int(r[2:])

def swi( swi): _prog(_asm.swi(swi))
def stm(): _prog(_asm.stm())
def woi(): _prog(_asm.woi())
def sii(): _prog(_asm.sii())
def r_eq_r_xor_r(     rD, rB,  rA):  _prog(_asm.r_eq_r_xor_r(     _r(rD), _r(rB), _r(rA)))
def r_eq_r_or_r(      rD, rB,  rA):  _prog(_asm.r_eq_r_or_r(      _r(rD), _r(rB), _r(rA)))
def r_eq_r_and_r(     rD, rB,  rA):  _prog(_asm.r_eq_r_and_r(     _r(rD), _r(rB), _r(rA)))
def r_eq_r_plus_r(    rD, rB,  rA):  _prog(_asm.r_eq_r_plus_r(    _r(rD), _r(rB), _r(rA)))
def r_eq_r_minus_r(   rD, rB,  rA):  _prog(_asm.r_eq_r_minus_r(   _r(rD), _r(rB), _r(rA)))
def r_eq_r_shl_r(     rD, rB,  rA):  _prog(_asm.r_eq_r_shl_r(     _r(rD), _r(rB), _r(rA)))
def r_eq_r_shr_r(     rD, rB,  rA):  _prog(_asm.r_eq_r_shr_r(     _r(rD), _r(rB), _r(rA)))
def r_eq_r_sar_r(     rD, rB,  rA):  _prog(_asm.r_eq_r_sar_r(     _r(rD), _r(rB), _r(rA)))
def r_eq_r_mul_r(     rD, rB,  rA):  _prog(_asm.r_eq_r_mul_r(     _r(rD), _r(rB), _r(rA)))
def r_eq_r_plus_t(    rD, rB,  imm): _prog(_asm.r_eq_r_plus_t(    _r(rD), _r(rB), _t(imm)))

def r_eq_I_xor_r(   rD, imm, rB): _prog(_asm.r_eq_I_xor_r(   _r(rD), _I(imm), _r(rB)))
def r_eq_I_or_r(    rD, imm, rB): _prog(_asm.r_eq_I_or_r(    _r(rD), _I(imm), _r(rB)))
def r_eq_I_and_r(   rD, imm, rB): _prog(_asm.r_eq_I_and_r(   _r(rD), _I(imm), _r(rB)))
def r_eq_I_plus_r(  rD, imm, rB): _prog(_asm.r_eq_I_plus_r(  _r(rD), _I(imm), _r(rB)))
def r_eq_I_minus_r( rD, imm, rB): _prog(_asm.r_eq_I_minus_r( _r(rD), _I(imm), _r(rB)))
def r_eq_I_shl_r(   rD, imm, rB): _prog(_asm.r_eq_I_shl_r(   _r(rD), _I(imm), _r(rB)))
def r_eq_I_shr_r(   rD, imm, rB): _prog(_asm.r_eq_I_shr_r(   _r(rD), _I(imm), _r(rB)))
def r_eq_I_sar_r(   rD, imm, rB): _prog(_asm.r_eq_I_sar_r(   _r(rD), _I(imm), _r(rB)))
def r_eq_I_mul_r(   rD, imm, rB): _prog(_asm.r_eq_I_mul_r(   _r(rD), _I(imm), _r(rB)))

def r_eq_i_xor_r(   rD, imm, rA ): _prog(_asm.r_eq_i_xor_r(   _r(rD), _i(imm), _r(rA)))
def r_eq_i_or_r(    rD, imm, rA ): _prog(_asm.r_eq_i_or_r(    _r(rD), _i(imm), _r(rA)))
def r_eq_i_and_r(   rD, imm, rA ): _prog(_asm.r_eq_i_and_r(   _r(rD), _i(imm), _r(rA)))
def r_eq_i_plus_r(  rD, imm, rA ): _prog(_asm.r_eq_i_plus_r(  _r(rD), _i(imm), _r(rA)))
def r_eq_r_plus_i(  rD, rA, imm ): _prog(_asm.r_eq_i_plus_r(  _r(rD), _i(imm), _r(rA)))
def r_eq_i_minus_r( rD, imm, rA ): _prog(_asm.r_eq_i_minus_r( _r(rD), _i(imm), _r(rA)))
def r_eq_r_shl_i(   rD, rA , imm): _prog(_asm.r_eq_r_shl_i(   _r(rD), _r(rA), _i(imm)))
def r_eq_r_shr_i(   rD, rA , imm): _prog(_asm.r_eq_r_shr_i(   _r(rD), _r(rA), _i(imm)))
def r_eq_r_sar_i(   rD, rA , imm): _prog(_asm.r_eq_r_sar_i(   _r(rD), _r(rA), _i(imm)))
def r_eq_i_mul_r(   rD, imm, rA ): _prog(_asm.r_eq_i_mul_r(   _r(rD), _i(imm), _r(rA)))

def fence(): _prog(_asm.fence())
def pc_eq_r( rD):  _prog(_asm.pc_eq_r(_r(rD)))
def tpc_eq_r( rD): _prog(_asm.tpc_eq_r(_r(rD)))
def r_eq_pc( rD):  _prog(_asm.r_eq_pc(_r(rD)))
def r_eq_tpc( rD): _prog(_asm.r_eq_tpc(_r(rD)))
def r_eq_t( rD, imm): _prog(_asm.r_eq_t(_r(rD), _t(imm)))
def r_eq_pc_plus_t( rD, imm): _prog(_asm.r_eq_pc_plus_t(_r(rD), _t(imm)))
def r_eq_neg_r( rD, rA): _prog(_asm.r_eq_neg_r(_r(rD), _r(rA)))
def r_eq_not_r( rD, rA): _prog(_asm.r_eq_not_r(_r(rD), _r(rA)))
def r_eq_bse_r( rD, rA): _prog(_asm.r_eq_bse_r(_r(rD), _r(rA)))
def r_eq_wse_r( rD, rA): _prog(_asm.r_eq_wse_r(_r(rD), _r(rA)))

def r_eq_I( rD, imm): _prog(_asm.r_eq_I(_r(rD), _I(imm)))
def pc_eq_I( imm): _prog(_asm.pc_eq_I(_I(imm)))
def tpc_eq_I( imm): _prog(_asm.tpc_eq_I(_I(imm)))
def r_eq_i( rD, imm): _prog(_asm.r_eq_i(_r(rD), _i(imm)))
def pc_eq_i( imm): _prog(_asm.pc_eq_i(_i(imm)))
def tpc_eq_i( imm): _prog(_asm.tpc_eq_i(_i(imm)))
def if_r_eq_z(  rA, imm): _prog(_asm.if_r_eq_z(_r(rA), _pc_rel(imm)))
def if_r_ne_z(  rA, imm): _prog(_asm.if_r_ne_z(_r(rA), _pc_rel(imm)))
def if_r_lts_z( rA, imm): _prog(_asm.if_r_lts_z(_r(rA), _pc_rel(imm)))
def if_r_ges_z( rA, imm): _prog(_asm.if_r_ges_z(_r(rA), _pc_rel(imm)))
def if_r_gts_z( rA, imm): _prog(_asm.if_r_gts_z(_r(rA), _pc_rel(imm)))
def if_r_les_z( rA, imm): _prog(_asm.if_r_les_z(_r(rA), _pc_rel(imm)))
def if_r_eq_r(  rB, rA, imm): _prog(_asm.if_r_eq_r(_r(rB), _r(rA), _pc_rel(imm)))
def if_r_ne_r(  rB, rA, imm): _prog(_asm.if_r_ne_r(_r(rB), _r(rA), _pc_rel(imm)))
def if_r_lts_r( rB, rA, imm): _prog(_asm.if_r_lts_r(_r(rB), _r(rA), _pc_rel(imm)))
def if_r_ges_r( rB, rA, imm): _prog(_asm.if_r_ges_r(_r(rB), _r(rA), _pc_rel(imm)))
def if_r_lt_r(  rB, rA, imm): _prog(_asm.if_r_lt_r(_r(rB), _r(rA), _pc_rel(imm)))
def if_r_ge_r(  rB, rA, imm): _prog(_asm.if_r_ge_r(_r(rB), _r(rA), _pc_rel(imm)))
def if_r_setb(  rA, bit, imm): _prog(_asm.if_r_setb(_r(rA), bit, _pc_rel(imm)))
def if_r_clrb(  rB, bit, imm): _prog(_asm.if_r_clrb(_r(rB), bit, _pc_rel(imm)))

def mem32_r_plus_t_eq_r( rA, imm, rD): _prog(_asm.mem32_r_plus_t_eq_r(_r(rA), _T(imm), _r(rD)))
def r_eq_mem32_r_plus_t( rD, rA, imm): _prog(_asm.r_eq_mem32_r_plus_t(_r(rD), _r(rA), _T(imm)))

def r_eq_mem8_r(    rD, rA): _prog(_asm.r_eq_mem8_r(   _r(rD), _r(rA)))
def r_eq_mem16_r(   rD, rA): _prog(_asm.r_eq_mem16_r(  _r(rD), _r(rA)))
def r_eq_mem32_r(   rD, rA): _prog(_asm.r_eq_mem32_r(  _r(rD), _r(rA)))
def r_eq_memll32_r( rD, rA): _prog(_asm.r_eq_memll32_r(_r(rD), _r(rA)))
def mem8_r_eq_r(    rA, rD): _prog(_asm.mem8_r_eq_r(   _r(rA), _r(rD)))
def mem16_r_eq_r(   rA, rD): _prog(_asm.mem16_r_eq_r(  _r(rA), _r(rD)))
def mem32_r_eq_r(   rA, rD): _prog(_asm.mem32_r_eq_r(  _r(rA), _r(rD)))
def memsr32_r_eq_r( rA, rD): _prog(_asm.memsr32_r_eq_r(_r(rA), _r(rD)))
def r_eq_smem8_r(   rD, rA): _prog(_asm.r_eq_smem8_r(  _r(rD), _r(rA)))
def r_eq_smem16_r(  rD, rA): _prog(_asm.r_eq_smem16_r( _r(rD), _r(rA)))

def r_eq_mem8_r_plus_i(    rD, rA, imm): _prog(_asm.r_eq_mem8_r_plus_i(   _r(rD), _r(rA), _i(imm)))
def r_eq_mem16_r_plus_i(   rD, rA, imm): _prog(_asm.r_eq_mem16_r_plus_i(  _r(rD), _r(rA), _i(imm)))
def r_eq_mem32_r_plus_i(   rD, rA, imm): _prog(_asm.r_eq_mem32_r_plus_i(  _r(rD), _r(rA), _i(imm)))
def r_eq_memll32_r_plus_i( rD, rA, imm): _prog(_asm.r_eq_memll32_r_plus_i(_r(rD), _r(rA), _i(imm)))
def mem8_r_plus_i_eq_r(    rA, imm, rD): _prog(_asm.mem8_r_plus_i_eq_r(   _r(rA), _i(imm), _r(rD)))
def mem16_r_plus_i_eq_r(   rA, imm, rD): _prog(_asm.mem16_r_plus_i_eq_r(  _r(rA), _i(imm), _r(rD)))
def mem32_r_plus_i_eq_r(   rA, imm, rD): _prog(_asm.mem32_r_plus_i_eq_r(  _r(rA), _i(imm), _r(rD)))
def memsr32_r_plus_i_eq_r( rA, imm, rD): _prog(_asm.memsr32_r_plus_i_eq_r(_r(rA), _i(imm), _r(rD)))
def r_eq_smem8_r_plus_i(   rD, rA, imm): _prog(_asm.r_eq_smem8_r_plus_i(  _r(rD), _r(rA), _i(imm)))
def r_eq_smem16_r_plus_i(  rD, rA, imm): _prog(_asm.r_eq_smem16_r_plus_i( _r(rD), _r(rA), _i(imm)))

def r_eq_mem8_I(    rD, imm): _prog(_asm.r_eq_mem8_I(   _r(rD), _I(imm)))
def r_eq_mem16_I(   rD, imm): _prog(_asm.r_eq_mem16_I(  _r(rD), _I(imm)))
def r_eq_mem32_I(   rD, imm): _prog(_asm.r_eq_mem32_I(  _r(rD), _I(imm)))
def r_eq_memll32_I( rD, imm): _prog(_asm.r_eq_memll32_I(_r(rD), _I(imm)))
def mem8_I_eq_r(    imm, rD): _prog(_asm.mem8_I_eq_r(   _I(imm), _r(rD)))
def mem16_I_eq_r(   imm, rD): _prog(_asm.mem16_I_eq_r(  _I(imm), _r(rD)))
def mem32_I_eq_r(   imm, rD): _prog(_asm.mem32_I_eq_r(  _I(imm), _r(rD)))
def memsr32_I_eq_r( imm, rD): _prog(_asm.memsr32_I_eq_r(_I(imm), _r(rD)))
def r_eq_smem8_I(   rD, imm): _prog(_asm.r_eq_smem8_I(  _r(rD), _I(imm)))
def r_eq_smem16_I(  rD, imm): _prog(_asm.r_eq_smem16_I( _r(rD), _I(imm)))

def r_eq_csr( rD, imm): _prog(_asm.r_eq_csr(_r(rD), _I(imm)))
def csr_eq_r(   imm, rD): _prog(_asm.csr_eq_r(  _I(imm), _r(rD)))
