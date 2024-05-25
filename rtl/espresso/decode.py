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
    RSV_ADDR:      1 --> needs async decode
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
from copy import deepcopy

@dataclass
class SelectorDesc:
    local_port: JunctionBase
    buf_port: JunctionBase
    decoder_port_name: str
    masks: OrderedDict

@dataclass
class SelectorGroup:
    selectors: OrderedDict[str, SelectorDesc]
    name_base: str
    for_rf: bool
    valid_generator: bool
    output_port: JunctionBase
    intermediate_port: JunctionBase
    default_value: JunctionBase = None


def replace_char(s: str, idx: int, c: str) -> str:
    s = list(s)
    s[idx] = c
    return "".join(s)

# Return a new selector that's grouped into as few terms as possible.
#    This is a recursive algorithm
def optimize_once(selector: OrderedDict[str, OrderedDict]) -> OrderedDict[str, OrderedDict]:
    if len(selector) == 1: return selector
    # 1. Find the most common digit in all the 'key' masks
    counts = OrderedDict()
    digits = "*.0123456789abcdef_"
    for digit in digits:
        counts[digit] = [0,0,0,0]

    for key in selector.keys():
        for position in range(4):
            counts[key[position]][position] += 1

    selected_digit = None
    selected_position = None
    max_count = -1
    for digit, count_for_pos in counts.items():
        if digit == "_": continue
        if digit == "*": continue
        for idx, count in enumerate(count_for_pos):
            if count > max_count:
                max_count = count
                selected_digit = digit
                selected_position = idx

    # There's nothing to be optimized
    if max_count == -1:
        return selector
    if max_count == 1:
        return selector

    assert max_count != 0
    assert selected_position is not None
    assert selected_position is not None

    # 2. Create a group of all the terms that match the selected digit at the selected position
    optimized_selector = OrderedDict()
    optimized_term = replace_char("____", selected_position, selected_digit)
    optimized_sub_terms = OrderedDict()
    optimized_selector[optimized_term] = optimized_sub_terms
    for term, sub_terms in selector.items():
        if term[selected_position] == selected_digit:
            term = replace_char(term, selected_position, "_")
            optimized_sub_terms[term] = sub_terms
        else:
            optimized_selector[term] = sub_terms

    return optimized_selector

def optimize_recursively(selector: OrderedDict[str, OrderedDict]) -> OrderedDict[str, OrderedDict]:
    if selector is None: return None
    while True:
        optimized_selector = optimize_once(selector)
        if optimized_selector is selector:
            break
        selector = optimized_selector
    optimized_selector = OrderedDict()
    for term, sub_selectors in selector.items():
        optimized_selector[term] = optimize_recursively(sub_selectors)
    return optimized_selector

def merge_recursively(selector: OrderedDict[str, OrderedDict]) -> OrderedDict[str, OrderedDict]:
    if selector is None: return None

    # If a term has a single sub_selector, we can merge the two
    if len(selector) == 1:
        merged_selector = OrderedDict()
        term, sub_selectors = first(selector.items())
        if len(sub_selectors) == 1:
            term2, sub_selectors = first(sub_selectors.items())
            for digit in range(4):
                assert term2[digit] == "_" or term[digit] == "_"
                if term2[digit] != "_":
                    term = replace_char(term, digit, term2[digit])
            merged_selector[term] = sub_selectors
            changed = True
        else:
            merged_selector[term] = sub_selectors
    else:
        merged_selector = selector

    final_selector = OrderedDict()
    for term, sub_selectors in merged_selector.items():
        final_selector[term] = merge_recursively(sub_selectors)
    return final_selector

def optimize_masks(selector: OrderedDict[str, OrderedDict]) -> OrderedDict[str, OrderedDict]:
    optimized_selector = optimize_recursively(deepcopy(selector))
    #optimized_selector = merge_recursively(optimized_selector)
    return optimized_selector


