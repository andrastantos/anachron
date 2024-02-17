
Graphics to The Masses Controller
=================================

The idea here is to use a GoWin GW1NR-9 (probably) FPGA with an integrated 64MB PSRAM die to create a nice, self-contained graphics controller chip for retro-computing. It should be simple to interface it to era-accurate CPUs, like a Z80 or a 6502. It should be completely self-contained including the frame-buffer and clocks. It should support direct connection to a VGA monitor.

Let's start with the pinout!

========== ================ =============== ===========
Pin Number Pin Name         Pin Direction   Description
========== ================ =============== ===========
1          a0               I               Address bus
2          a1               I               Address bus
3          a2               I               Address bus
4          a3               I               Address bus
5          a4               I               Address bus
6          a5               I               Address bus
7          a6               I               Address bus
8          a7               I               Address bus
9          a8               I               Address bus
10         a9               I               Address bus
11         a10              I               Address bus
12         a11              I               Address bus
13         d0               I/O             Data bus
14         d1               I/O             Data bus
15         d2               I/O             Data bus
16         d3               I/O             Data bus
17         d4               I/O             Data bus
18         d5               I/O             Data bus
19         d6               I/O             Data bus
20         d7               I/O             Data bus
21         n_fb_cs          Input           Active low frame-buffer chip-select
22         n_reg_cs         Input           Active low register chip-select
23         n_rd             Input           Active low read strobe
24         n_wr             Input           Active low write strobe
25         n_wait           Output, OD      Active low, open-drain wait output
26         n_rst            Input           Active low reset input
27         int              Output          Interrupt output with programmable polarity (defaults to tri-state)
28         int_ack          Input           Interrupt acknowledge with programmable polarity
29         iei              Input           Interrupt daisy-chain input
30         ieo              Output          Interrupt daisy-chain output
31         video_r          Analog          Analog 'red' channel output
32         video_g          Analog          Analog 'green' channel output
33         video_b          Analog          Analog 'blue' channel output
34         video_h_sync     Output          Horizontal video sync output with programmable polarity
35         video_v_sync     Output          Vertical video sync output with programmable polarity
36         audio_l_out      Analog          Audio output left channel
37         audio_r_out      Analog          Audio output right channel
38         audio_in         Analog          Mono audio input
39         VCC              5V power        Power input
40         GND              GND             Ground input
========== ================ =============== ===========

This allows for a memory-mapped 2k frame-buffer window and a separate register section that can be in I/O space or memory-mapped, depending on how address-decoding is connected.

An alternative, multiplexed address/data bus can also be used:

========== ================ =============== ===========
Pin Number Pin Name         Pin Direction   Description
========== ================ =============== ===========
1          a8               I               Address bus
2          a9               I               Address bus
3          a10              I               Address bus
4          a11              I               Address bus
5          a12              I               Address bus
6          a13              I               Address bus
7          a14              I               Address bus
8          a15              I               Address bus
9          a16              I               Address bus
10         a17              I               Address bus
11         a18              I               Address bus
12         ale              I               Address latch enable
13         ad0              I/O             Data bus
14         ad1              I/O             Data bus
15         ad2              I/O             Data bus
16         ad3              I/O             Data bus
17         ad4              I/O             Data bus
18         ad5              I/O             Data bus
19         ad6              I/O             Data bus
20         ad7              I/O             Data bus
21         n_fb_cs          Input           Active low frame-buffer chip-select
22         n_reg_cs         Input           Active low register chip-select
23         n_rd             Input           Active low read strobe
24         n_wr             Input           Active low write strobe
25         n_wait           Output, OD      Active low, open-drain wait output
26         n_rst            Input           Active low reset input
27         int              Output          Interrupt output with programmable polarity (defaults to tri-state)
28         int_ack          Input           Interrupt acknowledge with programmable polarity
29         iei              Input           Interrupt daisy-chain input
30         ieo              Output          Interrupt daisy-chain output
31         video_r          Analog          Analog 'red' channel output
32         video_g          Analog          Analog 'green' channel output
33         video_b          Analog          Analog 'blue' channel output
34         video_h_sync     Output          Horizontal video sync output with programmable polarity
35         video_v_sync     Output          Vertical video sync output with programmable polarity
36         audio_l_out      Analog          Audio output left channel
37         audio_r_out      Analog          Audio output right channel
38         audio_in         Analog          Mono audio input
39         VCC              5V power        Power input
40         GND              GND             Ground input
========== ================ =============== ===========

