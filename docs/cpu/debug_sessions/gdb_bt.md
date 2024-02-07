First call to create a frame, with 'this_frame' pointer: 0x0000555556b33b30. The prologue cache is set to 0x0000555556b33bf0, which will be our frame_info.

Next, `brew_frame_prev_register` gets called on this frame (and filled prolog cache) for $tpc. Since $tpc is not saved yet,
we return `frame_unwind_got_register`. This I think it's not right: we should return the value in $lr instead. Even better: we should have saved $lr into our cache as our caller address. Indeed, this just turns into us saying that our previous $pc is 0x1406.

After fixing that, we are not returning the return address (not quite right, but better). So, now we're called upon creating a
cache for another 'this_frame', this time at address 0x0000555556b33c50.

This is getting interesting here: as we're trying to fill the previous frame, we need 'fp', so we call the 'brew_frame_prev_register' with $fp as the target on our previous 'this_frame'.

OK, NOW we're called again with the proper start address and PC for the caller.

Finally!!!!! back-trace is working, sort of.

We do get the two entries of the stack, but the caller address in main is reported incorrectly: it's our return address.

So, we'll somehow, magically we'll have to figure out where the call originated *from*. That sounds tough. Maybe there is a function for that? I mean, this is a common problem.
