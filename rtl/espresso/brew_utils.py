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

def get_phy_addr(logical_addr, base):
    return concat(logical_addr[31:28], (logical_addr[27:0] + (base << BrewMemShift))[27:0])

def is_over_limit(logical_addr, limit):
    return (logical_addr[27:BrewMemShift] > limit)

