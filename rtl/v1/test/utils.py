from silicon import *

from assembler import *
try:
    from .rig import con_base
except ImportError:
    from rig import con_base

def fail():
    mem32_I_eq_r(con_base+8, "$r0")

def check_reg(reg, value):
    r_eq_I_xor_r(reg, value, reg)
    if_r_eq_z(reg, get_dot()+10) # 10 bytes equals a 4-byte test and a 6-byte write instructions
    fail()
    r_eq_I_xor_r(reg, value, reg)

def terminate():
    mem32_I_eq_r(con_base+4, "$r0")

#def con_wr(reg, tmp_reg=14):
#    prog(a.r_eq_r_or_r(tmp_reg, reg, reg))
#    prog(a.r_eq_r_shl_i(tmp_reg, tmp_reg, 28))
#    prog(a.r_eq_r_and_i(tmp_reg, tmp_reg, 16))
#    prog(a.if_r_)
#def con_wr(self, reg):
#    self.prog(self.asm.mem32_I_eq_r(con_base, reg))

test_netlist = None

def prep_test(top) -> Netlist:
    with Netlist().elaborate() as netlist:
        top()
    global test_netlist
    test_netlist = netlist
    return netlist

def run_test(netlist: Netlist, programmer: callable, test_name: str = None):
    global test_netlist
    clear_asm()
    if netlist is None:
        netlist = test_netlist
    top_inst = netlist.top_level

    if test_name is None:
        test_name = programmer.__name__

    vcd_filename = f"brew_v1_{test_name}.vcd"

    top_inst.clear()
    programmer(top_inst)
    reloc()
    top_inst.program(get_all_segments())
    netlist.simulate(vcd_filename, add_unnamed_scopes=False)

def prog_wrapper(func):
    def wrapper():
        run_test(None, func)
    return wrapper

def pc_rel(location):
    # Return a pc-relative address, based on munging for conditional branch instruction rules:
    #    replicate LSB to bit positions [31:16], replace LSB with 0.
    # To munge an address, we'll take the sign bit (bit 16) and stuff it in the location of bit-0.
    # We assert that bit-0 is 0 and that the relative location is within 64kWords
    #nonlocal pc
    linear = location-pc
    assert(abs(linear) < 0xffff)
    assert(linear & 1 == 0)
    bit_16 = (linear >> 16) & 1
    return (linear & 0xffff) | bit_16



r = [None]*15

def init_regs():
    for i in range(15):
        if i <= 7:
            r_eq_t(f"$r{i}",i)
        else:
            r_eq_r_plus_t(f"$r{i}",f"$r{i-7}",7)
        r[i] = i

def startup(call_init_regs = True):
    """
    Setting up initial segments, jump to DRAM and load all registers
    """
    global r

    create_segment("code", 0)
    create_segment("code_dram", 0x0800_0000)
    set_active_segment("code_dram")
    place_symbol("_start")
    set_active_segment("code")

    pc_eq_I("_start")

    set_active_segment("code_dram")
    if call_init_regs: init_regs()

def check(start=0, stop=14):
    """
    Test that all HW registers match the expectations
    """
    global r
    for idx in range(start, stop+1):
        check_reg(f"$r{idx}",   r[idx])



def load_reg(reg, value):
    idx = int(reg[2:])
    r[idx] = value
    if value < 0x7fff and value > -0x8000:
        r_eq_i(reg, value & 0xffff)
    else:
        r_eq_I(reg, value)

def shl(a,b):
    return (a << (b & 31)) & 0xffffffff

def shr(a,b):
    return ((a & 0xffffffff) >> (b & 31)) & 0xffffffff

def sar(a,b):
    lsb = (a >> 31) & 1
    if lsb != 0:
        top_bits = (lsb << (b & 31)) - 1
    else:
        top_bits = 0
    top_bits <<= (32-(b & 31))
    return shr(a,b) | (top_bits & 0xffffffff)

def bse(a):
    lsb = (a >> 7) & 1
    if lsb != 0:
        top_bits = 0xffffff00
    else:
        top_bits = 0
    return (a & 0x000000ff) | top_bits

def wse(a):
    lsb = (a >> 15) & 1
    if lsb != 0:
        top_bits = 0xffff0000
    else:
        top_bits = 0
    return (a & 0x0000ffff) | top_bits
