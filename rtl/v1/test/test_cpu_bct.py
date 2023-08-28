#!/usr/bin/python3
# Basic confidence tests for the Brew V1 CPU
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / ".." / "silicon"))
sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / ".." / "silicon" / "unit_tests"))
#sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / ".." ))
sys.path.append(str(Path(__file__).parent / ".." ))

from brew_v1 import BrewV1Top
from brew_types import *
from assembler import *
from silicon import *
try:
    from .utils import *
    from .rig import *
except ImportError:
    from utils import *
    from rig import *

@prog_wrapper
def test_1(top):
    """
    This test loads a few registers, then jumps to a zero-wait-state ROM address, but continues executing from the same physical location.
    It then loads a few more registers before terminating. This test is not self-checking, the log should be diffed for catching regressions.
    """

    create_segment("code", 0)
    create_segment("code0", 0x1000_0000)
    set_active_segment("code0")
    place_symbol("code0_start")
    set_active_segment("code")

    r_eq_t("$r0",0)
    r_eq_r_plus_t("$r1","$r0",1)
    r_eq_r_plus_t("$r2","$r0",2)
    r_eq_r_plus_t("$r3","$r0",3)
    r_eq_r_plus_t("$r4","$r0",4)
    r_eq_r_plus_t("$r5","$r0",5)
    r_eq_r_plus_r("$r6","$r5","$r1")
    r_eq_r_plus_r("$r7","$r5","$r2")
    pc_eq_I(get_dot().offset+0x1000_0000+6) # Setting internal wait-states to 0, but otherwise continue execution
    r_eq_r_plus_r("$r8","$r5","$r3")
    r_eq_r_plus_r("$r9","$r5","$r4")
    r_eq_r_plus_r("$r10","$r5","$r5")
    r_eq_r_plus_r("$r11","$r6","$r5")
    r_eq_I("$r12",12)
    r_eq_r_plus_r("$r13","$r7","$r6")
    r_eq_r_plus_r("$r14","$r7","$r7")
    # Some loads and stores to test timing
    r_eq_I("$r4", 0x1234_5678)
    mem8_I_eq_r(0x1000_0100, "$r4")
    mem16_I_eq_r(0x1000_0200, "$r4")
    mem32_I_eq_r(0x1000_0300, "$r4")
    terminate()


@prog_wrapper
def test_2(top):
    """
    This test jumps to DRAM right out of reset, loads the registers, tests them and terminates
    """

    top.set_timeout(3000)

    create_segment("code", 0)
    create_segment("code_dram", 0x800_0000)
    set_active_segment("code_dram")
    place_symbol("_start")
    set_active_segment("code")

    pc_eq_I("_start")

    set_active_segment("code_dram")
    r_eq_t("$r0",0)
    r_eq_r_plus_t("$r1","$r0",1)
    r_eq_r_plus_t("$r2","$r0",2)
    r_eq_r_plus_t("$r3","$r0",3)
    r_eq_r_plus_t("$r4","$r0",4)
    r_eq_r_plus_t("$r5","$r0",5)
    r_eq_r_plus_r("$r6","$r5","$r1")
    r_eq_r_plus_r("$r7","$r5","$r2")
    r_eq_r_plus_r("$r8","$r5","$r3")
    r_eq_r_plus_r("$r9","$r5","$r4")
    r_eq_r_plus_r("$r10","$r5","$r5")
    r_eq_r_plus_r("$r11","$r6","$r5")
    r_eq_I("$r12",12)
    r_eq_r_plus_r("$r13","$r7","$r6")
    r_eq_r_plus_r("$r14","$r7","$r7")
    for i in range(14):
        check_reg(f"$r{i}", i)
    terminate()


@prog_wrapper
def test_3(top):
    """
    This test jumps to DRAM right out of reset, then loads a few registers, and a few loads and stores before entering an endless loop.
    """

    create_segment("code", 0)
    create_segment("code_dram", 0x800_0000)
    set_active_segment("code_dram")
    place_symbol("_start")
    set_active_segment("code")

    pc_eq_I("_start")

    set_active_segment("code_dram")
    r_eq_I("$r13",0xdeadbeef)
    r_eq_I("$r14",0x12345678)
    mem32_I_eq_r(0x0800_1000,"$r14")
    r_eq_r_plus_t("$r14","$r14",5)
    r_eq_mem32_I("$r13",0x0800_1000)

    check_reg("$r13", 0x12345678)
    check_reg("$r14", 0x12345678+5)
    terminate()


