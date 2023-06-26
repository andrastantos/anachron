Getting UART working
====================

This is going to be a slow slog. So, the synthesized FPGA design doesn't work. Loading it into the simulator (ModelSim) and running it shows that we reset after a few instructions from DRAM.

Tracing down the instruction stream, it seems that we drop a word and start issuing the wrong instructions shortly after the first jump:

    80000832 <memset>:
    80000832:	ff cc       	mem32[$sp - tiny 4 (0xfffffffc)] <- $fp    <-- ISSUES OK
    80000834:	fd 8c       	mem32[$sp - tiny 8 (0xfffffff8)] <- $r8    <-- ISSUES OK
    80000836:	dd c2       	$fp <- $sp                                 <-- ISSUES OK
    80000838:	fd d4 f8 ff 	$sp <- short -8 (0xfffffff8) + $sp         <-- ISSUES AS 0xfff8 0x2244, drops 0x4ddf.
    8000083c:	44 22       	$r2 <- $r4
    8000083e:	f4 03 03 00 	$r0 <- short 3 (0x3) & $r4
    80000842:	00 f0 b4 00 	if $r0 == 0 $pc <- $pc + 180 (0xb4)
    80000846:	6e 1b       	$r1 <- tiny $r6 - 1
    80000848:	06 f0 9a 00 	if $r6 == 0 $pc <- $pc + 154 (0x9a)

This happens (the first time) at around 19239ns.

Now, as to why??? That's anybody's guess at this point and teasing the state machines out of a gate-level sim is ... fun.

One thing we can see if the bytes at least left the DRAM. ... They did: we've read them at around 18421ns.

At that point this data should have found it's way to inst_buf, then inst_queue then inst_assemble.

OOOH! One thing I've changed was the 0-wait FIFO bypass. If that doesn't work properly (and it might not as curiously around the missing word, I get 0x0000 in all three instruction words) that could be the problem. Still, let's see if I can find something out!

I think I've found the input data to inst_queue: it contains the missing word.

It very much seems like that is where the problem is. So, as a quick test, let's replace the FIFO with the old one and see what happens!

OK, so that helped somewhat. The missing word is back and we're executing more. However, pretty soon all things go X-es.

I will try to find 'spc'. Found it!

The next to last instruction executed is:

    8000087a:	f0 20 0f 00 	$r2 <- short 15 (0xf)
    8000087e:	21 f6 80 00 	if $r2 >= $r1 $pc <- $pc + 128 (0x80)   <-- next to last instruction
    80000882:	f1 74 f0 ff 	$r7 <- short -16 (0xfffffff0) + $r1     <-- $spc points here, then all things go X-es

We've done several, similar jumps successfully, and the fact that $spc doesn't go X-es, is suspicious, but at the same time, fetch goes all belly-up...

The instruction queue empty counter goes X-es first (of what I can see). This points towards some sort of handshake issue.

Finally, some progress: reg_file.req_advance goes to X. That's:

    req_advance = self.read_req.ready & self.read_req.valid

Actually, a cycle earlier the input to 'out_buf_full' goes X. I'm thinking it's do_branch that goes out to lunch, actually.

    out_buf_full <<= Reg(Select(self.do_branch, Select(req_advance, Select(rsp_advance, out_buf_full, 0), 1), 0))

As far as I can tell 'req_advance' is valid (high) on the cycle where out_buf_full reg input goes X. Which means that self.do_branch goes X.

I couldn't really find 'do_branch', but I did find 's1_was_branch', which should, on it's input contain do_branch. And indeed it goes 'X'.

So, why could that be? Instruction assembly contains the right offset and instruction word. Could it be that decode goes into some sort of default state?

We send branch_op=6 (cb_ge) and exec_unit=3 (branch). So that seems OK. I guess I'll have to look at op_a op_b and op_c...

Well, actually, the reason for not knowing if there was a branch would be if the register file contained or read a corrupted value. We're comparing $r2...

Bingo! op_a is X. Which would indicate that we've written X into the reg file previously.

In fact, we write $r2 just in the previous instruction. So we either f*ck up the reading/reservation logic or we write the wrong value.

I don't have the high data output, but low output is valid and correct: 0x0f.

So, it's most likely not the write logic, it's the read and/or lock-out. The fact that it goes X seems to indicate that we depend on some weird read-and-write behavior that we shouldn't.

So, the simulated RAM it seems outputs X-es for whenever we read and write the same location. This is inspite of that being a perfectly valid things to do...

So, what seems to be happening is this:

1. Underlying memory X-es out reads, if reads and writes happen to the same address on the same cycle
2. Writes are actually registered in the sense that write-enable gets delayed by one cycle. i.e. the actual array access happens the cycle *after* the outside-visible write
3. Reads are of course also registered in the sense that reads return data the next cycle compared to the address given.