This type of pinout is a direct fit for the 8085/8088/8051 processors. Intel was quite a bit in love with this organization for some reason.

While it would be a pain to use this pinout with a Z80 or an 6502, this has the extra benefit that the chip can also serve as the main memory for the microprocessor (up to 512k for an 8088)

In both cases, we can double the memory address space, by deleting n_rd and requiring slightly more complex external address decode.

I/O to The Masses Controller
=================================

Similar idea, except for I/O. To keep things simple, we don't use DMA, and have internal packet buffers instead.

The 8 registers are as follows:
- register index register
- register data register
- buffer index register
- buffer data register
- secondary buffer index register
- secondary buffer data register
- interrupt control register
- interrupt status register

========== ================ =============== ===========
Pin Number Pin Name         Pin Direction   Description
========== ================ =============== ===========
1          a0               I               Address bus
2          a1               I               Address bus
3          a2               I               Address bus
4          d0               I/O             Data bus
5          d1               I/O             Data bus
6          d2               I/O             Data bus
7          d3               I/O             Data bus
8          d4               I/O             Data bus
9          d5               I/O             Data bus
10         d6               I/O             Data bus
11         d7               I/O             Data bus
12         n_cs             Input           Active low chip-select
13         n_rd             Input           Active low read strobe
14         n_wr             Input           Active low write strobe
15         n_wait           Output, OD      Active low, open-drain wait output
16         n_rst            Input           Active low reset input
17         int              Output          Interrupt output with programmable polarity (defaults to tri-state)
18         int_ack          Input           Interrupt acknowledge with programmable polarity
19         iei              Input           Interrupt daisy-chain input
20         ieo              Output          Interrupt daisy-chain output
21         pa_0 sd_clk
22         pa_1 sd_cmd
23         pa_2 sd_d0
24         pa_3 sd_d1
25         pa_4 sd_d2
26         pa_5 sd_d2
27         pa_6 i2c_sda
28         pa_7 i2c_scl
31         pb_0 uart_tx
32         pb_1 uart_rx
33         pb_2 uart_cts
34         pb_3 uart_rts
35         pb_4 ps2_kbd_d
36         pb_5 ps2_kbd_c
37         pb_6 ps2_mouse_d
38         pb_7 ps2_mouse_c
37         usb_dp           I/O             USB (1.1) signals
38         usb_dm           I/O             USB (1.1) signals
39         VCC              5V power        Power input
40         GND              GND             Ground input
========== ================ =============== ===========

Similarly, an Intel, multiplexed interface could be provided as well.

Alternatives
===================

There is a chip out there, that *almost* fits the bill. The RA8875 from https://www.raio.com.tw.