@prog_wrapper
def test_4(top):
    """
    Test jumping to task mode, then back to scheduler mode due to a fetch AV
    """

    top.set_timeout(3000)

    create_segment("code", 0)
    create_segment("code_dram", 0x800_0000)
    create_segment("code_task", 0x800_1000)
    set_active_segment("code_dram")
    place_symbol("_start")
    set_active_segment("code_task")
    place_symbol("_task_start")
    set_active_segment("code")

    pc_eq_I("_start")

    set_active_segment("code_dram")
    r_eq_t("$r0",0)
    r_eq_r_plus_t("$r1","$r0",1)
    r_eq_r_plus_t("$r2","$r0",2)
    r_eq_r_plus_t("$r3","$r0",3)
    r_eq_r_plus_t("$r4","$r0",4)
    r_eq_r_plus_t("$r5","$r0",5)
    r_eq_r_plus_r("$r6","$r5","$r1")
    r_eq_r_plus_r("$r7","$r5","$r2")
    r_eq_r_plus_r("$r8","$r5","$r3")
    r_eq_r_plus_r("$r9","$r5","$r4")
    r_eq_r_plus_r("$r10","$r5","$r5")
    r_eq_r_plus_r("$r11","$r6","$r5")
    r_eq_I("$r12",12)
    r_eq_r_plus_r("$r13","$r7","$r6")
    r_eq_r_plus_r("$r14","$r7","$r7")

    place_symbol("spc_loop")
    tpc_eq_I("_task_start")
    r_eq_r_plus_t("$r5","$r5",-1)
    stm()
    if_r_ne_z("$r5", "spc_loop")
    r_eq_r_plus_t("$r0","$r0",1)

    check_reg("$r0",   1)
    check_reg("$r1",   1)
    check_reg("$r2",   2)
    check_reg("$r3",   3)
    check_reg("$r4",   4)
    check_reg("$r5",   0)
    check_reg("$r6",   6)
    check_reg("$r7",   7)
    check_reg("$r8",   8)
    check_reg("$r9",   9)
    check_reg("$r10", 10)
    check_reg("$r11", 11)
    check_reg("$r12", 12)
    check_reg("$r13", 13)
    check_reg("$r14", 14)
    terminate()

    set_active_segment("code_task")
    r_eq_r_plus_t("$r2","$r2",1)
    pc_eq_I("_task_start")


@prog_wrapper
def test_5(top):
    """
    Test jumping back and forth between task and system mode, no exceptions thrown
    """

    top.set_timeout(3000)

    create_segment("code", 0)
    create_segment("code_dram", 0x800_0000)
    create_segment("code_task", 0x800_1000)
    set_active_segment("code_dram")
    place_symbol("_start")
    set_active_segment("code_task")
    place_symbol("_task_start")
    set_active_segment("code")

    pc_eq_I("_start")

    set_active_segment("code_dram")
    r_eq_t("$r0",0)
    r_eq_r_plus_t("$r1","$r0",1)
    r_eq_r_plus_t("$r2","$r0",2)
    r_eq_r_plus_t("$r3","$r0",3)
    r_eq_r_plus_t("$r4","$r0",4)
    r_eq_r_plus_t("$r5","$r0",5)
    r_eq_r_plus_r("$r6","$r5","$r1")
    r_eq_r_plus_r("$r7","$r5","$r2")
    r_eq_r_plus_r("$r8","$r5","$r3")
    r_eq_r_plus_r("$r9","$r5","$r4")
    r_eq_r_plus_r("$r10","$r5","$r5")
    r_eq_r_plus_r("$r11","$r6","$r5")
    r_eq_I("$r12",12)
    r_eq_r_plus_r("$r13","$r7","$r6")
    r_eq_r_plus_r("$r14","$r7","$r7")

    r_eq_I("$r0",0xffffffff)
    csr_eq_r(top.cpu.csr_pmem_limit_reg,"$r0")
    csr_eq_r(top.cpu.csr_dmem_limit_reg,"$r0")
    r_eq_t("$r0",0)
    csr_eq_r(top.cpu.csr_pmem_base_reg,"$r0")
    csr_eq_r(top.cpu.csr_dmem_base_reg,"$r0")
    tpc_eq_I("_task_start")

    # Scheduler mode loop: decrementing $r5
    place_symbol("spc_loop")
    r_eq_r_plus_t("$r5","$r5",-1)
    stm()
    r_eq_tpc("$r10") # Adjust $tpc to be over the SWI instruction
    r_eq_r_plus_t("$r10","$r10",2)
    tpc_eq_r("$r10")
    if_r_ne_z("$r5", "spc_loop")
    r_eq_r_plus_t("$r0","$r0",1)

    check_reg("$r0",   1)
    check_reg("$r1",   1)
    check_reg("$r2",   2)
    check_reg("$r3",   3)
    check_reg("$r4",   4)
    check_reg("$r5",   0)
    check_reg("$r6",   1)
    check_reg("$r7",   3)
    check_reg("$r8",   8)
    check_reg("$r9",   9)
    #check_reg("$r10", 10)
    check_reg("$r11", 11)
    check_reg("$r12", 12)
    check_reg("$r13", 13)
    check_reg("$r14", 14)
    terminate()


    # Task mode loop: decrementing $r6 and $r7
    set_active_segment("code_task")
    r_eq_r_plus_t("$r6","$r6",-1)
    swi(3)
    r_eq_r_plus_t("$r7","$r7",-1)
    pc_eq_I("_task_start")
    r_eq_r_plus_t("$r1","$r1",1)

