#!/usr/bin/python3
from random import *
from typing import *
from silicon import *
from silicon.memory import SimpleDualPortMemory

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
The register file for Brew consists of a single write and two read ports.

The V1 version doesn't implement types, so only values are provided.

For FPGAs, BRAMs can be used to implement the register file.

The register file also implements the score-board for the rest of the pipeline to handle reservations
"""

class RegFile(Module):
    clk = ClkPort()
    rst = RstPort()

    # Interface towards decode
    read_req = Input(RegFileReadRequestIf)
    read_rsp = Output(RegFileReadResponseIf)

    # Interface towards the write-back of the pipeline
    write = Input(RegFileWriteBackIf)

    do_branch = Input(logic)

    '''
    CLK                    /^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__
    write.valid            ______/^^^^^\_______________________/^^^^^\_______________________________________________/^^^^^\___________
    write.addr             ------<=====>-----------------------<=====>-----------------------------------------------<=====>-----------
    write.data             ------<=====>-----------------------<=====>-----------------------------------------------<=====>-----------
    CLK                    /^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__
    score_clr              ______/^^^^^\_______________________/^^^^^\_______________________________________________/^^^^^\___________
    score_set              ______/^^^^^\_______________________/^^^^^\___________/^^^^^\_____/^^^^^^^^^^^\_____/^^^^^^^^^^^\___________
    score_value            ^^^^^^^^^^^^\_____________ ^^^^^^^^^^^^^^^\______________________________________________ ^^^^^^\___________
    CLK                    /^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__
    read_req.valid         ______/^^^^^\_________________/^^^^^\_________________/^^^^^\_____/^^^^^^^^^^^\_____/^^^^^^^^^^^\___________
    read_req.ready         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    read_req.readX_valid   ______/^^^^^\_________________/^^^^^\_________________/^^^^^\_____/^^^^^^^^^^^\_____/^^^^^^^^^^^\___________
    read_req.readX_addr    ------<=====>-----------------<=====>-----------------<=====>-----<=====X=====>-----<=====X=====>-----------
    read_rsp.valid         ____________/^^^^^\_______________________/^^^^^\___________/^^^^^\_____/^^^^^^^^^^^\_____/^^^^^^^^^^^\_____
    read_rsp.readX_data    ------------<=====>-----------------------<=====>-----------<=====>-----<=====X=====>-----<=====X=====>-----
                                 bypass behavior           bypass behavior       simple read   back-to-back read  back-to-back read w bypass
    '''

    def body(self):
        buf_read_req = Wire(RegFileReadRequestIf)
        read_req_buf = ForwardBuf()
        buf_read_req <<= read_req_buf(self.read_req)
        read_req_reg_en = read_req_buf.out_reg_en

        buf_write = Wire(RegFileWriteBackIf)
        buf_write <<= Reg(self.write)

        # We have two memory instances, one for each read port. The write ports of
        # these instances are connected together so they get written the same data
        # TODO: check which setting Quartus likes better
        user_address_registers = False
        mem1 = SimpleDualPortMemory(registered_input_a=True, registered_output_a=True, registered_input_b=user_address_registers, registered_output_b=not user_address_registers, addr_type=BrewRegAddr, data_type=BrewData)
        mem2 = SimpleDualPortMemory(registered_input_a=True, registered_output_a=True, registered_input_b=user_address_registers, registered_output_b=not user_address_registers, addr_type=BrewRegAddr, data_type=BrewData)

        # We disable forwarding and writing to the RF if write.data_en is not asserted.
        # This allows for clearing a reservation without touching the data
        # during (branch/exception recovery).
        mem1.port1_write_en <<= self.write.valid & self.write.data_en
        mem1.port1_data_in <<= self.write.data
        mem1.port1_addr <<= self.write.addr
        mem2.port1_write_en <<= self.write.valid & self.write.data_en
        mem2.port1_data_in <<= self.write.data
        mem2.port1_addr <<= self.write.addr

        # NOTE: Bypass logic seems to be necessary independent of address/data registering
        #       on the read interface (in other words read-new-data behavior). Not sure
        #       why, it could be that this is a bug in my memory models.
        # NOTE: Quartus at least has a really hard time with 'read new data' configuration of
        #       the memories. It outputs a note that it generates bypass logic, but the gate
        #       level simulation shows bad behavior for not even conflicting, but adjacent
        #       writes. The issue appears to be that write is double-registered and adjacent
        #       read of the same address conflicts with the write, generating X-es. Not sure
        #       if this is a simulation issue or a true problem in the operation of the RAMs
        #       but since we have the bypass logic here anyway, let's not depend on the RAMS.
        # NOTE: If we don't register the inputs on the memory, we have to use latches to
        #       early-load addresses into the memory block. The reason is that we can't use
        #       clock-enable now to mask out invalid addresses from the input in this case:
        #       The clock-enable would prevent latching results, not the latching of addresses.
        #       The write port in the case of a reservation conflict (on the other memory
        #       bank) can change the content of the underlying memory and result in returning
        #       the old register value since the clock-enable has long been gone. If we
        #       registered the addresses on the memory block, clock-enable based logic is
        #       fine.
        # NOTE: Latches are needed (normal flops won't do it) because the underling memory
        #       in this case registers the output. So we can't incur another clock cycle
        #       of latency in handling the addresses.
        if user_address_registers:
            mem1.port2_addr <<= self.read_req.read1_addr
            mem1.port2_clk_en <<= read_req_reg_en
        else:
            mem1.port2_addr <<= LatchReg(self.read_req.read1_addr, enable = read_req_reg_en)
        self.read_rsp.read1_data <<= Select(
            (buf_write.addr == buf_read_req.read1_addr) & buf_write.valid & buf_write.data_en,
            mem1.port2_data_out,
            buf_write.data
        )

        if user_address_registers:
            mem2.port2_addr <<= self.read_req.read2_addr
            mem2.port2_clk_en <<= read_req_reg_en
        else:
            mem2.port2_addr <<= LatchReg(self.read_req.read2_addr, enable = read_req_reg_en)
        self.read_rsp.read2_data <<= Select(
            (buf_write.addr == buf_read_req.read2_addr) & buf_write.valid & buf_write.data_en,
            mem2.port2_data_out,
            buf_write.data
        )

        # Reservation logic
        rsv_board = Wire(Unsigned(BrewRegCnt))

        def to_one_hot(addr):
            args = []
            for i in range(BrewRegCnt):
                args.append(1 << i)
            return Select(addr, *args)

        rsv_clr_mask = Select(buf_write.valid,    0, to_one_hot(buf_write.addr))
        read1_mask =   Select(buf_read_req.valid & buf_read_req.read1_valid, 0, to_one_hot(buf_read_req.read1_addr))
        read2_mask =   Select(buf_read_req.valid & buf_read_req.read2_valid, 0, to_one_hot(buf_read_req.read2_addr))
        rsv_set_mask = Select(buf_read_req.valid & buf_read_req.rsv_valid,   0, to_one_hot(buf_read_req.rsv_addr))

        rsv_board_next = rsv_board & ~rsv_clr_mask | Select(buf_read_req.ready, 0, rsv_set_mask)
        rsv_board <<= Reg(rsv_board_next)

        # Handshake
        rsv_board_read1_ready = Select(
            buf_read_req.read1_valid,
            1,
            (rsv_board & ~rsv_clr_mask & read1_mask) == 0
        )

        rsv_board_read2_ready = Select(
            buf_read_req.read2_valid,
            1,
            (rsv_board & ~rsv_clr_mask & read2_mask) == 0
        )

        rsv_board_rsv_ready = Select(
            buf_read_req.rsv_valid,
            1,
            (rsv_board & ~rsv_clr_mask & rsv_set_mask) == 0
        )

        all_ready = rsv_board_read1_ready & rsv_board_read2_ready & rsv_board_rsv_ready
        buf_read_req.ready <<= all_ready & self.read_rsp.ready
        self.read_rsp.valid <<= all_ready & buf_read_req.valid





def gen():
    def top():
        return ScanWrapper(RegFile, {"clk", "rst"})

    netlist = Build.generate_rtl(top, "reg_file.sv")
    top_level_name = netlist.get_module_class_name(netlist.top_level)
    flow = QuartusFlow(target_dir="q_reg_file", top_level=top_level_name, source_files=("reg_file.sv",), clocks=(("clk", 10), ("top_clk", 100)), project_name="reg_file")
    flow.generate()
    flow.run()

if __name__ == "__main__":
    gen()
