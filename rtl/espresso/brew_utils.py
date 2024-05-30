from typing import *
from silicon import *
try:
    from .brew_types import *
except ImportError:
    from brew_types import *

@module(1)
def field_d(inst_word):
    return inst_word[15:12]

@module(1)
def field_c(inst_word):
    return inst_word[11:8]

@module(1)
def field_b(inst_word):
    return inst_word[7:4]

@module(1)
def field_a(inst_word):
    return inst_word[3:0]

def hold(signal, enable):
    return Select(enable, Reg(signal, clock_en=enable), signal)

def get_phy_addr(logical_addr, base):
    return concat(logical_addr[31:28], (logical_addr[27:0] + (base << BrewMemShift))[27:0])

def is_over_limit(logical_addr, limit):
    return (logical_addr[27:BrewMemShift] > limit)

def SRReg(set, reset):
    state = Wire(logic)
    state <<= Reg(Select(
        set,
        Select(
            reset,
            state,
            0
        ),
        1
    ))
    return state

def SRReg(set, reset):
    state = Wire(logic)
    state <<= Reg(Select(
        reset,
        Select(
            set,
            state,
            1
        ),
        0
    ))
    return state
