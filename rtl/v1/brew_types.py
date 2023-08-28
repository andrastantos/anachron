#!/usr/bin/python3
from typing import *
from silicon import *

BrewLineAddrWidth = 29

BrewByte = Unsigned(8)
BrewAddr = Unsigned(32)
BrewInstAddr = Unsigned(31)
BrewDWordAddr = Unsigned(30)
BrewLineAddr = Unsigned(BrewLineAddrWidth)
BrewLineAddrBtm = 2 # This is in words
BrewBusAddr = Unsigned(31)
BrewBusData = Unsigned(16)
BrewData = Unsigned(32)
BrewRegCnt = 15
#BrewRegAddr = Unsigned(BrewRegCnt.bit_length())
BrewRegAddr = Number(min_val=0, max_val=BrewRegCnt-1)

BrewMemBase = Unsigned(22)
BrewMemShift = 10 # This is in bytes

BrewCsrAddrWidth = 10 # We have 4kB of CSR space, in 1024 32-bit registers
BrewCsrAddr = Unsigned(BrewCsrAddrWidth)
BrewCsrData = Unsigned(32)

inst_len_16 = 0
inst_len_32 = 1
inst_len_48 = 2
inst_len_bubble = 3

acc_len_8 = 0
acc_len_16 = 1
acc_len_32 = 2

class alu_ops(Enum):
    a_plus_b     = 0
    a_minus_b    = 1
    a_and_b      = 2
    a_or_b       = 3
    a_xor_b      = 4
    tpc          = 5
    pc_plus_b    = 6

class shifter_ops(Enum):
    shll     = 0
    shlr     = 1
    shar     = 2

class branch_ops(Enum):
    cb_eq    = 1
    cb_ne    = 2
    cb_lts   = 3
    cb_ges   = 4
    cb_lt    = 5
    cb_ge    = 6

    # Bit-selection coming in op_b
    bb_one   = 7
    # Bit-selection coming in op_a
    bb_zero  = 8

    swi      = 9 # SWI index comes in op_a
    stm      = 10
    pc_w   = 11
    tpc_w  = 12

class ldst_ops(Enum):
    store = 0
    load  = 1
    csr_store = 2
    csr_load =3

class op_class(Enum):
    alu     = 0
    mult    = 1
    shift   = 2
    branch  = 3
    ld_st   = 4

access_len_8 = 0
access_len_16 = 1
access_len_32 = 2

class BusIfRequestIf(ReadyValid):
    read_not_write  = logic
    byte_en         = Unsigned(2)
    addr            = BrewBusAddr
    data            = BrewBusData

class BusIfResponseIf(Interface):
    valid           = logic
    data            = BrewBusData

class BusIfDmaRequestIf(ReadyValid):
    read_not_write  = logic
    one_hot_channel = GenericMember
    byte_en         = Unsigned(2)
    addr            = BrewBusAddr
    is_master       = logic
    terminal_count  = logic

class BusIfDmaResponseIf(Interface):
    valid           = logic

class ExternalBusIf(Interface):
    n_ras_a       = logic
    n_ras_b       = logic
    n_cas_0       = logic
    n_cas_1       = logic
    addr          = Unsigned(11)
    n_we          = logic
    data_in       = Reverse(BrewByte)
    data_out      = BrewByte
    data_out_en   = logic
    n_nren        = logic
    n_wait        = Reverse(logic)
    n_dack        = Unsigned(4)
    tc            = logic
    bus_en        = logic

class FetchDecodeIf(ReadyValid):
    inst_0 = Unsigned(16)
    inst_1 = Unsigned(16)
    inst_2 = Unsigned(16)
    inst_len = Unsigned(2) # Len 3 is reserved
    av = logic

class DecodeExecIf(ReadyValid):
    exec_unit = EnumNet(op_class)
    alu_op = EnumNet(alu_ops)
    shifter_op = EnumNet(shifter_ops)
    branch_op = EnumNet(branch_ops)
    ldst_op = EnumNet(ldst_ops)
    op_a = BrewData
    op_b = BrewData
    op_c = BrewData
    mem_access_len = Unsigned(2) # 0 for 8-bit, 1 for 16-bit, 2 for 32-bit
    inst_len = Unsigned(2)
    do_bse = logic
    do_wse = logic
    do_bze = logic
    do_wze = logic
    result_reg_addr = BrewRegAddr
    result_reg_addr_valid = logic
    fetch_av = logic

