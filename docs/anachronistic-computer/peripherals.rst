Peripherals
===========

Serial ports
------------

For this machine we will simply reuse something that's on the market already. With hind-sight, I will standardize on the Intel 8250, later 16450/16550 UARTs.

Here's a relatively modern datasheet for the original part: https://www.moxsyn.com/Altera/c8250.pdf.

Alternatively, we can have a multi-purpose, custom I/O chip that includes a UART.

Modern variants are still available, so no issues here.


Floppy interface
----------------

Here I really don't want to re-invent the wheel, so the more pertinent
question is: can we handle standard floppy-controllers?

Here's one popular in PCs:
- https://ardent-tool.com/datasheets/NEC_uPD72065.pdf
- http://dunfield.classiccmp.org/r/765.pdf
A much more modern version (this one is still in stock in some places):
- https://www.mouser.com/datasheet/2/268/37c78-468028.pdf

This guy can interface directly to our bus and our DMA bridge for DMAs. No issues what so ever, except that the reset input is active-high.

There were other controllers as well:
 - http://www.bitsavers.org/components/westernDigital/WD57C65_Floppy_Disk_Subsystem_Controller_May88.pdf
 - http://www.bitsavers.org/components/westernDigital/FD179X-02_Data_Sheet_May1980.pdf
 - http://info-coach.fr/atari/documents/_mydoc/WD1772-JLG.pdf

I will stick with the PC-style FDD controller though, especially with the knowledge of hind-sight.


Hard drive interface
--------------------

If this computer was to compete with early PCs and MACs, initially HDD support is not a primary concern. Yet, pretty soon it would become mandatory and that would probably be apparent already during development. So how would one interface an HDD in those days?
- MAC went the SCSI way with the `AM5380 <https://amazingdiy.files.wordpress.com/2012/09/am5380pc.pdf>`_ chip
- PC/TX went originally with MFM/RLE interfaces

For SCSI, the interface is rather common. It seems that the only thing we would need is to invert TC to connect to nEOP.