#@prog_wrapper
#def test_6(top):
#    """
#    Test conditional branches.
#    """
#    #nonlocal pc
#    #nonlocal top_inst
#    pc = 0
#    task_start = 0x8000_1000
#    prog(a.pc_eq_I(0x800_0000)) # Jumping to DRAM
#    pc = 0x800_0000
#    prog(a.r_eq_t(0,0))
#    prog(a.r_eq_r_plus_t(1,0,1))
#    prog(a.r_eq_r_plus_t(2,0,2))
#    prog(a.r_eq_r_plus_t(3,0,3))
#    prog(a.r_eq_r_plus_t(4,0,4))
#    prog(a.r_eq_r_plus_t(5,0,5))
#    prog(a.r_eq_r_plus_r(6,5,1))
#    prog(a.r_eq_r_plus_r(7,5,2))
#    prog(a.r_eq_r_plus_r(8,5,3))
#    prog(a.r_eq_r_plus_r(9,5,4))
#    prog(a.r_eq_r_plus_r(10,5,5))
#    prog(a.r_eq_r_plus_r(11,6,5))
#    prog(a.r_eq_I(12,12))
#    prog(a.r_eq_r_plus_r(11,6,5))
#    prog(a.r_eq_r_plus_r(12,6,6))
#    prog(a.r_eq_r_plus_r(13,7,6))
#    prog(a.r_eq_r_plus_r(14,7,7))
#    check_reg(10,10)
#    prog(a.r_eq_mem32_I(0,0x800_0000))
#    prog(a.mem32_I_eq_r(0x800_0800,14))
#    loop = pc
#    prog(a.r_eq_r_minus_r(4,4,1))
#    prog(a.if_r_ne_z(4,pc_rel(loop)))
#    loop = pc
#    prog(a.r_eq_r_plus_t(4,4,1))
#    prog(a.if_r_ne_r(4,5,pc_rel(loop)))
#    terminate()
#    loop = pc
#    prog(a.pc_eq_I(loop))



@prog_wrapper
def test_framework(top):
    """
    Test register-to-register ALU operations
    """

    top.set_timeout(3000)

    startup()
    check()
    terminate()

@prog_wrapper
def test_alu_rr(top):
    """
    Test register-to-register ALU operations
    """

    top.set_timeout(6000)

    startup()
    load_reg("$r3", 0xff00f0f0)
    load_reg("$r4", 0x0f0f00ff)
    r[5] = (r[3] ^ r[4]) & 0xffffffff
    r[6] = (r[3] | r[4]) & 0xffffffff
    r[7] = (r[3] & r[4]) & 0xffffffff
    r[8] = (r[3] + r[4]) & 0xffffffff
    r[9] = (r[3] - r[4]) & 0xffffffff
    r[10] = shl(r[3], r[2])
    r[11] = shr(r[3], r[2])
    r[12] = sar(r[3], r[2])
    r[13] = (r[3] * r[4]) & 0xffffffff
    r_eq_r_xor_r("$r5", "$r3", "$r4")
    r_eq_r_or_r("$r6", "$r3", "$r4")
    r_eq_r_and_r("$r7", "$r3", "$r4")
    r_eq_r_plus_r("$r8", "$r3", "$r4")
    r_eq_r_minus_r("$r9", "$r3", "$r4")
    r_eq_r_shl_r("$r10", "$r3", "$r2")
    r_eq_r_shr_r("$r11", "$r3", "$r2")
    r_eq_r_sar_r("$r12", "$r3", "$r2")
    r_eq_r_mul_r("$r13", "$r3", "$r4")

    check()
    terminate()

