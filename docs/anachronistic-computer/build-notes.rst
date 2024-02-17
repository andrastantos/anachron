Build notes
===========

Given that I don't actually own a chip company and can't tape out silicon, how would I go about realizing these designs?

The idea would be the following:

#. Use FPGAs (3.3V compatible, small ones)
#. Put them on small PCBs that implement the breakout to the DIP package and pinout
#. Get `lead-frame pins <http://www.dasarodesigns.com/product/batten-and-allen-ba3760-dill-leadframe-dip-pcb-edge-clip-pins/>`_ to make the PCBs into something that can be inserted into a socket. There are others too:
#. TE also seems to be making these: https://www.te.com/usa-en/plp/leadframes/Y30nn.html?q=&n=42057&d=652833%20544927&type=products&samples=N&inStoreWithoutPL=false&instock=N
#.
   #. http://oshchip.org/products/Flip-Pins_Product.html
   #. http://www.dipmicro.com/store/HDR40X1MM
   #. https://www.precidip.com/AppHost/9696,1/Scripts/Modules/Catalog/Default.aspx?c=8
   #. https://www.reichelt.de/ic-adapter-strip-20-pin-single-row-2-54-pitch-aw-122-20-p4426.html?GROUPID=7429&START=0&OFFSET=100&SID=96XlYlEKDUvydFgRrcvved99d993f4fa2102c70692ed0d8e7cb19&LANGUAGE=EN&&r=1
   #. https://www.eevblog.com/forum/projects/best-way-to-put-dil-pins-on-a-small-pcb-to-create-replacement-for-old-parts/
   #. https://www.reactivemicro.com/product/lead-frame-pins/ <-- I've bought some pins from them, this seems to be BA3502.
   #. https://www.kinsun.com/en/product/Lead-frame-for-Guide-Pin.html

#. `Create silicon moulds <https://www.wikihow.com/Make-a-Silicone-Mold>`_ for the DIP packages
#. Use epoxy to coat the PCBs to make them look like DIP packages

I've ordered from these guys before: https://www.reactivemicro.com/product/lead-frame-pins/#lightbox/0/
100 pins for $10, $0.1 per pin. Above 1000 pins, this drops to $0.07. TE seems to want to sell pins for $0.045 at very
high volumes. Their drawings on the page however don't match what they sell. Their description is closer to the truth.
Their pins are for 1.6mm PCBs, while the Batten Allen ones are for 1.0mm PCBs.

For larger packages (more pins), we would need machined pins to emulate PGA packages:
https://www.hitachi-metals.co.jp/e/products/elec/di/p01_58.html

After that, the build process is as usual:

#. Design schematics
#. Lay out PCB
#. Make PCB
#. Assemble PCBA

For a case, I can use 3D printers, at least initially. For keyboards, there's always the option to buy mechanical keys or just make the system accept existing keyboards (mice, joysticks), so I don't even have to bother with them at all.
