#!/usr/bin/python3
from random import *
from typing import *
from silicon import *
from brew_types import *
from brew_utils import *

"""
The front-end decode stage takes 32-bit words from the ICache.

It takes those words and decodes them into (up to) two instructions.

Since instruction length can vary from 16 bits to 64 (with prefix instructions),
some internal state will need to be kept to keep collecting fragments.

The only case when multiple instructions are decoded in a single cycle is
when the bottom word contains the last fragment (maybe the only fragment) of
the current instruction and the upper word is a 16-bit instruction.

Latency is at least 1 cycle.
"""



class FeDecode(Module):
    clk = ClkPort()
    rst = RstPort()

    fetch = Input(FeFetch())
    push_data = Output(FeBeQueue())

    def body(self):
        inst_len_16 = 0
        inst_len_32 = 1
        inst_len_48 = 2

        @module(1)
        def inst_len(inst_word):
            """
            Decodes and returns the instruction length:
                0 -> 16 bits
                1 -> 32 bits
                2 -> 48 bits
            """
            multi_parcel_inst = \
                (field_d(inst_word) == 0xf) | \
                ((field_c(inst_word) == 0xf) & ((field_b(inst_word) != 0xf) | (field_a(inst_word) == 0xf))) | \
                ((field_c(inst_word) == 0xe) & (field_a(inst_word) == 0xf)) | \
                ((field_c(inst_word) < 0xc) & ((field_b(inst_word) == 0xf) | (field_a(inst_word) == 0xf)))

            inst_32_bit = (field_d(inst_word) == 0xf) | (field_a(inst_word) != 0xf)

            # 0 -> 16 bits, 1 -> 32 bits, 2 -> 48 bits
            return concat(
                multi_parcel_inst & ~inst_32_bit,
                multi_parcel_inst &  inst_32_bit
            )

        @module(1)
        def is_prefix_inst(inst_word):
            """
            Decodes if instruction is a prefix one. Returns '1' if it is, '0' otherwise
            """
            return ((field_c(inst_word) & 0xe) == 0xe) | (field_b(inst_word) == 0xf)


        fsm_advance = Wire(logic)
        load_from_top = Wire(logic)

        # Datapath registers
        top_inst_is_prefix_reg = Wire(logic)
        top_inst_len_reg = Wire(Unsigned(2))
        top_inst_reg = Wire(Unsigned(16))
        top_inst_valid_reg = Wire(logic)
        top_inst_pre_cond_reg = Wire(logic) # set over the paths where we load something into top that then needs to be re-loaded into the bottom
        top_inst_fetch_addr = Wire(BrewDWordAddr)

        btm_inst_has_prefix_reg = Wire(logic)
        btm_inst_prefix_reg = Wire(Unsigned(16))
        btm_inst_len_reg = Wire(Unsigned(2))
        btm_inst_reg = Wire(Unsigned(48))
        btm_inst_fetch_addr = Wire(BrewInstAddr)

        # Instruction pre-decode: in this stage, all we care about is whether an instruction is a prefix and what it's length is
        top_inst_fragment = self.fetch.data[31:16]
        top_inst_len = inst_len(top_inst_fragment)
        top_inst_is_prefix = is_prefix_inst(top_inst_fragment) & (top_inst_len == inst_len_16)

        btm_inst_fragment = self.fetch.data[15:0]
        btm_inst_len = inst_len(btm_inst_fragment)
        btm_inst_is_prefix = is_prefix_inst(btm_inst_fragment) & (btm_inst_len == inst_len_16)

        # State machine
        self.decode_fsm = FSM()

        class States(Enum):
            have_0_fragments = 0
            have_1_fragments = 1
            have_2_fragments = 2
            have_all_fragments = 3

        self.decode_fsm.reset_value <<= States.have_0_fragments
        self.decode_fsm.default_state <<= States.have_0_fragments

        fsm_state = Wire()
        fsm_state <<= self.decode_fsm.state
        decode_btm = (self.decode_fsm.state == States.have_0_fragments) | (self.decode_fsm.state == States.have_all_fragments) & (~top_inst_pre_cond_reg | top_inst_is_prefix_reg)
        decode_btm_allow_pref = decode_btm & ~(top_inst_is_prefix_reg & top_inst_pre_cond_reg)

        """
        The following instruction fragment sequences are possible
            btm  top
            ---- ----
            PRE  PRE  # This is invalid and intentionally interpreted as PRE;0of0
            PRE  0of0 # Full prefix instruction into bottom
            PRE  0of1 # Partial prefix+32 instruction into bottom
            PRE  0of2 # Partial prefix+48 instruction into bottom
            0of0 PRE  # Full 16-bit instruction into bottom, **pre-condition next bottom for prefix**
            0of0 0of0 # Two 16-bit instructions
            0of0 0of1 # Full 16-bit instructions, **pre-condition next bottom for 32-bit**
            0of0 0of2 # Full 16-bit instructions, **pre-condition next bottom for 48-bit**
            0of1 1of1 # Full 32-bit instruction into bottom
            0of2 1of2 # Partial 48-bit instruction into bottom
            1of1 PRE  # Final 32-bit instruction into bottom, **pre-condition next bottom for prefix**
            1of1 0of0 # Final 32-bit instruction into bottom, full 16-bit instruction into top
            1of1 0of1 # Final 32-bit instruction into bottom, **pre-condition next bottom for 32-bit**
            1of1 0of2 # Final 32-bit instruction into bottom, **pre-condition next bottom for 48-bit**
            1of2 2of2 # Final 48-bit instruction into bottom
            2of2 PRE  # Final 48-bit instruction into bottom, **pre-condition next bottom for prefix**
            2of2 0of0 # Final 48-bit instruction into bottom, full 16-bit instruction into top
            2of2 0of1 # Final 48-bit instruction into bottom, **pre-condition next bottom for 32-bit**
            2of2 0of2 # Final 48-bit instruction into bottom, **pre-condition next bottom for 48-bit**
        """
        #case_pref_pref = decode_btm_allow_pref & btm_inst_is_prefix & top_inst_is_prefix
        #case_pref_0of0 = decode_btm_allow_pref & btm_inst_is_prefix & ~top_inst_is_prefix & (top_inst_len == inst_len_16)
        inst_len_to_compare = Select(top_inst_pre_cond_reg, btm_inst_len_reg, top_inst_len_reg)
        case_pref_0of0 = decode_btm_allow_pref & btm_inst_is_prefix & (top_inst_len == inst_len_16)
        case_pref_0of1 = decode_btm_allow_pref & btm_inst_is_prefix & (top_inst_len == inst_len_32)
        case_pref_0of2 = decode_btm_allow_pref & btm_inst_is_prefix & (top_inst_len == inst_len_48)
        case_0of0_pref = decode_btm & ~btm_inst_is_prefix & (btm_inst_len == inst_len_16) & top_inst_is_prefix
        case_0of0_0of0 = decode_btm & ~btm_inst_is_prefix & (btm_inst_len == inst_len_16) & ~top_inst_is_prefix & (top_inst_len == inst_len_16)
        case_0of0_0of1 = decode_btm & ~btm_inst_is_prefix & (btm_inst_len == inst_len_16) & (top_inst_len == inst_len_32)
        case_0of0_0of2 = decode_btm & ~btm_inst_is_prefix & (btm_inst_len == inst_len_16) & (top_inst_len == inst_len_48)
        case_0of1_1of1 = decode_btm & (btm_inst_len == inst_len_32)
        case_0of2_1of2 = decode_btm & (btm_inst_len == inst_len_48)
        case_1of1_pref = ~decode_btm & (inst_len_to_compare == inst_len_32) & top_inst_is_prefix
        case_1of1_0of0 = ~decode_btm & (inst_len_to_compare == inst_len_32) & ~top_inst_is_prefix & (top_inst_len == inst_len_16)
        case_1of1_0of1 = ~decode_btm & (inst_len_to_compare == inst_len_32) & (top_inst_len == inst_len_32)
        case_1of1_0of2 = ~decode_btm & (inst_len_to_compare == inst_len_32) & (top_inst_len == inst_len_48)
        case_1of2_2of2 = ~decode_btm & (inst_len_to_compare == inst_len_48)

        case_2of2_pref = (self.decode_fsm.state == States.have_2_fragments) & top_inst_is_prefix
        case_2of2_0of0 = (self.decode_fsm.state == States.have_2_fragments) & ~top_inst_is_prefix & (top_inst_len == inst_len_16)
        case_2of2_0of1 = (self.decode_fsm.state == States.have_2_fragments) & (top_inst_len == inst_len_32)
        case_2of2_0of2 = (self.decode_fsm.state == States.have_2_fragments) & (top_inst_len == inst_len_48)

        # We're in a state where we don't have anything partial
        self.decode_fsm.add_transition(States.have_0_fragments,  fsm_advance & case_pref_0of0, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_0_fragments,  fsm_advance & case_pref_0of1, States.have_1_fragments)
        self.decode_fsm.add_transition(States.have_0_fragments,  fsm_advance & case_pref_0of2, States.have_1_fragments)
        self.decode_fsm.add_transition(States.have_0_fragments,  fsm_advance & case_0of0_pref, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_0_fragments,  fsm_advance & case_0of0_0of0, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_0_fragments,  fsm_advance & case_0of0_0of1, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_0_fragments,  fsm_advance & case_0of0_0of2, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_0_fragments,  fsm_advance & case_0of1_1of1, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_0_fragments,  fsm_advance & case_0of2_1of2, States.have_2_fragments)
        self.decode_fsm.add_transition(States.have_0_fragments, ~fsm_advance                 , States.have_0_fragments)
        # We're in a state where we have 1 parcel for the bottom
        self.decode_fsm.add_transition(States.have_1_fragments,  fsm_advance, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_1_fragments, ~fsm_advance, States.have_1_fragments)
        # We're in a state where we have 2 fragments for the bottom
        self.decode_fsm.add_transition(States.have_2_fragments,  fsm_advance, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_2_fragments, ~fsm_advance, States.have_2_fragments)
        # We have all the fragments: we either advance to the next set of instructions, or reset if the source is not valid
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_pref_0of0, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_pref_0of1, States.have_1_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_pref_0of2, States.have_1_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_0of0_pref, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_0of0_0of0, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_0of0_0of1, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_0of0_0of2, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_0of1_1of1, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_0of2_1of2, States.have_2_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_1of1_pref, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_1of1_0of0, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_1of1_0of1, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_1of1_0of2, States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & self.fetch.valid & case_1of2_2of2, States.have_all_fragments)

        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & ~self.fetch.valid & ~load_from_top, States.have_0_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & ~self.fetch.valid & load_from_top & top_inst_is_prefix_reg, States.have_0_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & ~self.fetch.valid & load_from_top & ~top_inst_is_prefix_reg & (top_inst_len_reg == inst_len_16), States.have_all_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & ~self.fetch.valid & load_from_top & (top_inst_len_reg == inst_len_32), States.have_1_fragments)
        self.decode_fsm.add_transition(States.have_all_fragments,  fsm_advance & ~self.fetch.valid & load_from_top & (top_inst_len_reg == inst_len_48), States.have_1_fragments)

        self.decode_fsm.add_transition(States.have_all_fragments, ~fsm_advance                    , States.have_all_fragments)

        # Handshake logic: we're widening the datapath, so it's essentially the same as a ForwardBuf
        terminal_fsm_state = Wire(logic)
        terminal_fsm_state <<= (self.decode_fsm.state == States.have_all_fragments)
        fetch_ready = (~terminal_fsm_state & ~top_inst_pre_cond_reg) | self.push_data.ready
        self.fetch.ready <<= fetch_ready
        self.push_data.valid <<= terminal_fsm_state
        fsm_advance <<= (~terminal_fsm_state & self.fetch.valid & fetch_ready) | (terminal_fsm_state & self.push_data.ready)

        # Loading of the datapath registers
        #load_from_top = (self.decode_fsm.state == States.have_all_fragments) & top_inst_pre_cond_reg
        load_from_top <<= top_inst_pre_cond_reg
        with fsm_advance as clk_en:
            btm_inst_prefix_reg <<= RegEn(
                Select(
                    load_from_top,
                    SelectOne(
                        decode_btm & btm_inst_is_prefix,    btm_inst_fragment,
                        default_port = btm_inst_prefix_reg
                    ),
                    top_inst_reg
                )
            )
            btm_inst_has_prefix_reg <<= RegEn(
                Select(
                    load_from_top,
                    SelectOne(
                        decode_btm, btm_inst_is_prefix,
                        default_port = btm_inst_has_prefix_reg
                    ),
                    top_inst_is_prefix_reg
                )
            )
            btm_inst_reg[15:0] <<= RegEn(
                Select(
                    load_from_top & ~top_inst_is_prefix_reg,
                    SelectOne(
                        decode_btm & ~btm_inst_is_prefix,    btm_inst_fragment,
                        decode_btm &  btm_inst_is_prefix,    top_inst_fragment,
                        default_port = btm_inst_reg[15:0]
                    ),
                    top_inst_reg
                )
            )
            btm_inst_reg[31:16] <<= RegEn(
                Select(
                    load_from_top,
                    # Not loading from top
                    SelectOne(
                        case_0of1_1of1, top_inst_fragment,
                        case_0of2_1of2, top_inst_fragment,
                        self.decode_fsm.state == States.have_1_fragments,    btm_inst_fragment,
                        default_port = btm_inst_reg[31:16]
                    ),
                    # Loading from top
                    Select(
                        top_inst_is_prefix_reg,
                        # Loading a non-prefix instruction from top
                        btm_inst_fragment,
                        # Loading a prefix instruction from top
                        top_inst_fragment,
                    )
                )
            )
            btm_inst_reg[47:32] <<= RegEn(
                Select(
                    load_from_top,
                    SelectOne(
                        self.decode_fsm.state == States.have_1_fragments,    top_inst_fragment,
                        self.decode_fsm.state == States.have_2_fragments,    btm_inst_fragment,
                        default_port = btm_inst_reg[47:32]
                    ),
                    top_inst_fragment
                )
            )
            btm_inst_len_reg <<= RegEn(
                Select(
                    load_from_top & ~top_inst_is_prefix_reg,
                    SelectOne(
                        decode_btm &  btm_inst_is_prefix, top_inst_len,
                        decode_btm & ~btm_inst_is_prefix, btm_inst_len,
                        default_port = btm_inst_len_reg
                    ),
                    top_inst_len_reg
                )
            )
            btm_inst_fetch_addr <<= RegEn(
                Select(
                    load_from_top,
                    SelectOne(
                        decode_btm, (self.fetch.addr, "1'b0"),
                        default_port = btm_inst_fetch_addr
                    ),
                    (top_inst_fetch_addr, "1'b1") # top captures the DWORD address, but bottom captures the instruction address. Top is always an odd address, so simply append a '1' to the end
                )
            )


            top_inst_reg <<= RegEn(
                top_inst_fragment,
            )

            top_inst_is_prefix_reg <<= RegEn(
                top_inst_is_prefix
            )

            top_inst_len_reg <<= RegEn(
                top_inst_len
            )

            top_inst_valid_reg <<= RegEn(
                SelectOne(
                    case_0of0_0of0, 1,
                    case_1of1_0of0, 1,
                    case_2of2_0of0, 1,
                    default_port = 0
                )
            )

            top_inst_pre_cond_reg <<= RegEn(
                SelectOne(
                    case_0of0_pref, 1,
                    case_0of0_0of1, 1,
                    case_0of0_0of2, 1,
                    case_1of1_pref, 1,
                    case_1of1_0of1, 1,
                    case_1of1_0of2, 1,
                    case_2of2_pref, 1,
                    case_2of2_0of1, 1,
                    case_2of2_0of2, 1,
                    default_port = 0
                )
            )

            top_inst_fetch_addr <<= RegEn(
                self.fetch.addr
            )

        # Filling the output data
        self.push_data.inst_bottom.inst <<= btm_inst_reg
        self.push_data.inst_bottom.prefix <<= btm_inst_prefix_reg
        self.push_data.inst_bottom.has_prefix <<= btm_inst_has_prefix_reg
        self.push_data.inst_bottom.inst_len <<= btm_inst_len_reg
        self.push_data.inst_top <<= top_inst_reg
        self.push_data.has_top <<= top_inst_valid_reg
        self.push_data.addr <<= btm_inst_fetch_addr

