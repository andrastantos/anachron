import sys
from pathlib import Path
import itertools

sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon"))
sys.path.append(str(Path(__file__).parent / ".." / ".." / ".." / "silicon" / "unit_tests"))

try:
    from .brew_types import *
    from .scan import *
    from .synth import *
except ImportError:
    from brew_types import *
    from scan import *
    from synth import *

from silicon import *

class UartParityType(Enum):
    none = 0
    even = 1
    odd  = 2

class UartStopBits(Enum):
    one = 0
    one_and_half = 1
    two = 2

class UartWordSize(Enum):
    bit8 = 0
    bit7 = 1
    bit6 = 2
    bit5 = 3

class PhyDataIf(ReadyValid):
    data = Unsigned(8)

class ApbUart(Module):
    clk = ClkPort()
    rst = RstPort()

    bus_if = Input(Apb8If)
    interrupt = Output(logic)

    rxd = Input(logic)
    txd = Output(logic)
    cts = Input(logic)
    rts = Output(logic)
    n_tx_en = Output(logic)

    class UartTxPhy(Module):
        clk = ClkPort()
        rst = RstPort()

        data_in = Input(PhyDataIf)

        parity = Input(EnumNet(UartParityType))
        stop_cnt = Input(EnumNet(UartStopBits))
        word_size = Input(Unsigned(3))
        hw_flow_ctrl = Input(logic)
        use_tx_en = Input(logic)

        prescaler_select = Input(Unsigned(3))
        divider_limit = Input(Unsigned(8))

        txd = Output(logic)
        cts = Input(logic)
        cts_out = Output(logic)
        tx_en = Output(logic)

        def body(self):
            fsm = FSM()

            class UartTxPhyStates(Enum):
                idle = 0
                tx_en = 1
                start = 2
                data = 3
                parity = 4
                stop_half = 5
                stop = 6
                stop_two = 7

            fsm.reset_value <<= UartTxPhyStates.idle
            fsm.default_state <<= UartTxPhyStates.idle

            cts = Reg(Reg(self.cts))
            self.cts_out <<= cts

            state = Wire()
            state <<= fsm.state


            prescaler_counter = Wire(Unsigned(self.prescaler_select.get_net_type().max_val))
            prescaler_counter <<= Reg(increment(prescaler_counter))
            masks = ((1 << i)-1 for i in range(self.prescaler_select.get_net_type().max_val+1))
            prescaler_tick = (prescaler_counter & Select(self.prescaler_select, *masks)) == 0

            divider_counter = Wire(Unsigned(8))
            divider_tick = (divider_counter == 0) & prescaler_tick
            divider_counter <<= Reg(Select(
                divider_tick | (state == UartTxPhyStates.idle),
                decrement(divider_counter),
                self.divider_limit
            ), clock_en=prescaler_tick)

            oversampler = Wire(logic)
            oversampler <<= Reg(
                SelectOne(
                    state == UartTxPhyStates.idle, 0,
                    state == UartTxPhyStates.stop_half, oversampler,
                    state == UartTxPhyStates.tx_en, oversampler,
                    default_port = ~oversampler
                ),
                clock_en=divider_tick
            )
            baud_tick = oversampler & divider_tick
            baud_half_tick = ~oversampler & divider_tick

            bit_counter = Wire(Unsigned(3))

            starting = self.data_in.ready & self.data_in.valid
            self.data_in.ready <<= (state == UartTxPhyStates.idle) & (cts | ~self.hw_flow_ctrl)

            bit_counter <<= Reg(Select(
                starting,
                Select(
                    baud_tick,
                    bit_counter,
                    (bit_counter -1)[2:0]
                ),
                self.word_size
            ))
            shift_reg = Wire(Unsigned(8))
            shift_reg <<= Reg(
                Select(
                    starting,
                    Select(
                        baud_tick & (state == UartTxPhyStates.data),
                        shift_reg,
                        shift_reg >> 1
                    ),
                    self.data_in.data
                )
            )

            parity_reg = Wire(logic)
            parity_reg <<= Reg(
                Select(
                    starting,
                    Select(
                        baud_tick,
                        parity_reg,
                        parity_reg ^ shift_reg[0]
                    ),
                    (self.parity == UartParityType.odd)
                )
            )


            self.tx_en <<= Reg(Select(state == UartTxPhyStates.tx_en, Select(state == UartTxPhyStates.stop, self.tx_en, 0), 1))

            fsm.add_transition(UartTxPhyStates.idle, starting & ~self.use_tx_en, UartTxPhyStates.start)
            fsm.add_transition(UartTxPhyStates.idle, starting &  self.use_tx_en, UartTxPhyStates.tx_en)
            fsm.add_transition(UartTxPhyStates.tx_en, baud_half_tick, UartTxPhyStates.start)
            fsm.add_transition(UartTxPhyStates.start, baud_tick, UartTxPhyStates.data)
            fsm.add_transition(UartTxPhyStates.data, (bit_counter == 0) & (self.parity == UartParityType.none) & baud_tick & (self.stop_cnt == UartStopBits.one), UartTxPhyStates.stop)
            fsm.add_transition(UartTxPhyStates.data, (bit_counter == 0) & (self.parity == UartParityType.none) & baud_tick & (self.stop_cnt == UartStopBits.one_and_half), UartTxPhyStates.stop_half)
            fsm.add_transition(UartTxPhyStates.data, (bit_counter == 0) & (self.parity == UartParityType.none) & baud_tick & (self.stop_cnt == UartStopBits.two), UartTxPhyStates.stop_two)
            fsm.add_transition(UartTxPhyStates.data, (bit_counter == 0) & (self.parity != UartParityType.none) & baud_tick, UartTxPhyStates.parity)
            fsm.add_transition(UartTxPhyStates.parity, baud_tick & (self.stop_cnt == UartStopBits.one), UartTxPhyStates.stop)
            fsm.add_transition(UartTxPhyStates.parity, baud_tick & (self.stop_cnt == UartStopBits.one_and_half), UartTxPhyStates.stop_half)
            fsm.add_transition(UartTxPhyStates.parity, baud_tick & (self.stop_cnt == UartStopBits.two), UartTxPhyStates.stop_two)
            fsm.add_transition(UartTxPhyStates.stop_two, baud_tick, UartTxPhyStates.stop)
            fsm.add_transition(UartTxPhyStates.stop_half, baud_half_tick, UartTxPhyStates.stop)
            fsm.add_transition(UartTxPhyStates.stop, baud_tick, UartTxPhyStates.idle)

            self.txd <<= Reg(SelectOne(
                state == UartTxPhyStates.start, 0,
                state == UartTxPhyStates.data, shift_reg[0],
                state == UartTxPhyStates.parity, parity_reg,
                default_port = 1
            ), reset_value_port = 1)


    class UartRxPhy(Module):
        clk = ClkPort()
        rst = RstPort()

        data_out = Output(PhyDataIf)

        parity = Input(EnumNet(UartParityType))
        stop_cnt = Input(EnumNet(UartStopBits))
        word_size = Input(Unsigned(3))
        hw_flow_ctrl = Input(logic)

        rxd = Input(logic)
        rts = Output(logic)

        framing_error = Output(logic)
        parity_error = Output(logic)
        overrun_error = Output(logic)
        clear = Input(logic)

        prescaler_select = Input(Unsigned(3))
        divider_limit = Input(Unsigned(8))

        enable = Input(logic)

        def body(self):
            fsm = FSM()

            class UartRxPhyStates(Enum):
                idle = 0
                half_start = 1
                start = 2
                data = 3
                parity = 4
                stop_half = 5
                stop = 6
                stop_two = 7

            fsm.reset_value <<= UartRxPhyStates.idle
            fsm.default_state <<= UartRxPhyStates.idle

            state = Wire()
            state <<= fsm.state
            next_state = Wire()
            next_state <<= fsm.next_state

            rxd = Wire()

            prescaler_counter = Wire(Unsigned(self.prescaler_select.get_net_type().max_val))
            prescaler_counter <<= Reg(increment(prescaler_counter))
            masks = ((1 << i)-1 for i in range(self.prescaler_select.get_net_type().max_val+1))
            prescaler_tick = (prescaler_counter & Select(self.prescaler_select, *masks)) == 0

            divider_counter = Wire(Unsigned(8))
            divider_tick = (divider_counter == 0) & prescaler_tick
            divider_counter <<= Reg(Select(
                divider_tick | (state == UartRxPhyStates.idle),
                decrement(divider_counter),
                self.divider_limit
            ), clock_en=prescaler_tick)

            oversampler = Wire(logic)
            oversampler <<= Reg(
                SelectOne(
                    state == UartRxPhyStates.idle, 0,
                    state == UartRxPhyStates.stop_half, oversampler,
                    default_port = ~oversampler
                ),
                clock_en=divider_tick
            )
            baud_tick = oversampler & divider_tick
            baud_half_tick = ~oversampler & divider_tick

            bit_counter = Wire(Unsigned(3))

            starting = ~self.data_out.valid & (state == UartRxPhyStates.idle) & ~rxd & self.enable
            rx_full = Wire(logic)
            rx_full <<= Reg(
                Select(
                    (state == UartRxPhyStates.data) & (bit_counter == 0) & baud_tick,
                    Select(
                        self.data_out.ready,
                        rx_full,
                        0
                    ),
                    1
                )
            )
            self.data_out.valid <<= rx_full

            bit_counter <<= Reg(Select(
                starting,
                Select(
                    baud_tick,
                    bit_counter,
                    (bit_counter -1)[2:0]
                ),
                self.word_size
            ))
            shift_reg = Wire(Unsigned(8))
            shift_reg <<= Reg(
                Select(
                    starting,
                    Select(
                        baud_half_tick & (next_state == UartRxPhyStates.data),
                        shift_reg,
                        concat(rxd, shift_reg[7:1])
                    ),
                    0
                )
            )
            self.data_out.data <<= shift_reg

            ref_parity_reg = Wire(logic)
            ref_parity_reg <<= Reg(
                Select(
                    starting,
                    Select(
                        baud_tick,
                        ref_parity_reg,
                        ref_parity_reg ^ rxd
                    ),
                    (self.parity == UartParityType.odd)
                )
            )

            self.parity_error <<= Reg(
                Select(
                    self.clear,
                    Select(
                        (state == UartRxPhyStates.parity) & baud_tick,
                        self.parity_error,
                        self.parity_error | (rxd != ref_parity_reg)
                    ),
                    0
                )
            )
            self.framing_error <<= Reg(
                Select(
                    self.clear,
                    Select(
                        ((state == UartRxPhyStates.stop_half) | (state == UartRxPhyStates.stop_two) | (state == UartRxPhyStates.stop)) & (rxd == 0),
                        self.framing_error,
                        1
                    ),
                    0
                )
            )
            self.overrun_error <<= Reg(
                Select(
                    self.clear,
                    Select(
                        (state == UartRxPhyStates.data) & (bit_counter == 0) & baud_tick & rx_full & ~self.data_out.ready,
                        self.overrun_error,
                        1
                    ),
                    0
                )
            )

            fsm.add_transition(UartRxPhyStates.idle, starting, UartRxPhyStates.half_start)
            fsm.add_transition(UartRxPhyStates.half_start, self.enable & baud_half_tick, UartRxPhyStates.start)
            fsm.add_transition(UartRxPhyStates.start,      self.enable & baud_half_tick, UartRxPhyStates.data)
            fsm.add_transition(UartRxPhyStates.data,       self.enable & baud_tick & (bit_counter == 0) & (self.parity == UartParityType.none) & (self.stop_cnt == UartStopBits.one), UartRxPhyStates.stop)
            fsm.add_transition(UartRxPhyStates.data,       self.enable & baud_tick & (bit_counter == 0) & (self.parity == UartParityType.none) & (self.stop_cnt == UartStopBits.one_and_half), UartRxPhyStates.stop_half)
            fsm.add_transition(UartRxPhyStates.data,       self.enable & baud_tick & (bit_counter == 0) & (self.parity == UartParityType.none) & (self.stop_cnt == UartStopBits.two), UartRxPhyStates.stop_two)
            fsm.add_transition(UartRxPhyStates.data,       self.enable & baud_half_tick & (bit_counter == 0) & (self.parity != UartParityType.none), UartRxPhyStates.parity)
            fsm.add_transition(UartRxPhyStates.parity,     self.enable & baud_tick & (self.stop_cnt == UartStopBits.one), UartRxPhyStates.stop)
            fsm.add_transition(UartRxPhyStates.parity,     self.enable & baud_tick & (self.stop_cnt == UartStopBits.one_and_half), UartRxPhyStates.stop_half)
            fsm.add_transition(UartRxPhyStates.parity,     self.enable & baud_tick & (self.stop_cnt == UartStopBits.two), UartRxPhyStates.stop_two)
            fsm.add_transition(UartRxPhyStates.stop_two,   self.enable & baud_tick, UartRxPhyStates.stop)
            fsm.add_transition(UartRxPhyStates.stop_half,  self.enable & baud_half_tick, UartRxPhyStates.stop)
            fsm.add_transition(UartRxPhyStates.stop,       self.enable & baud_tick, UartRxPhyStates.idle)
            # Immediately return to idle if get disabled
            fsm.add_transition(UartRxPhyStates.half_start, ~self.enable, UartRxPhyStates.idle)
            fsm.add_transition(UartRxPhyStates.start,      ~self.enable, UartRxPhyStates.idle)
            fsm.add_transition(UartRxPhyStates.data,       ~self.enable, UartRxPhyStates.idle)
            fsm.add_transition(UartRxPhyStates.parity,     ~self.enable, UartRxPhyStates.idle)
            fsm.add_transition(UartRxPhyStates.stop_two,   ~self.enable, UartRxPhyStates.idle)
            fsm.add_transition(UartRxPhyStates.stop_half,  ~self.enable, UartRxPhyStates.idle)
            fsm.add_transition(UartRxPhyStates.stop,       ~self.enable, UartRxPhyStates.idle)

            # CDC crossing
            rxd <<= Reg(Reg(self.rxd, reset_value_port = 1), reset_value_port = 1)
            self.rts <<= Select(self.hw_flow_ctrl, 0, ~rx_full)

    data_buf_reg_ofs = 0
    status_reg_ofs = 1
    config1_reg_ofs = 2
    config2_reg_ofs = 3
    divider_reg_ofs = 4
    """
    Reg 0:
        read  - received data (block if not ready)
        write - data to transmit (block if full)
    Reg 1: status
        bit 0 - rx full
        bit 1 - tx empty
        bit 2 - parity error
        bit 3 - framing error
        bit 4 - overrun error
        bit 5 - cts pin value (inverted)
    Reg 2: config1
        bit 0-1 - parity
        bit 2-3 - stop_cnt
        bit 4-5 - word-size
        bit 6   - flow-control
        bit 7   - interrupt enable
    Reg 3: config2
        bit 0-2 - pre-scaler
        bit 4   - rts (if SW flow-ctrl) (inverted)
        bit 5   - RX enable
        bit 6   - use HW tx_en
        bit 7   - tx_en (1 to enable TX)
    Reg 4: divider
        divider
    """
    def body(self):
        tx_phy = ApbUart.UartTxPhy()
        rx_phy = ApbUart.UartRxPhy()

        config_reg = Wire(Unsigned(8))
        rx_data = Wire(PhyDataIf)
        rx_data <<= ForwardBuf(rx_phy.data_out)
        tx_data = Wire(PhyDataIf)
        tx_phy.data_in <<= ForwardBuf(tx_data)
        prescaler_select = Wire(Unsigned(3))
        soft_rts = Wire(logic)
        divider_limit = Wire(Unsigned(8))
        interrupt_en = Wire(logic)
        hw_flow_ctrl = Wire(logic)
        rx_enable = Wire(logic)
        use_hw_tx_en = Wire(logic)
        soft_tx_en = Wire(logic)

        self.bus_if.pready <<= Reg(
            Select(
                self.bus_if.psel,
                1,
                Select(
                    self.bus_if.paddr == 0,
                    1,
                    Select(
                        self.bus_if.pwrite,
                        rx_data.valid,
                        tx_data.ready
                    )
                )
            )
        )
        self.bus_if.prdata <<= Reg(
            Select(
                self.bus_if.paddr,
                # Reg 0: data
                rx_data.data,
                # Reg 1: status
                concat(
                    tx_phy.cts_out,
                    rx_phy.overrun_error,
                    rx_phy.framing_error,
                    rx_phy.parity_error,
                    tx_data.ready,
                    rx_data.valid
                ),
                # Reg 2: config1
                config_reg,
                # Reg 3: config2
                concat(
                    prescaler_select,
                    "1'b0",
                    soft_rts,
                    rx_enable,
                    use_hw_tx_en,
                    soft_tx_en,
                ),
                # Reg 4: divider 2
                divider_limit,
            )
        )
        data_reg_wr =    (self.bus_if.psel & self.bus_if.penable &  self.bus_if.pwrite & (self.bus_if.paddr == ApbUart.data_buf_reg_ofs))
        data_reg_rd =    (self.bus_if.psel & self.bus_if.penable & ~self.bus_if.pwrite & (self.bus_if.paddr == ApbUart.data_buf_reg_ofs))
        status_reg_wr =  (self.bus_if.psel & self.bus_if.penable &  self.bus_if.pwrite & (self.bus_if.paddr == ApbUart.status_reg_ofs))
        config1_reg_wr = (self.bus_if.psel & self.bus_if.penable &  self.bus_if.pwrite & (self.bus_if.paddr == ApbUart.config1_reg_ofs))
        config2_reg_wr = (self.bus_if.psel & self.bus_if.penable &  self.bus_if.pwrite & (self.bus_if.paddr == ApbUart.config2_reg_ofs))
        divider_reg_wr = (self.bus_if.psel & self.bus_if.penable &  self.bus_if.pwrite & (self.bus_if.paddr == ApbUart.divider_reg_ofs))
        config_reg <<= Reg(self.bus_if.pwdata, clock_en=config1_reg_wr)
        prescaler_select <<= Reg(self.bus_if.pwdata[2:0], clock_en=config2_reg_wr)
        soft_rts <<= Reg(self.bus_if.pwdata[4], clock_en=config2_reg_wr)
        rx_enable <<= Reg(self.bus_if.pwdata[5], clock_en=config2_reg_wr)
        use_hw_tx_en <<= Reg(self.bus_if.pwdata[6], clock_en=config2_reg_wr)
        soft_tx_en <<= Reg(self.bus_if.pwdata[7], clock_en=config2_reg_wr)

        divider_limit <<= Reg(self.bus_if.pwdata, clock_en=divider_reg_wr)
        tx_data.data <<= self.bus_if.pwdata
        tx_data.valid <<= data_reg_wr
        rx_data.ready <<= data_reg_rd
        rx_phy.clear <<= status_reg_wr

        self.interrupt <<= (rx_phy.overrun_error | rx_phy.framing_error | rx_phy.parity_error | tx_data.ready | rx_data.valid) & interrupt_en

        rx_phy.prescaler_select <<= prescaler_select
        rx_phy.divider_limit <<= divider_limit
        tx_phy.prescaler_select <<= prescaler_select
        tx_phy.divider_limit <<= divider_limit

        tx_phy.parity <<= (EnumNet(UartParityType))(config_reg[1:0])
        tx_phy.stop_cnt <<= (EnumNet(UartStopBits))(config_reg[3:2])
        word_size = Select(config_reg[5:4], 0, 7, 6, 5)
        tx_phy.word_size <<= word_size
        tx_phy.hw_flow_ctrl <<= hw_flow_ctrl
        tx_phy.use_tx_en <<= use_hw_tx_en

        rx_phy.parity <<= (EnumNet(UartParityType))(config_reg[1:0])
        rx_phy.stop_cnt <<= (EnumNet(UartStopBits))(config_reg[3:2])
        rx_phy.word_size <<= word_size
        rx_phy.hw_flow_ctrl <<= hw_flow_ctrl
        rx_phy.enable <<= rx_enable

        hw_flow_ctrl <<= config_reg[6]
        interrupt_en <<= config_reg[7]

        self.txd <<= tx_phy.txd
        rx_phy.rxd <<= self.rxd
        tx_phy.cts <<= ~self.cts
        self.rts <<= ~Select(
            hw_flow_ctrl,
            soft_rts,
            rx_phy.rts
        )
        self.n_tx_en <<= ~Select(
            use_hw_tx_en,
            soft_tx_en,
            tx_phy.tx_en
        )


