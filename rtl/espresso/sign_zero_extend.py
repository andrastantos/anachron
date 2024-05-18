#!/usr/bin/python3
from random import *
from typing import *

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
except ImportError:
    from brew_types import *
    from brew_utils import *
    from scan import ScanWrapper
    from synth import *

"""
Sign and Zero-extension logic for the V1 pipeline.

This stage is sandwiched between 'execute/memory' and 'write-back'.

It does the needed sign/zero extension of the result. It doesn't introduce any pipeline stages, it's purely combinational.

"""
class ResultExtendStage(Module):
    #clk = ClkPort()
    #rst = RstPort()

    input_port = Input(ResultExtendIf)
    output_port = Output(RegFileWriteBackIf)

    def body(self):
        self.output_port.valid <<= self.input_port.valid

        self.output_port.data_en <<= self.input_port.data_en
        self.output_port.addr <<= self.input_port.addr

        def bse(value):
            return concat(
                value[7], value[7], value[7], value[7], value[7], value[7], value[7], value[7],
                value[7], value[7], value[7], value[7], value[7], value[7], value[7], value[7],
                value[7], value[7], value[7], value[7], value[7], value[7], value[7], value[7],
                value[7:0]
            )

        def wse(value):
            return concat(
                value[15], value[15], value[15], value[15], value[15], value[15], value[15], value[15],
                value[15], value[15], value[15], value[15], value[15], value[15], value[15], value[15],
                value[15:0]
            )

        self.output_port.data <<= SelectOne(
            self.input_port.do_bse, bse(self.input_port.data_l),
            self.input_port.do_wse, wse(self.input_port.data_l),
            self.input_port.do_bze, self.input_port.data_l[7:0],
            self.input_port.do_wze, self.input_port.data_l[15:0],
            default_port = concat(self.input_port.data_h, self.input_port.data_l)
        )
