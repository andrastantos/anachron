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
TODO:

Changes needed to co-exist with Disco and fix DMA timing.

Espresso should (when programmed to) delay the start of a DRAM/I/O/DMA cycle if dram.n_wait is asserted.
Espresso should (when programmed to) back-off DRAM cycle, if dram.n_wait is asserted in the same cycle as dram.n_ras_X is. Then, wait until dram.n_wait is de-asserted and retry.
Espresso should (when programmed to) delay asserting dram.n_dack until after dram.n_ras is asserted and confirmed not-interfering with dram.n_wait

Espresso should delay asserting dram.n_cas_X during DMA cycles until dram.n_wait is de-asserted.

Espresso should sample dram.n_wait on the falling edge of clk.

Espresso should sample DMA requests on the falling edge of clk (this is in cpu_dma.py).

"""

"""
Bus interface of the V1 pipeline.

This module is not part of the main pipeline, it sits on the side.

It communicates with 'fetch' and 'memory' to serve memory requests.

It does the following:
- Handles arbitration (internal and external)
- Generates appropriately timed signals for (NMOS) DRAM chips
- Sends data (in case of reads) back to requestors


                        <------- 4-beat burst -------------><---- single ----><---- single ----><---------- 4-beat burst ----------><- refresh->
    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\_
    DRAM_nRAS       ^^^^^^^^^\_____________________________/^^^^^\___________/^^^^^\___________/^^^^^\_____________________________/^^^^^\_____/^^^^^^^^^^
    DRAM_nCAS_A     ^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_nCAS_B     ^^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_ADDR       ---------<==X=====X=====X=====X=====>--------<==X=====>--------<==X=====>--------<==X=====X=====X=====X=====>--------<==>-------------
    DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_DATA       --------------<>-<>-<>-<>-<>-<>-<>-<>-------------<>-<>--------------<>-<>-------------<>-<>-<>-<>-<>-<>-<>-<>------------------------
    DRAM_nWE        ^^^^^^^^^\_____________________________/^^^^^\___________/^^^^^\___________/^^^^^\_____________________________/^^^^^\-----/^^^^^^^^^^
    DRAM_DATA       ------------<==X==X==X==X==X==X==X==>-----------<==X==>-----------<==X==>-----------<==X==X==X==X==X==X==X==>-------------------------
    n_wait          --------/^^^^^^^^^^^^^^^^^^^^^^^^^^^\-------/^^^^^^^^^\-------/^^^^^^^^^\-------/^^^^^^^^^^^^^^^^^^^^^^^^^^^\-------------------------
    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\_
    req_valid       ___/^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^\___________/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\_____________________________/^^^^
    req_ready       ^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^\___________/^^^^^\___________/^^^^^^^^^^^^^^^^^^^^^^^\_______________________/^^^^^^^^^^
    req_wr          _________________________________________________________/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    req_addr        ---<=====X=====X=====X=====>-----------<=====>-----------<=====X=================X=====X=====X=====>----------------------------------
    req_data        ---------------------------------------------------------------<=================X=====X=====X=====>----------------------------------
                       |----------------->                 |---------------->|----------------->---------------->
    rsp_valid       _____________________/^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^\___________/^^^^^\____________________________________________________
    rsp_ready       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    rsp_data        ---------------------<=====X=====X=====X=====>-----------<=====>-----------<=====>----------------------------------------------------

                        <----------- delayed 4-beat burst -------------><---- abandonded burst ----><---- single ----><---------- 4-beat burst ----------><- refresh->
    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\_
    DRAM_nRAS       ^^^^^^^^^^^^^^^^^^^^^\_____________________________/^^^^^\___________/^^^^^\___________/^^^^^\_____________________________/^^^^^\_____/^^^^^^^^^^
    DRAM_nCAS_A     ^^^^^^^^^^^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_nCAS_B     ^^^^^^^^^^^^^^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_ADDR       ---------------------<==X=====X=====X=====X=====>--------------------------<==X=====>--------<==X=====X=====X=====X=====>--------<==>-------------
    DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_DATA       --------------------------<>-<>-<>-<>-<>-<>-<>-<>-------------------------------<>-<>-------------<>-<>-<>-<>-<>-<>-<>-<>------------------------
    DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^\_____________________________/^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^\_____________________________/^^^^^\-----/^^^^^^^^^^
    DRAM_DATA       ------------------------<==X==X==X==X==X==X==X==>------------------------------<==X==>-----------<==X==X==X==X==X==X==X==>-------------------------
    n_wait          --\______________/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\-------\___^^^^^^^\-------/^^^^^^^^^\-------/^^^^^^^^^^^^^^^^^^^^^^^^^^^\-------------------------
    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\_
    req_valid       ___/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^\___________/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\_____________________________/^^^^
    req_ready       ^^^^^^\___________/^^^^^^^^^^^^^^^^^^^^\___________/^^^^^\___________/^^^^^\___________/^^^^^^^^^^^^^^^^^^^^^^^\_______________________/^^^^^^^^^^
    req_wr          _____________________________________________________________________/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    req_addr        ---<=====<=====<=====X=====X=====X=====>-----------<=====>-----------<=====X=================X=====X=====X=====>----------------------------------
    req_data        ---------------------------------------------------------------------------<=================X=====X=====X=====>----------------------------------
                       |-----|-----|----------------->                 |---------------->|----------------->---------------->
    rsp_valid       _________________________________/^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^\___________/^^^^^\____________________________________________________
    rsp_ready       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    rsp_data        ---------------------------------<=====X=====X=====X=====>-----------<=====>-----------<=====>----------------------------------------------------


    4-beat burst (req_valid is driven on both edges)
    ================================================

    CLK             \_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\
    DRAM_nRAS       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________________________________________________________/^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_nCAS_A     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_nCAS_B     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_ADDR       -------------------------------< ROW><   COL 0  ><   COL 1  ><   COL 2  ><   COL 3  >--------------------------------
    DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________________________________________________________/^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_DATA       -------------------------------------< D0 >< D1 >< D2 >< D3 >< D4 >< D5 >< D6 >< D7 >--------------------------------
    DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_DATA       ----------------------------------------< D0 >< D1 >< D2 >< D3 >< D4 >< D5 >< D6 >< D7 >-----------------------------
    DRAM_N_WAIT     *^^^^^^^^\__*________/^^*^^^^^^^^^^^*^^^^^^^^^^^*^^^^^^^^^^^*^^^^^^^^^^^*^^^^^^^^^^^*^^^^^^^^^^^*^^^^^^^^^^^*^^^^^^^^
    CLK             \_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\
    req_valid       ______*/^^^^^^^^^^*^^^^^^^^^^^*^^^^^^^^^^^*^^^^^^^^^^^*^^^^^^^^^^^*\__________*___________*___________*___________*__
    req_ready       ^^^^^^*^^^^^^\____*_______/^^^*^^^^^^^^^^^*^^^^^^^^^^^*^^^^^^^^^^^*^^\________*___________*/^^^^^^^^^^*^^^^^^^^^^^*^^
    req_wr
    req_addr
    req_data

    rsp_valid
    rsp_ready
    rsp_data

