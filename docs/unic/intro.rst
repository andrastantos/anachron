Universal Chips (UniC)
======================

An interesting idea is to make an FPGA-based chip, that can pretend to be anything.

Logic levels allow for a 3.3V I/O to be TTL compatible, provided we take care of the above-the-limit voltages:

https://en.wikipedia.org/wiki/7400-series_integrated_circuits#/media/File:Niveaux_logiques_CMOS-TTL-LVTTL.png

This can be done by a series 330 ohm resistor and a diode towards VCC. The resistor will limit the current to 5mA on the driver, if it hard-pulls to 5V. The resistor also (unfortunately) slows the transitions down, but hopefully not to the level where it's problematic: the RC constant with a 10pF load is 3.3ns, which is half the propagation delay of a single LS gate.

Power is more problematic: we don't know where the GND and VDD pins on the to-be-simulated package are. What we can do is to provide a pair of (Schottky) diodes towards the internal VDD and GND from each pin. These diodes would be on the 'outer' pin of the 330 ohm resistor and tied together on the top and bottom to provide my internal VDD and GND. This setup is tested in LTSpice and seems to work, albeit shifts the GND by maybe as much as 0.4V.

An LDO can then generate VCC from VDD. Due to the GND-shift, maybe it's better to generate a somewhat lower VCC, maybe 3.1V or so. That would split the difference in half.

There is a part (74S107 or something) that contains the right diode arrangement for 16 pins, though it might be a bit too large (TSSOP20 is the best it can do). There are quad-diode packages (2 pins worth) as well in the BV56 family.

We can add a tiny OLED display (https://www.ebay.com/itm/293291361583 for instance) to the top for fun displaying of the part number being emulated, maybe even small animations.

The PCB could be covered by a 3D printed snap-on plastic cover, pretending to be a DIP package.

Programming ideally would be done through USB, with a USB connector on one end of the package, but that might be a little too expensive, especially since that would need an FTDI chip of sorts as well.