@prog_wrapper
def test_alu_Ir(top):
    """
    Test long immediate-to-register ALU operations
    """

    top.set_timeout(6000)

    startup()
    load_reg("$r4", 0xff00f0f0)
    i1 = 0x0f0f00ff
    r[5] = (r[4] ^ i1) & 0xffffffff
    r[6] = (r[4] | i1) & 0xffffffff
    r[7] = (r[4] & i1) & 0xffffffff
    r[8] = (r[4] + i1) & 0xffffffff
    r[9] = (i1 - r[4]) & 0xffffffff
    r[10] = shl(i1, r[4])
    r[11] = shr(i1, r[4])
    r[12] = sar(i1, r[4])
    r[13] = (r[4] * i1) & 0xffffffff

    r_eq_I_xor_r("$r5", i1, "$r4")
    r_eq_I_or_r("$r6", i1, "$r4")
    r_eq_I_and_r("$r7", i1, "$r4")
    r_eq_I_plus_r("$r8", i1, "$r4")
    r_eq_I_minus_r("$r9", i1, "$r4")
    r_eq_I_shl_r("$r10", i1, "$r4")
    r_eq_I_shr_r("$r11", i1, "$r4")
    r_eq_I_sar_r("$r12", i1, "$r4")
    r_eq_I_mul_r("$r13", i1, "$r4")

    check()
    terminate()

@prog_wrapper
def test_alu_ir(top):
    """
    Test short immediate-to-register ALU operations
    """

    top.set_timeout(6000)

    startup()
    load_reg("$r4", 0xff00f0f0)
    i1 = 0x0f0f
    r[5] = (r[4] ^ i1) & 0xffffffff
    r[6] = (r[4] | i1) & 0xffffffff
    r[7] = (r[4] & i1) & 0xffffffff
    r[8] = (r[4] + i1) & 0xffffffff
    r[9] = (i1 - r[4]) & 0xffffffff
    r[10] = shl(r[4], i1)
    r[11] = shr(r[4], i1)
    r[12] = sar(r[4], i1)
    r[13] = (r[4] * i1) & 0xffffffff
    r_eq_i_xor_r("$r5", i1, "$r4")
    r_eq_i_or_r("$r6", i1, "$r4")
    r_eq_i_and_r("$r7", i1, "$r4")
    r_eq_i_plus_r("$r8", i1, "$r4")
    r_eq_i_minus_r("$r9", i1, "$r4")
    r_eq_r_shl_i("$r10", "$r4", i1)
    r_eq_r_shr_i("$r11", "$r4", i1)
    r_eq_r_sar_i("$r12", "$r4", i1)
    r_eq_i_mul_r("$r13", i1, "$r4")

    check()
    terminate()


@prog_wrapper
def test_alu_r(top):
    """
    Test unary ALU operations
    """

    top.set_timeout(6000)

    startup()
    load_reg("$r4", 0xff00f0f0)
    i1 = 0x0f0f
    r[5] = (-r[4]) & 0xffffffff
    r[6] = (~r[4]) & 0xffffffff
    r[7] = bse(r[4])
    r[8] = wse(r[4])

    r_eq_neg_r("$r5", "$r4")
    r_eq_not_r("$r6", "$r4")
    r_eq_bse_r("$r7", "$r4")
    r_eq_wse_r("$r8", "$r4")

    check()
    terminate()