Notes:
1. Burst length is not communicated over the interface: only the de-assertion of req_valid/req_ready signals the end of a burst.
2. write data is captured with the address on every transaction.
3. rsp_ready is not monitored. It is expected to stay asserted at all times when there are outstanding reads.
4. Writes don't have any response
5. Client arbitration happens only during the idle state: i.e. we don't support clients taking over bursts from each other

Contract details:
1. If requestor lowers req_valid, it means the end of a burst: the bus interface
   will immediately lower req_ready and go through pre-charge and arbitration
   cycles.
2. Similarly, if 'client_id' changes, it signals the end of a burst. The bus
   interface reacts the same was in previous point
3. Bus interface is allowed to de-assert req_ready independent of req_valid.
   This is the case for non-burst targets, such as ROMs or I/O.
4. Addresses must be consecutive and must not cross page-boundary within a
   burst. The bus_if doesn't check for this (maybe it should assert???) and
   blindly puts the address on the DRAM bus. Address incrementing is the
   responsibility of the requestor (it probably does it anyway). Bursts don't
   have to be from/to contiguous addresses, as long as they stay within one page
   (only lower 8 address bits change).
4. Reads and writes are not allowed to be mixed within a burst. This is
   - again - not checked by the bus_if.
5. Resposes to bursts are uninterrupted, that is to say, rsp_valid will go
   inactive (and *will* go inactive) only on burst boundaries.
6. There isn't pipelining between requests and responses. That is to say, that
   in the cycle the next request is accepted, the previous response is either
   completed or the last response is provided in the same cycle.


