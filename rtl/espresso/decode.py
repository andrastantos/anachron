#!/usr/bin/python3
from random import *
from typing import *
from copy import copy

try:
    from silicon import *
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str((Path() / ".." / ".." / ".." / "silicon").absolute()))
    from silicon import *

try:
    from .brew_types import *
    from .brew_utils import *
    from .scan import ScanWrapper
    from .synth import *
    from .assembler import *
except ImportError:
    from brew_types import *
    from brew_utils import *
    from scan import ScanWrapper
    from synth import *
    from assembler import *

"""
Decode logic

Decode takes a single instruction from the fetch unit. It is just 3 bytes, a length and an 'av' flag.

Decode generates a bunch of logic signals for Execute. It also deals with the register file, and thus
reservations.

Decode is ready to issue an instruction to Execute if all reservations are met.

Since the register file has a single-cycle latency, we'll have to start the reservation process
before we knew if Execute is going to be able to accept the results. Because of that, we'll have
to remember the results of a read result if Execute is not ready for us.

TODO: DIET DIET DIET: there's another way of dealing with this, but I will not do it right now
as it requires an interface change: we could change the interface in some way to ensure that
the RF keeps it's output reliable even if a new request isn't sent in, or change things so
that we can keep re-issuing the same request again and again (we can't at this point due
to reservations)

In case of a fetch AV, we pretend to get an instruction with no dependencies and no reservation and push it as
the next instruction. There's no harm in using the instruction fields: while they're invalid, or may even
contain some sensitive info, they don't produce side-effects: all they do is to generate some mux changes
that then will be ignored in execute. However, we *have* to make sure that the output register enable is
de-asserted, so no matter what, no write-back will occur. Execute assumes that.

HW interrupts are dealt with in the execute stage.
"""