This 5380 chip seems to have been rather popular with many clones:
- Z53C80 was until fairly recently in production from Zilog (http://www.zilog.com/docs/serial/ps0108.pdf). Even Mouser has some limited stock and it's still in Digikeys' catalog.
- NCR53c80
There is a whole family of these as well:
- 53c90/94/95/96
- 53c400 (still available at least for some retailers)
- 53c416 (16-bit version)
- 53c7x0 (32-bit, designed for i386 and such, but might work on 16-bit buses as well)
- 53cf90/94/96

http://www.bitsavers.org/components/westernDigital/WD33C93A_SCSI_Bus_Controller_1991.pdf is another SCSI controller. It has roughly the same signals as the AM5380 part. Except there's no interrupt. Also an 8-bit part.

Early MFM controller boards were a chip cemetary, and looking up datasheets from bitsavers confirms this: there was a chipset fro WDC, but it consisted of several parts and required a bazzilion glue-logic chips to make it work. I would have passed on it rather quicly.

Then there was IDE (a.k.a ATA), but that was introduced later, at '87: https://en.wikipedia.org/wiki/Parallel_ATA#IDE_and_ATA-1

.. note:: Early Amiga HDDs also used some sort of SCSI interface.

.. note::
    Atari apparently had a ACSI to MFM interface in SH-205. It's heart is the AIC-010 chip from Adaptec http://www.bitsavers.org/pdf/adaptec/asic/AIC-010_Programmable_Mass_Storage_Controller.pdf

    This chip doesn't have DMA apparently, but does have a multiplexed data/address bus. This would need significant external logic for us. It is a chip-graveyard anyway, as external buffers are also needed to buffer the data.

There was the `HD63463 <https://datasheetspdf.com/pdf-file/1285972/HitachiSemiconductor/HD63463/1>`_ for MFM controllers. It seems a very nice 16-bit, DMA-based controller, not a nuisance to deal with at all. A decent competitor to the SCSI chips above. I just don't know when it was introduced. It was used in the `Archimedes A300 Hard-disk poddle <http://chrisacorns.computinghistory.org.uk/docs/Acorn/Manuals/Acorn_A300_SMCLSup.pdf>`_, so before second half of '80s for sure.

Overall, surveying the landscape, even today - let alone back in the day - I would have come to the conclusion that SCSI is the way to, and most likely would have gone the same route as Apple did: the 5380 or one of it's many variants.

As far as price is concerned, I have bad news: hard drives were *very* expensive in those days. Here's a Byte magazine:

https://ia801609.us.archive.org/16/items/byte-magazine-1984-11/1984_11_BYTE_09-12_New_Chips.pdf

It lists a 10MB hard drive (MFM, with interface card) for $800, a 20MB one for $1100 and a 40MB one for $2300.

Networking
----------

In the '80s, especially in the beginning of it, networks mostly meant modems for home users, though LANs did exist for corporations and schools. These were mostly proprietary solutions and vendor-specific. Even the venerable PET from Commodore had some support for LANs.

Here I'm going to rely heavily on hind-sight and pick Ethernet. It was developed in the '70s and was `commercialized in 1980 <https://en.wikipedia.org/wiki/Ethernet>`_, so it certainly was a thing by the time our little machine was going to go in the market.

10Base5 (thick Ethernet) was introduced in '82, I can't find any reference to when 10Base2 (thin Ethernet) was introduced, but 10BaseT was commercialized in 1990. So I would venture to say '83 or '84.

So how did people interface to Ethernet back then?

.. note:: the NE2000
    *The NE2000* was by far the most popular card. It (and it's 8-bit version, the NE1000) was introduced in '87 and was based on the `DP8390 <pdf.datasheetcatalog.com/datasheets2/70/706490_1.pdf>`_. There were many many clones and variants. There is a `reference design <http://www.bitsavers.org/components/national/ethernet/DP849x_Demonstration_Kit_1987.pdf>`_ from National for this chip, very similar to the NE1000. This chip uses a local bus and a local SRAM to store the packet ring-buffer, and thus uses only a few I/O registers and no DMA to interface with the system. The chip itself supports bus-mastering (as I gather that's what it calls DMA), but it's pretty far from what we're doing: there's no daisy-chaining of BREQ, it has a multiplexed address-data bus and doesn't generate any nRAS/nCAS signals. So, it's probably easier to follow the reference design and add an external packet buffer SRAM then try to integrate it into system memory.

Nowadays, there are still some alternatives: `LAN91C113 <https://media.digikey.com/pdf/Data%20Sheets/Microchip%20PDFs/LAN91C113.pdf>`_, the `LAN9210 <https://ww1.microchip.com/downloads/en/DeviceDoc/9210.pdf>`_ and the `CS8900 <https://www.digchip.com/datasheets/download_datasheet.php?id=242902&part-number=CS8900A>`_

This is all later though it seems, fine for the second generation machine, but not for the first gen.

For the first generation machines, I would say I would have developed some sort of home-grown, serial (probably `RS-485 <https://en.wikipedia.org/wiki/RS-485>`_-based) protocol.

There is something interesting, called HDLC/SDLC. These are L2 protocols that are developed by IBM, worked probably through RS-232 or RS-485 or similar physical layers, but had controllers, such as the Motorola `mc6854 <https://heyrick.eu/econet/mc6854fixed.pdf>`_. This device could reach about 1Mbps, so not shabby for the time. It was used in the `Acorn Archimedes Econet poddle <http://chrisacorns.computinghistory.org.uk/docs/Acorn/Manuals/Acorn_A300_SMCLSup.pdf>`_, from which I got the idea.

Printers
--------

Centronics was the rage, I would have just rolled with it through some 3rd party GPIO chip, I think. Or, if I could scavenge together enough GPIOs for the handshake control, maybe just a 74LS373 for the data-bus. We would need 5 inputs and 4 outputs on top of the data-bus. That's annoying. So maybe a 2-port GPIO chip (such as whatever the C64 used) and a single extra GPIO down on the HID interface chip?

MIDI
----

Midi is just a serial port, but for some reason people liked to use something else then the 16450. I probably would have stuck with it, but it would have needed a custom crystal to get the baud-rate right.

RTC
---

The Archimedes A300 used the `PCF8573 <https://www.picmicrolab.com/wp-content/uploads/2014/05/PCF8573.pdf>`_, but *also* the `PCF8583 <https://www.nxp.com/docs/en/data-sheet/PCF8583.pdf?>`_. My guess is that one was introduced earlier then the other and they wanted to be able to populate either. The second one has some memory in it for configuration and stuff, so my guess is that they would have gone with just that had it been available on time. Either way, they are both I2C peripherals, which make interfacing them into just a pair of GPIOs, stolen from the HID device below. Or, if I'm so inclined, a full I2C controller in that very same chip.

Human interface
---------------

This was the era of the original MAC, the Amiga 1000 and of course the IBM PC. The common thing about these is that all had some sort of serial protocol for an external keyboard. Mice were not that common and the approach to them was mostly based on either hacked-up joystick ports (Amiga) or some custom interface very similar to it (Mac). PCs didn't have mice and once they did, they were serial based. Of course PS/2 computers introduced the same interface for both, albeit on two different ports. Later Macs introduced the APB connector and interface.

For joysticks, the common interface was similar to what the C64 used: some GPIOs and slow (R/C-based) ADCs.

I probably should have gone down a similar road: a serial interface, probably PC-style for the keyboard, an analog/digital joystick port for ... well, joysticks and mice. The main reason would have been that these were existing standards with many compatible products available and I really would not have enjoyed developing them all from scratch.

So, PS/2 port for Keyboard: `good info on the protocol <http://www.burtonsys.com/ps2_chapweske.htm>`_

The Amiga had a very `simple <http://pavouk.org/hw/en_amigamouse.html>`_ mouse, not much more than the optical encoders. While I don't have the schematic, but the Macintosh mouse was very similar judging from the `pinout <https://old.pinouts.ru/InputCables/MacMouse_pinout.shtml>`_. The Amiga had integrated encoder counters in Denise. The Mac apparently counted the cycles in SW as the pins go to a 6522. I don't quite know how the Atari ST did it, but the mouse itself was very much similar to the Amiga one.

I would have cobbled together something in a custom chip, or tagged it on to one of the existing ones. I would have needed:

6 pins per mouse/joystick (with two-button mice)
1 pin per analog controller (so 4 total for 2 analog joysticks)
2 pins for keyboard (CLK and DATA)

That's a total of... a lot of pins. I would not be able to tag it on to anything I already have. The sound chip can take 10 more pins, so that would be 1 mouse/joy port, including analog inputs and a keyboard interface. The DMA bridge has 8 pins available which could be the second joystick. But... yuck!

I would be really tempted to use a `Z8430 <https://www.zilog.com/docs/z80/ps0181.pdf>`_ CTC for the mouse counters and analog inputs. However it's only good for timing the analog joysticks, not for the mouse: it doesn't support up/down counters. There was the 74LS469 which was an 8-bit up/down counter, but I'm not sure when it was introduced. Certainly after '84. You could use pairs of SN74LS192 to get the same, that was available already in '81. And at that point you have 4 chips just to get the counters and then a few to latch and read the counter values.

GALs had something like 8 registers in them, so they are just a very expensive replacement for the 74LS469.

So, custom chip then!

But in reality, this is not the way I'm going to go. This is where I'm going to draw the line and use USB.

Cores needed
------------

- UART (done)
- PS/2 interface
- I2C interface (maybe, maybe just GPIO)
- GPIO
  - programmable input/output
  - programmable interrupt capability (edge/level/which edge/level)
- SD-card (maybe just SPI)
- USB host (high-speed)
- Timers of various sorts

Custom networking
-----------------

I'm interested in this, so let's think a little more:

We will use single-pair CAN-style interconnect, but a different protocol (because CAN was somewhat later and because I want longer cables).

Due to the dominant-recessive signalling, AC-coupling is out of question, and probably 1Mbps is the upper limit.

To minimize clock accuracy requirements, we'll ensure that there are regular transitions and require that any transition re-syncs the receiver.
We will do this by inserting a start bit (dominant) and a parity bit (odd parity) to every byte.

Collision detection works by realizing that the bus is in dominant state while I'm trying
to drive it recessive. The behavior under collision detection is to drive a dominant state for 10 bit-times on the bus. This will cause an
edge-detect timeout on every device on the bus (transmitter or receiver). The response is to release the bus immediately (for transmitters)
and to drop the incoming packet (for receivers). Then a slotted ALOHA-style retry takes place.

Transmissions can only start when the bus has been in recessive state for 10 bit-times.

The MAC packet format is something like this:

0: destination PHY address (0xff is broadcast)
1: source PHY address (0xff is special)
2: packet length (including first two bytes, maximum is 255)
3: packet type
4...n: payload

Each device has a 128-bit unique ID, but no address. Communication starts with a DHCP-like process:

DHCP request packet:
--------------------
0: 0xff
1: 0xff
2: length
3: packet type (DHCP request)
4...20: requestor unique ID

DHCP response packet:
---------------------
0: 0xff
1: <address of DHCP server>
2: length
3: packet type (DHCP response)
4...20: requestor unique ID
21: assigned PHY address
22...n: additional fields in the following format:
   0: field type
   1: field length
   2...m: field content

We could theoretically use a different setup, where length and packet type share the same 16-bit, but in a 12/4 division. Still allows for what we need, but also for 4096-byte packets, enough to pretend to be Ethernet.

We would need to be a DMA client and implement a ring-buffer in memory. We would generate about 100kBps traffic, really nothing, on the bus and if we had an internal FIFO of a few words, we could tolerate quite a lot of request-response latency. During transmission, a buffer-under-flow would be treated as a collision and handled the same way.

So, this is not going to work: on a network, it's paramount that we don't need a common ground, which means AC coupling.

Long-term DC balance is relatively easy to achieve: we could send either the symbol or its inverted version to make sure that the imbalance gets
minimized. This, combined with the fact that odd parity ensures that there aren't equal number of 0-s and 1-s in a symbol (what about the start-bit???)
makes it possible to control DC imbalance to within 5 bits. Beyond that, we could regularly inject balancing symbols that bring that number down to 0 or +/-1.

A little bit of DC balance of course is not a big deal, it still allows for proper detection of 0-s and 1-s.

Ethernet uses 120ohm, with 50pf/m capacitance, so we obviously want to terminate with 120 ohms.

At 300m limit we get ~1us propagation delay, a load capacitance of 15nf and a load resistance of 120 ohms. These later things might not be all that interesting, but at 1Mbps, the propagation delay is on the same order as the bit-time. This is to say that reflections can easily cause *huge* ISI.

That is, both ends of the cable must be terminated.

The amount of DC imbalance a single bit of mismatch causes should depend on the time-constant of the RC filter. If that time constant is two orders of magnitude higher then the maximum imbalance, we're OK.

So, the maximum imbalance could be 8 bits in our primitive system. That's 8us. So the time-constant should be 800us, make it 1ms.

If the 'R' in that constant is 60 ohms (both ends are terminated, remember), the C must be 16uF. However, we have 4 of these caps in series (two on TX, two on RX), so really, C should be 64uF. Quite large, but not problematic if can be polarized. That is hard to do though. At the same time, thought more rare, unipolar capacitors of that size existed, see all the TV circuitry of the age. The voltage rating is not all that interesting, I might not want to drive more than 5V into the cable.

I have the whole PHY modelled up in LTSpice (phy_ac.asc). It appears to work rather nicely, even with 2Mbps transfer rates. No droop all the way to 10us
consecutive 0-s or 1-s, AC coupled, 5V supply, all the goodies.

Will have to find components  that were actually available at the time, but damn, this seems to work!

**NEW IDEA:**
What if the PHY layer is based on either a floppy or a HDD controller? Those devices needed to deal with CDR from the very beginning...

According to <WikiPedia `https://en.wikipedia.org/wiki/Floppy_disk`>_ the raw datarate of a 2.88Mbps floppy was 1Mbps, so earlier ones are clearly much slower.

Other stuff: WD2501/11 - for CCITT X.25 (1.6Mbps)

Even in 1981, the WD1000 board could do 5Mbps on a hard drive

Page 394 onward of http://www.bitsavers.org/components/westernDigital/_dataBooks/1981_Western_Digital_Product_Handbook.pdf provides what appears to be a complete schematic for an early Shugart SA400 FDD, including CDR.

The WD1691 (page 406) uses a 74LS629 VCO for it's PLL. This VCO supports clocks of up to 20MHz apparently!
The WD2143-01 could generate four (non-overlapping) clock phases at 3MHz.

With that 4-phase clock, one can cobble together a CDR, though rather part-consuming.

The WD1100-12 can be used to generate an MFM data-stream at 5Mbps rates.

The WD1010 is a (mostly) single-chip implementation of the WD1000 board. It uses the WD1011 data separator.

The WD9216-01 could be used as a CDR albeit only up to 0.5Mbps datarates. It uses an 8.3MHz clock input and a (nominally) 16x oversampled internal clock. (http://www.bitsavers.org/components/westernDigital/_dataBooks/wd1984storageProducts_01.pdf)

Routing
~~~~~~~

Beyond the MAC, maybe TCP-IP is the best thing, though the relatively limited packet length (compared to Ethernet) is limiting, especially since it was introduced in 1982, just in time for us to adopt it.