@prog_wrapper
def test_branch_zc(top):
    """
    Test zero-compare conditional branches
    """

    top.set_timeout(6000)

    startup()
    load_reg("$r1", 0xffffffff)
    load_reg("$r14", 0)

    if_r_eq_z(  "$r0", "r_eq_z1")
    fail()
    place_symbol("r_eq_z1")
    if_r_eq_z(  "$r1", "r_eq_z2")
    pc_eq_I("r_eq_z3")
    place_symbol("r_eq_z2")
    fail()
    place_symbol("r_eq_z3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1

    if_r_ne_z(  "$r1", "r_ne_z1")
    fail()
    place_symbol("r_ne_z1")
    if_r_ne_z(  "$r0", "r_ne_z2")
    pc_eq_I("r_ne_z3")
    place_symbol("r_ne_z2")
    fail()
    place_symbol("r_ne_z3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1

    if_r_lts_z(  "$r1", "r_lts_z1")
    fail()
    place_symbol("r_lts_z1")
    if_r_lts_z(  "$r0", "r_lts_z2")
    if_r_lts_z(  "$r2", "r_lts_z2")
    pc_eq_I("r_lts_z3")
    place_symbol("r_lts_z2")
    fail()
    place_symbol("r_lts_z3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1

    if_r_ges_z(  "$r0", "r_ges_z1")
    fail()
    place_symbol("r_ges_z1")
    if_r_ges_z(  "$r2", "r_ges_z1b")
    fail()
    place_symbol("r_ges_z1b")
    if_r_ges_z(  "$r1", "r_ges_z2")
    pc_eq_I("r_ges_z3")
    place_symbol("r_ges_z2")
    fail()
    place_symbol("r_ges_z3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1

    if_r_gts_z(  "$r2", "r_gts_z1")
    fail()
    place_symbol("r_gts_z1")
    if_r_gts_z(  "$r0", "r_gts_z2")
    if_r_gts_z(  "$r1", "r_gts_z2")
    pc_eq_I("r_gts_z3")
    place_symbol("r_gts_z2")
    fail()
    place_symbol("r_gts_z3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1

    if_r_les_z(  "$r1", "r_les_z1")
    fail()
    place_symbol("r_les_z1")
    if_r_les_z(  "$r0", "r_les_z1b")
    fail()
    place_symbol("r_les_z1b")
    if_r_les_z(  "$r2", "r_les_z2")
    pc_eq_I("r_les_z3")
    place_symbol("r_les_z2")
    fail()
    place_symbol("r_les_z3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1

    check()
    terminate()


@prog_wrapper
def test_branch_rc(top):
    """
    Test register-compare conditional branches
    """

    top.set_timeout(6000)

    startup()
    load_reg("$r1", 0xffffffff)
    load_reg("$r14", 0)

    if_r_eq_r(  "$r5", "$r5", "r_eq_r1")
    fail()
    place_symbol("r_eq_r1")
    if_r_eq_r(  "$r1", "$r5", "r_eq_r2")
    pc_eq_I("r_eq_r3")
    place_symbol("r_eq_r2")
    fail()
    place_symbol("r_eq_r3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1

    if_r_ne_r(  "$r1", "$r5", "r_ne_r1")
    fail()
    place_symbol("r_ne_r1")
    if_r_ne_r(  "$r5", "$r5", "r_ne_r2")
    pc_eq_I("r_ne_r3")
    place_symbol("r_ne_r2")
    fail()
    place_symbol("r_ne_r3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1

    if_r_lts_r(  "$r1", "$r5", "r_lts_r1")
    fail()
    place_symbol("r_lts_r1")
    if_r_lts_r(  "$r2", "$r5", "r_lts_r1b")
    fail()
    place_symbol("r_lts_r1b")
    if_r_lts_r(  "$r8", "$r5", "r_lts_r2")
    if_r_lts_r(  "$r5", "$r1", "r_lts_r2")
    if_r_lts_r(  "$r5", "$r5", "r_lts_r2")
    pc_eq_I("r_lts_r3")
    place_symbol("r_lts_r2")
    fail()
    place_symbol("r_lts_r3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1

    if_r_ges_r(  "$r8", "$r5", "r_ges_r1")
    fail()
    place_symbol("r_ges_r1")
    if_r_ges_r(  "$r5", "$r1", "r_ges_r1b")
    fail()
    place_symbol("r_ges_r1b")
    if_r_ges_r(  "$r5", "$r5", "r_ges_r1c")
    fail()
    place_symbol("r_ges_r1c")
    if_r_ges_r(  "$r1", "$r5", "r_ges_r2")
    if_r_ges_r(  "$r2", "$r5", "r_ges_r2")
    pc_eq_I("r_ges_r3")
    place_symbol("r_ges_r2")
    fail()
    place_symbol("r_ges_r3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1

    if_r_lt_r(  "$r5", "$r1", "r_lt_r1")
    fail()
    place_symbol("r_lt_r1")
    if_r_lt_r(  "$r2", "$r5", "r_lt_r1b")
    fail()
    place_symbol("r_lt_r1b")
    if_r_lt_r(  "$r1", "$r5", "r_lt_r2")
    if_r_lt_r(  "$r8", "$r5", "r_lt_r2")
    if_r_lt_r(  "$r5", "$r5", "r_lt_r2")
    pc_eq_I("r_lt_r3")
    place_symbol("r_lt_r2")
    fail()
    place_symbol("r_lt_r3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1

    if_r_ge_r(  "$r8", "$r5", "r_ge_r1")
    fail()
    place_symbol("r_ge_r1")
    if_r_ge_r(  "$r1", "$r5", "r_ge_r1b")
    fail()
    place_symbol("r_ge_r1b")
    if_r_ge_r(  "$r5", "$r5", "r_ge_r1c")
    fail()
    place_symbol("r_ge_r1c")
    if_r_ge_r(  "$r5", "$r1", "r_ge_r2")
    if_r_ge_r(  "$r2", "$r5", "r_ge_r2")
    pc_eq_I("r_ge_r3")
    place_symbol("r_ge_r2")
    fail()
    place_symbol("r_ge_r3")

    r_eq_r_plus_t("$r14", "$r14", 1)
    r[14] += 1


    check()
    terminate()


@prog_wrapper
def test_branch_bit(top):
    """
    Test register-compare conditional branches
    """

    top.set_timeout(6000)

    startup(call_init_regs=False)
    load_reg("$r0",  0x00000001)
    load_reg("$r1",  0x00000002)
    load_reg("$r2",  0x00000004)
    load_reg("$r3",  0x00000008)
    load_reg("$r4",  0x00000010)
    load_reg("$r5",  0x00000020)
    load_reg("$r6",  0x00000040)
    load_reg("$r7",  0x00000080)
    load_reg("$r8",  0x00000100)
    load_reg("$r9",  0x00000200)
    load_reg("$r10", 0x00004000)
    load_reg("$r11", 0x00008000)
    load_reg("$r12", 0x00010000)
    load_reg("$r13", 0x40000000)
    load_reg("$r14", 0x80000000)

    def bit(idx):
        b = (0,1,2,3,4,5,6,7,8,9,14,15,16,30,31)
        return b[idx]

    for i in range(15):
        if_r_setb(f"$r{i}", bit(i), f"r_setb{i}_j")
        fail()
        place_symbol(f"r_setb{i}_j")

    mem32_I_eq_r(con_base+0, "$r0")

    for i in range(15):
        if_r_clrb(f"$r{i}", bit(i), f"r_clrb_nj_error")
    pc_eq_I("r_clrb_nj_ok")
    place_symbol("r_clrb_nj_error")
    fail()
    place_symbol("r_clrb_nj_ok")

    mem32_I_eq_r(con_base+0, "$r1")

    for i in range(15):
        r_eq_not_r(f"$r{i}", f"$r{i}")
        r[i] = ~r[i]

    mem32_I_eq_r(con_base+0, "$r2")

    for i in range(15):
        if_r_clrb(f"$r{i}", bit(i), f"r_clrb{i}_j")
        fail()
        place_symbol(f"r_clrb{i}_j")

    mem32_I_eq_r(con_base+0, "$r3")

    for i in range(15):
        if_r_setb(f"$r{i}", bit(i), f"r_setb_nj_error")
    pc_eq_I("r_setb_nj_ok")
    place_symbol("r_setb_nj_error")
    fail()
    place_symbol("r_setb_nj_ok")

    mem32_I_eq_r(con_base+0, "$r4")

    check()
    terminate()

@prog_wrapper
def test_ldst(top):
    """
    Test load-store operations
    """

    top.set_timeout(10000)

    data_base = 0x08002000

    startup()
    load_reg("$r3", 0x01020304)
    load_reg("$r4", 0xfffefdfc)
    load_reg("$r5", data_base)

    r_eq_i("$r13", 0)

    # Test I loads
    mem32_I_eq_r(data_base, "$r3")
    mem32_I_eq_r(data_base+4, "$r4")
    r_eq_mem32_I("$r0", data_base)
    check_reg("$r0", 0x01020304)
    r_eq_mem16_I("$r1", data_base)
    check_reg("$r1", 0x0304)
    r_eq_mem8_I("$r2", data_base+3)
    check_reg("$r2", 0x01)
    r_eq_smem16_I("$r1", data_base+2)
    check_reg("$r1", 0x0102)
    r_eq_smem8_I("$r0", data_base+2)
    check_reg("$r0", 0x02)

    r_eq_i("$r13", 1)

    r_eq_mem16_I("$r1", data_base+4)
    check_reg("$r1", 0xfdfc)
    r_eq_mem8_I("$r2", data_base+4)
    check_reg("$r2", 0xfc)
    r_eq_mem8_I("$r2", data_base+5)
    check_reg("$r2", 0xfd)
    r_eq_smem16_I("$r1", data_base+4)
    check_reg("$r1", 0xfffffdfc)
    r_eq_smem16_I("$r1", data_base+4+2)
    check_reg("$r1", 0xfffffffe)
    r_eq_smem8_I("$r0", data_base+4)
    check_reg("$r0", 0xfffffffc)
    r_eq_smem8_I("$r0", data_base+5)
    check_reg("$r0", 0xfffffffd)

    r_eq_i("$r13", 2)

    # Test r loads
    init_regs()
    load_reg("$r3", 0x01020304)
    load_reg("$r4", 0xfffefdfc)
    load_reg("$r5", data_base)
    load_reg("$r6", data_base+4)

    mem32_I_eq_r(data_base, "$r3")
    mem32_I_eq_r(data_base+4, "$r4")
    r_eq_mem32_r("$r0", "$r5")
    check_reg("$r0", 0x01020304)
    r_eq_mem16_r("$r1", "$r5")
    check_reg("$r1", 0x0304)
    r_eq_r_plus_t("$r10", "$r5", 3)
    r_eq_mem8_r("$r2", "$r10")
    check_reg("$r2", 0x01)
    r_eq_r_plus_t("$r10", "$r5", 2)
    r_eq_smem16_r("$r1", "$r10")
    check_reg("$r1", 0x0102)
    r_eq_smem8_r("$r0", "$r10")
    check_reg("$r0", 0x02)

    r_eq_i("$r13", 3)

    r_eq_mem16_r("$r1", "$r6")
    check_reg("$r1", 0xfdfc)
    r_eq_mem8_r("$r2", "$r6")
    check_reg("$r2", 0xfc)
    r_eq_r_plus_t("$r10", "$r6", 1)
    r_eq_mem8_r("$r2", "$r10")
    check_reg("$r2", 0xfd)
    r_eq_smem16_r("$r1", "$r6")
    check_reg("$r1", 0xfffffdfc)
    r_eq_r_plus_t("$r10", "$r6", 2)
    r_eq_smem16_r("$r1", "$r10")
    check_reg("$r1", 0xfffffffe)
    r_eq_smem8_r("$r0", "$r6")
    check_reg("$r0", 0xfffffffc)
    r_eq_r_plus_t("$r10", "$r6", 1)
    r_eq_smem8_r("$r0", "$r10")
    check_reg("$r0", 0xfffffffd)

    r_eq_i("$r13", 4)




    init_regs()
    load_reg("$r3", 0x01020304)
    load_reg("$r4", 0xfffefdfc)
    load_reg("$r5", data_base)

    r_eq_i("$r13", 5)

    # Test r+i loads
    mem32_I_eq_r(data_base, "$r3")
    mem32_I_eq_r(data_base+4, "$r4")
    load_reg("$r5", data_base)
    load_reg("$r6", data_base+4)
    r_eq_mem32_r_plus_i("$r0", "$r5", 0)
    check_reg("$r0", 0x01020304)
    r_eq_mem16_r_plus_i("$r1", "$r5", 0)
    check_reg("$r1", 0x0304)
    r_eq_mem8_r_plus_i("$r2", "$r5", 3)
    check_reg("$r2", 0x01)
    r_eq_smem16_r_plus_i("$r1", "$r5", 2)
    check_reg("$r1", 0x0102)
    r_eq_smem8_r_plus_i("$r0", "$r5", 2)
    check_reg("$r0", 0x02)

    r_eq_i("$r13", 6)

    r_eq_mem16_r_plus_i("$r1", "$r5", 4)
    check_reg("$r1", 0xfdfc)
    r_eq_mem8_r_plus_i("$r2", "$r5", 4)
    check_reg("$r2", 0xfc)
    r_eq_mem8_r_plus_i("$r2", "$r5", 5)
    check_reg("$r2", 0xfd)
    r_eq_smem16_r_plus_i("$r1", "$r6", 0)
    check_reg("$r1", 0xfffffdfc)
    r_eq_smem16_r_plus_i("$r1", "$r6", 2)
    check_reg("$r1", 0xfffffffe)
    r_eq_smem8_r_plus_i("$r0", "$r6", 0)
    check_reg("$r0", 0xfffffffc)
    r_eq_smem8_r_plus_i("$r0", "$r6", 1)
    check_reg("$r0", 0xfffffffd)

    r_eq_i("$r13", 7)

    # Test I stores

    load_reg("$r10", 0xaabbccdd)
    load_reg("$r11", 0x11223344)

    mem32_I_eq_r(data_base, "$r3")
    mem32_I_eq_r(data_base+4, "$r4")
    mem8_I_eq_r(data_base, "$r10")
    mem8_I_eq_r(data_base+3, "$r11")
    r_eq_mem32_I("$r9", data_base)
    check_reg("$r9", 0x440203dd)
    mem32_I_eq_r(data_base, "$r3")
    mem16_I_eq_r(data_base+2, "$r11")
    r_eq_mem32_I("$r9", data_base)
    check_reg("$r9", 0x33440304)

    r_eq_i("$r13", 8)

    # Test r+i stores

    load_reg("$r0", data_base+4)
    load_reg("$r1", data_base)

    mem32_I_eq_r(data_base, "$r3")
    mem32_I_eq_r(data_base+4, "$r4")
    mem8_r_plus_i_eq_r("$r0", -4, "$r10")
    mem8_r_plus_i_eq_r("$r0", -1, "$r11")
    r_eq_mem32_I("$r9", data_base)
    check_reg("$r9", 0x440203dd)
    mem32_I_eq_r(data_base, "$r3")
    mem16_r_plus_i_eq_r("$r1", 2, "$r11")
    r_eq_mem32_I("$r9", data_base)
    check_reg("$r9", 0x33440304)
    mem32_r_plus_i_eq_r("$r0", -4, "$r10")
    r_eq_mem32_I("$r9", data_base)
    check_reg("$r9", 0xaabbccdd)

    r_eq_i("$r13", 9)

    # Test r stores

    mem32_I_eq_r(data_base, "$r3")
    mem32_I_eq_r(data_base+4, "$r4")
    mem8_r_eq_r("$r1", "$r10")
    r_eq_r_plus_i("$r13", "$r1", 3)
    mem8_r_eq_r("$r13", "$r11")
    r_eq_mem32_I("$r9", data_base)
    check_reg("$r9", 0x440203dd)
    mem32_I_eq_r(data_base, "$r3")
    r_eq_r_plus_i("$r13", "$r1", 2)
    mem16_r_eq_r("$r13", "$r11")
    r_eq_mem32_I("$r9", data_base)
    check_reg("$r9", 0x33440304)
    mem32_r_eq_r("$r1", "$r10")
    r_eq_mem32_I("$r9", data_base)
    check_reg("$r9", 0xaabbccdd)

    # Test stack ops

    r_eq_i("$r13", 10)

    load_reg("$r10", 0x01234567)
    load_reg("$r11", 0x89abcdef)
    load_reg("$r12", data_base)
    load_reg("$r13", data_base+4)

    mem32_r_plus_t_eq_r("$r12", 0, "$r2")
    mem32_r_plus_t_eq_r("$r13", 0, "$r2")
    mem32_r_plus_t_eq_r("$r12", 4, "$r11")
    mem32_r_plus_t_eq_r("$r13", -4, "$r10")
    r_eq_mem32_r_plus_t("$r5", "$r12", 4)
    r_eq_mem32_r_plus_t("$r6", "$r13", -4)
    r_eq_mem32_r_plus_t("$r7", "$r12", 0)
    r_eq_mem32_r_plus_t("$r8", "$r13", 0)

    check_reg("$r5", 0x89abcdef)
    check_reg("$r6", 0x01234567)
    check_reg("$r7", 0x01234567)
    check_reg("$r8", 0x89abcdef)

    terminate()


# TODO: zero-compare branches; compare branches; bit-test branches
#       stack operations
#       load-stores

if __name__ == "__main__":
    prep_test(top)
    #test_1()
    #test_2()
    #test_3()
    #test_4()
    test_5()
    #test_framework()
    #test_alu_rr()
    #test_alu_Ir()
    #test_alu_ir()
    #test_alu_r()
    #test_branch_zc()
    #test_branch_rc()
    #test_branch_bit()
    #test_ldst()

if "pytest" in sys.modules:
    prep_test(top)