class MemInputIf(ReadyValid):
    read_not_write = logic
    data = BrewData
    addr = BrewAddr
    is_csr = logic
    access_len = Unsigned(2) # 0 for 8-bit, 1 for 16-bit, 2 for 32-bit

class MemOutputIf(Interface):
    valid = logic
    data_l = BrewBusData
    data_h = BrewBusData

class RegFileWriteBackIf(Interface):
    valid = logic
    data = BrewData
    data_en = logic
    addr = BrewRegAddr

class ResultExtendIf(Interface):
    valid = logic
    data_l = BrewBusData
    data_h = BrewBusData
    data_en = logic
    addr = BrewRegAddr
    do_bse = logic
    do_wse = logic
    do_bze = logic
    do_wze = logic

class RegFileReadRequestIf(ReadyValid):
    read1_addr = BrewRegAddr
    read1_valid = logic
    read2_addr = BrewRegAddr
    read2_valid = logic
    rsv_addr = BrewRegAddr
    rsv_valid = logic

class RegFileReadResponseIf(ReadyValid):
    read1_data = BrewData
    read2_data = BrewData


class ApbIf(Interface):
    pwrite = logic
    psel = logic
    penable = logic
    pready = Reverse(logic)

    paddr = GenericMember
    pwdata = BrewCsrData
    prdata = Reverse(BrewCsrData)

class Apb8If(Interface):
    pwrite = logic
    psel = logic
    penable = logic
    pready = Reverse(logic)

    paddr = GenericMember
    pwdata = Unsigned(8)
    prdata = Reverse(Unsigned(8))

class Apb16If(Interface):
    pwrite = logic
    psel = logic
    penable = logic
    pready = Reverse(logic)

    paddr = GenericMember
    pwdata = Unsigned(16)
    prdata = Reverse(BrewCsrData)

'''
APB signalling

               <-- read -->      <-- write ->
    CLK     \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/
    psel    ___/^^^^^^^^^^^\_____/^^^^^^^^^^^\______
    penable _________/^^^^^\___________/^^^^^\______
    pready  ---------/^^^^^\-----------/^^^^^\------
    pwrite  ---/^^^^^^^^^^^\-----\___________/------
    paddr   ---<===========>-----<===========>------
    prdata  ---------<=====>------------------------
    pwdata  ---------------------<===========>------
'''

# Exception types:
'''
The following exceptions are supported:

- MIP: MMU Exception on the instruction port (details are in EX_ADDR_I/EX_OP_I)
- MDP: MMU Exception on the data port (details are in EX_ADDR_D/EX_OP_D)
- SWI: SWI instruction (details are in the ECAUSE/RCAUSE registers)
- CUA: unaligned access

Since we do posted writes (or at least should supported it), we can't really do precise bus error exceptions. So, those are not precise:

- IAV: interconnect access violation
- IIA: interconnect invalid address (address decode failure)
- ITF: interconnect target fault (target signaled failure)

These - being imprecise - can't be retried, so if they occur in TASK mode, the only recourse is to terminate the app, and if they happen in SCHEDULER mode, they will reboot, after setting RCAUSE and, if possible, RADDR.

All these sources are mapped into the ECAUSE and RCAUSE registers:

+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|IAV|IIA|ITF|MIP|MDP|CUA|SW7|SW6|SW5|SW4|SW3|SW2|SW1|SW0|
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
'''

exc_swi_0 = 0
exc_swi_1 = 1
exc_swi_2 = 2
exc_swi_3 = 3
exc_swi_4 = 4
exc_swi_5 = 5
exc_swi_6 = 6
exc_swi_7 = 7
exc_cua   = 8
exc_mdp   = 9
exc_mip   = 10
exc_hwi   = 11
exc_itf   = 12
exc_iia   = 13
exc_iav   = 14