"""
If we were to do the decoding using ROMs, this is how things would transpire:

On clock 0:
    - we detect a valid input (fetch.valid & fetch.ready).
    - we need to do some pre-decode to come up with the ROM address;
      this would be in the same logic cone as the output of the fetch, unfortunately.
On clock 1:
    - we get the result of decode, which is the RF addresses and their their reservations;
      this we feed to the RF
    - we register all the rest of the outputs from the ROM as those will need to go to
      execute
    - the RF starts processing the request
On clock 2:
    - We get the results from the RF, which we feed to execute with the rest of the
      control signals

In other words: we're extending decode latency to two.

If we were to forgo the decode ROM and stayed with the current logic, we could:

On clock 0:
    - we detect a valid input (fetch.valid & fetch.ready)
    - we decode RF addresses and reservations; feed them to RF
      all this logic is within the logic cones of fetch, unfortunately
    - RF starts working on our request
On clock 1:
    - we decode the rest of the control signals <== this can still be done using a ROM
    - we get the result from RF

So, overall, the following logic will have to happen front-loaded:

- RegA address;needed selection
- RegB address;needed selection
- Rsv  address;needed selection
- ROM  address creation

As far as the ROM is concerned, currently the following bit-counts are needed (I think):

    EXEC_UNIT:     3
    ALU_OP:        3
    SHIFTER_OP:    2
    BRANCH_OP:     4
    LDST_OP:       2
    RD1_ADDR:      2 --> needs async decode
    RD2_ADDR:      2 --> needs async decode
    RES_ADDR:      1 --> needs async decode
    OP_A:          3
    OP_B:          3
    OP_C:          2
    MEM_LEN:       2
    BSE:           1
    WSE:           1
    BZE:           1
    WZE:           1
    WOI:           1
    ----------------
    TOTAL:        34

So, if I'm not mistaken, we would need 31-bit wide memories; something that most FPGAs support. GoWin gets there
with 9 address bits. So, with the right compression we should be able to get away with a single ROM.

There seems to be about 40 compression groups, which can be decoded in 5 bits. Each group is no longer than 16 instructions,
so group+ins is 9 bits. Soo... a single ROM would do it?
"""
class DecodeStage(GenericModule):
    clk = ClkPort()
    rst = RstPort()

    fetch = Input(FetchDecodeIf)
    output_port = Output(DecodeExecIf)

    # Interface to the register file
    reg_file_req = Output(RegFileReadRequestIf)
    reg_file_rsp = Input(RegFileReadResponseIf)

    do_branch = Input(logic)

    break_fetch_burst = Output(logic)

    def construct(self, has_multiply: bool = True, has_shift: bool = True, use_mini_table: bool = False, use_decode_rom: bool = False, register_mask_signals: bool = False):
        self.has_multiply = has_multiply
        self.has_shift = has_shift
        self.use_mini_table = use_mini_table
        self.use_decode_rom = use_decode_rom
        self.register_mask_signals = register_mask_signals

    def body(self):
        # We're not being very nice with Silicons' type system: we have a bunch of unsigned types
        # here that we want do sign-extension on. Silicon will not help us (it would do zero-extend)
        # so let's introduce a quick function
        def sign_extend_to(a, size, *, num_bits = None):
            if num_bits == None:
                num_bits = a.get_num_bits()
            return concat(*(a[num_bits-1], )* (size-num_bits), a)

        # Pre-decode logic: these signals are technically operate in the fetch stage, but are implemented in Decode for the hierarchy.
        # They participate in generating the signals necessary for RF (that is, the operand and reservation register addresses and their validity)

        pre_field_d = self.fetch.inst_0[15:12]
        pre_field_c = self.fetch.inst_0[11:8]
        pre_field_b = self.fetch.inst_0[7:4]
        pre_field_a = self.fetch.inst_0[3:0]
        pre_tiny_field_a = 12 | self.fetch.inst_0[0]

        pre_field_a_is_f = pre_field_a == 0xf
        pre_field_b_is_f = pre_field_b == 0xf
        pre_field_c_is_f = pre_field_c == 0xf
        pre_field_d_is_f = pre_field_d == 0xf

        # We are totally dependent on RF to provide handshaking. We're simply registering our own input at the same time.
        buf_fetch = Wire(self.fetch.get_data_member_type())
        buf_en = self.fetch.ready & self.fetch.valid
        buf_fetch <<= Reg(self.fetch.get_data_members(), clock_en=buf_en)

        buf_field_d = Reg(pre_field_d, clock_en=buf_en)
        buf_field_c = Reg(pre_field_c, clock_en=buf_en)
        buf_field_b = Reg(pre_field_b, clock_en=buf_en)
        buf_field_a = Reg(pre_field_a, clock_en=buf_en)
        buf_field_e = Select(
            buf_fetch.inst_len == inst_len_48,
            sign_extend_to(buf_fetch.inst_1, 32),
            concat(buf_fetch.inst_2, buf_fetch.inst_1)
        )

        buf_field_a_is_f = Reg(pre_field_a_is_f, clock_en=buf_en)
        buf_field_b_is_f = Reg(pre_field_b_is_f, clock_en=buf_en)
        buf_field_c_is_f = Reg(pre_field_c_is_f, clock_en=buf_en)
        buf_field_d_is_f = Reg(pre_field_d_is_f, clock_en=buf_en)

        buf_tiny_ofs = Wire(Unsigned(32))
        buf_tiny_ofs <<= sign_extend_to(concat(buf_fetch.inst_0[7:1], "2'b0"), 32, num_bits = 9)

        # Convert field_a from ones-complement to twos complement for certain instructions that use that encoding
        buf_ones_field_a = Select(
            buf_field_a[3],
            buf_field_a,
            sign_extend_to((buf_field_a+1)[3:0], 32, num_bits=4)
        )
        buf_ones_field_a_2x = concat(buf_ones_field_a[30:0], "1'b0")

        reg_val_a = self.reg_file_rsp.read1_data
        reg_val_b = self.reg_file_rsp.read2_data

        # Codes: 0123456789abcde <- exact match to that digit
        #        . <- anything but 0xf
        #        * <- anything, including 0xf
        #        < <- less then subsequent digit
        #        > <- greater than subsequent digit (but not 0xf)
        #        : <- anything after that is comment
        #        $ <- part of the mini set (for fast sims)
        # Fields:
        #    exec_unit = EnumNet(op_class)
        #    alu_op = EnumNet(alu_ops)
        #    shifter_op = EnumNet(shifter_ops)
        #    branch_op = EnumNet(branch_ops)
        #    ldst_op = EnumNet(ldst_ops)
        #    op_a = BrewData
        #    op_b = BrewData
        #    op_c = BrewData
        #    mem_access_len = Unsigned(2) # 0 for 8-bit, 1 for 16-bit, 2 for 32-bit
        #    inst_len = Unsigned(2)
        #    do_bse = logic
        #    do_wse = logic
        #    do_bze = logic
        #    do_wze = logic
        #    result_reg_addr = BrewRegAddr
        #    result_reg_addr_valid = logic
        #    fetch_av = logic
        bo = branch_ops
        ao = alu_ops
        so = shifter_ops
        lo = ldst_ops
        oc = op_class
        a32 = access_len_32
        a16 = access_len_16
        a8  = access_len_8
        REG_SP = 14

        #      CODE                                  EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP    RD1_ADDR    RD2_ADDR        RES_ADDR   OP_A             OP_B          OP_C        MEM_LEN BSE WSE BZE WZE WOI
        #invalid_instruction =                        (oc.branch,   None,         None,        bo.unknown,  None,      None,       None,           None,      None,            None,         None,       None,   0,  0,  0,  0,  0 )
        if self.has_shift:
            shift_ops = (
                #  CODE                                  EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP    RD1_ADDR        RD2_ADDR        RES_ADDR       OP_A             OP_B          OP_C        MEM_LEN BSE WSE BZE WZE WOI
                ( "  .6..: $rD <- $rA << $rB",            oc.shift,    None,         so.shll,     None,        None,      pre_field_a,    pre_field_b,    pre_field_d,   reg_val_a,       reg_val_b,    None,       None,   0,  0,  0,  0,  0 ),
                ( "  .7..: $rD <- $rA >> $rB",            oc.shift,    None,         so.shlr,     None,        None,      pre_field_a,    pre_field_b,    pre_field_d,   reg_val_a,       reg_val_b,    None,       None,   0,  0,  0,  0,  0 ),
                ( "  .8..: $rD <- $rA >>> $rB",           oc.shift,    None,         so.shar,     None,        None,      pre_field_a,    pre_field_b,    pre_field_d,   reg_val_a,       reg_val_b,    None,       None,   0,  0,  0,  0,  0 ),
                ( "  .6.f: $rD <- FIELD_E << $rB",        oc.shift,    None,         so.shll,     None,        None,      None,           pre_field_b,    pre_field_d,   buf_field_e,     reg_val_b,    None,       None,   0,  0,  0,  0,  0 ),
                ( "  .7.f: $rD <- FIELD_E >> $rB",        oc.shift,    None,         so.shlr,     None,        None,      None,           pre_field_b,    pre_field_d,   buf_field_e,     reg_val_b,    None,       None,   0,  0,  0,  0,  0 ),
                ( "  .8.f: $rD <- FIELD_E >>> $rB",       oc.shift,    None,         so.shar,     None,        None,      None,           pre_field_b,    pre_field_d,   buf_field_e,     reg_val_b,    None,       None,   0,  0,  0,  0,  0 ),
                ( "  .6f.: $rD <- $rA << FIELD_E",        oc.shift,    None,         so.shll,     None,        None,      pre_field_a,    None,           pre_field_d,   reg_val_a,       buf_field_e,  None,       None,   0,  0,  0,  0,  0 ),
                ( "  .7f.: $rD <- $rA >> FIELD_E",        oc.shift,    None,         so.shlr,     None,        None,      pre_field_a,    None,           pre_field_d,   reg_val_a,       buf_field_e,  None,       None,   0,  0,  0,  0,  0 ),
                ( "  .8f.: $rD <- $rA >>> FIELD_E",       oc.shift,    None,         so.shar,     None,        None,      pre_field_a,    None,           pre_field_d,   reg_val_a,       buf_field_e,  None,       None,   0,  0,  0,  0,  0 ),
            )
        else:
            shift_ops = (
                #( "  .6..: $rD <- $rA << $rB",            *invalid_instruction),
                #( "  .7..: $rD <- $rA >> $rB",            *invalid_instruction),
                #( "  .8..: $rD <- $rA >>> $rB",           *invalid_instruction),
                #( "  .6.f: $rD <- FIELD_E << $rB",        *invalid_instruction),
                #( "  .7.f: $rD <- FIELD_E >> $rB",        *invalid_instruction),
                #( "  .8.f: $rD <- FIELD_E >>> $rB",       *invalid_instruction),
                #( "  .6f.: $rD <- FIELD_E << $rA",        *invalid_instruction),
                #( "  .7f.: $rD <- FIELD_E >> $rA",        *invalid_instruction),
                #( "  .8f.: $rD <- FIELD_E >>> $rA",       *invalid_instruction),
            )
        if self.has_multiply:
            mult_ops = (
                #  CODE                                  EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP    RD1_ADDR        RD2_ADDR        RES_ADDR       OP_A             OP_B          OP_C        MEM_LEN BSE WSE BZE WZE WOI
                ( "  .9..: $rD <- $rA * $rB",             oc.mult,     None,         None,        None,        None,      pre_field_a,    pre_field_b,    pre_field_d,   reg_val_a,       reg_val_b,    None,       None,   0,  0,  0,  0,  0 ),
                ( "  .9.f: $rD <- FIELD_E * $rB",         oc.mult,     None,         None,        None,        None,      None,           pre_field_b,    pre_field_d,   buf_field_e,     reg_val_b,    None,       None,   0,  0,  0,  0,  0 ),
                ( "  .9f.: $rD <- FIELD_E * $rA",         oc.mult,     None,         None,        None,        None,      None,           pre_field_a,    pre_field_d,   buf_field_e,     reg_val_b,    None,       None,   0,  0,  0,  0,  0 ),
            )
        else:
            mult_ops = (
                #( "  .9..: $rD <- $rA * $rB",             *invalid_instruction),
                #( "  .9.f: $rD <- FIELD_E * $rB",         *invalid_instruction),
                #( "  .9f.: $rD <- FIELD_E * $rA",         *invalid_instruction),
            )
        full_inst_table = (
            *shift_ops,
            *mult_ops,
            #  Number of bits needed:                     3         3              2            4           2              2                2                   1              3               3                    2                  2     1   1   1   1   1
            #  Exception group                       EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "$ 0000: SWI_0",                        oc.branch,   None,         None,        bo.swi,      None,          None,           None,               None,          buf_field_d,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "$ 1000: SWI_1",                        oc.branch,   None,         None,        bo.swi,      None,          None,           None,               None,          buf_field_d,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "$ 2000: SWI_2",                        oc.branch,   None,         None,        bo.swi,      None,          None,           None,               None,          buf_field_d,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "$ 3000: SWI_3",                        oc.branch,   None,         None,        bo.swi,      None,          None,           None,               None,          buf_field_d,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "$ 4000: SWI_4",                        oc.branch,   None,         None,        bo.swi,      None,          None,           None,               None,          buf_field_d,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "$ 5000: SWI_5",                        oc.branch,   None,         None,        bo.swi,      None,          None,           None,               None,          buf_field_d,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "$ 6000: SWI_6",                        oc.branch,   None,         None,        bo.swi,      None,          None,           None,               None,          buf_field_d,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "$ 7000: SWI_7",                        oc.branch,   None,         None,        bo.swi,      None,          None,           None,               None,          buf_field_d,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  8000: STM",                          oc.branch,   None,         None,        bo.stm,      None,          None,           None,               None,          None,            None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  9000: WOI",                          oc.branch,   ao.a_minus_b, None,        bo.cb_eq,    None,          pre_field_a,    pre_field_b,        None,          reg_val_a,       reg_val_b,           0,                None,   0,  0,  0,  0,  1 ), # Decoded as 'if $0 == $0 $pc <- $pc'
            ( "  a000: PFLUSH",                       oc.branch,   ao.a_minus_b, None,        bo.cb_ne,    None,          pre_field_a,    pre_field_b,        None,          reg_val_a,       reg_val_b,           0,                None,   0,  0,  0,  0,  0 ), # Decoded as 'if $0 != $0 $pc <- $pc'
            #  PC manipulation group                 EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .001: FENCE",                        oc.alu,      None,         None,        None,        None,          None,           None,               None,          None,            None,                None,             None,   0,  0,  0,  0,  0 ), # Decoded as a kind of NOP
            ( "$ .002: $pc <- $rD",                   oc.branch,   None,         None,        bo.pc_w,     None,          pre_field_d,    None,               None,          reg_val_a,       None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  .003: $tpc <- $rD",                  oc.branch,   None,         None,        bo.tpc_w,    None,          pre_field_d,    None,               None,          reg_val_a,       None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "$ .004: $rD <- $pc",                   oc.alu,      ao.pc_plus_b, None,        None,        None,          None,           None,               pre_field_d,   None,            0,                   None,             None,   0,  0,  0,  0,  0 ),
            ( "  .005: $rD <- $tpc",                  oc.alu,      ao.tpc,       None,        None,        None,          None,           None,               pre_field_d,   None,            None,                None,             None,   0,  0,  0,  0,  0 ),
            # Unary group                            EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "$ .01.: $rD <- tiny FIELD_A",          oc.alu,      ao.a_or_b,    None,        None,        None,          None,           None,               pre_field_d,   0,               buf_ones_field_a,    None,             None,   0,  0,  0,  0,  0 ),
            ( "  .02.: $rD <- $pc + FIELD_A*2",       oc.alu,      ao.pc_plus_b, None,        None,        None,          None,           None,               pre_field_d,   None,            buf_ones_field_a_2x, None,             None,   0,  0,  0,  0,  0 ),
            ( "  .03.: $rD <- -$rA",                  oc.alu,      ao.a_minus_b, None,        None,        None,          None,           pre_field_a,        pre_field_d,   0,               reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "$ .04.: $rD <- ~$rA",                  oc.alu,      ao.a_xor_b,   None,        None,        None,          None,           pre_field_a,        pre_field_d,   0xffffffff,      reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .05.: $rD <- bse $rA",               oc.alu,      ao.a_or_b,    None,        None,        None,          None,           pre_field_a,        pre_field_d,   0,               reg_val_b,           None,             None,   1,  0,  0,  0,  0 ),
            ( "  .06.: $rD <- wse $rA",               oc.alu,      ao.a_or_b,    None,        None,        None,          None,           pre_field_a,        pre_field_d,   0,               reg_val_b,           None,             None,   0,  1,  0,  0,  0 ),
            #( "  .07.: $rD <- popcnt $rA",            ),
            #( "  .08.: $rD <- 1 / $rA",               ),
            #( "  .09.: $rD <- rsqrt $rA",             ),
            #( "  .0c.: $rD <- type $rD <- $rA",       ),
            #( "  .0d.: $rD <- $rD <- type $rA",       ),
            #( "  .0e.: $rD <- type $rD <- FIELD_A",   ),
            ## Binary ALU group                      EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .1..: $rD <- $rA ^ $rB",             oc.alu,      ao.a_xor_b,   None,        None,        None,          pre_field_a,    pre_field_b,        pre_field_d,   reg_val_a,       reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "$ .2..: $rD <- $rA | $rB",             oc.alu,      ao.a_or_b,    None,        None,        None,          pre_field_a,    pre_field_b,        pre_field_d,   reg_val_a,       reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .3..: $rD <- $rA & $rB",             oc.alu,      ao.a_and_b,   None,        None,        None,          pre_field_a,    pre_field_b,        pre_field_d,   reg_val_a,       reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .4..: $rD <- $rA + $rB",             oc.alu,      ao.a_plus_b,  None,        None,        None,          pre_field_a,    pre_field_b,        pre_field_d,   reg_val_a,       reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .5..: $rD <- $rA - $rB",             oc.alu,      ao.a_minus_b, None,        None,        None,          pre_field_a,    pre_field_b,        pre_field_d,   reg_val_a,       reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            #( "  .a..: $rD <- TYPE_NAME $rB",         ),
            ( "  .b..: $rD <- tiny $rB + FIELD_A",    oc.alu,      ao.a_plus_b,  None,        None,        None,          pre_field_b,    None,               pre_field_d,   reg_val_a,       buf_ones_field_a,    None,             None,   0,  0,  0,  0,  0 ),
            # Load immediate group                   EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "$ .00f: $rD <- VALUE",                 oc.alu,      ao.a_or_b,    None,        None,        None,          None,           None,               pre_field_d,   buf_field_e,     0,                   None,             None,   0,  0,  0,  0,  0 ),
            ( "  20ef: $pc <- VALUE",                 oc.branch,   None,         None,        bo.pc_w,     None,          None,           None,               None,          buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  30ef: $tpc <- VALUE",                oc.branch,   None,         None,        bo.tpc_w,    None,          None,           None,               None,          buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  40ef: call VALUE",                   oc.branch,   None,         None,        bo.pc_w,     None,          None,           None,               REG_SP,        buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            #( "  80ef: type $r0...$r7 <- VALUE", ),
            #( "  90ef: type $r8...$r14 <- VALUE, ),
            # Constant ALU group                     EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .1.f: $rD <- FIELD_E ^ $rB",         oc.alu,      ao.a_xor_b,   None,        None,        None,          None,           pre_field_b,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .2.f: $rD <- FIELD_E | $rB",         oc.alu,      ao.a_or_b,    None,        None,        None,          None,           pre_field_b,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "$ .3.f: $rD <- FIELD_E & $rB",         oc.alu,      ao.a_and_b,   None,        None,        None,          None,           pre_field_b,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .4.f: $rD <- FIELD_E + $rB",         oc.alu,      ao.a_plus_b,  None,        None,        None,          None,           pre_field_b,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .5.f: $rD <- FIELD_E - $rB",         oc.alu,      ao.a_minus_b, None,        None,        None,          None,           pre_field_b,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            # Short load immediate group             EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "$ .0f0: $rD <- short VALUE",           oc.alu,      ao.a_or_b,    None,        None,        None,          None,           None,               pre_field_d,   buf_field_e,     0,                   None,             None,   0,  0,  0,  0,  0 ),
            ( "  20fe: $pc <- short VALUE",           oc.branch,   None,         None,        bo.pc_w,     None,          None,           None,               None,          buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  30fe: $tpc <- short VALUE",          oc.branch,   None,         None,        bo.tpc_w,    None,          None,           None,               None,          buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  40fe: call short VALUE",             oc.branch,   None,         None,        bo.pc_w,     None,          None,           None,               REG_SP,        buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            # Short constant ALU group               EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .1f.: $rD <- FIELD_E ^ $rA",         oc.alu,      ao.a_xor_b,   None,        None,        None,          None,           pre_field_a,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .2f.: $rD <- FIELD_E | $rA",         oc.alu,      ao.a_or_b,    None,        None,        None,          None,           pre_field_a,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .3f.: $rD <- FIELD_E & $rA",         oc.alu,      ao.a_and_b,   None,        None,        None,          None,           pre_field_a,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "$ .4f.: $rD <- FIELD_E + $rA",         oc.alu,      ao.a_plus_b,  None,        None,        None,          None,           pre_field_a,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .5f.: $rD <- FIELD_E - $rA",         oc.alu,      ao.a_minus_b, None,        None,        None,          None,           pre_field_a,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            # Zero-compare conditional branch group  EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  f00.: if $rA == 0",                  oc.branch,   ao.a_minus_b, None,        bo.cb_eq,    None,          pre_field_a,    None,               None,          reg_val_a,       0,                   buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f01.: if $rA != 0",                  oc.branch,   ao.a_minus_b, None,        bo.cb_ne,    None,          pre_field_a,    None,               None,          reg_val_a,       0,                   buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f02.: if $rA < 0",                   oc.branch,   ao.a_minus_b, None,        bo.cb_lts,   None,          pre_field_a,    None,               None,          reg_val_a,       0,                   buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f03.: if $rA >= 0",                  oc.branch,   ao.a_minus_b, None,        bo.cb_ges,   None,          pre_field_a,    None,               None,          reg_val_a,       0,                   buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f04.: if $rA > 0",                   oc.branch,   ao.a_minus_b, None,        bo.cb_lts,   None,          None,           pre_field_a,        None,          0,               reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f05.: if $rA <= 0",                  oc.branch,   ao.a_minus_b, None,        bo.cb_ges,   None,          None,           pre_field_a,        None,          0,               reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f08.: if $rA == 0",                  oc.branch,   ao.a_minus_b, None,        bo.cb_eq,    None,          pre_field_a,    None,               None,          reg_val_a,       0,                   buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f09.: if $rA != 0",                  oc.branch,   ao.a_minus_b, None,        bo.cb_ne,    None,          pre_field_a,    None,               None,          reg_val_a,       0,                   buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f0a.: if $rA < 0",                   oc.branch,   ao.a_minus_b, None,        bo.cb_lts,   None,          pre_field_a,    None,               None,          reg_val_a,       0,                   buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f0b.: if $rA >= 0",                  oc.branch,   ao.a_minus_b, None,        bo.cb_ges,   None,          pre_field_a,    None,               None,          reg_val_a,       0,                   buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f0c.: if $rA > 0",                   oc.branch,   ao.a_minus_b, None,        bo.cb_lts,   None,          None,           pre_field_a,        None,          0,               reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f0d.: if $rA <= 0",                  oc.branch,   ao.a_minus_b, None,        bo.cb_ges,   None,          None,           pre_field_a,        None,          0,               reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            # Conditional branch group               EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  f1..: if $rB == $rA",                oc.branch,   ao.a_minus_b, None,        bo.cb_eq,    None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f2..: if $rB != $rA",                oc.branch,   ao.a_minus_b, None,        bo.cb_ne,    None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f3..: if signed $rB < $rA",          oc.branch,   ao.a_minus_b, None,        bo.cb_lts,   None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f4..: if signed $rB >= $rA",         oc.branch,   ao.a_minus_b, None,        bo.cb_ges,   None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f5..: if $rB < $rA",                 oc.branch,   ao.a_minus_b, None,        bo.cb_lt,    None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f6..: if $rB >= $rA",                oc.branch,   ao.a_minus_b, None,        bo.cb_ge,    None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f9..: if $rB == $rA",                oc.branch,   ao.a_minus_b, None,        bo.cb_eq,    None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  fa..: if $rB != $rA",                oc.branch,   ao.a_minus_b, None,        bo.cb_ne,    None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  fb..: if signed $rB < $rA",          oc.branch,   ao.a_minus_b, None,        bo.cb_lts,   None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  fc..: if signed $rB >= $rA",         oc.branch,   ao.a_minus_b, None,        bo.cb_ges,   None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  fd..: if $rB < $rA",                 oc.branch,   ao.a_minus_b, None,        bo.cb_lt,    None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  fe..: if $rB >= $rA",                oc.branch,   ao.a_minus_b, None,        bo.cb_ge,    None,          pre_field_b,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      None,   0,  0,  0,  0,  0 ),
            # Bit-set-test branch group              EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  f.f.: if $rA[.]  == 1",              oc.branch,   None,         None,        bo.bb_one,   None,          pre_field_a,    None,               None,          reg_val_a,       buf_field_c,         buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f..f: if $rB[.]  == 0",              oc.branch,   None,         None,        bo.bb_zero,  None,          pre_field_b,    None,               None,          reg_val_a,       buf_field_c,         buf_field_e,      None,   0,  0,  0,  0,  0 ),
            # Stack group                            EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "$ .c**: MEM[$rA+tiny OFS*4] <- $rD",   oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    pre_tiny_field_a,   None,          reg_val_a,       reg_val_b,           buf_tiny_ofs,     a32,    0,  0,  0,  0,  0 ),
            ( "$ .d**: $rD <- MEM[$rA+tiny OFS*4]",   oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_tiny_field_a,   pre_field_d,   None,            reg_val_b,           buf_tiny_ofs,     a32,    0,  0,  0,  0,  0 ),
            # Indirect load/store group              EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "$ .e4.: $rD <- MEM8[$rA]",             oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           0,                a8,     0,  0,  1,  0,  0 ),
            ( "  .e5.: $rD <- MEM16[$rA]",            oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           0,                a16,    0,  0,  0,  1,  0 ),
            ( "  .e6.: $rD <- MEM32[$rA]",            oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            ( "  .e7.: $rD <- MEMLL32[$rA]",          oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            ( "$ .e8.: MEM8[$rA] <- $rD",             oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    pre_field_a,        None,          reg_val_a,       reg_val_b,           0,                a8,     0,  0,  0,  0,  0 ),
            ( "  .e9.: MEM16[$rA] <- $rD",            oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    pre_field_a,        None,          reg_val_a,       reg_val_b,           0,                a16,    0,  0,  0,  0,  0 ),
            ( "  .ea.: MEM32[$rA] <- $rD",            oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    pre_field_a,        None,          reg_val_a,       reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            ( "  .eb.: MEMSC32[$rA] <- $rD",          oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    pre_field_a,        pre_field_d,   reg_val_a,       reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            ( "  .ec.: $rD <- SMEM8[$rA]",            oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           0,                a8,     1,  0,  0,  0,  0 ),
            ( "  .ed.: $rD <- SMEM16[$rA]",           oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           0,                a16,    0,  1,  0,  0,  0 ),
            # Indirect jump group                    EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  1ee.: INV[$rA]",                     oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            ( "  2ee.: $pc <- MEM32[$rA]",            oc.branch_ind, None,       None,        bo.pc_w_ind, lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            ( "  3ee.: $tpc <- MEM32[$rA]",           oc.branch_ind, None,       None,        bo.tpc_w_ind,lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            ( "  4ee.: call MEM32[$rA]",              oc.branch_ind, None,       None,        bo.pc_w_ind, lo.load,       None,           pre_field_a,        REG_SP,        None,            reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            # Offset-indirect load/store group       EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .f4.: $rD <- MEM8[$rA+FIELD_E]",     oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           buf_field_e,      a8,     0,  0,  1,  0,  0 ),
            ( "  .f5.: $rD <- MEM16[$rA+FIELD_E]",    oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           buf_field_e,      a16,    0,  0,  0,  1,  0 ),
            ( "  .f6.: $rD <- MEM32[$rA+FIELD_E]",    oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  .f7.: $rD <- MEMLL32[$rA+FIELD_E]",  oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  .f8.: MEM8[$rA+FIELD_E] <- $rD",     oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      a8,     0,  0,  0,  0,  0 ),
            ( "  .f9.: MEM16[$rA+FIELD_E] <- $rD",    oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      a16,    0,  0,  0,  0,  0 ),
            ( "  .fa.: MEM32[$rA+FIELD_E] <- $rD",    oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    pre_field_a,        None,          reg_val_a,       reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  .fb.: MEMSC32[$rA+FIELD_E] <- $rD",  oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    pre_field_a,        pre_field_d,   reg_val_a,       reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  .fc.: $rD <- SMEM8[$rA+FIELD_E]",    oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           buf_field_e,      a8,     1,  0,  0,  0,  0 ),
            ( "  .fd.: $rD <- SMEM16[$rA+FIELD_E]",   oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        pre_field_d,   None,            reg_val_b,           buf_field_e,      a16,    0,  1,  0,  0,  0 ),
            # Offset-indirect jump group             EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  1fe.: INV[$rA+FIELD_E]",             oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  2fe.: $pc <- MEM32[$rA+FIELD_E]",    oc.branch_ind, None,       None,        bo.pc_w_ind, lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  3fe.: $tpc <- MEM32[$rA+FIELD_E]",   oc.branch_ind, None,       None,        bo.tpc_w_ind,lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  4fe.: call MEM32[$rA+FIELD_E]",      oc.branch_ind, None,       None,        bo.pc_w_ind, lo.load,       None,           pre_field_a,        REG_SP,        None,            reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            # CSR group                              EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .0f8: $rD <- CSR[FIELD_E]",          oc.ld_st,    None,         None,        None,        lo.csr_load,   None,           None,               pre_field_d,   None,            0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  .0f9: CSR[FIELD_E] <- $rD",          oc.ld_st,    None,         None,        None,        lo.csr_store,  pre_field_d,    None,               None,          reg_val_a,       0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            # Absolute load/store group              EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .f4f: $rD <- MEM8[FIELD_E]",         oc.ld_st,    None,         None,        None,        lo.load,       None,           None,               pre_field_d,   None,            0,                   buf_field_e,      a8,     0,  0,  1,  0,  0 ),
            ( "  .f5f: $rD <- MEM16[FIELD_E]",        oc.ld_st,    None,         None,        None,        lo.load,       None,           None,               pre_field_d,   None,            0,                   buf_field_e,      a16,    0,  0,  0,  1,  0 ),
            ( "  .f6f: $rD <- MEM32[FIELD_E]",        oc.ld_st,    None,         None,        None,        lo.load,       None,           None,               pre_field_d,   None,            0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  .f7f: $rD <- MEMLL32[FIELD_E]",      oc.ld_st,    None,         None,        None,        lo.load,       None,           None,               pre_field_d,   None,            0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  .f8f: MEM8[FIELD_E] <- $rD",         oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    None,               None,          reg_val_a,       0,                   buf_field_e,      a8,     0,  0,  0,  0,  0 ),
            ( "  .f9f: MEM16[FIELD_E] <- $rD",        oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    None,               None,          reg_val_a,       0,                   buf_field_e,      a16,    0,  0,  0,  0,  0 ),
            ( "  .faf: MEM32[FIELD_E] <- $rD",        oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    None,               None,          reg_val_a,       0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  .fbf: MEMSC32[FIELD_E] <- $rD",      oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    None,               pre_field_d,   reg_val_a,       0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  .fcf: $rD <- SMEM8[FIELD_E]",        oc.ld_st,    None,         None,        None,        lo.load,       None,           None,               pre_field_d,   None,            0,                   buf_field_e,      a8,     1,  0,  0,  0,  0 ),
            ( "  .fdf: $rD <- SMEM16[FIELD_E]",       oc.ld_st,    None,         None,        None,        lo.load,       None,           None,               pre_field_d,   None,            0,                   buf_field_e,      a16,    0,  1,  0,  0,  0 ),
            # Absolute jump group                    EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RES_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  1fef: INV[FIELD_E]",                 oc.ld_st,    None,         None,        None,        lo.load,       None,           None,               None,          None,            0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  2fef: $pc <- MEM32[FIELD_E]",        oc.branch_ind, None,       None,        bo.pc_w_ind, lo.load,       None,           None,               None,          None,            0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  3fef: $tpc <- MEM32[FIELD_E]",       oc.branch_ind, None,       None,        bo.tpc_w_ind,lo.load,       None,           None,               None,          None,            0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  4fef: call MEM32[FIELD_E]",          oc.branch_ind, None,       None,        bo.pc_w_ind, lo.load,       None,           None,               REG_SP,        None,            0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
        )

        def optimize_selector(selectors, selector_name, name_prefix="group_"):
            # Here, we look through all the selected items and group the selectors into as few groups as possible.
            groups = dict()
            for (selector, selected) in zip(selectors[::2],selectors[1::2]):
                if selected not in groups:
                    groups[selected] = []
                groups[selected].append(selector)
            # Re-create a new list by combining all the selectors for a given group
            final_list = []
            for idx, (selected, selector_list) in enumerate(groups.items()):
                group_selector = or_gate(*selector_list)
                setattr(self, f"{name_prefix}{idx+1}_for_{selector_name}", group_selector)
                final_list += (group_selector, selected)
            return final_list

        def is_mini_set(full_mask:str) -> bool:
            return full_mask.strip()[0] == "$"

        def parse_bit_mask(full_mask: str) -> Tuple[Wire, str]:
            """Create an expression that checks for the provided pattern

            Args:
                full_mask (str): bit-mask string in the format of .-s, *-s and hex digits, as described in the decode table

            Returns:
                Wire: An expression that returns '1' if the instruction code matches that pattern, '0' otherwise.
            """
            mask = full_mask.split(':')[0].strip() # Remove comment and trailing/leading spaces
            if mask[0] == "$": mask = mask[1:]
            mask = mask.strip()
            ins_name = full_mask.split(':')[1].strip() # This is the comment part, which we'll use to make up the name for the wire
            ins_name = ins_name.replace('<-', 'eq')
            ins_name = ins_name.replace('-$', 'minus_')
            ins_name = ins_name.replace('$', '')
            ins_name = ins_name.replace('[.]', '_bit')
            ins_name = ins_name.replace('[', '_')
            ins_name = ins_name.replace(']', '')
            ins_name = ins_name.replace('>>>', 'asr')
            ins_name = ins_name.replace('>>', 'lsr')
            ins_name = ins_name.replace('<<', 'lsl')
            ins_name = ins_name.replace('&', 'and')
            ins_name = ins_name.replace('|', 'or')
            ins_name = ins_name.replace('^', 'xor')
            ins_name = ins_name.replace('+', 'plus')
            ins_name = ins_name.replace('-', 'minus')
            ins_name = ins_name.replace('*', 'times')
            ins_name = ins_name.replace('~', 'not')
            ins_name = ins_name.replace('<=', 'le')
            ins_name = ins_name.replace('>=', 'ge')
            ins_name = ins_name.replace('<', 'lt')
            ins_name = ins_name.replace('>', 'gt')
            ins_name = ins_name.replace('==', 'eq')
            ins_name = ins_name.replace('!=', 'ne')
            ins_name = ins_name.replace(' ', '_')
            ins_name = ins_name.lower()
            # If we're creating the buffered decode signals by simply registering the unbuffered ones, we only need to generate the 'pre' versions.
            if self.register_mask_signals:
                field_sets      = ((pre_field_d,      pre_field_c,      pre_field_b,      pre_field_a),      )
                field_is_f_sets = ((pre_field_d_is_f, pre_field_c_is_f, pre_field_b_is_f, pre_field_a_is_f), )
            else:
                field_sets      = ((pre_field_d,      pre_field_c,      pre_field_b,      pre_field_a),      (buf_field_d,      buf_field_c,      buf_field_b,      buf_field_a)     )
                field_is_f_sets = ((pre_field_d_is_f, pre_field_c_is_f, pre_field_b_is_f, pre_field_a_is_f), (buf_field_d_is_f, buf_field_c_is_f, buf_field_b_is_f, buf_field_a_is_f))
            expressions = []
            for fields, field_is_fs in zip(field_sets, field_is_f_sets):
                idx = 0
                expr = 1
                bitmask = ""
                for field, field_is_f in zip(fields, field_is_fs):
                    digit = mask[idx]
                    bitmask += digit
                    if digit == '.':
                        expr = expr & ~field_is_f
                    elif digit == '*':
                        pass
                    elif digit in ('0123456789abcdef'):
                        value = int(digit, 16)
                        expr = expr & (field == value)
                    else:
                        raise SyntaxErrorException(f"Unknown digit {digit} in decode mask {full_mask}")
                    idx += 1
                expressions.append(expr)
            # Generate the registered version, if that's the way we want to go
            if self.register_mask_signals:
                assert len(expressions) == 1
                expressions.append(Reg(expressions[0], clock_en=buf_en))
            return *expressions, bitmask, ins_name

        # Field and their mapping to output signals:
        CODE       =  0    #
        EXEC_UNIT  =  1    #    exec_unit = EnumNet(op_class)
        ALU_OP     =  2    #    alu_op = EnumNet(alu_ops)
        SHIFTER_OP =  3    #    shifter_op = EnumNet(shifter_ops)
        BRANCH_OP  =  4    #    branch_op = EnumNet(branch_ops)
        LDST_OP    =  5    #    ldst_op = EnumNet(ldst_ops)
        RD1_ADDR   =  6    #
        RD2_ADDR   =  7    #
        RES_ADDR   =  8    #    result_reg_addr = BrewRegAddr
        OP_A       =  9    #    op_a = BrewData
        OP_B       = 10    #    op_b = BrewData
        OP_C       = 11    #    op_c = BrewData
        MEM_LEN    = 12    #    mem_access_len = Unsigned(2) # 0 for 8-bit, 1 for 16-bit, 2 for 32-bit
        BSE        = 13    #    do_bse = logic
        WSE        = 14    #    do_wse = logic
        BZE        = 15    #    do_bze = logic
        WZE        = 16    #    do_wze = logic
        WOI        = 17    #    woi = logic

        if self.use_mini_table:
            inst_table = tuple(line for line in full_inst_table if is_mini_set(line[CODE]))
        else:
            inst_table = full_inst_table

        print("Available instructions:")
        for inst in inst_table:
            print(f"    {inst[0]}")

        # At this point we have all the required selections for the various control lines in 'inst_table' and their selection expressions in 'mask_expressions'.
        # All we need to do is to create the appropriate 'SelectOne' expressions.

        buf_mask_expressions = []
        pre_mask_expressions = []
        mask_bitmasks = []
        mask_expression_names = set()
        for pre_expr, buf_expr, bitmask, name in (parse_bit_mask(line[CODE]) for line in inst_table):
            idx = 1
            base_name = name
            while name in mask_expression_names:
                name = f"{base_name}_{idx}"
                idx += 1
            mask_expression_names.add(name)
            setattr(self, f"mask_for_buf_{name}", buf_expr)
            buf_mask_expressions.append(buf_expr)
            setattr(self, f"mask_for_pre_{name}", pre_expr)
            pre_mask_expressions.append(pre_expr)
            mask_bitmasks.append(bitmask)

        if self.use_decode_rom:
            # Compression groups have '0..f' for exact match, '.' for non-f match and 'X' for match non-F and retain.
            # There could be at most one X in a group
            # Any instruction should match exactly one compression group. This is checked during group
            # generation. Group IDs are just indices into the 'compression_groups' array
            compression_groups = (
                ("  .X..", "_12345678ab____"),
                ("  .X.f", "_12345678______"),
                ("  .Xf.", "_12345678______"),
                ("  X000", "0123456789a____"),
                ("  .00X", "_12345_________"),
                ("  .0X.", "_123456789__cde"),
                ("  .00f", "_______________"),
                ("  20ef", "_______________"),
                ("  30ef", "_______________"),
                ("  40ef", "_______________"),
                ("  .0f0", "_______________"),
                ("  20fe", "_______________"),
                ("  30fe", "_______________"),
                ("  40fe", "_______________"),
                ("  f0X.", "0123456789abcd_"),
                ("  fX..", "_123456789abcde"),
                ("  f.f.", "_______________"),
                ("  f..f", "_______________"),
                ("  .c**", "_______________"),
                ("  .d**", "_______________"),
                ("  .eX.", "____456789abcd_"),
                ("  1ee.", "_______________"),
                ("  2ee.", "_______________"),
                ("  3ee.", "_______________"),
                ("  4ee.", "_______________"),
                ("  .fX.", "____456789abcd_"),
                ("  1fe.", "_______________"),
                ("  2fe.", "_______________"),
                ("  3fe.", "_______________"),
                ("  4fe.", "_______________"),
                ("  .0f8", "_______________"),
                ("  .0f9", "_______________"),
                ("  .fXf", "____456789abcd_"),
                ("  1fef", "_______________"),
                ("  2fef", "_______________"),
                ("  3fef", "_______________"),
                ("  4fef", "_______________"),
            )
            # Generate check that all instructions belong to exactly one compression group
            def is_inst_in_group(instrunction: str, grp: str, x_match: str):
                grp = grp.strip()
                instrunction = instrunction.split(':')[0].replace("$","").strip()
                for (digit, g_digit) in zip(instrunction, grp):
                    if g_digit == "." and digit in "0123456789abcde.*": continue
                    if g_digit == "X" and digit in "0123456789abcde.*":
                        if digit in x_match: continue
                        if digit in ".*": continue
                        return False
                    if g_digit != digit:
                        if digit == "." and g_digit == "f": return False
                        if digit == "*": continue
                        return False
                return True
            inst_to_grp = []
            for inst in inst_table:
                found = False
                for idx, (grp, x_match) in enumerate(compression_groups):
                    if is_inst_in_group(inst[0], grp, x_match):
                        if found:
                            print(f"Instruction {inst[0]} matches group {compression_groups[inst_to_grp[-1]]} and {grp}")
                        inst_to_grp.append(idx)
                        found = True

            # We start by creating the group selector expressions
            group_selectors = []

            for grp_idx, (mask, x_match) in enumerate(compression_groups):
                idx = 0
                selector_terms = []
                selected = 0
                mask = mask.split(':')[0].replace("$","").strip()
                for field, field_is_f in zip((buf_field_d, buf_field_c, buf_field_b, buf_field_a), (buf_field_d_is_f, buf_field_c_is_f, buf_field_b_is_f, buf_field_a_is_f)):
                    do_gt = mask[idx] == '>'
                    do_lt = mask[idx] == '<'
                    if do_gt or do_lt: idx += 1
                    digit = mask[idx]

                    if digit == '.':
                        selector_terms.append(~field_is_f)
                    elif digit == '*':
                        pass
                    elif digit in ('0123456789abcdef'):
                        value = int(digit, 16)
                        if do_gt:
                            selector_terms.append((field > value) & ~field_is_f)
                        elif do_lt:
                            selector_terms.append(field < value)
                        else:
                            selector_terms.append(field == value)
                    elif digit == 'X':
                        options = 0
                        for option in x_match:
                            if option == '_': continue
                            options = options | (field == int(option,base=16))
                        selector_terms.append(options)
                        selected = field
                    else:
                        raise SyntaxErrorException(f"Unknown digit {digit} in decode mask {mask}")
                    selector = and_gate(*selector_terms)
                    group_selectors += (selector, concat(f"6'b{grp_idx:05b}", selected))
                    idx += 1

            self.decode_rom_addr = Wire(Unsigned(10))
            #self.decode_rom_addr <<= SelectOne(*group_selectors)
            self.decode_rom_addr <<= SelectOne(*optimize_selector(group_selectors, "decoder_rom", "inst_group_"))


        select_list_exec_unit  = []
        select_list_alu_op     = []
        select_list_shifter_op = []
        select_list_branch_op  = []
        select_list_ldst_op    = []
        pre_select_list_rd1_addr   = []
        pre_select_list_rd2_addr   = []
        pre_select_list_res_addr   = []
        select_list_op_a       = []
        select_list_op_b       = []
        select_list_op_c       = []
        select_list_mem_len    = []
        select_list_bse        = []
        select_list_wse        = []
        select_list_bze        = []
        select_list_wze        = []
        select_list_int_en     = []

        select_lists = (
            select_list_exec_unit,
            select_list_alu_op,
            select_list_shifter_op,
            select_list_branch_op,
            select_list_ldst_op,
            pre_select_list_rd1_addr,
            pre_select_list_rd2_addr,
            pre_select_list_res_addr,
            select_list_op_a,
            select_list_op_b,
            select_list_op_c,
            select_list_mem_len,
            select_list_bse,
            select_list_wse,
            select_list_bze,
            select_list_wze,
            select_list_int_en,
        )

        bitmask_list_exec_unit  = OrderedDict()
        bitmask_list_alu_op     = OrderedDict()
        bitmask_list_shifter_op = OrderedDict()
        bitmask_list_branch_op  = OrderedDict()
        bitmask_list_ldst_op    = OrderedDict()
        pre_bitmask_list_rd1_addr   = OrderedDict()
        pre_bitmask_list_rd2_addr   = OrderedDict()
        pre_bitmask_list_res_addr   = OrderedDict()
        bitmask_list_op_a       = OrderedDict()
        bitmask_list_op_b       = OrderedDict()
        bitmask_list_op_c       = OrderedDict()
        bitmask_list_mem_len    = OrderedDict()
        bitmask_list_bse        = OrderedDict()
        bitmask_list_wse        = OrderedDict()
        bitmask_list_bze        = OrderedDict()
        bitmask_list_wze        = OrderedDict()
        bitmask_list_int_en     = OrderedDict()

        bitmask_lists = (
            bitmask_list_exec_unit,
            bitmask_list_alu_op,
            bitmask_list_shifter_op,
            bitmask_list_branch_op,
            bitmask_list_ldst_op,
            pre_bitmask_list_rd1_addr,
            pre_bitmask_list_rd2_addr,
            pre_bitmask_list_res_addr,
            bitmask_list_op_a,
            bitmask_list_op_b,
            bitmask_list_op_c,
            bitmask_list_mem_len,
            bitmask_list_bse,
            bitmask_list_wse,
            bitmask_list_bze,
            bitmask_list_wze,
            bitmask_list_int_en,
        )


        for line, pre_mask_expr, buf_mask_expr, bitmask in zip(inst_table, pre_mask_expressions, buf_mask_expressions, mask_bitmasks):
            for idx, (select_list, bitmask_list, value) in enumerate(zip(select_lists, bitmask_lists, line[EXEC_UNIT:])):
                idx += 1 # We are skipping the first column, so we have to accommodate it here

                # RF drive signals are generated from pre-buffer expresisons
                if idx in (RD1_ADDR, RD2_ADDR, RES_ADDR):
                    assert not isinstance(value, str)
                    select_list += (pre_mask_expr, value)
                    if value not in bitmask_list: bitmask_list[value] = []
                    bitmask_list[value].append(bitmask)
                else:
                    # Remove all the 0-s from the selectors for these fields and rely on default_ports to restore them
                    if idx in (BSE, WSE, BZE, WZE, WOI) and value == 0:
                        value = None
                    if value is not None:
                        select_list += (buf_mask_expr, value)
                        if value not in bitmask_list: bitmask_list[value] = []
                        bitmask_list[value].append(bitmask)

        #### DEBUG ####
        # Dump the selectors into a file
        #with open("masklist.csv", "wt") as masklist_file:
        #    for bitmask in bitmask_lists:
        #        for masklist in bitmask.values():
        #            masklist_file.write(",".join(masklist)+"\n")


        # ... actually a little more than that: we have to also generate the reservation logic. So let's start with that.
        pre_select_list_read1_needed = []
        pre_select_list_read2_needed = []
        pre_select_list_rsv_needed = []

        for line, pre_mask_expr in zip(inst_table, pre_mask_expressions):
            for select_list, value in zip((pre_select_list_read1_needed, pre_select_list_read2_needed, pre_select_list_rsv_needed), line[RD1_ADDR:RES_ADDR+1]):
                if value is not None: select_list += (pre_mask_expr, 1)



        # Now that we have the selection lists, we can compose the muxes
        # We will use the default ports to create an 'exc_unknown_inst' exception in case no selectors hit. We only need to set the EXEC_UNIT and BRANCH_OP fields.
        exec_unit      = SelectOne(*optimize_selector(select_list_exec_unit,      "exec_unit"), default_port = op_class.branch)         if len(select_list_exec_unit) > 0 else None
        alu_op         = SelectOne(*optimize_selector(select_list_alu_op,         "alu_op"))                                            if len(select_list_alu_op) > 0 else None
        shifter_op     = SelectOne(*optimize_selector(select_list_shifter_op,     "shifter_op"))                                        if len(select_list_shifter_op) > 0 else None
        branch_op      = SelectOne(*optimize_selector(select_list_branch_op,      "branch_op"), default_port=branch_ops.unknown)        if len(select_list_branch_op) > 0 else None
        ldst_op        = SelectOne(*optimize_selector(select_list_ldst_op,        "ldst_op"))                                           if len(select_list_ldst_op) > 0 else None
        pre_rd1_addr   = SelectOne(*optimize_selector(pre_select_list_rd1_addr,   "pre_rd1_addr"))                                      if len(pre_select_list_rd1_addr) > 0 else None
        pre_rd2_addr   = SelectOne(*optimize_selector(pre_select_list_rd2_addr,   "pre_rd2_addr"))                                      if len(pre_select_list_rd2_addr) > 0 else None
        pre_res_addr   = SelectOne(*optimize_selector(pre_select_list_res_addr,   "pre_res_addr"))                                      if len(pre_select_list_res_addr) > 0 else None
        op_a           = SelectOne(*optimize_selector(select_list_op_a,           "op_a"))                                              if len(select_list_op_a) > 0 else None
        op_b           = SelectOne(*optimize_selector(select_list_op_b,           "op_b"))                                              if len(select_list_op_b) > 0 else None
        op_c           = SelectOne(*optimize_selector(select_list_op_c,           "op_c"))                                              if len(select_list_op_c) > 0 else None
        mem_len        = SelectOne(*optimize_selector(select_list_mem_len,        "mem_len"))                                           if len(select_list_mem_len) > 0 else None
        bse            = SelectOne(*optimize_selector(select_list_bse,            "bse"), default_port = 0)                             if len(select_list_bse) > 0 else 0
        wse            = SelectOne(*optimize_selector(select_list_wse,            "wse"), default_port = 0)                             if len(select_list_wse) > 0 else 0
        bze            = SelectOne(*optimize_selector(select_list_bze,            "bze"), default_port = 0)                             if len(select_list_bze) > 0 else 0
        wze            = SelectOne(*optimize_selector(select_list_wze,            "wze"), default_port = 0)                             if len(select_list_wze) > 0 else 0
        woi            = SelectOne(*optimize_selector(select_list_int_en,         "woi"), default_port = 0)                             if len(select_list_int_en) > 0 else 0

        pre_read1_needed = Select(self.fetch.av, SelectOne(*optimize_selector(pre_select_list_read1_needed, "pre_read1_needed"), default_port=0) if len(pre_select_list_read1_needed) > 0 else 0, 0)
        pre_read2_needed = Select(self.fetch.av, SelectOne(*optimize_selector(pre_select_list_read2_needed, "pre_read2_needed"), default_port=0) if len(pre_select_list_read2_needed) > 0 else 0, 0)
        pre_rsv_needed   = Select(self.fetch.av, SelectOne(*optimize_selector(pre_select_list_rsv_needed,   "pre_rsv_needed"),   default_port=0) if len(pre_select_list_rsv_needed)   > 0 else 0, 0)

        buf_rsv_needed = Reg(pre_rsv_needed, clock_en=buf_en)
        buf_res_addr   = Reg(pre_res_addr,   clock_en=buf_en)

        # We let the register file handle the hand-shaking for us. We just need to implement the data
        self.fetch.ready <<= self.reg_file_req.ready
        self.reg_file_req.valid <<= self.fetch.valid

        self.output_port.valid <<= self.reg_file_rsp.valid
        self.reg_file_rsp.ready <<= self.output_port.ready

        self.reg_file_req.read1_addr  <<= BrewRegAddr(pre_rd1_addr)
        self.reg_file_req.read1_valid <<= pre_read1_needed
        self.reg_file_req.read2_addr  <<= BrewRegAddr(pre_rd2_addr)
        self.reg_file_req.read2_valid <<= pre_read2_needed
        self.reg_file_req.rsv_addr    <<= BrewRegAddr(pre_res_addr)
        self.reg_file_req.rsv_valid   <<= pre_rsv_needed

        self.output_port.exec_unit             <<= exec_unit
        self.output_port.alu_op                <<= alu_op
        self.output_port.shifter_op            <<= shifter_op if shifter_op is not None else None
        self.output_port.branch_op             <<= branch_op
        self.output_port.ldst_op               <<= ldst_op
        self.output_port.op_a                  <<= op_a
        self.output_port.op_b                  <<= op_b
        self.output_port.op_c                  <<= op_c
        self.output_port.mem_access_len        <<= mem_len
        self.output_port.inst_len              <<= buf_fetch.inst_len
        self.output_port.do_bse                <<= bse
        self.output_port.do_wse                <<= wse
        self.output_port.do_bze                <<= bze
        self.output_port.do_wze                <<= wze
        self.output_port.woi                   <<= woi
        self.output_port.result_reg_addr       <<= BrewRegAddr(buf_res_addr)
        self.output_port.result_reg_addr_valid <<= buf_rsv_needed
        self.output_port.fetch_av              <<= buf_fetch.av

        #self.break_fetch_burst <<= (self.output_port.valid & self.output_port.ready) & ((exec_unit == op_class.ld_st) | (exec_unit == op_class.branch))
        #self.break_fetch_burst <<= (self.output_port.valid & self.output_port.ready) & ((exec_unit == op_class.branch))
        self.break_fetch_burst <<= (self.output_port.valid & self.output_port.ready) & (exec_unit == op_class.ld_st)





def gen():
    def top():
        #return ScanWrapper(DecodeStage, {"clk", "rst"})
        return DecodeStage(use_mini_table = False, use_decode_rom = False)

    netlist = Build.generate_rtl(top, "decode.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    #top_level_name = "DecodeStage"
    #flow = QuartusFlow(
    #    target_dir="q_decode",
    #    top_level=top_level_name,
    #    source_files=("decode.sv",),
    #    clocks=(("clk", 10),),# ("top_clk", 100)),
    #    project_name="decode",
    #    no_timing_report_clocks="clk",
    #    family="MAX 10",
    #    device="10M50DAF672C7G" # Something large with a ton of pins
    #)
    #flow.generate()
    #flow.run()

if __name__ == "__main__":
    gen()
