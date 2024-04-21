Random ideas
============

DRAM emulation using SDRAMs
---------------------------

Since SDRAMs are much more prevalent these days, it might be interesting to construct an interface that works with these devices.

This is especially interesting as some GoWin FPGA variants have co-packaged SDRAM in them.

First, let's consider a case where the SDRAM runs at 4x the CPU speed. The regular DRAM timing for Espresso is (simplified):

1. RAS
2. read/write 2 bytes
3. read/write 2 bytes
4. ...
5. PRECHARGE

This can be translated to the following cycles on an SDRAM (with CL=2):

1.1. Bank activate
1.2. NOP
1.3. NOP
1.4. NOP
2.1. read A
2.2. read B
2.3. data A
2.4. data B
3.1. Precharge all
3.2. NOP
3.3. NOP
3.4. NOP

For writes:

1.1. Bank activate
1.2. NOP
1.3. NOP
1.4. NOP
2.1. write A
2.2. NOP
2.3. write B
2.4. NOP
3.1. Precharge all
3.2. NOP
3.3. NOP
3.4. NOP

For refresh:

1.1. Auto refresh
1.2. NOP
1.3. NOP
1.4. NOP
2.1. NOP
2.2. NOP
2.3. NOP
2.4. NOP

This is slightly different from DRAM in that the two data bytes are coming back-to-back, but at least take the same amount of time.

If 8x clocks are used, even more lax command sequences are possible.

1.1. Auto refresh
1.2. NOP
1.3. NOP
1.4. NOP
1.5. NOP
1.6. Bank activate
1.7. NOP
1.8. NOP
2.1. read A
2.2. NOP
2.3. data A
2.4. NOP
2.5. read B
2.6. NOP
2.7. data B
2.8. NOP
3.1. Precharge all
3.2. NOP
3.3. NOP
3.4. NOP
3.5. NOP
3.6. NOP
3.7. NOP
3.8. NOP

This puts the data return to it's place in the original timing. Of course it doesn't allow for much faster operation (i.e. the SDRAM is massively underutilized), but should work.

nRAS falling edge: auto-refresh + (back activate - if nCAS is high; otherwise auto-refresh only)
nCAS falling edge: read/write depending on nWE, if nRAS low
nWE falling edge: write cycle, if both nRAS and nCAS are low
nRAS rising edge: precharge all

This seems to cover all the cycles a FPM DRAM could have.

Data output from SDRAM would need to be latched and held on the data-bus as it would otherwise disappear.
