Debugging CoreMark
==================

So, this is interesting...

The coremark test runs to completion in the simulator (i.e. iVerilog), yet it keeps restarting in the FPGA.

I've tried different compiler flags, but it didn't make a difference (in real HW). The next thing to do is to pepper the test with printf-s to see where it bails. It would also be interesting to see what the ecause/eaddr registers show, so maybe I'll roll up my sleeves and write the proper dump functions in rom.s.

In fact, I did all this, plus plunged DRAM into TASK mode before giving control over to it. So I even have $tpc in the dump.

After that - it's actually really fun! - I get an unaligned access violation.

[10:55:22:393] cormark starting...
[10:55:22:393] ecause: 00000032
[10:55:22:393] eaddr:  0802f852
[10:55:22:474] $tpc:   08000de8 <-- this is 0x40006f4

The offending code is:

 8000de8:	93 0f 02 00 	mem16[$r3 + 2 (0x2)] <- $r0

This is strange - as it should be: the access *is* aligned. Let's dump all the registers as well!

[15:17:23:205] $r0     0000000f
[15:17:23:205] $r1     00001000
[15:17:23:205] $r2     0000000f
[15:17:23:205] $r3     0801f95b
[15:17:23:205] $r4     00000006
[15:17:23:205] $r5     0000000f
[15:17:23:205] $r6     00000000
[15:17:23:205] $r7     0800f8f8
[15:17:23:205] $r8     0800f878
[15:17:23:205] $r9     0802f852
[15:17:23:205] $ra     00000000
[15:17:23:205] $rb     0800f800
[15:17:23:205] $rc     0800f788
[15:17:23:205] $rd     0800f75c
[15:17:23:205] $re     08000db4
[15:17:23:205] ecause: 00000032
[15:17:23:205] eaddr:  0802f852
[15:17:23:205] $tpc:   08000de8

Hmm... that's strange: $r3 is not the value I get from eaddr. That's $r9. But even that doesn't make too much sense because of the '+2'.

Now, that's not all that surprising. Since the thing passes in RTL, we should expect some weird stuff. How to get closer to the root cause though?

Here's the disassembly around there:

 8000dd2:	00 92       	$r9 <- $r0
 8000dd4:	68 3f 04 00 	$r3 <- mem32[$r8 + 4 (0x4)]
 8000dd8:	24 f5 e7 ff 	if $r2 < $r4 $pc <- $pc - 26 (0x1a)
 8000ddc:	f1 03 00 07 	$r0 <- short 1792 (0x700) & $r1
 8000de0:	a2 51       	$r5 <- $r2 ^ $r10
 8000de2:	50 02       	$r0 <- $r0 | $r5
 8000de4:	f0 03 ff 3f 	$r0 <- short 16383 (0x3fff) & $r0
 8000de8:	93 0f 02 00 	mem16[$r3 + 2 (0x2)] <- $r0 <============== This is where we die.
 8000dec:	69 0e       	$r0 <- mem32[$r9]
 8000dee:	21 2b       	$r2 <- tiny $r2 + 1
 8000df0:	f1 14 00 01 	$r1 <- short 256 (0x100) + $r1

In simulation, I've managed to find the same location.

In there:
 8000dd4: $r3 is 0x0800f958
 8000ddc: $r0 is 0x00000700
 8000de0: $r5 is 0x00000006
 8000de2: $r0 is 0x00000706
 8000de4: $r0 is 0x00000706
 8000de8: $r0 is 0x0800f8b0

This is at around 2397us. Now, to be fair, this might not be the only time this thing gets executed. It's the first...

In the above dump $r0 is 0xf, so is $r5.

Apparently we iterate 23 times through this piece of code. So, do we get anything remotely similar?

 $r9 in the FPGA is 0802f852, that never occurs in the simulation. What we see is 0x0800f8b8 and such like. In fact, the '2' there is way too high! In fact, all the addresses are way too high!!! Those are outside the RAM area, aren't they?

The size of the DRAM is set in fpga_top.py at line 93. It's set to 128*1024, or 128k. We only create two DRAM instances (8-bits each), so we only hookup one of the banks. Bank A in fact. But, I don't think we do anything clever about excluding higher addresses, we appear to be simply alias back.

