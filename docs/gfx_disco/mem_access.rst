Memory cycles
=============

Disco uses dedicated video memory (VRAM) to store and access the frame buffer. This memory of course can also be accessed by Espresso, the CPU. Sharing of the memory bus is coordinated by the following signals:

The :code:`nBUSY` signal is an output from Disco. It is asserted whenever Disco is active on the VRAM bus.
The :code:`nWAIT` signal is an input on Espresso. It is sampled prior any access to VRAM by Espresso. If asserted, Espresso holds off accessing the bus until the wait condition disappears. (The same same :code:`nWAIT` signal is used to insert wait-states to non-DRAM accesses)
The :code:`nRAS` VRAM signal that is driven by both Disco and Espresso, but also sampled by Disco. Disco holds off accessing the VRAM bus if it samples :code:`nRAS` asserted and waits until it is released.

While things will become a little more complicated later on, for this explanation, we're going to assume the following:

1. Whenever nBUSY is asserted, the VRAM signals are connected to Disco
2. Whenever nBUSY is de-asserted, all Disco VRAM signals are tri-stated and the CPU has access to VRAM
3. The nBUSY output of Disco is directly connected to nWAIT of Espresso
4. VRAM nRAS (and nCAS as well though it's not shown) has a pull-up resistor so these signals idle high with no drivers.
5. Whenever nBUSY is asserted, Espresso is completely isolated from VRAM. It of course can continue to issue bus cycles to other targets (it's own DRAM or I/O for instance), but isolation switches guarantee no interference between it and Discos' VRAM access.

In the following the 'desire' signals are internal states of Disco and Espresso, reflecting the fact the these chips decided that they want to (have a desire to) access VRAM. This is normally a state-machine change and as such, changes on the rising edge of the clock. Whether such a signal exist in the RTL depends on the actual implementation and not relevant to this discussion.

The algorithm is as follows:

2. Espresso monitors nWAIT (which is connected to nBUSY of Disco). Can only assert nRAS if nWAIT is de-asserted.
3. Disco monitors nRAS. Can only assert nRAS (or nBUSY) if nRAS is de-asserted.
4. Disco also monitors n_we. It can only start a VRAM access (asserting nRAS) if n_we is inactive.
5. If collision is detected (i.e. Espresso detects nBUSY getting asserted in the same cycle where it asserted nRAS), it de-asserts nRAS and waits for nBUSY to go inactive.
6. nBUSY is essentially the same as nRAS as far as Disco is concerned, but asserted sufficiently early that the isolation switches have time to respond with no glitching

This scheme doesn't guarantee no starvation for the low priority master (Espresso), but it's otherwise collision and deadlock-free. Starvation can be fended off in two ways:
1. Disco inserts an extra wait-state after every transfer, giving Espresso a chance to get an uncontested transaction in. (this can be modulated by any duty-cycle)
2. By design of careful bandwidth calculations

In practice, since Disco will intend to fill its input FIFO, if it's FIFO is full (enough) it will insert more than one idle cycles between bursts (so #1 will happen). If the FIFO is still too empty after a burst, Disco *should* win the next arbitration cycle, so that's fine too. Finally, during horizontal and vertical retrace there are times when Disco will idle for a considerable period of time, so any starvation situation should resolve itself.

Some example timing diagrams:

                     < GFX access                                             < CPU access            < GFX gets delayed     < GFX gets access
CLK          /```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___
cpu desire   ________________________________________________________________/```````````````````````````````````````\________________________________
gfx desire   ________/```````````````````````````````````````````````\_______________________________/```````````````````````````````````````````````\________
nBUSY        ````````\_______________________________________________/```````````````````````````````````````````````````````\_______________/````````
cpu sample       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^
nRAS cpu     `````````````````````````````````````````````````````````````````\_______________________________________/````````````````````````````````
nRAS gfx     ---------\_______________________________________________/-------------------------------------------------------\_______________/--------
nRAS VRAM    `````````\______________________________________________/````````\_______________________________________/```````\______________/`````````
gfx sample       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^

                     < GFX access with CPU collision and starvation          < CPU finally wins
CLK          /```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___
cpu desire   ________/```````````````````````````````````````````````````````````````````````````````\_____________
gfx desire   ________/```````````````````````\_______/```````````````\_____________________________________________
nBUSY        ````````\_______________________/```````\_______________/`````````````````````````````````````````````
cpu sample       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^
nRAS cpu     `````````\_______/```````````````````````\_______/```````````````\_______________________/````````````
nRAS gfx     ---------\_______________________/-------\______________/---------------------------------------------
nRAS VRAM    `````````\______________________/````````\_____________/`````````\_______________________/````````````
gfx sample       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^

                     < GFX access with DMA collision and starvation          < DMA finally wins
CLK          /```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___
cpu desire   ________/```````````````````````````````````````````````````````````````````````````````\_____________
gfx desire   ________/```````````````````````\_______/```````````````\_____________________________________________
nBUSY        ````````\_______________________/```````\_______________/`````````````````````````````````````````````
cpu sample       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^
nRAS cpu     `````````\_______/```````````````````````\_______/```````````````\_______________________/````````````
nRAS gfx     ---------\_______________________/-------\______________/---------------------------------------------
nRAS VRAM    `````````\______________________/````````\_____________/`````````\_______________________/````````````
gfx sample       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^
nDACK_x      ````````````````````````````````````````````````````````````````````````\________________/````````````

                     < GFX access with register access collision     < Espresso finishes register access
CLK          /```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___/```\___
cpu desire   ________/```````````````````````````````````````````````````````````````\_____________________________________________________
gfx desire   ________/```````````````````````````````````````````````\_______/```````````````\_____________________________________________
nBUSY        ````````\_______________________________________________/```````\_______________/`````````````````````````````````````````````
cpu sample       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^
nRAS cpu     `````````\_______/````````````````````````````````````````````````````````````````````````````````````````````````````````````
nRAS gfx     ---------\_______________________________________________/---------------\_______/--------------------------------------------
nRAS VRAM    ``````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````
gfx sample       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^
nGFX_IO_SEL  ````````\_______________________________________________________________/`````````````````````````````````````````````````````
nWAIT        ````````\_______________________________________________/```````````````\_______________/`````````````````````````````````````


We have to be careful about connecting nBUSY to nWAIT in that:
- It should *not* get connected when nNRAM is active (i.e. I/O cycles)
- It should *not* be connected for DMA cycles (any of nDACK is active)
- To support DMA into VRAM, nDACK must be delayed up until arbitration process is finished. **This is a change to current DMA timing on Espresso**
- I/O nWAIT should *only* be connected to nWAIT during nNRAM and DMA cycles, or be guaranteed to be inactive during those cycles.
- Espresso has to have configuration registers controlling which bank (nRAS_A/nRAS_B/nNRAM) should use nWAIT in what way **This is a change to current Espresso CSRs**
- Disco can't generate wait-states during register accesses.

**The way this is hooked up on A1_Micro_ATX is that ISA iochrdy can drive nCPU_WAIT at any time. This is fine for well-behaving ISA cards that only assert this signal when addressed, which should be all of them. Not sure if it's worth the trouble fixing**

There are a few things to note here:

1. Both Espresso and Disco samples nWAIT/nRAS on the falling edge of clock
2. Espresso and Disco *must be* synchronous to one another (i.e. share the same clock)
3. The isolation of the CPU and GFX buses needs some external buffers.

The isolation gates pose a challenge as CPU bus timing is quite a bit tight: after asserting nRAS, it assert nCAS within half a clock-cycle. We need to be able to signal nWAIT within that window. That's about 50ns. However, a single open-collector OR gate should be able to accomplish that even in LS logic.

Priority inversion?
-------------------
I don't think that's an issue: if Espresso starts a transfer and, during the burst Disco decides it needs the bus, it will start it's cycle one clock after nRAS is released by Espresso. Since Espresso *has to* release nRAS between bursts to honor precharge timing requirements on the DRAM, this will happen after every burst. At that point, even if Espresso decides to start a new burst as soon as possible, Disco will win arbitration and thus will get ownership of the bus.

As longs as Espresso doesn't *execute* from VRAM, it's bursts are limited to 3 cycles (32-bit reads or writes). Right now Espressos max fetch burst is 8x16-bits long, which is 10 cycles. In an expensive setup, where VRAM is separate, we can assume that Espresso will not execute from VRAM. At least not when used properly.

In a cheap setup, where VRAM *is* the only RAM, long bursts of Espresso fetches could potentially be a problem. If Discos bursts are as long as Espressos' are, we can guarantee about 50% of bus time to Disco. On a system such as that, the total amount of memory is most likely 128k. Out of that, we can probably not afford more than 32k for a frame buffer, so max resolution is ~320x240@4bpp. That's not stretching the memory bandwidth limits so we're fine.

Memory use for audio and sprites
--------------------------------
How would one handle audio memory accesses? Those would need to go into the blanking periods. Since the horizontal sync-rate is ~15kHz for QVGA (worst case) and ~31kHz for VGA, we won't need more than 3 samples per channel per line. That's 12 bytes per scan-line, or a 15-cycle burst. We have about 100 cycles of blanking, so this is fine.

8 sprites (with 4 bytes each) would take another 40 cycles, still well within timing budget. We might have to be greedy and assert nBusy for the whole duration of sprite fetching, even though it's multiple bursts to make sure we don't incur too much arbitration penalty.

The curious case of missing address bits
----------------------------------------

There is a mismatch between the address bus size of Espresso and Disco; Discos address bus is narrower. What to do about the missing address bits?

Espresso uses the following muxing scheme when talking to DRAM:

=========== =========== =========
Pin Name     DRAM accesses
----------- ---------------------
             row         col
=========== =========== =========
a[0]         addr[9]     addr[1]
a[1]         addr[10]    addr[2]
a[2]         addr[11]    addr[3]
a[3]         addr[12]    addr[4]
a[4]         addr[13]    addr[5]
a[5]         addr[14]    addr[6]
a[6]         addr[15]    addr[7]
a[7]         addr[16]    addr[8]
a[8]         addr[18]    addr[17]
a[9]         addr[20]    addr[19]
a[10]        addr[22]    addr[21]
=========== =========== =========

The video controller thus is missing addr[22:19], four address bits. The two missing address lines can be driven by static registers outside of Disco, so 4 pages (out of 8 possible) can be utilized.

When accessed by Espresso, all address bits are patched over, so it can address the whole physical memory. All this is a bit academic though as it's unlikely that a system would have ever been built with more than 512k of VRAM. It's only slightly relevant for modern systems where - due to component availability - the VRAM size is mist likely 2MB.

Refresh
-------

In some video modes (especially if character modes are implemented), the frame buffer is too small for any reasonable way for Disco to do it's own memory refresh. Thus, we rely on Espresso for that functionality, which means it needs to be able to win arbitration often enough for at least that to happen. In terms of bandwidth reduction, it's rather minor, about 4 clock cycles per scan-line (at 32kHz Hsync).

**We should consider burst-refreshes from Espresso, whereby all refreshes can be done back-to-back in the blanking period. This would be a change to the way it's done today.**

Register accesses
-----------------

Disco uses the same address and data pins for VRAM and internal register accesses. The process is as follows:

1. The CPU puts the desired register address on a[0..8]; and n_cas_0; n_cas_1 and drives n_we low to signal a register access.
2. Exactly one of the n_cas signals need to be asserted and this information encodes the lowest address bit. Disco doesn't start an I/O transfer until both n_we and one of the n_cas signals are low.
3. Espresso also drives n_we to the desired level.
4. Data is then transferred in the appropriate direction on the d[7..0] lines.

This process also poses an opportunity for collisions: what happens if Disco starts a VRAM access in the same cycle that n_ce is asserted? Since nBUSY is lowered by Disco, if this signal is connected to Espressos nWAIT input, the CPU simply will insert wait-states into it's I/O cycle and only completes the transfer after the collision is resolved. Since at the same time the isolation switches are engaged (isolating), the VRAM transfer from Disco finishes without interruption.

However, once nBUSY is de-asserted, the I/O cycle *will* complete. This means that Disco is not allowed to start a VRAM burst if n_we is sampled active. The behavior of the isolation switches also means that Disco can't insert wait-states into an I/O access. It is compelled to complete the transfer in a single cycle. While Espresso supports internal wait-state generation, those wait-states are counted before nWAIT is sampled. This means that Espresso can't reliably insert wait-states into Disco register accesses either.

**Overall, the requirement is that Disco *has to* be able to respond to and complete I/O accesses in a single cycle.**