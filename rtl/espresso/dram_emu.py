#!/usr/bin/python3
from random import *
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

"""
This is a simple DRAM emulator, using an SDRAM chip. It is particularly suitable for the GoWin FPGAs, which have on-package SDRAM.

!!!!! THIS PROJECT IS HIGHLY INCOMPLETE !!!!!
"""

class SDRamIf(Interface):
    clk           = logic
    cke           = logic # Clock enable, active high
    ba            = Unsigned(2) # bank-activate selection
    n_cs          = logic
    n_ras         = logic
    n_cas         = logic
    n_we          = logic
    addr          = Unsigned(11)
    dqm           = logic(4) # byte-enables (active low)
    data_in       = Reverse(Unsigned(32))
    data_out      = Unsigned(32)
    data_out_en   = logic

class DramEmu(Module):
    clk = ClkPort()
    rst = RstPort()

    # DRAM interface
    dram = Input(ExternalBusIf)

    # SDRAM interface
    sdram = Output(SDRamIf)

    def body(self):
        def cmd_bank_activate(bank, row):
            self.sdram.cke = 1
            #self.sdram.dqm = None
            self.sdram.ba = bank
            self.sdram.addr = row
            self.sdram.n_cs = 0
            self.sdram.n_ras = 0
            self.sdram.n_cas = 1
            self.sdram.n_we = 1
            #self.sdram.data_out = None
            self.sdram.data_out_en = 0
        def cmd_bank_precharge(bank):
            self.sdram.cke = 1
            #self.sdram.dqm = None
            self.sdram.ba = bank
            self.sdram.addr = 0b1_00000_00000
            self.sdram.n_cs = 0
            self.sdram.n_ras = 0
            self.sdram.n_cas = 1
            self.sdram.n_we = 0
            #self.sdram.data_out = None
            self.sdram.data_out_en = 0
        def cmd_precharge_all():
            self.sdram.cke = 1
            #self.sdram.dqm = None
            #self.sdram.ba = None
            self.sdram.addr = 0b0_00000_00000
            self.sdram.n_cs = 0
            self.sdram.n_ras = 0
            self.sdram.n_cas = 1
            self.sdram.n_we = 0
            #self.sdram.data_out = None
            self.sdram.data_out_en = 0
        def cmd_write(bank, col, data, dqm):
            self.sdram.cke = 1
            self.sdram.dqm = dqm
            self.sdram.ba = bank
            self.sdram.addr = col # MAKE SURE col DOESN'T SET A10!!
            self.sdram.n_cs = 0
            self.sdram.n_ras = 1
            self.sdram.n_cas = 0
            self.sdram.n_we = 0
            self.sdram.data_out = data
            self.sdram.data_out_en = 1


        refresh_counter = Wire(Unsigned(self.refresh_counter_size))
        # CSR interface
        reg_write_strobe = self.reg_if.psel & self.reg_if.pwrite & self.reg_if.penable
        self.reg_if.pready <<= 1

        reg_addr = self.reg_if.paddr

        refresh_divider = Reg(self.reg_if.pwdata[self.refresh_counter_size-1:0], clock_en=(reg_addr == self.reg_dram_config_ofs) & reg_write_strobe, reset_value_port=128)
        refresh_disable = Reg(self.reg_if.pwdata[self.refresh_counter_size], clock_en=(reg_addr == self.reg_dram_config_ofs) & reg_write_strobe)
        dram_bank_size = Reg(self.reg_if.pwdata[self.refresh_counter_size+2:self.refresh_counter_size+1], clock_en=(reg_addr == self.reg_dram_config_ofs) & reg_write_strobe)
        dram_bank_swap = Reg(self.reg_if.pwdata[self.refresh_counter_size+3], clock_en=(reg_addr == self.reg_dram_config_ofs) & reg_write_strobe)
        dram_single_bank = Reg(self.reg_if.pwdata[self.refresh_counter_size+4], clock_en=(reg_addr == self.reg_dram_config_ofs) & reg_write_strobe)
        self.reg_if.prdata <<= concat(
            dram_single_bank,
            dram_bank_swap,
            dram_bank_size,
            refresh_disable,
            refresh_counter
        )

        # Refresh logic
        # We seem to need to generate 256 refresh cycles in 4ms. That would mean a refresh cycle
        # every 200 or so cycles at least. So, an 8-bit counter should suffice
        refresh_tc = refresh_counter == 0
        refresh_rsp = Wire(logic)
        refresh_req = Wire(logic)
        refresh_req <<= Reg(Select(
            refresh_tc & ~refresh_disable,
            Select(
                refresh_rsp,
                refresh_req,
                0
            ),
            1
        ))
        refresh_counter <<= Reg(Select(
                refresh_tc,
                Select(
                    refresh_req,
                    (refresh_counter-1)[self.refresh_counter_size-1:0],
                    refresh_counter
                ),
                refresh_divider
        ))
        refresh_addr = Wire(self.dram.addr.get_net_type())
        refresh_addr <<= Reg(Select(refresh_rsp, refresh_addr, self.dram.addr.get_net_type()(refresh_addr+1)))

        class BusIfStates(Enum):
            idle                 = 0
            first                = 1
            middle               = 2
            external             = 3
            precharge            = 4
            non_dram_first       = 5
            non_dram_wait        = 6
            non_dram_dual        = 7
            non_dram_dual_first  = 8
            non_dram_dual_wait   = 9
            non_dram_last        = 10
            dma_first            = 11
            dma_wait             = 12
            refresh              = 13

        self.fsm = FSM()

        self.fsm.reset_value   <<= BusIfStates.idle
        self.fsm.default_state <<= BusIfStates.idle

        state = Wire()
        next_state = Wire()
        state <<= self.fsm.state
        next_state <<= self.fsm.next_state

        class Ports(Enum):
            fetch_port = 0
            mem_port = 1
            dma_port = 2
            refresh_port = 3

        arb_port_select = Wire()
        arb_port_comb = SelectFirst(
            refresh_req, Ports.refresh_port,
            self.dma_request.valid, Ports.dma_port,
            self.mem_request.valid, Ports.mem_port,
            default_port = Ports.fetch_port
        )
        arb_port_select <<= hold(arb_port_comb, enable=state == BusIfStates.idle)

        req_ready = Wire()
        req_ready <<= (state == BusIfStates.idle) | (state == BusIfStates.first) | (state == BusIfStates.middle)
        refresh_rsp <<= (state == BusIfStates.refresh)
        self.mem_request.ready <<= req_ready & (arb_port_select == Ports.mem_port)
        self.fetch_request.ready <<= req_ready & (arb_port_select == Ports.fetch_port)
        self.dma_request.ready <<= (req_ready & (arb_port_select == Ports.dma_port)) | (state == BusIfStates.external)

        req_valid = Wire()
        start = Wire()
        req_addr = Wire()
        req_data = Wire()
        req_read_not_write = Wire()
        req_byte_en = Wire()

        req_valid <<= Select(arb_port_select, self.fetch_request.valid, self.mem_request.valid, self.dma_request.valid, 1)
        start <<= (state == BusIfStates.idle) & req_valid
        req_addr <<= Select(arb_port_select, self.fetch_request.addr, self.mem_request.addr, self.dma_request.addr)
        req_data <<= Select(arb_port_select, self.fetch_request.data, self.mem_request.data, None)
        req_read_not_write <<= Select(arb_port_select, self.fetch_request.read_not_write, self.mem_request.read_not_write, self.dma_request.read_not_write, 1)
        req_byte_en <<= Select(arb_port_select, self.fetch_request.byte_en, self.mem_request.byte_en, self.dma_request.byte_en)
        req_advance = req_valid & req_ready

        req_dram = (req_addr[26:25] != self.nram_base) & ((arb_port_select == Ports.mem_port) | (arb_port_select == Ports.fetch_port))
        req_nram = (req_addr[26:25] == self.nram_base) & ((arb_port_select == Ports.mem_port) | (arb_port_select == Ports.fetch_port))
        req_dma  = (arb_port_select == Ports.dma_port) & ~self.dma_request.is_master
        req_ext  = (arb_port_select == Ports.dma_port) &  self.dma_request.is_master
        req_rfsh = (arb_port_select == Ports.refresh_port)

        dram_addr_muxing = Select(start, Reg(req_dram | req_dma, clock_en=start), req_dram | req_dma)
        dma_ch = Reg(self.dma_request.one_hot_channel, clock_en=start)
        tc = Reg(self.dma_request.terminal_count, clock_en=start)

        req_wait_states = (req_addr[30:27]-1)[3:0]
        wait_states_store = Reg(req_wait_states, clock_en=start)
        wait_states = Wire(Unsigned(4))
        wait_states <<= Reg(
            Select(
                start,
                Select(
                    wait_states == 0,
                    (wait_states - ((state == BusIfStates.dma_wait) | (state == BusIfStates.non_dram_dual_wait) | (state == BusIfStates.non_dram_wait)))[3:0],
                    Select(
                        state == BusIfStates.non_dram_dual,
                        0,
                        wait_states_store
                    )
                ),
                req_wait_states
            )
        )
        waiting = ~self.dram.n_wait | (wait_states != 0)

        two_cycle_nram_access = Wire(logic)
        two_cycle_nram_access <<= Reg((req_byte_en == 3) & req_nram, clock_en=start)
        nram_access = Wire(logic)
        nram_access <<= Reg(req_nram, clock_en=start)

        self.event_bus_idle <<= (state == BusIfStates.idle) & (next_state == BusIfStates.idle)

        self.fsm.add_transition(BusIfStates.idle,                         req_valid & req_ext,                                  BusIfStates.external)
        self.fsm.add_transition(BusIfStates.idle,                         req_valid & req_nram,                                 BusIfStates.non_dram_first)
        self.fsm.add_transition(BusIfStates.idle,                         req_valid & req_dma,                                  BusIfStates.dma_first)
        self.fsm.add_transition(BusIfStates.idle,                         req_valid & req_dram,                                 BusIfStates.first)
        self.fsm.add_transition(BusIfStates.idle,                         req_valid & req_rfsh,                                 BusIfStates.refresh)
        self.fsm.add_transition(BusIfStates.external,                     req_valid & ~req_ext,                                 BusIfStates.idle)
        self.fsm.add_transition(BusIfStates.external,                    ~req_valid,                                            BusIfStates.idle)
        self.fsm.add_transition(BusIfStates.first,                       ~req_valid,                                            BusIfStates.precharge)
        self.fsm.add_transition(BusIfStates.first,                        req_valid,                                            BusIfStates.middle)
        self.fsm.add_transition(BusIfStates.middle,                      ~req_valid,                                            BusIfStates.precharge)
        self.fsm.add_transition(BusIfStates.precharge, 1,                                                                       BusIfStates.idle)
        self.fsm.add_transition(BusIfStates.non_dram_first, 1,                                                                  BusIfStates.non_dram_wait)
        self.fsm.add_transition(BusIfStates.non_dram_wait,  waiting,                                                            BusIfStates.non_dram_wait)
        self.fsm.add_transition(BusIfStates.non_dram_wait, ~waiting &  two_cycle_nram_access,                                   BusIfStates.non_dram_dual)
        self.fsm.add_transition(BusIfStates.non_dram_wait, ~waiting & ~two_cycle_nram_access,                                   BusIfStates.non_dram_last)
        self.fsm.add_transition(BusIfStates.non_dram_dual, 1,                                                                   BusIfStates.non_dram_dual_first)
        self.fsm.add_transition(BusIfStates.non_dram_dual_first, 1,                                                             BusIfStates.non_dram_dual_wait)
        self.fsm.add_transition(BusIfStates.non_dram_dual_wait,  waiting,                                                       BusIfStates.non_dram_dual_wait)
        self.fsm.add_transition(BusIfStates.non_dram_dual_wait, ~waiting,                                                       BusIfStates.non_dram_last)
        self.fsm.add_transition(BusIfStates.non_dram_last, 1,                                                                   BusIfStates.idle)
        self.fsm.add_transition(BusIfStates.dma_first, 1,                                                                       BusIfStates.dma_wait)
        self.fsm.add_transition(BusIfStates.dma_wait,  waiting,                                                                 BusIfStates.dma_wait)
        self.fsm.add_transition(BusIfStates.dma_wait, ~waiting,                                                                 BusIfStates.idle)
        self.fsm.add_transition(BusIfStates.refresh, 1,                                                                         BusIfStates.idle)

        dram_bank = Wire()
        dram_bank_next = Select(
            dram_bank_size,
            req_addr[16],
            req_addr[18],
            req_addr[20],
            req_addr[22],
        )
        dram_bank <<= Select(start, Reg(dram_bank_next, clock_en=start), dram_bank_next)

        input_row_addr = Wire()
        input_row_addr <<= Select(
            dram_addr_muxing,
            req_addr[21:11],
            concat(req_addr[21], req_addr[19], req_addr[17], req_addr[15:8])
        )
        row_addr = Wire()
        row_addr <<= Reg(Select(req_rfsh, input_row_addr, refresh_addr), clock_en=start)
        col_addr = Wire()
        col_addr <<= Reg(Select(
            dram_addr_muxing,
            req_addr[10:0],
            concat(req_addr[20], req_addr[18], req_addr[16], req_addr[7:0])
        ), clock_en=req_advance)
        read_not_write = Wire()
        read_not_write <<= Reg(req_read_not_write, clock_en=start, reset_value_port=1) # reads and writes can't mix within a burst
        data_out_en = Wire()
        data_out_en <<= Reg(~req_read_not_write & (arb_port_select != Ports.dma_port), clock_en=start) # reads and writes can't mix within a burst
        byte_en = Wire()
        byte_en <<= hold(req_byte_en, enable=req_advance)
        data_out = Wire()
        data_out <<= Reg(
            Select(
                req_byte_en[0],
                concat(req_data[7:0], req_data[7:0]), # low-byte-en is 0 --> 8-bit access to the high-byte
                req_data, # low-byte-en is 1 --> either 16-bit access or 8-bit access from the low-byte
            ),
            clock_en=req_advance
        )

        #AssertOnClk((input_row_addr == row_addr) | (state == BusIfStates.idle))

        '''
        CAS generation:

            CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/
            CAS_nWINDOW_A   ^^^^^^^^^\_______________________/^^^^^\_____/^^^^^\_____/^^^^^\_______________________/^^^^^^^^^^^^^^^^^^^^^^^^
            CAS_nWINDOW_B   ^^^^^^^^^^^^\_______________________/^^^^^\_____/^^^^^\_____/^^^^^\_______________________/^^^^^^^^^^^^^^^^^^^^^
            CAS_nWINDOW_C   ^^^^^^^^^^^^^^^\_______________________/^^^^^\_____/^^^^^\_____/^^^^^\_______________________/^^^^^^^^^^^^^^^^^^
            CAS_nEN_A       ^^^^^^^^^^^^\____________________/^^^^^^^^\__/^^^^^^^^\__/^^^^^^^^\____________________/^^^^^^^^^^^^^^^^^^^^^^^^
            DRAM_nCAS_A     ^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^\__/^^^^^^^^\__/^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^^^^^^^^^^^
            CAS_nEN_A       ^^^^^^^^^^^^^^^\____________________/^^^^^^^^\__/^^^^^^^^\__/^^^^^^^^\____________________/^^^^^^^^^^^^^^^^^^^^^
            DRAM_nCAS_B     ^^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^\__/^^^^^^^^\__/^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^^^^^^^^

        We need to avoid changing the enable signal on opposite edges of the clock.
        That is, CAS_nEN falls with ~CLK falling and rises with ~CLK rising.

        This way timing is not that critical, provided the LUT is just as glitch-free
        as logic gates would be. That's actually up to debate. Apparently Xilinx only
        guarantees glitch-free output for single input toggling, but in practice it
        appears to be true that the output doesn't glitch if normal logic wouldn't.

        From what I've gathered, the glitch-free nature of the output comes from
        depending on the output capacitance of the read-wire and careful timing of
        the switching of the pass-gates that make up the LUT read mux. So, fingers
        crossed, this is a safe circuit...
        '''

        dram_ras_active = (
            (next_state == BusIfStates.first) |
            (next_state == BusIfStates.middle) |
            (next_state == BusIfStates.precharge) |
            (next_state == BusIfStates.dma_first) |
            (next_state == BusIfStates.dma_wait)
        )
        # Decode DRAM banks as follows:
        #
        # dram_bank    bank_swap    single_bank   ras_a     ras_b
        #     0            0              0         1         0
        #     1            0              0         0         1
        #     0            1              0         0         1
        #     1            1              0         1         0
        #     0            0              1         1         0
        #     1            0              1         1         0
        #     0            1              1         0         1
        #     1            1              1         0         1
        dram_ras_a = Reg((dram_ras_active & ((dram_bank == dram_bank_swap) | (~dram_bank_swap & dram_single_bank))) | (next_state == BusIfStates.refresh)) # We re-register the state to remove all glitches
        dram_ras_b = Reg((dram_ras_active & ((dram_bank != dram_bank_swap) | ( dram_bank_swap & dram_single_bank))) | (next_state == BusIfStates.refresh)) # We re-register the state to remove all glitches
        dram_n_ras_a = ~dram_ras_a
        dram_n_ras_b = ~dram_ras_b
        n_nren = Wire()
        n_nren <<= Reg(
            (next_state != BusIfStates.non_dram_first) & (next_state != BusIfStates.non_dram_wait) & (next_state != BusIfStates.non_dram_dual_first) & (next_state != BusIfStates.non_dram_dual_wait),
            reset_value_port = 1
        ) # We re-register the state to remove all glitches
        n_dack = Wire(self.dma_request.one_hot_channel.get_net_type())
        n_dack <<= ~Reg(
            Select(
                (state == BusIfStates.dma_first) | ((state == BusIfStates.dma_wait) & waiting) | ((state == BusIfStates.external) & req_valid & req_ext),
                0,
                dma_ch
            )
        )
        nr_cas_logic = (
            (state == BusIfStates.non_dram_dual_first) | (state == BusIfStates.non_dram_first) | (state == BusIfStates.dma_first) |
            (waiting & ((state == BusIfStates.non_dram_dual_wait) | (state == BusIfStates.non_dram_wait) | (state == BusIfStates.dma_wait)))
        )
        """
        BUG BUG BUG
        for DMA accesses, n_cas needs to be delayed until data is ready on the data-bus, as it gets latched in the falling edge.
        This probably means that n_cas will have to go down for the last half-cycle of the DMA, after n_wait is sampled high.
        BUG BUG BUG
        """
        nr_cas_logic_0 = nr_cas_logic & (~two_cycle_nram_access | (state == BusIfStates.non_dram_first) | (state == BusIfStates.non_dram_wait) | (state == BusIfStates.dma_first) | (state == BusIfStates.dma_wait))
        nr_cas_logic_1 = nr_cas_logic & (~two_cycle_nram_access | (state == BusIfStates.non_dram_dual_first) | (state == BusIfStates.non_dram_dual_wait) | (state == BusIfStates.dma_first) | (state == BusIfStates.dma_wait))
        nr_n_cas_0 = Wire()
        nr_n_cas_0 <<= Reg(~nr_cas_logic_0 | ~byte_en[0], reset_value_port = 1) # We re-register the state to remove all glitches
        nr_n_cas_1 = Wire()
        nr_n_cas_1 <<= Reg(~nr_cas_logic_1 | ~byte_en[1], reset_value_port = 1) # We re-register the state to remove all glitches
        cas_n_window_a_0 = Wire()
        cas_n_window_a_0 <<= Reg(
            ~byte_en[0] |
            (next_state == BusIfStates.idle) |
            (next_state == BusIfStates.precharge) |
            (next_state == BusIfStates.non_dram_first) |
            (next_state == BusIfStates.non_dram_wait) |
            (next_state == BusIfStates.non_dram_dual) |
            (next_state == BusIfStates.non_dram_dual_first) |
            (next_state == BusIfStates.non_dram_dual_wait) |
            (next_state == BusIfStates.non_dram_last) |
            (next_state == BusIfStates.dma_first) |
            (next_state == BusIfStates.dma_wait) |
            (next_state == BusIfStates.refresh),
            reset_value_port = 1
        ) # We re-register the state to remove all glitches
        cas_n_window_a_1 = Wire()
        cas_n_window_a_1 <<= Reg(
            ~byte_en[1] |
            (next_state == BusIfStates.idle) |
            (next_state == BusIfStates.precharge) |
            (next_state == BusIfStates.non_dram_first) |
            (next_state == BusIfStates.non_dram_wait) |
            (next_state == BusIfStates.non_dram_dual) |
            (next_state == BusIfStates.non_dram_dual_first) |
            (next_state == BusIfStates.non_dram_dual_wait) |
            (next_state == BusIfStates.non_dram_last) |
            (next_state == BusIfStates.dma_first) |
            (next_state == BusIfStates.dma_wait) |
            (next_state == BusIfStates.refresh),
            reset_value_port = 1
        ) # We re-register the state to remove all glitches
        #cas_n_window_c_0 = Wire()
        #cas_n_window_c_0 <<= Reg(cas_n_window_a_0, reset_value_port = 1)
        cas_n_window_b_0 = Wire()
        cas_n_window_b_0 <<= NegReg(cas_n_window_a_0, reset_value_port = 1)
        cas_n_window_c_1 = Wire()
        cas_n_window_c_1 <<= Reg(cas_n_window_a_1, reset_value_port = 1)
        cas_n_window_b_1 = Wire()
        cas_n_window_b_1 <<= NegReg(cas_n_window_a_1, reset_value_port = 1)

        dram_n_cas_0 = cas_n_window_a_0 | cas_n_window_b_0 |  self.clk
        dram_n_cas_1 = cas_n_window_b_1 | cas_n_window_c_1 | ~self.clk

        self.dram.n_ras_a     <<= dram_n_ras_a
        self.dram.n_ras_b     <<= dram_n_ras_b
        self.dram.n_cas_0     <<= dram_n_cas_0 & nr_n_cas_0
        self.dram.n_cas_1     <<= dram_n_cas_1 & nr_n_cas_1
        col_addr_nr = NegReg(col_addr)
        dram_addr = Select(
            (
                (state == BusIfStates.first) |
                (state == BusIfStates.non_dram_first) |
                (state == BusIfStates.non_dram_dual_first) |
                (state == BusIfStates.dma_first) |
                (state == BusIfStates.refresh)
            ) & self.clk,
            col_addr_nr,
            row_addr
        )
        self.dram.addr        <<= dram_addr
        self.dram.n_we        <<= read_not_write
        self.dram.data_out_en <<= data_out_en
        data_out_low = Wire()
        nr_cas_logic_1_reg = Wire(logic)
        nr_cas_logic_1_reg <<= Reg(Select(
            n_nren,
            nr_cas_logic_1_reg | nr_cas_logic_1,
            0
        ))
        data_out_low <<= NegReg(
            Select(
                nram_access,
                data_out[7:0],
                Select(
                    two_cycle_nram_access & (nr_cas_logic_1_reg | nr_cas_logic_1 | ~nr_n_cas_1),
                    data_out[7:0],
                    data_out[15:8]
                )
            )
        )
        data_out_high = Wire()
        data_out_high <<= Reg(
            Select(
                nram_access,
                data_out[15:8],
                Select(
                    two_cycle_nram_access & (nr_cas_logic_1_reg | nr_cas_logic_1),
                    data_out[7:0],
                    data_out[15:8]
                )
            )
        )
        self.dram.data_out   <<= Select(
            self.clk,
            data_out_low,
            data_out_high
        )

        self.dram.n_nren      <<= n_nren
        self.dram.n_dack      <<= n_dack
        self.dram.tc         <<= tc
        self.dram.bus_en     <<= state != BusIfStates.external

        read_active = Wire()
        read_active <<= (
            (state == BusIfStates.first) |
            (state == BusIfStates.middle) |
            ((state == BusIfStates.dma_wait) & ~waiting) |
            ((state == BusIfStates.non_dram_wait) & ~waiting & ~two_cycle_nram_access) |
            ((state == BusIfStates.non_dram_dual_wait) & ~waiting)
        ) & read_not_write
        data_in_low = Wire()
        data_in_low <<= Reg(self.dram.data_in, clock_en=(
            (state == BusIfStates.non_dram_wait) |
            (state == BusIfStates.first) |
            (state == BusIfStates.middle)
        ))

        ndram_data_in_high = Reg(self.dram.data_in, clock_en=(state == BusIfStates.non_dram_dual_wait))
        data_in_high = Select(
            nram_access,
            NegReg(self.dram.data_in),
            Select(two_cycle_nram_access, data_in_low, ndram_data_in_high)
        )

        resp_data = Wire()
        resp_data <<= Reg(Select(
            byte_en,
            None, # Invalid
            concat("8'b0", data_in_low), # 8-bit read from low-byte
            concat("8'b0", data_in_high), # 8-bit read from high-byte
            concat(data_in_high, data_in_low) # 16-bit read
        ))

        self.mem_response.valid <<= Reg(Reg(read_active & (arb_port_select == Ports.mem_port)))
        self.fetch_response.valid <<= Reg(Reg(read_active & (arb_port_select == Ports.fetch_port)))
        self.dma_response.valid <<= (state == BusIfStates.dma_wait) & ~waiting
        self.mem_response.data <<= resp_data
        self.fetch_response.data <<= resp_data