def sim():

    class test_top(Module):
        clk               = ClkPort()
        rst               = RstPort()

        interrupt1 = Output(logic)
        interrupt2 = Output(logic)

        def body(self):
            self.uart1 = ApbUart()
            self.uart2 = ApbUart()

            self.reg_if1 = Wire(Apb8If)
            self.reg_if1.paddr.set_net_type(Unsigned(3))
            self.uart1.bus_if <<= self.reg_if1

            self.reg_if2 = Wire(Apb8If)
            self.reg_if2.paddr.set_net_type(Unsigned(3))
            self.uart2.bus_if <<= self.reg_if2

            self.uart1.rxd <<= self.uart2.txd
            self.uart2.rxd <<= self.uart1.txd
            self.uart1.cts <<= self.uart2.rts
            self.uart2.cts <<= self.uart1.rts

            self.interrupt1 <<= self.uart1.interrupt
            self.interrupt2 <<= self.uart2.interrupt

        def simulate(self, simulator: Simulator):
            from copy import copy
            reg_ifs = (self.reg_if1, self.reg_if2)

            def wait_clk():
                yield (self.clk, )
                while self.clk.get_sim_edge() != EdgeType.Positive:
                    yield (self.clk, )

            def wait_rst():
                yield from wait_clk()
                while self.rst == 1:
                    yield from wait_clk()

            def write_reg(uart_idx, addr, value):
                nonlocal reg_ifs
                reg_if = reg_ifs[uart_idx]
                reg_if.psel <<= 1
                reg_if.penable <<= 0
                reg_if.pwrite <<= 1
                reg_if.paddr <<= addr
                reg_if.pwdata <<= value
                yield from wait_clk()
                reg_if.penable <<= 1
                yield from wait_clk()
                while not reg_if.pready:
                    yield from wait_clk()
                simulator.log(f"UART{uart_idx+1} {addr} written with value {value:02x} {value:02b}")
                reg_if.psel <<= 0
                reg_if.penable <<= None
                reg_if.pwrite <<= None
                reg_if.paddr <<= None
                reg_if.pwdata <<= None

            def read_reg(uart_idx, addr):
                nonlocal reg_ifs
                reg_if = reg_ifs[uart_idx]

                reg_if.psel <<= 1
                reg_if.penable <<= 0
                reg_if.pwrite <<= 0
                reg_if.paddr <<= addr
                reg_if.pwdata <<= None
                yield from wait_clk()
                reg_if.penable <<= 1
                yield from wait_clk()
                while not reg_if.pready:
                    yield from wait_clk()
                ret_val = copy(reg_if.prdata)
                simulator.log(f"UART{uart_idx+1} {addr} read returned value {ret_val:02x} {ret_val:02b}")
                reg_if.psel <<= 0
                reg_if.penable <<= None
                reg_if.pwrite <<= None
                reg_if.paddr <<= None
                reg_if.pwdata <<= None
                return ret_val

            self.reg_if1.psel <<= 0
            self.reg_if2.psel <<= 0
            yield from wait_rst()
            for _ in range(3):
                yield from wait_clk()
            # Set up both UARTs to the same config
            yield from write_reg(0, ApbUart.config1_reg_ofs, (UartParityType.none.value << 0) | (UartStopBits.one_and_half.value << 2) | (UartWordSize.bit8.value << 4) | (1 << 6))
            yield from write_reg(1, ApbUart.config1_reg_ofs, (UartParityType.none.value << 0) | (UartStopBits.one_and_half.value << 2) | (UartWordSize.bit8.value << 4) | (1 << 6))
            yield from write_reg(0, ApbUart.config2_reg_ofs, (0 << 0) | (0 << 5) | (1 << 6))
            yield from write_reg(1, ApbUart.config2_reg_ofs, (0 << 0) | (1 << 5) | (1 << 6)) # Enable RX on UART2
            yield from write_reg(0, ApbUart.divider_reg_ofs, 5)
            yield from write_reg(1, ApbUart.divider_reg_ofs, 5)
            yield from write_reg(0, ApbUart.status_reg_ofs, 0) # clear any pending status
            yield from write_reg(1, ApbUart.status_reg_ofs, 0) # clear any pending status

            for _ in range(5):
                yield from write_reg(0, ApbUart.data_buf_reg_ofs, 0x55)
                yield from read_reg(1,  ApbUart.data_buf_reg_ofs)
            for i in range(5):
                yield from write_reg(0, ApbUart.data_buf_reg_ofs, i)

    class top(Module):
        clk               = ClkPort()
        rst               = RstPort()

        interrupt1 = Output(logic)
        interrupt2 = Output(logic)

        def body(self):
            local_top = test_top()

            self.interrupt1 <<= local_top.interrupt1
            self.interrupt2 <<= local_top.interrupt2

        def simulate(self, simulator: Simulator) -> TSimEvent:
            def clk() -> int:
                yield 50
                self.clk <<= ~self.clk & self.clk
                yield 50
                self.clk <<= ~self.clk
                yield 0

            #self.program()
            simulator.log("Simulation started")

            self.rst <<= 1
            self.clk <<= 1
            yield 10
            for i in range(5):
                yield from clk()
            self.rst <<= 0

            for i in range(1500):
                yield from clk()
            yield 10
            simulator.log("Done")

    top_class = top
    vcd_filename = "uart.vcd"
    if vcd_filename is None:
        vcd_filename = top_class.__name__.lower()
    with Netlist().elaborate() as netlist:
        top_inst = top_class()
    netlist.simulate(vcd_filename, add_unnamed_scopes=False)

def gen():
    class ApbUart(globals()["ApbUart"]):
        def construct(self):
            self.bus_if.paddr.set_net_type(Unsigned(3))

    #def top():
    #    return ScanWrapper(UartWrapper, {"clk", "rst"})
    def top():
        return ApbUart()

    back_end = SystemVerilog()
    back_end.support_unique_case = False
    netlist = Build.generate_rtl(top, "apb_uart.sv", back_end=back_end)
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(
        target_dir="q_uart",
        top_level=top_level_name,
        source_files=("apb_uart.sv",),
        clocks=(("clk", 10), ("top_clk", 100)),
        project_name="apb_uart",
        device="10M50DAF484C6G" # Device on the DECA board
    )
    flow.generate()
    flow.run()


if __name__ == "__main__":
    gen()
    #sim()