The SSD1963 is a similar thingy (https://www.solomon-systech.com/product/ssd1963/ and https://www.crystalfontz.com/controllers/SolomonSystech/SSD1963/), but in a small-enough package to fit on a 40-pin DIP package. It seems in the LQFP package it's available for about $5.00 a pop.

Both of these things are TFT display controllers, but output parallel RBB data and HSYNC/VSYNC/HBLANK signals with controllable timing.

Looking at the register set, it's pretty clear that VGA compatible timing can be achieved. The active levels of the sync pulses can be programmed, the location, width and active periods of everything can be set in a flexible manner, even a PLL is provided so the pixel clock can be set in a relatively flexible manner.

What these things can't do (I think) is scan-line replication. So VGA would be the lowest resolution to support with them. Still, a pretty nice solution, if you asked me...

And here's someone selling something along these lines proving the concept: https://versamodule.com/vm8.html and https://www.rayslogic.com/propeller/Products/DviGraphics/DVI.htm

What this solution doesn't get us:

- Character modes
- Palettized modes
- Sprites
- Multiple drawing planes
- Scan-line replication
- 'GPU' features (though the RA8875 has some capabilities along these lines, but doesn't come in the right package)

Overall, it's a shortcut, but not a solution.

As for how to get from digital RGB to something that monitors like?

DVI/HDMI:
https://www.ti.com/product/TFP410 ($15)
https://www.analog.com/media/en/technical-documentation/data-sheets/ADV7513.pdf ($5, but scarce)

VGA:
https://www.ti.com/lit/ds/symlink/ths8136.pdf ($8)
https://www.analog.com/media/en/technical-documentation/data-sheets/ADV7125.pdf ($15)
https://www.analog.com/media/en/technical-documentation/data-sheets/adv7120.pdf ($30, but all over the map)


BTW: the GoWin FPGA alone is like $30 for the 9k gate part and $20 for the 4k gate one.


How to test this thing?
=======================

The 6502 is still in production by these guys: https://wdc65xx.com/integrated-circuit.
The Z80 is also in production by Zilog.

So I guess old stuff never dies...

One could use (resuscitate) the H-storm project and create new CPU/peripheral boards. Or do something custom...

Notes on USB
============

USB bus timing is completely host-driven, but that's not to say that there aren't restrictions.

1. Every 1ms, a SOF packet must be sent out.
2. The host must schedule all communication into these 'frames'. The general process of transferring data (with few exceptions) is:
   a. IN/OUT/SETUP packet (always host->device)
   b. DATA0/DATA1 packet (in the appropriate direction)
   c. ACK/NAK/STALL packet (in the appropriate direction)
3. Low-speed device transfers must be in (well, d'uh) low-speed, but must be preceded by a PRE packet and some idle time.
4. Since host sets up all transfers, the host can't reject a packet: host can only respond with NAK or not at all in case of protocol violations
5. Host must support packets of up to 64 bytes of payload length
6. There are two kinds of CRCs: 5-bit and 8-bit long; usage depends on packet type.

HID devices are usually using interrupt EPs. These are not all that different from bulk ones, except that they need to be periodically polled by the host. In other words, interrupts are not really interrupts at all.

Isochronous EPs are - again - things that need periodic servicing from the host, but the transfers lack the ACK/NAK packets. Invalid transmissions are simply ignored. The difficulty it seems is mostly around making sure in the scheduler that we keep the buffers going.

From the hosts perspective, the most complicated things seem to be:
1. PNP management
2. Enumeration
3. Error management and recovery
4. Scheduling

I'm thinking if there's a way to abstract these away into the controller and giving something of a device/interface/EP level interface to the true host. These would of course dynamically appear/disappear but enumeration, scheduling, etc. would not be something that the host would need to be bothered with.

What is more problematic is that class drivers probably want to send/get transfers to the devices control EP. So that would need to be exposed too.

Maybe even higher level for ex. HID devices (https://wiki.osdev.org/USB_Human_Interface_Devices; https://www.usb.org/sites/default/files/hid1_11.pdf).
There is a rather complex 'report' structure, but the 'boot' protocol is rather trivial for at least keyboards and mice.
There are of course a ton of quirks and what not as always. Joystick and gamepads are especially problematic as they are neither keyboards or mice yet I want to support them.

Descriptors
-----------
These are the bane of USB. There are soo many of them, each being custom and convoluted. Just the HID class has several!

At any rate, the important point is that, since descriptors are longer than a single USB packet (8 for low-speed, 64 for full-speed), they are usually broken up into several packets. So, a GET_DESCRIPTOR transfer would look something like this:

   SETUP   IN(DATA0)  IN(DATA0)   IN(DATA0)  STATUS

The SETUP packet would contain the 'GET_DESCRIPTOR' request code. It also contains the 'length' field, but I'm not sure how that applies for IN transfers.

This is what the standard says about packet fragmentation:

  >> An endpoint must always transmit data payloads with a data field less than or equal to the endpoint's
  >> wMaxPacketSize (refer to Chapter 9). When a control transfer involves more data than can fit in one data
  >> payload of the currently established maximum size, all data payloads are required to be maximum-sized
  >> except for the last data payload, which will contain the remaining data.

wMaxPacketSize if EP specific, to make things more fun.

Packet sizes
------------
In general packet sizes (MAX_PACKET_SIZE) is set in the EP descriptors. There however are maximum sizes for various transfer types.

================   =======================    =======================
Transfer type      Full-speed device          Low-speed device
================   =======================    =======================
CONTROL:           64 bytes                   8 bytes
BULK:              64 bytes                   N/A (???)
ISOCHRONOUS:       1023 bytes
INTERRUPT:         64 bytes                   8 bytes
================   =======================    =======================

This is how the standard talks about the bootstrapping of packet sizes:

  >> In order to determine the maximum packet size for the Default Control Pipe, the USB System Software
  >> reads the device descriptor. The host will read the first eight bytes of the device descriptor. The device
  >> always responds with at least these initial bytes in a single packet. After the host reads the initial part of
  >> the device descriptor, it is guaranteed to have read this default pipe's wMaxPacketSize field (byte 7 of the
  >> device descriptor). It will then allow the correct size for all subsequent transactions. For all other control
  >> endpoints, the maximum data payload size is known after configuration so that the USB System Software
  >> can ensure that no data payload will be sent to the endpoint that is larger than the supported size. The host
  >> will always use a maximum data payload size of at least eight bytes.

The length of a packet on the wire can be determined apparently from the EOP marker at the end (SE0;SE0;J sequence, which is not a valid data-sequence).

USB framework
-------------

From this, the following picture seems to emerge:

- Upon device insertion, we go through enumeration (chapter 9.1.9), including address assignment, discovery of configurations/interfaces/EPs. We will - unless know better through quirks - select configuration 0. We leave the device in the 'configured' state.

For every EP, we provide the following, FIFO-style interface; One location contains a FIFO of packet sizes, another contains the data-stream.

So, one could do this:
1. Read transfer size (return 0 for empty, some other for packet size) from control stream
2. Read transfer-size number of bytes from data stream.
3. Rinse and repeat.
Important to note that once (1) is complete, code is obligated to read as many bytes from the data stream as was given. The transfer size FIFO already stepped to the next transfer, thus it should not be read again until the data is exhausted.

To send packets to the EP:
1. Write transfer-size number of bytes to the data stream
2. Write transfer size into control stream
3. Rinse and repeat

For writes we have an issue with FIFO full conditions: how do we know that we can send a packet and of what size? We need to expose the following additional information for every EP:
2. Number of free transfer entries (OUT direction)
3. Number of free data bytes (OUT direction)

Notice, that we don't control packetization; this we don't expose wMaxPacketSize. That is done internally. This can be problematic for mass storage devices, where the first packet is supposed to contain the SCSI control info. Not sure if it can be separated into a unique transfer.

For isochronous EPs, the FIFO should have 'drop oldest' behavior for overflow.
For interrupt EPs, we should support a - well - interrupt feature, where we trigger an interrupt every time the input control stream has non-zero entries (that is, we have at least one data-packet to be read).

We should also expose the bus topology and device descriptors to the host so it knows what is where.
We should also generate interrupts on topology/device/power state changes.

IMPORTANT: USB is not an interleaved bus. IN/OUT/SETUP packets must be followed by their associated data packets and their associated status responses. Some of these flow in the opposite direction and the bus is 'locked up' until all three phases (if exist) complete. Thus, the above interface really doesn't talk about packets, but transfers. This could be problematic if a protocol puts strict restrictions on transfer fragmentation other than what's communicated in wMaxPacketSize.

We can be tricky about address assignment to put some order into USB chaos:
- Address 0 is special, it's used before address assignment, so that's reserved.
- we have 7-bit device; and 4-bit EP addresses.
We can use the following ranges for device classes:

===============   ======================================================
Address range     Device class (category, not necessarily USB class!)
===============   ======================================================
1-3               keyboards
4-7               mice
7-11              joysticks
12-15             game controllers
16-19             serial portions (including MODEMs and other serial-looking things)
20-23             NICs
24-31             mass storage
32-35             printers
36-39             scanners (imaging devices)
40-43             video (web-cams)
44-47             audio (sound cards)
120-127           unrecognized
===============   ======================================================

The neat thing about this is that now we can expose EPs in fixed locations in the memory map and the host knows what to expect there.
The not-so-neat thing about this is that we need to decode a large section of the memory map.

Hubs and topology in general should be automatically handled and not exposed.

I really don't think we will (at least initially) support isochronous devices though.

If one plugs in ex. a 4th mice, we just won't enumerate it. I think we're already overly generous...

This - needless to say - requires a lot of intelligence and memory on the interface.

Since the RP2040 has a USB1.1 host controller, maybe the best way to deal with this would be in that chip? It has 30 GPIOs, so let's see how that would work out for a pinout!


========== ================ =============== =============== ===========
Pin Number Pin Name         Pin Direction   RP2040 GPIO     Description
========== ================ =============== =============== ===========
1          a0               Input           0               Address bus
2          a1               Input           1               Address bus
3          a2               Input           2               Address bus
4          a3               Input           3               Address bus
5          a4               Input           4               Address bus
6          a5               Input           5               Address bus
7          a7               Input           6               Address bus
7          d0               I/O             7               Data bus
8          d1               I/O             8               Data bus
9          d2               I/O             9               Data bus
10         d3               I/O             10              Data bus
11         d4               I/O             11              Data bus
12         d5               I/O             12              Data bus
13         d6               I/O             13              Data bus
14         d7               I/O             14              Data bus
15         n_cs             Input           15              Active low chip-select
17         n_wr             Input           16              Active low write strobe
15         n_wait           Output, OD      17              Active low, open-drain wait output
16         n_rst            Input           18              Active low reset input
17         int              Output          19              Interrupt output with programmable polarity (defaults to tri-state)
21         pa_0 sd_clk      I/O             20
22         pa_1 sd_cmd      I/O             21
23         pa_2 sd_d0       I/O             22
24         pa_3 sd_d1       I/O             23
25         pa_4 sd_d2       I/O             24
26         pa_5 sd_d2       I/O             25
27         pb_0 i2c_sda     I/O             26
28         pb_1 i2c_scl     I/O             27
31         pb_2 uart_tx     I/O             28
32         pb_3 uart_rx     I/O             29
33         usb_dp           I/O                             USB (1.1) signals
34         usb_dm           I/O                             USB (1.1) signals
35         VCC              5V power                        Power input
36         GND              GND                             Ground input
========== ================ =============== =============== ===========

So this sort of works, but it doesn't allow to map all the EP buffers into memory.

What we would need per EP:

=======   =============   ==================   =====================================
Offset    Direction       Name                 Note
=======   =============   ==================   =====================================
0         READ            IN_BYTE_AVAIL_LOW    Bytes in the next IN transfer (low)
1         READ            IN_BYTE_AVAIL_HIGH   Bytes in the next IN transfer (high)
2         READ            OUT_BYTE_FREE_LOW    Number of free entries in the OUT byte FIFO (low)
3         READ            OUT_BYTE_FREE_HIGH   Number of free entries in the OUT byte FIFO (high)
4         READ/WRITE      BYTE_FIFO            byte FIFO (IN/OUT depending on read/write)
5         READ/WRITE      EP_CONFIG            EP configuration
6         WRITE           TRANSFER_LEN_LOW     Trigger an OUT or IN transfer of N bytes (low)
7         WRITE           TRANSFER_LEN_HIGH    Trigger an OUT or IN transfer of N bytes (high)
6         READ            USB_CLASS            device class (from USB)
7         READ
=======   =============   ==================   =====================================



So, I think we can squeeze this into 8 bytes. If we have 64 possible device addresses and 16 EPs each, this results in 6+4+3=13 address bits. That's 8kBytes of address space. Not only we don't have that many address pins, I don't even think if we should.

So, what we should be doing is to have an index-register. But even with that, we need more than 8 bits, just to select the EP.

We might be able to reshuffle the bits such that:
We use MSB to decode class (so, first mouse,kbd, etc. comes adjacent in address space)
We use even higher MSBs to decode EP (since most interesting devices have just one EP)

Thus, for *most* use-cases we can use a simple 8-bit decoder to get to the right EP.

Another way of dealing with it (since we won't have more than a dozen or so USB functions ever attached) is to say that address 1/2/3 are reserved for the first keyboard/mouse/serial port attached, and the rest is just assigned sequentially.

Special classes:
-------------------
Mass storage: https://usb.org/sites/default/files/Mass_Storage_Specification_Overview_v1.4_2-19-2010.pdf
              https://www.usb.org/sites/default/files/usbmassbulk_10.pdf
              https://wiki.osdev.org/USB_Mass_Storage_Class_Devices
HID: https://www.usb.org/sites/default/files/hid1_11.pdf
     https://www.usb.org/sites/default/files/documents/hut1_12v2.pdf




https://www.usbmadesimple.co.uk/ums_4.htm

Function hierarchy
------------------

Another fun topic: a USB device could have several configurations, in each several interfaces and in each of *that* several EPs. So the hierarchy is:

  function
  +--- configuration (almost always 1 thanks to Windows)
       +--- interface (composite devices have multiple interfaces)
            +--- EP

Hmm hmm...

Looking at the devices that my laptop have (lsusb -v btw.) reveals a few interesting concepts:

1. There are things, like cameras that have multiple interfaces that act in concert (Maybe InterfaceAssociation descriptors?) to create a single device (this is a USB 2.0 thing and is described here: https://www.usb.org/sites/default/files/iadclasscode_r10.pdf)
2. Interfaces can have several (I do mean *several*) alternative settings (bAlternateSetting). They come with their own descriptors and EPs. These settings can differ in the number/type of EPs or the maximum supported packet size. The idea seems to be to select an interface that best fits the use-cases (such as isochronous or bulk transfers on a BT interface though mine doesn't seem to use that feature).

So, the trouble is that it's not possible to start up a USB device without knowing what the right alternative interfaces are. It's also impossible to know if composite devices have interfaces as unique, independent entities or multiple, combined functions. I guess this later distinction doesn't matter all that much: all interfaces must select an alternative.

There is a default alternative though (bAlternateSetting == 0). So the framework can start there but *must* allow a way to set the alternatives.

OK, so the reason I'm struggling here is that I've been thinking about this wrong. What this 'chip' provides is in essence a USB bus driver. And what I need to devise is a HW (register/FIFO/whatever) based interface between the device drivers and the bus driver.

I'm not sure the Linux driver architecture is going to be useful here: https://www.kernel.org/doc/html/v5.0/driver-api/usb/index.html. It's a bloated mess of an interface, hopefully much more complicated then what I would need.

To get 'report descriptors' from lsusb, one first has to unbind the device from the hid driver: http://tiebing.blogspot.com/2015/03/how-to-get-linux-usb-report-descriptor.html