These all conspire to give us X-es even though the write should occur on 24100ns (that's the time it should take effect) and the read should get registered on 24200ns, that is the read data should return on 24200ns. This - from the outside - doesn't appear as a simultaneous read-write, so the bypass logic doesn't get engaged and the X-es propagate through the system.

Now, what to do about it? First things first, check what kind of memory I'm asking for. Maybe Quartus inferred something slightly different from what I had hoped for...

I manually patched up the memory instances to be more like what a Quartus template asks for and the X-es went away. This of course needs further debugging and understanding. As is, every regeneration will bring the problem back.

Now, we're going much further. Maybe even running? I'm not sure if I changed memory since I got it working the previous time...

OK, so after some more fiddling, it appears that the UART is *transmitting* in gate-level simulation. Yet, nothing noteworthy seems to be happening on the physical FPGA if I download the design.

Now, back to the FPGA:
- We have a 10MHz clock - and does measure as 10MHz.
- We have a 50MHz clock - and does measure as 50MHz.
- I can get a simple RLT counter on the output pins
- I CAN'T get even the simplest counter from C
- The same gate-level code does output a counter from C (even data to the serial port).

WTF???

SignalTap
~~~~~~~~~

That's an amazing (albeit a little unstable) tool for inspecting in-circuit state. A logic analyzer on steroids.

This helped me debug the problem to this point:

The instruction stream on FPGA is:

    0x80000102
    0x80000106
    0x80000108
    0x8000010a
    0x8000010c
    0x8000016e (0x400000b7)

The relevant stream on iVerilog:

    0x80000102
    0x80000106
    0x80000108
    0x8000010a
    0x8000010c
    0x8000017a (0x400000bd) <========= Difference in code point.

This all seems to be part of this:

    800000c6 <register_tm_clones>:
    800000c6:	ff cc       	mem32[$sp - tiny 4 (0xfffffffc)] <- $fp
    800000c8:	fd ec       	mem32[$sp - tiny 8 (0xfffffff8)] <- $lr
    800000ca:	dd c2       	$fp <- $sp
    800000cc:	fd d4 e8 ff 	$sp <- short -24 (0xffffffe8) + $sp
    800000d0:	0f 50 44 19 	$r5 <- 2147490116 (0x80001944)
    800000d4:	00 80
    800000d6:	5f 54 bc e6 	$r5 <- 2147477180 (0x7fffe6bc) + $r5
    800000da:	ff 7f
    800000dc:	f5 08 02 00 	$r0 <- short $r5 >>> 2 (0x2)
    800000e0:	f5 57 1f 00 	$r5 <- short $r5 >> 31 (0x1f)
    800000e4:	05 54       	$r5 <- $r5 + $r0
    800000e6:	f5 58 01 00 	$r5 <- short $r5 >>> 1 (0x1)
    800000ea:	05 f0 18 00 	if $r5 == 0 $pc <- $pc + 24 (0x18)
    800000ee:	0f 00 00 00 	$r0 <- 0 (0x0)
    800000f2:	00 00
    800000f4:	00 f0 0e 00 	if $r0 == 0 $pc <- $pc + 14 (0xe)
    800000f8:	0f 40 44 19 	$r4 <- 2147490116 (0x80001944)
    800000fc:	00 80
    800000fe:	22 e0       	$lr <- $pc + 4 (0x4)
    80000100:	02 00       	$pc <- $r0
    80000102:	fd d4 18 00 	$sp <- short 24 (0x18) + $sp
    80000106:	fd ed       	$lr <- mem32[$sp - tiny 8 (0xfffffff8)]
    80000108:	ff cd       	$fp <- mem32[$sp - tiny 4 (0xfffffffc)]
    8000010a:	02 e0       	$pc <- $lr

So, what seems to be happening is that $lr is different. Not by much, by 12 bytes.

The call happens on 0x400000ba in both cases.

    8000014e <frame_dummy>:
    8000014e:	ff cc       	mem32[$sp - tiny 4 (0xfffffffc)] <- $fp
    80000150:	fd ec       	mem32[$sp - tiny 8 (0xfffffff8)] <- $lr
    80000152:	dd c2       	$fp <- $sp
    80000154:	fd d4 e8 ff 	$sp <- short -24 (0xffffffe8) + $sp
    80000158:	0f 00 00 00 	$r0 <- 0 (0x0)
    8000015c:	00 00
    8000015e:	00 f0 14 00 	if $r0 == 0 $pc <- $pc + 20 (0x14)
    80000162:	0f 50 48 19 	$r5 <- 2147490120 (0x80001948)
    80000166:	00 80
    80000168:	0f 40 0c 15 	$r4 <- 2147489036 (0x8000150c)
    8000016c:	00 80
    8000016e:	22 e0       	$lr <- $pc + 4 (0x4)
    80000170:	02 00       	$pc <- $r0
    80000172:	24 e0       	$lr <- $pc + 8 (0x8)
    80000174:	ef 20 c6 00 	$pc <- 2147483846 (0x800000c6) <========== CALL of interest
    80000178:	00 80
    8000017a:	fd d4 18 00 	$sp <- short 24 (0x18) + $sp
    8000017e:	fd ed       	$lr <- mem32[$sp - tiny 8 (0xfffffff8)]
    80000180:	ff cd       	$fp <- mem32[$sp - tiny 4 (0xfffffffc)]
    80000182:	02 e0       	$pc <- $lr

So, how can this be corrupted? I think I'll have to monitor the write port of the register file...

Let's remember that $lr is $r14 in disguise.

According to the RTL, we should see 0x8000017a written into $rE on the second cycle $spc is $400000ba.

BTW: the exception we get is a fetch_av (exc_mip).

This is an f-ing Heisenbug! Now, that I tapped the register file write, the behavior changed.

OK, so Gabor helped me out. His explanation was the following:

We have a bunch of signals in the 'slow' clock domain (on the CPU side), such as DRAM address nRAS nCAS etc., that - according to the synthesizer - need to reach their destination within 100ns. These signals are then sampled on the 'fast' clock domain. So, if there is a large skew between these signals, it's possible that at the time we capture the edge on nRAS or nCAS not all address signals arrived to the fast clock domain so we occasionally capture the wrong (old) value.

This theory is given more credence to by the fact that the 'slow' clock domain - according to synthesis - closes timing at an Fmax of ~43MHz, which is close to, but below the 50MHz clock.

What I've tried to suss this problem out was to put a PLL in that generates a 1 and a 10MHz clock as the two clock domains. Yet, I still instructed synthesis to close timing at 10 and 50MHz respectively.

In this setup I now - again - have hold violations reported on the original 50MHz clock (which only feeds the PLL, so what??), but it appears that somehow the synthesis propagates timing through the PLL. At any rate...

Drum-roll please: the program works now. I have blinking LEDs and even serial communication (albeit at 2x the baud-rate that I programmed it to).

So are we there yet? Not quite. This is a nice test, something of a good check-point, but not a solution. What I need is to properly constrain the system so that the arrival times on the CDC are properly managed. I also don't like the internal PLL because that makes the design even more platform specific. Not only that, but I need to use the God awful tooling that comes with Quartus which is ... well, let's just say unpleasant.

This took a while, but I finally created proper constraints. The theory is rather simple:

1. Make sure the clocks on the CPU and SYSTEM side are treated independently.
2. Create `set_net_delay` constraints for everything that crosses the domains. Relative setup times can be controlled by the `-min` or `-max` parameters. This way data for instance would be at least a few ns earlier then - say - `n_cas`.
3. Create `set_max_skew` constraints for extra points to keep the relative delays of wires within a bus close enough.

The problems are the following:

1. These constraints are set on the post-map nets, so anything that gets optimized out is generating warnings. Also, things have weird, hard-to-find names.
2. These constraints are set between registers, not ports. So one has to back-track to the registers within the driving instances in order to know what to set the constraints on. I guess this is one of the reasons that people like to register both inputs and outputs: this way the interface is the one that gets constrained, not the private guts of a module. This, BTW is a ripe area for some automation.
3. Even with all that, most constraints didn't stick.

For instance this path:

.. image::
    image/dram_datapath_to_constrain.png

One would think the following 4 constraints should work::

    set_net_delay -from [get_registers {*bus_if*data_out_high[*]}] -to [get_registers {*system*ext_if_data_out_nr[*]}] -max 18
    set_net_delay -from [get_registers {*bus_if*data_out_low[*]}]  -to [get_registers {*system*ext_if_data_out_nr[*]}] -max 18
    set_net_delay -from [get_registers {*bus_if*data_out_high[*]}] -to [get_registers {*system*ext_if_data_out_r[*]}] -max 18
    set_net_delay -from [get_registers {*bus_if*data_out_low[*]}]  -to [get_registers {*system*ext_if_data_out_r[*]}] -max 18

But no::

    No path was found satisfying set_net_delay assignment from "[get_registers {*bus_if*data_out_high[*]}]" to "[get_registers {*system*ext_if_data_out_nr[*]}]".
    No path was found satisfying set_net_delay assignment from "[get_registers {*bus_if*data_out_low[*]}]" to "[get_registers {*system*ext_if_data_out_nr[*]}]".
    No path was found satisfying set_net_delay assignment from "[get_registers {*bus_if*data_out_high[*]}]" to "[get_registers {*system*ext_if_data_out_r[*]}]".
    No path was found satisfying set_net_delay assignment from "[get_registers {*bus_if*data_out_low[*]}]" to "[get_registers {*system*ext_if_data_out_r[*]}]".

So, reading up more on this thing, one item sticks out: all documentation on set_net_delay is coming from Alters site. It appears that set_net_delay is an Altera-specific thing. There are four other, similar commands to consider::

    set_max_delay
    set_min_delay
    set_input_delay
    set_output_delay

So, according to one note set_net_delay is very similar to set_max/min_delay. Let's give it a shot!