class DecodeLogic(GenericModule):
    field_a = Input()
    field_b = Input()
    field_c = Input()
    field_d = Input()
    field_a_is_f = Input()
    field_b_is_f = Input()
    field_c_is_f = Input()
    field_d_is_f = Input()

    def construct(self, selector_groups: Sequence[SelectorGroup]):
        for selector_group in selector_groups:
            for selector in selector_group.selectors.values():
                port = Output(logic)
                setattr(self, selector.decoder_port_name, port)
                # Attach the mask-set to the port
                port.masks = deepcopy(selector.masks)

    def body(self):
        pass

    def simulate(self):
        def mask_match(mask: str, fields: Sequence[int], field_is_fs: Sequence[bool]) -> bool:
            def mask_char_match(mask_char: str, field: int, field_is_f: bool) -> bool:
                if mask_char in "*_":
                    return True
                if mask_char == ".":
                    return not field_is_f
                return field == int(mask_char, base=16)

            return all(mask_char_match(mask_char, field, field_is_f) for field, field_is_f, mask_char in zip(fields, field_is_fs, mask))

        while True:
            yield self.get_inputs().values()

            try:
                fields = tuple(int(f.sim_value) for f in (self.field_d, self.field_c, self.field_b, self.field_a))
                field_is_fs = tuple(bool(f.sim_value) for f in (self.field_d_is_f, self.field_c_is_f, self.field_b_is_f, self.field_a_is_f))
            except TypeError:
                # We have Nones --> set all outputs to None
                for output in self.get_outputs().values(): output <<= None
                continue

            #bp = ".*"
            #print(f">>>>>>>>>>>>>>>> GOT: {''.join(f'{a:01x}' for a in fields)}; {''.join(f'{bp[a]}' for a in field_is_fs)}")

            # Recurse through a selector hierarchy and test against the supplied fields
            def test_masks(selector: OrderedDict[str, OrderedDict], fields, field_is_fs) -> bool:
                for mask, sub_selector in selector.items():
                    if (
                        mask_match(mask, fields, field_is_fs) and  # Match the predicate
                        (sub_selector is None or test_masks(sub_selector, fields, field_is_fs)) # And match any of the sub-selectors
                    ): return True
                return False

            for output in self.get_outputs().values():
                try:
                    masks = output.masks
                except AttributeError:
                    continue
                output <<= test_masks(masks, fields, field_is_fs)

    def is_combinational(self) -> bool:
        """
        Returns True if the module is purely combinational, False otherwise
        """
        return True

    def generate(self, netlist: 'Netlist', back_end: 'BackEnd') -> str:
        assert back_end.language == "SystemVerilog", "Unknown back-end specified: {}".format(back_end.language)

        rtl_header = self._impl.generate_module_header(back_end)

        rtl_body =  ""

        #field_a_expr, _ = self.field_a.get_rhs_expression(back_end, target_namespace)
        #field_b_expr, _ = self.field_b.get_rhs_expression(back_end, target_namespace)
        #field_c_expr, _ = self.field_c.get_rhs_expression(back_end, target_namespace)
        #field_d_expr, _ = self.field_d.get_rhs_expression(back_end, target_namespace)
        #field_a_is_f_expr, _ = self.field_a_is_f.get_rhs_expression(back_end, target_namespace)
        #field_b_is_f_expr, _ = self.field_b_is_f.get_rhs_expression(back_end, target_namespace)
        #field_c_is_f_expr, _ = self.field_c_is_f.get_rhs_expression(back_end, target_namespace)
        #field_d_is_f_expr, _ = self.field_d_is_f.get_rhs_expression(back_end, target_namespace)

        def mask_to_verilog(mask: str) -> str:
            fields = "dcba"
            terms = []
            for digit, field in zip(mask, fields):
                if (digit == "."):
                    terms.append(f"~field_{field}_is_f")
                elif (digit in "_*"):
                    pass
                else:
                    terms.append(f"(field_{field} == 4'h{digit})")
                    #terms.append(f"field_{field}_is_{digit}")
            verilog = " & ".join(terms)
            if len(terms) > 1:
                verilog = "(" + verilog + ")"
            return verilog

        def create_selector_verilog(selector: OrderedDict[str, OrderedDict], indent = 1):
            assert selector is not None
            terms = []
            for mask, sub_selectors in selector.items():
                vmask = "\t" * indent + mask_to_verilog(mask)
                if sub_selectors is not None:
                    and_terms = create_selector_verilog(sub_selectors, indent + 1)
                    vmask = vmask + " & (\n" + and_terms + "\n" + "\t" * indent + ")"
                terms.append(vmask)
            joiner = " |\n"
            selector = joiner.join(terms)
            return selector

        for out_port_name, out_port in self.get_outputs().items():
            vselect = create_selector_verilog(out_port.masks)
            rtl_body += "//" + " ".join(f"[{x}]" for x in out_port.masks.keys()) + "\n"
            rtl_body += f"assign {out_port_name} =\n{vselect};\n\n"

        with back_end.indent_block():
            ret_val = (
                str_block(rtl_header, "", "\n\n") +
                str_block(back_end.indent(rtl_body), "", "") +
                "endmodule"
            )
        return ret_val

        return rtl_body
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

        #      CODE                                  EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP    RD1_ADDR    RD2_ADDR        RSV_ADDR   OP_A             OP_B          OP_C        MEM_LEN BSE WSE BZE WZE WOI
        #invalid_instruction =                        (oc.branch,   None,         None,        bo.unknown,  None,      None,       None,           None,      None,            None,         None,       None,   0,  0,  0,  0,  0 )
        if self.has_shift:
            shift_ops = (
                #  CODE                                  EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP    RD1_ADDR        RD2_ADDR        RSV_ADDR       OP_A             OP_B          OP_C        MEM_LEN BSE WSE BZE WZE WOI
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
                #  CODE                                  EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP    RD1_ADDR        RD2_ADDR        RSV_ADDR       OP_A             OP_B          OP_C        MEM_LEN BSE WSE BZE WZE WOI
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
        #      Exception group                       EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
        # These names MUST match that of the signals in DecodeExecIf or RegFileRequestIf
        selector_name_bases = (                     "exec_unit", "alu_op",     "shifter_op","branch_op", "ldst_op",     "read1_addr",   "read2_addr",       "rsv_addr",    "op_a",          "op_b",              "op_c",           "mem_access_len","do_bse","do_wse","do_bze","do_wze","woi")
        full_inst_table = (
            *shift_ops,
            *mult_ops,
            #  Number of bits needed:                     3         3              2            4           2              2                2                   1              3               3                    2                  2     1   1   1   1   1
            #  Exception group                       EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
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
            #  PC manipulation group                 EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .001: FENCE",                        oc.alu,      None,         None,        None,        None,          None,           None,               None,          None,            None,                None,             None,   0,  0,  0,  0,  0 ), # Decoded as a kind of NOP
            ( "$ .002: $pc <- $rD",                   oc.branch,   None,         None,        bo.pc_w,     None,          pre_field_d,    None,               None,          reg_val_a,       None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  .003: $tpc <- $rD",                  oc.branch,   None,         None,        bo.tpc_w,    None,          pre_field_d,    None,               None,          reg_val_a,       None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "$ .004: $rD <- $pc",                   oc.alu,      ao.pc_plus_b, None,        None,        None,          None,           None,               pre_field_d,   None,            0,                   None,             None,   0,  0,  0,  0,  0 ),
            ( "  .005: $rD <- $tpc",                  oc.alu,      ao.tpc,       None,        None,        None,          None,           None,               pre_field_d,   None,            None,                None,             None,   0,  0,  0,  0,  0 ),
            # Unary group                            EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
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
            ## Binary ALU group                      EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .1..: $rD <- $rA ^ $rB",             oc.alu,      ao.a_xor_b,   None,        None,        None,          pre_field_a,    pre_field_b,        pre_field_d,   reg_val_a,       reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "$ .2..: $rD <- $rA | $rB",             oc.alu,      ao.a_or_b,    None,        None,        None,          pre_field_a,    pre_field_b,        pre_field_d,   reg_val_a,       reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .3..: $rD <- $rA & $rB",             oc.alu,      ao.a_and_b,   None,        None,        None,          pre_field_a,    pre_field_b,        pre_field_d,   reg_val_a,       reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .4..: $rD <- $rA + $rB",             oc.alu,      ao.a_plus_b,  None,        None,        None,          pre_field_a,    pre_field_b,        pre_field_d,   reg_val_a,       reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .5..: $rD <- $rA - $rB",             oc.alu,      ao.a_minus_b, None,        None,        None,          pre_field_a,    pre_field_b,        pre_field_d,   reg_val_a,       reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            #( "  .a..: $rD <- TYPE_NAME $rB",         ),
            ( "  .b..: $rD <- tiny $rB + FIELD_A",    oc.alu,      ao.a_plus_b,  None,        None,        None,          pre_field_b,    None,               pre_field_d,   reg_val_a,       buf_ones_field_a,    None,             None,   0,  0,  0,  0,  0 ),
            # Load immediate group                   EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "$ .00f: $rD <- VALUE",                 oc.alu,      ao.a_or_b,    None,        None,        None,          None,           None,               pre_field_d,   buf_field_e,     0,                   None,             None,   0,  0,  0,  0,  0 ),
            ( "  20ef: $pc <- VALUE",                 oc.branch,   None,         None,        bo.pc_w,     None,          None,           None,               None,          buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  30ef: $tpc <- VALUE",                oc.branch,   None,         None,        bo.tpc_w,    None,          None,           None,               None,          buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  40ef: call VALUE",                   oc.branch,   None,         None,        bo.pc_w,     None,          None,           None,               REG_SP,        buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            #( "  80ef: type $r0...$r7 <- VALUE", ),
            #( "  90ef: type $r8...$r14 <- VALUE, ),
            # Constant ALU group                     EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .1.f: $rD <- FIELD_E ^ $rB",         oc.alu,      ao.a_xor_b,   None,        None,        None,          None,           pre_field_b,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .2.f: $rD <- FIELD_E | $rB",         oc.alu,      ao.a_or_b,    None,        None,        None,          None,           pre_field_b,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "$ .3.f: $rD <- FIELD_E & $rB",         oc.alu,      ao.a_and_b,   None,        None,        None,          None,           pre_field_b,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .4.f: $rD <- FIELD_E + $rB",         oc.alu,      ao.a_plus_b,  None,        None,        None,          None,           pre_field_b,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .5.f: $rD <- FIELD_E - $rB",         oc.alu,      ao.a_minus_b, None,        None,        None,          None,           pre_field_b,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            # Short load immediate group             EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "$ .0f0: $rD <- short VALUE",           oc.alu,      ao.a_or_b,    None,        None,        None,          None,           None,               pre_field_d,   buf_field_e,     0,                   None,             None,   0,  0,  0,  0,  0 ),
            ( "  20fe: $pc <- short VALUE",           oc.branch,   None,         None,        bo.pc_w,     None,          None,           None,               None,          buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  30fe: $tpc <- short VALUE",          oc.branch,   None,         None,        bo.tpc_w,    None,          None,           None,               None,          buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            ( "  40fe: call short VALUE",             oc.branch,   None,         None,        bo.pc_w,     None,          None,           None,               REG_SP,        buf_field_e,     None,                None,             None,   0,  0,  0,  0,  0 ),
            # Short constant ALU group               EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .1f.: $rD <- FIELD_E ^ $rA",         oc.alu,      ao.a_xor_b,   None,        None,        None,          None,           pre_field_a,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .2f.: $rD <- FIELD_E | $rA",         oc.alu,      ao.a_or_b,    None,        None,        None,          None,           pre_field_a,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .3f.: $rD <- FIELD_E & $rA",         oc.alu,      ao.a_and_b,   None,        None,        None,          None,           pre_field_a,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "$ .4f.: $rD <- FIELD_E + $rA",         oc.alu,      ao.a_plus_b,  None,        None,        None,          None,           pre_field_a,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            ( "  .5f.: $rD <- FIELD_E - $rA",         oc.alu,      ao.a_minus_b, None,        None,        None,          None,           pre_field_a,        pre_field_d,   buf_field_e,     reg_val_b,           None,             None,   0,  0,  0,  0,  0 ),
            # Zero-compare conditional branch group  EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
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
            # Conditional branch group               EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
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
            # Bit-set-test branch group              EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  f.f.: if $rA[.]  == 1",              oc.branch,   None,         None,        bo.bb_one,   None,          pre_field_a,    None,               None,          reg_val_a,       buf_field_c,         buf_field_e,      None,   0,  0,  0,  0,  0 ),
            ( "  f..f: if $rB[.]  == 0",              oc.branch,   None,         None,        bo.bb_zero,  None,          pre_field_b,    None,               None,          reg_val_a,       buf_field_c,         buf_field_e,      None,   0,  0,  0,  0,  0 ),
            # Stack group                            EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "$ .c**: MEM[$rA+tiny OFS*4] <- $rD",   oc.ld_st,    None,         None,        None,        lo.store,      pre_field_d,    pre_tiny_field_a,   None,          reg_val_a,       reg_val_b,           buf_tiny_ofs,     a32,    0,  0,  0,  0,  0 ),
            ( "$ .d**: $rD <- MEM[$rA+tiny OFS*4]",   oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_tiny_field_a,   pre_field_d,   None,            reg_val_b,           buf_tiny_ofs,     a32,    0,  0,  0,  0,  0 ),
            # Indirect load/store group              EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
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
            # Indirect jump group                    EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  1ee.: INV[$rA]",                     oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            ( "  2ee.: $pc <- MEM32[$rA]",            oc.branch_ind, None,       None,        bo.pc_w_ind, lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            ( "  3ee.: $tpc <- MEM32[$rA]",           oc.branch_ind, None,       None,        bo.tpc_w_ind,lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            ( "  4ee.: call MEM32[$rA]",              oc.branch_ind, None,       None,        bo.pc_w_ind, lo.load,       None,           pre_field_a,        REG_SP,        None,            reg_val_b,           0,                a32,    0,  0,  0,  0,  0 ),
            # Offset-indirect load/store group       EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
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
            # Offset-indirect jump group             EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  1fe.: INV[$rA+FIELD_E]",             oc.ld_st,    None,         None,        None,        lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  2fe.: $pc <- MEM32[$rA+FIELD_E]",    oc.branch_ind, None,       None,        bo.pc_w_ind, lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  3fe.: $tpc <- MEM32[$rA+FIELD_E]",   oc.branch_ind, None,       None,        bo.tpc_w_ind,lo.load,       None,           pre_field_a,        None,          None,            reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  4fe.: call MEM32[$rA+FIELD_E]",      oc.branch_ind, None,       None,        bo.pc_w_ind, lo.load,       None,           pre_field_a,        REG_SP,        None,            reg_val_b,           buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            # CSR group                              EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
            ( "  .0f8: $rD <- CSR[FIELD_E]",          oc.ld_st,    None,         None,        None,        lo.csr_load,   None,           None,               pre_field_d,   None,            0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            ( "  .0f9: CSR[FIELD_E] <- $rD",          oc.ld_st,    None,         None,        None,        lo.csr_store,  pre_field_d,    None,               None,          reg_val_a,       0,                   buf_field_e,      a32,    0,  0,  0,  0,  0 ),
            # Absolute load/store group              EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
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
            # Absolute jump group                    EXEC_UNIT    ALU_OP        SHIFTER_OP   BRANCH_OP    LDST_OP        RD1_ADDR        RD2_ADDR            RSV_ADDR       OP_A             OP_B                 OP_C              MEM_LEN BSE WSE BZE WZE WOI
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

        def get_inst_mask(full_mask: str) -> str:
            mask = full_mask.split(':')[0].strip() # Remove comment and trailing/leading spaces
            if mask[0] == "$": mask = mask[1:]
            mask = mask.strip()
            return mask

        # Field and their mapping to output signals:
        CODE       =  0    #
        EXEC_UNIT  =  1    #    exec_unit = EnumNet(op_class)
        ALU_OP     =  2    #    alu_op = EnumNet(alu_ops)
        SHIFTER_OP =  3    #    shifter_op = EnumNet(shifter_ops)
        BRANCH_OP  =  4    #    branch_op = EnumNet(branch_ops)
        LDST_OP    =  5    #    ldst_op = EnumNet(ldst_ops)
        RD1_ADDR   =  6    #
        RD2_ADDR   =  7    #
        RSV_ADDR   =  8    #    result_reg_addr = BrewRegAddr
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

        # What we care about is this: which instruction (masks) result in the ALU to perform an addition (as an example).
        # For that, for each column of the above table, we collect all the masks that result the same outcome.
        # This we collect into a dict for each column. The key is the output value, the value is the set of masks.
        # This set is also stored as a dict, this time the keys are the masks and the values are None.
        # We use this dict representation for masks as it allows for various optimizations to be performed better
        output_selectors = []
        output_cnt = len(full_inst_table[0]) - 1

        for output_idx, name_base in zip(range(1,output_cnt+1), selector_name_bases):
            for_rf = output_idx in (RD1_ADDR, RD2_ADDR, RSV_ADDR)
            output_port = getattr(self.reg_file_req, name_base) if for_rf else getattr(self.output_port, name_base)
            intermediate_port = Wire()
            setattr(self, f"intermediate_value_for_{name_base.upper()}", intermediate_port)
            output_selector = SelectorGroup(
                selectors = OrderedDict(),
                name_base = name_base,
                for_rf=for_rf,
                valid_generator=False,
                output_port = output_port,
                intermediate_port = intermediate_port
            )
            name_base = name_base.upper()
            wire_idx = 1
            for inst_line in full_inst_table:
                if not is_mini_set(inst_line[0]) and self.use_mini_table:
                    continue
                mask = get_inst_mask(inst_line[0])

                selected = inst_line[output_idx]
                if selected not in output_selector.selectors:
                    # Create a local wire to hold the selector
                    if is_junction_base(selected):
                        selected_name = f"wire_{wire_idx}"
                        wire_idx += 1
                    elif isinstance(selected, float):
                        selected_name = str(selected).replace(".","p")
                    else:
                        # Do some manipulation in case names contain '.'-s
                        selected_name = str(selected).split(".")[-1].upper()
                    # Create a name for the port on the DecoderLogic module; use the same name for local_port
                    # NOTE: the local_port member will eventually be swapped out for an actual Wire, but we
                    #       will do some transformations first that can introduce/eliminate some ports
                    port_name = f"select_{selected_name}_for_output_{name_base}"
                    buf_port_name = f"buf_select_{selected_name}_for_output_{name_base}"
                    output_selector.selectors[selected] = SelectorDesc(local_port=port_name, buf_port=buf_port_name, decoder_port_name=port_name, masks = OrderedDict())
                output_selector.selectors[selected].masks[mask] = None
            output_selectors.append(output_selector)

        # For the RF input groups we need to crate a 'valid' signal
        rf_valid_selectors = []
        for output_selector in output_selectors:
            if output_selector.for_rf:
                name_base = output_selector.name_base.replace("_addr", "_valid")
                output_port = getattr(self.reg_file_req, name_base)
                intermediate_port = Wire()
                setattr(self, f"intermediate_value_for_{name_base.upper()}", intermediate_port)

                valid_selector = SelectorGroup(
                    selectors=OrderedDict(),
                    default_value=0,
                    name_base=name_base,
                    for_rf=True,
                    valid_generator=True,
                    output_port=output_port,
                    intermediate_port=intermediate_port
                )
                masks = OrderedDict()
                # For these, we need to create a 'valid' signal as well
                for selector_key, selector_desc in output_selector.selectors.items():
                    if selector_key is not None:
                        masks.update(selector_desc.masks)
                port_name = f"select_for_output_{name_base.upper()}"
                valid_selector.selectors[1] = SelectorDesc(local_port=port_name,buf_port=None,decoder_port_name=port_name,masks=masks)
                rf_valid_selectors.append(valid_selector)

        # For each group, find the selector with the most conditions and create a default state for them
        for output_selector in output_selectors:
            default_cnt = -1
            default_key = None
            for selector_key, selector_desc in output_selector.selectors.items():
                if len(selector_desc.masks) > default_cnt:
                    default_cnt = len(selector_desc.masks)
                    default_key = selector_key
            if default_cnt > 1:
                output_selector.default_value = default_key
                del output_selector.selectors[default_key]

        # Merge valid selectors into output_selectors
        output_selectors += rf_valid_selectors
        # Create local and buffered ports for everybody; create buffer registers and hook the two up
        for output_selector in output_selectors:
            local_port = Wire()
            setattr(self, f"local_value_for_{output_selector.name_base.upper()}", local_port)

            for selector_key, selector_desc in output_selector.selectors.items():
                local_port = Wire()
                setattr(self, selector_desc.local_port, local_port)
                selector_desc.local_port = local_port
                if not output_selector.for_rf:
                    buf_port = Wire()
                    setattr(self, selector_desc.buf_port, buf_port)
                    selector_desc.buf_port = buf_port
                    buf_port <<= Reg(local_port, clock_en=buf_en)

        # Now we're ready to optimize the selectors
        for output_selector in output_selectors:
            for selector_key, selector_desc in output_selector.selectors.items():
                selector_desc.masks = optimize_masks(selector_desc.masks)

        # Hook up the decode logic instance
        decode_logic = DecodeLogic(output_selectors)
        decode_logic.field_a <<= pre_field_a
        decode_logic.field_b <<= pre_field_b
        decode_logic.field_c <<= pre_field_c
        decode_logic.field_d <<= pre_field_d
        decode_logic.field_a_is_f <<= pre_field_a_is_f
        decode_logic.field_b_is_f <<= pre_field_b_is_f
        decode_logic.field_c_is_f <<= pre_field_c_is_f
        decode_logic.field_d_is_f <<= pre_field_d_is_f
        for output_selector in output_selectors:
            for selector in output_selector.selectors.values():
                selector.local_port <<= getattr(decode_logic, selector.decoder_port_name)

        # For each group, create the final mux
        # For muxes that feed 'execute', we'll use the buffered selectors, for the ones
        # feeding the 'RF' we're going to use the unbuffered ones.
        # NOTE: we don't buffer the *SELECTED* value. That's the responsibility of the decode table above to name the appropriate values
        for output_selector in output_selectors:
            mux_arg_list = []
            for selector_key, selector_desc in output_selector.selectors.items():
                mux_arg_list += [selector_desc.local_port if output_selector.for_rf else selector_desc.buf_port, selector_key]
            if output_selector.default_value is not None:
                output_selector.intermediate_port <<= SelectOne(*mux_arg_list, default_port=output_selector.default_value)
            else:
                output_selector.intermediate_port <<= SelectOne(*mux_arg_list)

        # We need to special-case a few things:
        # 1. fetch.av should mask out all RF request valids
        # 2. fetch.av should also mask out write-back valid
        read1_valid = Select(self.fetch.av, self.intermediate_value_for_READ1_VALID, 0)
        read2_valid = Select(self.fetch.av, self.intermediate_value_for_READ2_VALID, 0)
        rsv_valid = Select(self.fetch.av, self.intermediate_value_for_RSV_VALID, 0)
        rsv_addr = self.intermediate_value_for_RSV_ADDR

        # Hook up execute drivers to their final output
        for output_selector in output_selectors:
            if not output_selector.for_rf:
                out_port = getattr(self.output_port, output_selector.name_base)
                out_port <<= output_selector.intermediate_port

        # We need to deal with the write-back signals and some other signals that aren't directly generated
        buf_rsv_valid  = Reg(rsv_valid, clock_en=buf_en)
        buf_rsv_addr   = Reg(rsv_addr,   clock_en=buf_en)
        self.output_port.result_reg_addr <<= BrewRegAddr(buf_rsv_addr)
        self.output_port.result_reg_addr_valid <<= buf_rsv_valid
        self.output_port.inst_len <<= buf_fetch.inst_len
        self.output_port.fetch_av <<= buf_fetch.av

        # We let the register file handle the hand-shaking for us. We just need to implement the data
        self.fetch.ready <<= self.reg_file_req.ready
        self.reg_file_req.valid <<= self.fetch.valid

        self.output_port.valid <<= self.reg_file_rsp.valid
        self.reg_file_rsp.ready <<= self.output_port.ready

        # Finally we have to hook up the data port of the RF (the responses are already part of the muxes)
        self.reg_file_req.read1_addr  <<= BrewRegAddr(self.intermediate_value_for_READ1_ADDR)
        self.reg_file_req.read1_valid <<= read1_valid
        self.reg_file_req.read2_addr  <<= BrewRegAddr(self.intermediate_value_for_READ2_ADDR)
        self.reg_file_req.read2_valid <<= read2_valid
        self.reg_file_req.rsv_addr    <<= BrewRegAddr(self.intermediate_value_for_RSV_ADDR)
        self.reg_file_req.rsv_valid   <<= rsv_valid

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! THE MUXES HAVE TO BE AFTER THE REGISTERS !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        #self.break_fetch_burst <<= (self.output_port.valid & self.output_port.ready) & ((exec_unit == op_class.ld_st) | (exec_unit == op_class.branch))
        #self.break_fetch_burst <<= (self.output_port.valid & self.output_port.ready) & ((exec_unit == op_class.branch))
        self.break_fetch_burst <<= (self.output_port.valid & self.output_port.ready) & (self.intermediate_value_for_EXEC_UNIT == op_class.ld_st)




def gen():
    def top():
        #return ScanWrapper(DecodeStage, {"clk", "rst"})
        return DecodeStage(use_mini_table = False, use_decode_rom = False)

    netlist = Build.generate_rtl(top, "decode.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    top_level_name = "DecodeStage"
    flow = QuartusFlow(
        target_dir="q_decode",
        top_level=top_level_name,
        source_files=("decode.sv",),
        clocks=(("clk", 10),),# ("top_clk", 100)),
        project_name="decode",
        no_timing_report_clocks="clk",
        family="MAX 10",
        device="10M50DAF672C7G" # Something large with a ton of pins
    )
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()