def gen():
    Build.generate_rtl(FeDecode)

def sim():

    inst_choices = (
        #(0x0ff0, 0x0ff0,                ), # prefix-prefix
        (0x1100,                        ), # $r1 <- $r0 ^ $r0
        (0x20f0, 0x2ddd,                ), # $r1 <- short b001
        (0x300f, 0x3dd0, 0x3dd1,        ), # $r1 <- 0xdeadbeef
        (0x0ff0, 0x1001,                ), # type override + $pc <- $r1
        (0x0ff1, 0x20f1, 0x5ddd,        ), # type override + $r1 <- short b001
        (0x0ff2, 0x301f, 0x6dd0, 0x6dd1,), # type override + $r1 <- 0xdeadbeef
    )
    inst_stream = []
    class Generator(RvSimSource):
        def construct(self, max_wait_state: int = 0):
            super().construct(FeFetch(), None, max_wait_state)
            self.addr = -1
            self.inst_fetch_stream = []
        def generator(self, is_reset):
            if is_reset:
                return 0,0
            self.addr += 1
            while len(self.inst_fetch_stream) < 2:
                inst = inst_choices[randint(0,len(inst_choices)-1)]
                inst_stream.append(inst)
                self.inst_fetch_stream += inst
            # Don't combine the two instructions, because I don't want to rely on expression evaluation order. That sounds dangerous...
            data = self.inst_fetch_stream.pop(0)
            data |= self.inst_fetch_stream.pop(0) << 16
            return self.addr, data

    class Checker(RvSimSink):
        def construct(self, max_wait_state: int = 0):
            super().construct(None, max_wait_state)
            self.cnt = 0
        def checker(self, value):
            def get_next_inst():
                inst = inst_stream.pop(0)
                print(f"  --- inst:", end="")
                for i in inst:
                    print(f" {i:04x}", end="")
                print("")
                has_prefix = inst[0] & 0x0ff0 == 0x0ff0
                if has_prefix:
                    prefix = inst[0]
                    inst = inst[1:]
                else:
                    prefix = None
                inst_len = len(inst)-1
                inst_code = 0
                for idx, word in enumerate(inst):
                    inst_code |= word << (16*idx)
                return prefix, has_prefix, inst_code, inst_len

            expected_prefix, expected_has_prefix, expected_inst_code, expected_inst_len = get_next_inst()
            print(f"Received: ", end="")
            if value.inst_bottom.has_prefix:
                print(f" [{value.inst_bottom.prefix:04x}]", end="")
            for i in range(value.inst_bottom.inst_len+1):
                print(f" {(value.inst_bottom.inst >> (16*i)) & 0xffff:04x}", end="")
            if value.has_top:
                print(f" top: {value.inst_top:04x}", end="")
            print("")

            assert expected_has_prefix == value.inst_bottom.has_prefix
            assert not expected_has_prefix or expected_prefix == value.inst_bottom.prefix
            assert expected_inst_len == value.inst_bottom.inst_len
            inst_mask = (1 << (16*(expected_inst_len+1))) - 1
            assert (expected_inst_code & inst_mask) == (value.inst_bottom.inst & inst_mask)
            if value.has_top == 1:
                expected_prefix, expected_has_prefix, expected_inst_code, expected_inst_len = get_next_inst()
                assert not expected_has_prefix
                assert expected_inst_len == 0
                assert expected_inst_code == value.inst_top

    class top(Module):
        clk = ClkPort()
        rst = RstPort()

        def body(self):
            seed(0)
            self.input_stream = Wire(FeFetch())
            self.checker = Checker()
            self.generator = Generator()
            self.input_stream <<= self.generator.output_port
            dut = FeDecode()
            dut.rst <<= self.rst
            dut.clk <<= self.clk
            self.checker.input_port <<= dut(self.input_stream)

        def simulate(self) -> TSimEvent:
            def clk() -> int:
                yield 10
                self.clk <<= ~self.clk & self.clk
                yield 10
                self.clk <<= ~self.clk
                yield 0

            print("Simulation started")

            self.rst <<= 1
            self.clk <<= 1
            yield 10
            for i in range(5):
                yield from clk()
            self.rst <<= 0

            self.generator.max_wait_state = 2
            self.checker.max_wait_state = 5
            for i in range(500):
                yield from clk()
            self.generator.max_wait_state = 0
            self.checker.max_wait_state = 0
            for i in range(500):
                yield from clk()
            now = yield 10
            self.generator.max_wait_state = 5
            self.checker.max_wait_state = 2
            for i in range(500):
                yield from clk()
            now = yield 10
            print(f"Done at {now}")

    Build.simulation(top, "fe_decode.vcd", add_unnamed_scopes=True)

#gen()
sim()