Non-DRAM accesses:

                             <-- even read ---><--- odd write ---><- even read w. wait -->
    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/
    n_nren          ^^^^^^^^^\___________/^^^^^\___________/^^^^^\_________________/^^^^^^
    DRAM_nCAS_A     ^^^^^^^^^^^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^^
    DRAM_nCAS_B     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_ADDR       ---------<==X========>-----<==X========>-----<==X==============>------
    DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_DATA       ---------------------<>----------------<>----------------------<>-----
    DRAM_nWE        ^^^^^^^^^\___________/^^^^^\___________/^^^^^\_________________/^^^^^^
    DRAM_DATA       ------------<========>-----------<=====>--------<==============>------
    n_wait          ---------------/^^^^^\-----------/^^^^^\-----------\_____/^^^^^\------
    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/
    req_valid       ___/^^^^^\_____/^^^^^^^^^^^\___________/^^^^^\________________________
    req_ready       ^^^^^^^^^\___________/^^^^^\___________/^^^^^\_________________/^^^^^^
    req_wr          _______________/^^^^^^^^^^^\__________________________________________
    req_addr        ---<=====>-----<===========>-----------<=====>------------------------
    req_data        ---------------<===========>------------------------------------------
                       |----------------->                 |----------------------->
    rsp_valid       _____________________/^^^^^\___________________________________/^^^^^\
    rsp_ready       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    rsp_data        ---------------------<=====>-----------------------------------<=====>

1. Bursts are not supported: req_ready goes low after the request is accepted
2. Only 8-bit transfers are allowed; LSB address can be recovered from DRAM_nCAS_A.
3. If 16-bit transfers are requested, those are broken down into two 8-bit transfers.
4. n_wait is sampled on the rising edge of every cycle, after internal wait-states are accounted for
5. There is at least one internal wait-state
6. For writes, the relevant byte of 'req_data' should be valid.

TODO: These timings don't really support external devices with non-0 data hold-time requirements. Maybe we can delay turning off data-bus drivers by half a cycle?

DRAM banks:

We allow 1, 2 or 4 DRAM banks (configured through a CSR, default to 1-bank)
We map banks on 64k page boundary.
    1. This means we'll need to shift the higher address lines around
       depending on the number of DRAM banks used
    2. This also means that NRAM accesses need to use yet another
       address muxing; we end up re-using the 1-bank setup.