def sim():
    inst_stream = []


    class DRAM_sim(Module):
        addr_bus_len = 12
        addr_bus_mask = (1 << addr_bus_len) - 1

        bus_if = Input(ExternalBusIf)

        def simulate(self, simulator) -> TSimEvent:
            full_addr = 0
            self.bus_if.data_in <<= None
            self.bus_if.n_wait <<= 1
            while True:
                yield (self.bus_if.n_ras_a, self.bus_if.n_nren, self.bus_if.n_cas_0, self.bus_if.n_cas_1)
                data_assigned = False
                for (byte, cas) in (("low", self.bus_if.n_cas_0), ("high", self.bus_if.n_cas_1)):
                    if (self.bus_if.n_ras_a.get_sim_edge() == EdgeType.Negative) or (self.bus_if.n_nren.get_sim_edge() == EdgeType.Negative):
                        #assert self.dram_n_cas_0.get_sim_edge() == EdgeType.NoEdge
                        #assert self.dram_n_cas_1.get_sim_edge() == EdgeType.NoEdge
                        #assert self.dram_n_cas_0 == 1
                        #assert self.dram_n_cas_1 == 1
                        # Falling edge or nRAS: capture row address
                        if full_addr is None:
                            full_addr = 0
                        full_addr = full_addr & self.addr_bus_mask | (self.bus_if.addr << self.addr_bus_len)
                        simulator.log("Capturing raw address {self.bus_if.addr:03x} into full address {full_addr:08x}")
                    else:
                        if cas.get_sim_edge() == EdgeType.Negative:
                            #assert self.DRAM_nRAS.get_sim_edge() == EdgeType.NoEdge
                            #assert self.DRAM_nRAS == 0
                            # Falling edge of nCAS
                            full_addr = full_addr & (self.addr_bus_mask << self.addr_bus_len) | self.bus_if.addr
                            if self.bus_if.n_we == 0:
                                # Write to the address
                                data = f"{self.bus_if.data_out:04x}"
                                simulator.log(f"Writing byte {byte} to address {full_addr:08x} {data}")
                            else:
                                shift = 8 if byte == "high" else 0
                                data = (full_addr >> shift) & 0xff
                                if data_assigned:
                                    simulator.log(f"Driving both bytes at the same time")
                                simulator.log(f"Reading byte {byte} from address {full_addr:08x} {data:04x}")
                                self.bus_if.data_in <<= data
                                data_assigned = True
                if not data_assigned:
                    self.bus_if.data_in <<= None

    class CsrDriver(Module):
        clk = ClkPort()
        rst = RstPort()

        reg_if = Output(CsrIf)

        def construct(self):
            self.reg_if.paddr.set_net_type(Unsigned(1))

        def simulate(self, simulator: Simulator):
            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_rst():
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()

            def write_reg(addr, value):
                self.reg_if.psel <<= 1
                self.reg_if.penable <<= 0
                self.reg_if.pwrite <<= 1
                self.reg_if.paddr <<= addr
                self.reg_if.pwdata <<= value
                yield from wait_clk()
                self.reg_if.penable <<= 1
                yield from wait_clk()
                while not self.reg_if.pready:
                    yield from wait_clk()
                simulator.log(f"REG {addr:02x} written with value {value:08x}")
                self.reg_if.psel <<= 0
                self.reg_if.penable <<= None
                self.reg_if.pwrite <<= None
                self.reg_if.paddr <<= None
                self.reg_if.pwdata <<= None

            def read_reg(addr):
                self.reg_if.psel <<= 1
                self.reg_if.penable <<= 0
                self.reg_if.pwrite <<= 0
                self.reg_if.paddr <<= addr
                self.reg_if.pwdata <<= None
                yield from wait_clk()
                self.reg_if.penable <<= 1
                yield from wait_clk()
                while not self.reg_if.pready:
                    yield from wait_clk()
                ret_val = copy(self.reg_if.prdata)
                simulator.log(f"REG {addr:02x} read returned value {ret_val:08x}")
                self.reg_if.psel <<= 0
                self.reg_if.penable <<= None
                self.reg_if.pwrite <<= None
                self.reg_if.paddr <<= None
                self.reg_if.pwdata <<= None
                return ret_val

            self.reg_if.psel <<= 0
            yield from wait_rst()
            for _ in range(3):
                yield from wait_clk()
            yield from write_reg(0, (1 << 8) | (10))


    # These two queues will contain the expected read-back values
    read_data_l = []
    read_data_h = []
    class Generator(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        request_port = Output(BusIfRequestIf)

        def construct(self, nram_base: int = 0) -> None:
            self.mode = None
            self.nram_base = nram_base
            self.dram_base = 2 if nram_base == 0 else 0

        def set_mode(self, mode):
            self.mode = mode

        #read_not_write  = logic
        #byte_en         = Unsigned(2)
        #addr            = BrewBusAddr
        #data            = BrewBusData
        #last            = logic

        def simulate(self) -> TSimEvent:
            self.burst_cnt = None
            self.burst_addr = None
            self.is_dram = None

            def reset():
                self.request_port.valid <<= 0
                self.request_port.read_not_write <<= None
                self.request_port.byte_en <<= None
                self.request_port.addr <<= None
                self.request_port.data <<= None

            def read_or_write(addr, is_dram, burst_len, byte_en, data, wait_states, do_write):
                if burst_len is not None:
                    assert addr is not None
                    assert is_dram is not None
                    self.burst_cnt = burst_len
                    self.burst_addr = addr
                    self.is_dram = is_dram
                    self.wait_states = wait_states
                else:
                    assert addr is None
                    assert is_dram is None
                    self.burst_addr += 1
                    self.burst_cnt -= 1
                assert self.burst_cnt >= 0

                self.request_port.valid <<= 1
                self.request_port.read_not_write <<= not do_write
                self.request_port.byte_en <<= byte_en
                self.request_port.addr <<= self.burst_addr | ((self.dram_base if self.is_dram else self.nram_base) << (29-4)) | ((self.wait_states + 1) << (29))
                self.request_port.data <<= data

            def start_read(addr, is_dram, burst_len, byte_en, wait_states):
                if burst_len > 0:
                    byte_en = 3
                read_or_write(addr, is_dram, burst_len, byte_en, None, wait_states, do_write=False)

            def cont_read():
                read_or_write(None, None, None, 3, None, None, False)

            def start_write(addr, is_dram, burst_len, byte_en, data, wait_states):
                if burst_len > 0:
                    byte_en = 3
                read_or_write(addr, is_dram, burst_len, byte_en, data, wait_states, do_write=True)

            def cont_write(data):
                read_or_write(None, None, None, 3, data, None, False)

            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_for_advance():
                yield from wait_clk()
                while not (self.request_port.ready & self.request_port.valid):
                    yield from wait_clk()

            def write(addr, is_dram, burst_len, byte_en, data, wait_states=0):
                idx = 0
                start_write(addr, is_dram, burst_len, byte_en, data[idx], wait_states)
                yield from wait_for_advance()
                while idx < burst_len:
                    idx += 1
                    cont_write(data[idx])
                    yield from wait_for_advance()
                reset()

            def read(addr, is_dram, burst_len, byte_en, wait_states=0):
                idx = 0
                start_read(addr, is_dram, burst_len, byte_en, wait_states)
                yield from wait_for_advance()
                while idx < burst_len:
                    idx += 1
                    cont_read()
                    yield from wait_for_advance()
                reset()
                yield from wait_clk()

            reset()
            if self.mode == "fetch":
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()
                yield from read(0x1234,True,0,3)
                yield from read(0x12,True,1,3)
                yield from read(0x24,True,3,3)
                yield from read(0x3,False,0,1)
                yield from read(0x4,False,0,2, wait_states=5)
                yield from wait_clk()
                yield from wait_clk()
                yield from wait_clk()
                yield from wait_clk()
                yield from read(0x34,True,0,2)
                yield from read(0x4,False,0,3)
            elif self.mode == "mem":
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()
                yield from read(0x5678,False,0,3, wait_states=2)

    class DmaGenerator(GenericModule):
        clk = ClkPort()
        rst = RstPort()

        request_port = Output(BusIfDmaRequestIf)

        def construct(self, nram_base: int = 0) -> None:
            self.mode = None
            self.nram_base = nram_base
            self.dram_base = 2 if nram_base == 0 else 0

        def body(self):
            self.request_port.one_hot_channel.set_net_type(Unsigned(4))

        def set_mode(self, mode):
            self.mode = mode

        #read_not_write  = logic
        #byte_en         = Unsigned(2)
        #addr            = BrewBusAddr
        #data            = BrewBusData
        #last            = logic

        def simulate(self) -> TSimEvent:
            def reset():
                self.request_port.valid <<= 0
                self.request_port.read_not_write <<= None
                self.request_port.byte_en <<= None
                self.request_port.addr <<= None
                self.request_port.one_hot_channel <<= None
                self.request_port.terminal_count <<= None

            def read_or_write(addr, is_dram, byte_en, channel, terminal_count, wait_states, do_write, is_master):
                assert addr is not None or is_master
                assert is_dram is not None or is_master

                self.request_port.valid <<= 1
                self.request_port.read_not_write <<= not do_write
                self.request_port.byte_en <<= byte_en
                self.request_port.addr <<= None if is_master else addr | ((self.dram_base if is_dram else self.nram_base) << (29-4)) | ((wait_states + 1) << (29))
                self.request_port.one_hot_channel <<= 1 << channel
                self.request_port.terminal_count <<= terminal_count
                self.request_port.is_master <<= is_master

            def start_read(addr, is_dram, byte_en, channel, terminal_count, wait_states):
                read_or_write(addr, is_dram, byte_en, channel, terminal_count, wait_states, do_write=False, is_master=False)

            def start_write(addr, is_dram, byte_en, channel, terminal_count, wait_states):
                read_or_write(addr, is_dram, byte_en, channel, terminal_count, wait_states, do_write=True, is_master=False)

            def start_master(channel):
                read_or_write(None, None, None, channel, None, None, do_write=None, is_master=True)

            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_for_advance():
                yield from wait_clk()
                while not (self.request_port.ready & self.request_port.valid):
                    yield from wait_clk()

            def write(addr, is_dram, byte_en, channel, terminal_count, wait_states=0):
                start_write(addr, is_dram, byte_en, channel, terminal_count, wait_states)
                yield from wait_for_advance()
                reset()
                yield from wait_clk()

            def read(addr, is_dram, byte_en, channel, terminal_count, wait_states=0):
                start_read(addr, is_dram, byte_en, channel, terminal_count, wait_states)
                yield from wait_for_advance()
                reset()
                yield from wait_clk()

            reset()
            #if self.mode == "fetch":
            yield from wait_clk()
            while self.rst == 1:
                yield from wait_clk()
            yield from read(0x1000e,True,1,0,0)
            yield from write(0x10010,True,2,0,0)
            for _ in range(20):
                yield from wait_clk()
            start_master(1)
            yield from wait_for_advance()
            for _ in range(40):
                yield from wait_clk()
            reset()
            yield from wait_clk()

            #    yield from read(0x12,True,1,3)
            #    yield from read(0x24,True,3,3)
            #    yield from read(0x3,False,0,1)
            #    yield from read(0x4,False,0,2)
            #    yield from wait_clk()
            #    yield from wait_clk()
            #    yield from wait_clk()
            #    yield from wait_clk()
            #    yield from read(0x34,True,0,2)
            #    yield from read(0x4,False,0,3)
            #elif self.mode == "mem":
            #    yield from wait_clk()
            #    while self.rst == 1:
            #        yield from wait_clk()
            #    yield from read(0x100e,False,0,3)

    '''
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
    '''

    class top(Module):
        clk = ClkPort()
        rst = RstPort()

        def body(self):
            seed(0)
            fetch_req = Wire(BusIfRequestIf)
            fetch_rsp = Wire(BusIfResponseIf)
            fetch_generator = Generator()
            fetch_generator.set_mode("fetch")
            fetch_req <<= fetch_generator.request_port

            mem_req = Wire(BusIfRequestIf)
            mem_rsp = Wire(BusIfResponseIf)
            mem_generator = Generator()
            mem_generator.set_mode("mem")
            mem_req <<= mem_generator.request_port

            dma_req = Wire(BusIfDmaRequestIf)
            dma_generator = DmaGenerator()
            dma_req <<= dma_generator.request_port

            csr_driver = CsrDriver()

            dram_if = Wire(ExternalBusIf)
            dram_sim = DRAM_sim()

            dut = BusIf()

            dut.fetch_request <<= fetch_req
            fetch_rsp <<= dut.fetch_response
            dut.mem_request <<= mem_req
            dut.dma_request <<= dma_req
            mem_rsp <<= dut.mem_response
            dram_if <<= dut.dram
            dram_sim.bus_if <<= dram_if
            dut.reg_if <<= csr_driver.reg_if


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

            for i in range(150):
                yield from clk()
            now = yield 10
            print(f"Done at {now}")

    Build.simulation(top, "bus_if.vcd", add_unnamed_scopes=True)


def gen():
    def top():
        return ScanWrapper(BusIf, {"clk", "rst"})

    netlist = Build.generate_rtl(top, "bus_if.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(target_dir="q_bus_if", top_level=top_level_name, source_files=("bus_if.sv",), clocks=(("clk", 10), ("top_clk", 100)), project_name="bus_if")
    flow.generate()
    flow.run()


if __name__ == "__main__":
    #gen()
    sim()