Now, if we could set the limit registers to be just at the end of DRAM, we could check the first dereference that goes off the rails.

OK, so it turns out setting limits is that that easy, now that WS aliases are at the top address nibble. Maybe I should mask that out in the AV compare logic? At any rate, luckily we have DRAM aliases as well, so we'll just have to use to the one beyond the WS setting for I/O.

And of course that needs to be set in the linker scripts as well, otherwise the first jump would get us back below...

So, now we're ready for a repro.

OK, that's weird. I got the same error:

[16:08:21:113] cormark starting...
[16:08:21:113] $r0     0000000f
[16:08:21:113] $r1     00001000
[16:08:21:113] $r2     0000000f
[16:08:21:113] $r3     1801f95b
[16:08:21:113] $r4     00000006
[16:08:21:113] $r5     0000000f
[16:08:21:113] $r6     00000000
[16:08:21:113] $r7     1800f8f8
[16:08:21:113] $r8     1800f878
[16:08:21:113] $r9     1802f852
[16:08:21:113] $ra     00000000
[16:08:21:113] $rb     1800f800
[16:08:21:113] $rc     1800f788
[16:08:21:113] $rd     1800f75c
[16:08:21:113] $re     18000db4
[16:08:21:113] ecause: 00000032
[16:08:21:113] eaddr:  1802f852
[16:08:21:113] $tpc:   18000de8 <-- that's 0xc0006f4

Except of course now with the '1' in the front. So, that seems to indicate that this is the *first* time anything really awful happens.

OK, so one thing to note is that apparently eaddr is not quite right, or $tpc is not. One of the two. I'm thinking $tpc is screwed up, because, if eaddr is to be believed, that is at least really is unaligned (and out of bounds too, but I think I'm reporting unaligned at higher priority).

So, from the top:

 8000dd2:	00 92       	$r9 <- $r0
 8000dd4:	68 3f 04 00 	$r3 <- mem32[$r8 + 4 (0x4)]
 8000dd8:	24 f5 e7 ff 	if $r2 < $r4 $pc <- $pc - 26 (0x1a)
 8000ddc:	f1 03 00 07 	$r0 <- short 1792 (0x700) & $r1
 8000de0:	a2 51       	$r5 <- $r2 ^ $r10
 8000de2:	50 02       	$r0 <- $r0 | $r5
 8000de4:	f0 03 ff 3f 	$r0 <- short 16383 (0x3fff) & $r0
 8000de8:	93 0f 02 00 	mem16[$r3 + 2 (0x2)] <- $r0
 8000dec:	69 0e       	$r0 <- mem32[$r9] <============== This is where we die.
 8000dee:	21 2b       	$r2 <- tiny $r2 + 1
 8000df0:	f1 14 00 01 	$r1 <- short 256 (0x100) + $r1

OK, so let's see the possible values for $r9 in the simulation:

1800f8b8, decreasing by 8 every time down to 1800f808.

Instead of these, we get 1802f852. This seems to be a corruption of the lower bytes. The upper bytes are just fine, but the lower ones are of the wrong value.

So, I think I have the root cause: the memory interface is not reliable. We have timing violations - either during reads or writes - that corrupts the memory. Damn!

Now, to catch this, I'll need to write a memory tester. One that executes from ROM, and reads/writes a lot of DRAM locations.

So, first things first, I'll need to make myself something that can work in C and from ROM...

Right now we have 8kB of ROM space.

Now, that's a bit of a chore, but I more or less have:

rom_c.lds for a linker script
rom_c.s for an appropriately modified startup code

The memory test seems to show that DRAM writes are problematic, though in a weird way.
The reason I'm saying this is that if reads were borken, I would not be able to execute almost anything.

If I write an incrementing pattern into memory, it appears that the value for address 0x10 would get written to address 0 *and* address 0x10. How two writes are possible? Maybe the DRAM model is wrong and it triggers twice??? And the setup time on the address bus causes
the slip? Let's investigate...

So, I've narrowed the write pulse into the DRAMs (in fact there are multiple DRAM write pulses). This changed the behavior, but didn't completely solve the problem.

Some further modification (not sure it's the right way) reduced the write pulse with to a single cycle. I might still want to change the location of the write pulse to be on the rising edge of the cycle, even if it happens to work.

It DID!!!!! IT DID WORK!!!!!