This setup requires us muxing the top 3 address lines in different ways,
but allows us to view memory as one contiguous region, independent of how many
DRAM banks are configured. It is still the responsibility of the system SW
to somehow auto-detect the number of DRAM banks installed and set up the
CSRs accordingly. I think there is a way to auto-detect this as unused banks
will not work in read/write tests.
"""

"""
I need to unify all client interfaces to the BusIf module such that
a single (maybe cascaded) arbiter can deal with all of them
"""



class BusIf(Module):
    clk = ClkPort()
    rst = RstPort()

    request = Input(BusIfRequestIf)
    response = Output(BusIfResponseIf)

    # CRS interface for config registers
    reg_if = Input(CsrIf)

    # DRAM interface
    dram = Output(ExternalBusIf)

    # Events
    event_bus_idle = Output(logic)

    """
    Address map:

        0x?000_0000 ... 0x?7ff_ffff: NRAM space (aliased twice due to lack of address pins)
        0x?800_0000 ... 0x?fff_ffff: DRAM space (divided into two banks based on CSR config)

        NOTE: addresses here are 16-bit word addresses.

        Address bits 30:27 determine the number of wait-states.
        Address bits 26    determine which space we're talking about
        Address bits 22:0  determine the location to address within a space, leaving 16MB of addressable space.
                           NOTE: for DRAM space, the A/B bank decode depends on CSR settings

        TODO: really what should happen is that address bit 30 should not partake in wait-state selection, instead
              it should be used by the address calculation unit to determine if logical-to-physical translation needs
              to happen.
        TODO: Espresso should (when programmed to) delay the start of a DRAM/I/O/DMA cycle if dram.n_wait is asserted.
        TODO: Espresso should (when programmed to) back-off DRAM cycle, if dram.n_wait is asserted in the same cycle as dram.n_ras_X is. Then, wait until dram.n_wait is de-asserted and retry.
        TODO: Espresso should (when programmed to) delay asserting dram.n_dack until after dram.n_ras is asserted and confirmed not-interfering with dram.n_wait
        TODO: Espresso should delay asserting dram.n_cas_X during DMA cycles until dram.n_wait is de-asserted.
        TODO: Espresso should sample dram.n_wait on the falling edge of clk.
        TODO: Espresso should sample DMA requests on the falling edge of clk (this is in cpu_dma.py).


        NOTE: wait-states are actually ignored by the bus-interface when interacting with non-DMA DRAM transfers.
              however, DMA transactions do need wait-state designation, so in reality no more than 64MB of DRAM
              can be addressed in each of the spaces
        NOTE: addressing more than 64MB of DRAM is a bit problematic because they can't be contiguous. This isn't
              a big deal for this controller as there aren't enough external banks to get to that high of memory
              configurations anyway. The maximum addressable memory is 16MB in a 2-bank setup.
        NOTE: since addresses are in 16-bit quantities inside here, we're counting bits 30 downwards
    """

    reg_dram_config_ofs = 0
    # Register setup:
    # bits 7-0: refresh divider
    # bit 8: refresh disable (if set)
    # bit 10-9: DRAM bank size: 0 - 16 bits, 1 - 18 bits, 2 - 20 bits, 3 - 22 bits
    # bit 11: DRAM bank swap: 0 - no swap, 1 - swap
    # bit 12: Single-bank DRAM: 0 - decode both banks, 1 - bank 0 and 1 are the same
    refresh_counter_size = 8

    #### TODO:
    #### - Wait-state selection should probably change. Have only three bits and decode as follows:
    ####    7 - 0  wait states
    ####    6 - 1  wait state
    ####    5 - 2  wait states
    ####    4 - 4  wait states
    ####    3 - 6  wait states
    ####    2 - 8  wait states
    ####    1 - 12 wait states
    ####    0 - 15 wait states
    ####   Or maybe even consider specifying wait-states in us, instead of cycles?
    def body(self):
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
        arb_port_select <<= LatchReg(arb_port_comb, enable=state == BusIfStates.idle)

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

        req_dram = (req_addr[26:25] != 0) & ((arb_port_select == Ports.mem_port) | (arb_port_select == Ports.fetch_port))
        req_nram = (req_addr[26:25] == 0) & ((arb_port_select == Ports.mem_port) | (arb_port_select == Ports.fetch_port))
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
        byte_en <<= LatchReg(req_byte_en, enable=req_advance)
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


def gen():
    def top():
        class BusIfWrapperDmaRequestIf(ReadyValid):
            read_not_write  = logic
            one_hot_channel = Unsigned(4)
            byte_en         = Unsigned(2)
            addr            = BrewBusAddr
            is_master       = logic
            terminal_count  = logic

        class BusIfWrapper(Module):
            clk = ClkPort()
            rst = RstPort()

            # Interface to fetch and memory
            fetch_request  = Input(BusIfRequestIf)
            fetch_response = Output(BusIfResponseIf)
            mem_request  = Input(BusIfRequestIf)
            mem_response = Output(BusIfResponseIf)
            dma_request = Input(BusIfWrapperDmaRequestIf)
            dma_response = Output(BusIfDmaResponseIf)

            # CRS interface for config registers
            reg_if = Input(ApbIf(BrewCsrData, Unsigned(4)))

            # DRAM interface
            dram = Output(ExternalBusIf)

            # Events
            event_bus_idle = Output(logic)

            def body(self):
                bus_if = BusIf()
                bus_if.fetch_request <<= self.fetch_request
                self.fetch_response <<= bus_if.fetch_response

                bus_if.mem_request <<= self.mem_request
                self.mem_response <<= bus_if.mem_response

                bus_if.dma_request.read_not_write <<= self.dma_request.read_not_write
                bus_if.dma_request.one_hot_channel <<= self.dma_request.one_hot_channel
                bus_if.dma_request.byte_en <<= self.dma_request.byte_en
                bus_if.dma_request.addr <<= self.dma_request.addr
                bus_if.dma_request.is_master <<= self.dma_request.is_master
                bus_if.dma_request.terminal_count <<= self.dma_request.terminal_count
                bus_if.dma_request.valid <<= self.dma_request.valid
                self.dma_request.ready <<= bus_if.dma_request.ready
                self.dma_response <<= bus_if.dma_response
                bus_if.reg_if <<= self.reg_if
                self.dram <<= bus_if.dram
                self.event_bus_idle <<= bus_if.event_bus_idle

        #return ScanWrapper(BusIf, {"clk", "rst"})
        return BusIfWrapper()

    netlist = Build.generate_rtl(top, "synth/bus_if.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(
        target_dir="synth/q_bus_if",
        top_level=top_level_name,
        source_files=("synth/bus_if.sv",),
        clocks=(("clk", 10),),# ("top_clk", 100)),
        project_name="bus_if",
        no_timing_report_clocks="clk",
        family="MAX 10",
        device="10M50DAF672C7G" # Something large with a ton of pins
    )
    flow.generate()
    flow.run()


if __name__ == "__main__":
    gen()

