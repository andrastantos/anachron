.. _introduction:

Preface
=======

As I'm getting old, I'm thinking more and more of the past. I grew up in the '70 and '80s. My childhood computer was a VIC20, followed by a C64. I was dreaming about owning an Amiga, but never had the money to have one. I admired the Mac and of course was fascinated by the Cray machines.

I was constantly dreaming about and designing my own computers. Never actually built anything, but had lots of paper designs all the way from processors built from 74-series gates to Z80 based massively parallel machines.

As I said, I'm getting old and thinking about those days a lot again. What would my dream-machine in the early '80s have looked like? If I was an engineer at - say - Commodore, what would I have designed the follow-on to the C64 to be?

Let's start up the imagination drive! Let's dive in!

The Story Begins
================

It's 1981. August. You and I are sitting in the office of Jack Tramiel, our boss. *The* boss. CEO of Commodore. Though the world doesn't know it yet, within a year the company will release the Commodore 64. Of course there's much to be done till then, but we are already discussing the future. After all, the custom chips are all done and Commodore should start queueing up the silicon for the next model.

Jack was caught off-guard by the Sinclair ZX81 earlier this year and is eager to compete. Wants to see an offering that beats that machine on performance and competes in price. He was loud and clear about that. Very loud... He also wanted a replacement for the aging PET series: something for the office, for the schools. Something more 'professional'.

We bring another idea. It's quite clear - we say - that most people are using home computers for gaming. Yes, most of us think that the VIC20 and the Pet are great productivity tools. You can use them for so many things. You can learn so much by using BASIC! But one has to just look at the software title sales to realize: most VIC20s spend most of their time running games. In fact, the C64 was designed for precisely that market. We think that's the right call: games, games and more games. That's where the true mass-market is.

We've looked at the history, we've studied the trends. It's quite clear that 8-bit micro-processors are getting long on the tooth: the C64 already has more memory than what its CPU can address. The Motorola 68000 has been on the market for two years. The Intel 8086 for three. The TMS9900 for five. The next wave of machines are going to be 16-bit ones. The only question is whether the processors will internally stay at 16-bits or jump to 32.

"Are you out of your mind?!" He snaps. "No one can afford those processors!"

Yes, those processors are expensive now, but Moore's law will take care of that: in every couple of few years transistor density doubles; these designs get ported over to new process nodes, their silicon size - and cost - will collapse. They *will* get cheaper. We predict that by '84 there will be machines on the market, targeting customers based on those CPUs.

Of course, our yet-to-be-introduced flagship machine is not immune to these trends either: we will have to keep slashing prices on the C64 to stay competitive. We will be able to too, if we take advantage of these same trends: silicon gets less and less expensive.

At any rate, in a few short years, our flagship will become a low-end commodity. Competing with the current low-end in the future is pointless. We will have to start designing our new flagship right now! It takes years to make a machine: if we want to be on the market by 1984, we have to start chip design right away.

Jack is interested, but not convinced. "Continue", he barks.

Our plan is simple: start development on a chipset for a machine that can ship in 1984. 1985 latest. It would require roughly the same number of custom chips as the C64, but would have a 16-bit data-bus. We've looked at the available processors but decided we can do better: we propose we develop our own CPU. It would be roughly the same area as the 68000, but would be at least four times as fast.

By the time 1984 rolls around, 128kB of memory should be mainstream, maybe even 256k is affordable. We certainly need more than 16 address lines. We propose 16MB of RAM space. That should be enough for a while.

We propose to develop a graphics chip that is a significant upgrade over the VIC-II: higher resolution, more colors. We propose to get rid of character mode (our processor is fast enough to deal with bit-map graphics), which should free up some resources. We then can use those resources to add other features, such as 256-color mode.

Our solution for sound is also a step-up from the SID: we want to add stereo sound and digitized sample playback. More channels. Four, maybe eight. We are on the fence about synthesizer capabilities: the SID is really great, and Yamaha showed some very exciting capabilities with their FM synthesis technique. It looks like they are finally ready to commercialize it, the GS1 just came out. We are fairly confident we can build a synthesizer, based on the heritage of the SID, but unclear on the patent and copyright implications.

"Is that it?", Jack asks. "Three chips?"

Well... not exactly, we fess up. We probably need at least one more: We will also need a chip to talk to all the peripherals: the keyboard, joysticks, the rest.

"What about floppy drives?" He's getting tense. That's not usually a good sign. But, at least he still listens and appears to be engaged.

Just between us, we say, the 1541 is a fuck-up. We should have never released it as we did, and we should burry it as quickly as possible. Plus, with 128-256k of memory, the 170kB of that drive is hardly adequate. We would prefer to move over to the new 3.5" format from Sony. We think it's going to be the winner.

"So let me get this straight" he growls. "You propose that we retool the whole company, throw all our existing work out the window and in three years come up with something completely new?" Now, he's getting red in the face. We do too, but not for the same reason. "New chips, new computer, new peripherals, new *everything*? I don't even dare to ask about software! I'm guessing you propose we start anew on that as well."

To be honest - we say somewhat sheepishly - all of our code is written in 6502 assembly. There's really no way to...

There's not much point in finishing the sentence. We've lost. It's not going to happen. As we leave the office, walking back to our cubicles, I ask:

- Do you still want to do it?
- Yeah! - you reply.
- All right, let's gather some friends, I'll get the pizza!

