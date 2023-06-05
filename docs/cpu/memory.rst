Memories
========

.. _dram::

DRAM
~~~~

.. _dram_datasheets:

Datasheets
----------

DRAM history from:
http://doctord.dyndns.org/Courses/UNH/CS216/Ram-Timeline.pdf:

======    ========
Year      Capacity
======    ========
1970      1kbit
1973      4kbit
1976      16kbit
1978      64kbit
1982      256kbit
1986      1Mbit
1988      4Mbit
1991      16Mbit
1994      64Mbit
1998      256Mbit
======    ========

Some DRAM datasheets:

- `16kx1 <https://www.jameco.com/Jameco/Products/ProdDS/2288023.pdf>`_
- `64kx1 <https://www.jameco.com/Jameco/Products/ProdDS/2290535SAM.pdf>`_
- `64kx4 <https://downloads.reactivemicro.com/Electronics/DRAM/NEC%20D41464%2064k%20x%204bit%20DRAM%20Data%20Sheet.pdf>`_
- `256kx1 <https://pdf1.alldatasheet.com/datasheet-pdf/view/37259/SAMSUNG/KM41256A.html>`_
- `256kx4 <https://pdf1.alldatasheet.com/datasheet-pdf/view/45238/SIEMENS/HYB514256B.html>`_
- `1Mx1 <https://datasheetspdf.com/pdf-file/550187/MicronTechnology/MT4C1024/1>`_
- `1Mx16 <https://www.mouser.com/datasheet/2/198/41lv16105b-1169632.pdf>`_
- `4Mx4 <https://www.digikey.com/htmldatasheets/production/1700164/0/0/1/MSM51V17400F.pdf>`_
- `16Mx1 <https://www.digchip.com/datasheets/parts/datasheet/409/KM41C16000CK-pdf.php>`_

There were two memory module formats: 30 pin and 72 pin.

- `<https://en.wikipedia.org/wiki/SIMM>`_
- `<https://www.pjrc.com/tech/mp3/simm/datasheet.html>`_

EDO datasheets:

- `4/8MB module <https://www.digchip.com/datasheets/download_datasheet.php?id=687767&part-number=MT2D132>`_
- `JEDEC standard extract <https://www.ele.uri.edu/iced/protosys/hardware/datasheets/simm/Jedec-Clearpoint-8MB.pdf>`_
- `16/32MB module <https://www.digchip.com/datasheets/download_datasheet.php?id=987285&part-number=TM893GBK32S>`_
- `Another 16/32MB Module <https://docs.rs-online.com/1faa/0900766b80027c7f.pdf>`_
- `Socket ($0.88 apiece) <https://www.peconnectors.com/sockets-pga-cpu-and-memory/hws8182/>`_


.. _dram_interface_intro::

Interface to DRAM
-----------------

We are absolutely maximizing DRAM bandwidth that's achievable using an 8-bit bus. We are using burst (page-mode) accesses to amortize nRAS and precharge cycle penalty as well as double-pumping the data (transferring data on both clock-edges).

We are using the same bus for non-DRAM accesses, that is to reach ROM memories and peripherals.

.. _dram_timing:

Timing diagrams
---------------

The DRAM bus::

                        <------- 4-beat burst -------------><---- single ----><---- single ----><---------- 4-beat burst ----------><- refresh->
    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\_
    DRAM_nRAS       ^^^^^^^^^\_____________________________/^^^^^\___________/^^^^^\___________/^^^^^\_____________________________/^^^^^\_____/^^^^^^^^^^
    DRAM_nCAS_A     ^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_nCAS_B     ^^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^^^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_ADDR       ---------<==X=====X=====X=====X=====>--------<==X=====>--------<==X=====>--------<==X=====X=====X=====X=====>--------<==>-------------
    DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_DATA       --------------<>-<>-<>-<>-<>-<>-<>-<>-------------<>-<>--------------<>-<>-------------<>-<>-<>-<>-<>-<>-<>-<>------------------------
    DRAM_nWE        ^^^^^^^^^\_____________________________/^^^^^\___________/^^^^^\___________/^^^^^\_____________________________/^^^^^\-----/^^^^^^^^^^
    DRAM_DATA       ------------<==X==X==X==X==X==X==X==>-----------<==X==>-----------<==X==>-----------<==X==X==X==X==X==X==X==>-------------------------
    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\_
    req_valid       ___/^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^\___________/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\_____________________________/^^^^
    req_ready       ^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^\___________/^^^^^\___________/^^^^^^^^^^^^^^^^^^^^^^^\_______________________/^^^^^^^^^^
    req_wr          _________________________________________________________/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    req_addr        ---<=====X=====X=====X=====>-----------<=====>-----------<=====X=================X=====X=====X=====>----------------------------------
    req_data        ---------------------------------------------------------------<=================X=====X=====X=====>----------------------------------
                       |----------------->                 |---------------->|----------------->---------------->
    rsp_valid       _____________________/^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^\___________/^^^^^\____________________________________________________
    rsp_data        ---------------------<=====X=====X=====X=====>-----------<=====>-----------<=====>----------------------------------------------------

Notes:
1. `req_ready` goes low for two cycles after req_last (during a transfer) is asserted. This is to allow for the pre-charge cycle to occur
2. addresses must be consecutive and must not cross page-boundary within a burst. The bus_if doesn't check for this (maybe it should assert???) and blindly puts the address on the DRAM bus. Address incrementing is the responsibility of the requestor (it probably does it anyway).
3. Burst length is not communicated over the interface: the burst ends when `req_valid` is de-asserted.
4. write data is captured with the address on every transaction.
5. Response bus doesn't support a ready signal: responses are always assumed to be accepted
6. writes don't have any response
7. Reads and writes are not allowed to be mixed within a burst. This is - again - not checked by the bus_if.
8. Client arbitration happens only after the idle cycle: i.e. we don't support clients taking over bursts from each other. Also, `req_ready` for any client will normally be low and only gets asserted by the interface, when arbitration is successful. Requestors should not hold back or depend on `req_ready` for generating requests.
9.  The bus controller can terminate a burst by de-asserting `req_ready`. This doesn't happen for DRAM transactions, but is the case for non-DRAM accesses, as shown later
10. The above timing only works for page-mode memories. Fast-page-mode memories support much faster access times, but need slightly different timing.
11. DRAM devices have pretty lengthy hold times on the data after the rising edge of `DRAM_nCAS_x`. So long in fact, that the two banks may fight for the bus in the center of the nCAS cycle. Probably the easiest solution is to have a set of series resistors with the data pins. That impacts rise and fall times though, so one should be careful.


Non-DRAM accesses::

                             <-- even read ---><--- odd write ---><- even read w. wait -->
    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/
    nNREN           ^^^^^^^^^\___________/^^^^^\___________/^^^^^\_________________/^^^^^^
    DRAM_nCAS_0     ^^^^^^^^^^^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\___________/^^^^^^
    DRAM_nCAS_1     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\_____/^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_ADDR       ---------<==X========>-----<==X========>-----<==X==============>------
    DRAM_nWE        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    DRAM_DATA       ---------------------<>----------------<>----------------------<>-----
    DRAM_nWE        ^^^^^^^^^\___________/^^^^^\___________/^^^^^\_________________/^^^^^^
    DRAM_DATA       ------------<========>-----------<=====>--------<==============>------
    nWAIT           ---------------/^^^^^\-----------/^^^^^\-----------\_____/^^^^^\------
    CLK             \__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/^^\__/
    req_valid       ___/^^^^^\_____/^^^^^^^^^^^\___________/^^^^^\________________________
    req_ready       ^^^^^^^^^\___________/^^^^^\___________/^^^^^\_________________/^^^^^^
    req_last        ___/^^^^^\___________/^^^^^\___________/^^^^^\________________________
    req_wr          _______________/^^^^^^^^^^^\__________________________________________
    req_addr        ---<=====>-----<===========>-----------<=====>------------------------
    req_data        ---------------<===========>------------------------------------------
                       |----------------->                 |----------------------->
    rsp_valid       _____________________/^^^^^\___________________________________/^^^^^\
    rsp_ready       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    rsp_data        ---------------------<=====>-----------------------------------<=====>

1. Bursts are not allowed; the interface de-asserts `req_ready` after every transfer.
2. Only 8-bit transfers are allowed - bus_if will break up 16-bit transfers into two individual transfers.
3. LSB address can be recovered by using DRAM_nCAS_0 as A0
4. nWAIT is sampled on the rising edge of every cycle, after internal wait-states are accounted for
5. There is at least one internal wait-state
6. For writes, the relevant byte of 'req_data' should be valid.

.. note:: These timings don't really support external devices with non-0 data hold-time requirements. Maybe we can delay turning off data-bus drivers by half a cycle?


FPM DRAMs support a slightly different timing. The first diagram below shows the simplified diagram for an NMOS memory::

     CLK __/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/
    nRAS ^^^^^^^^\_______________________________________________/^^^^^\
    nCAS ^^^^^^^^^^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^\_____/^^^^^^
    nWE  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    Data -------------------<>----------<>----------<>----------<>------

The second diagram shows the same for an FPM device::

     CLK __/^^\__/^^\__/^^\__/^^\__/^^\__/^^\
    nRAS ^^^^^\__________________________/^^\
    nCAS ^^^^^^^^^^^\__/^^\__/^^\__/^^\__/^^^
    nWE  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    Data -------------<>----<>----<>----<>---

Notice how we need to delay nCAS by half a cycle because while t_cas is much shorter, t_rcd doesn't change all that much.


.. _dram_speeds:

DRAM speeds
-----------

There are four important timing parameters for DRAM timing:

.. figure:: dram-timing.png
   :alt: DRAM timing

The earliest devices we potentially care about are 256kbit NMOS parts:

=========== ===== ===== ===== ===== ===== =====
Part number       uPD41464         KM41256
----------- ----------------- -----------------
Speed grade  -80   -10   -12   -10   -12   -15
=========== ===== ===== ===== ===== ===== =====
t_rcd        40ns  50ns  60ns  50ns  60ns  75ns
t_cas        40ns  50ns  60ns  50ns  60ns  75ns
t_cp         30ns  40ns  50ns  45ns  50ns  60ns
t_rp         70ns  90ns  90ns  90ns 100ns 100ns
=========== ===== ===== ===== ===== ===== =====

Fast-page-mode devices, such as the one used in late-issue Amiga A500 boards have significantly improved timing:

=========== ===== ===== ===== ===== ===== =====
Part number     HYB514256B         MT4C1024
----------- ----------------- -----------------
Speed grade  -50   -60   -70   -6    -7    -8
=========== ===== ===== ===== ===== ===== =====
t_rcd        35ns  45ns  50ns  40ns  50ns  60ns
t_cas        15ns  15ns  20ns  20ns  20ns  20ns
t_cp         10ns  10ns  10ns  10ns  10ns  10ns
t_rp         35ns  40ns  50ns  40ns  50ns  60ns
=========== ===== ===== ===== ===== ===== =====

=========== ====== ====== ====== ======
Part number  KM41C16000C  IS41LV16105B
----------- ------------- -------------
Speed grade   -5     -6     -50    -60
=========== ====== ====== ====== ======
t_rcd        37ns   45ns   37ns   45ns
t_cas        13ns   15ns    8ns   10ns
t_cp         10ns   10ns    9ns    9ns
t_rp         35ns   40ns   30ns   40ns
=========== ====== ====== ====== ======

EDO, when introduced in '95 was even faster. We are going to concentrate on NMOS devices and their timing characteristics for the first-generation processor to remain true to the times we pretend it was to be released. Newer devices will work with those timings as well, but you can't take advantage of their special modes.

Since we snap timings to half-clock-cycle boundaries, the bus (and thus CPU) clock rates we can support are as follows:

=========== ========= ========= ========= ========= ========= =========
Part number           uPD41464                       KM41256
----------- ----------------------------- -----------------------------
Speed grade  -80       -10       -12       -10       -12       -15
=========== ========= ========= ========= ========= ========= =========
t_rcd        40ns      50ns       60ns     50ns      60ns      75ns
t_cas        40ns      50ns       60ns     50ns      60ns      75ns
t_cp         30ns      40ns       50ns     45ns      50ns      60ns
t_rp         70ns      90ns       90ns     90ns     100ns     100ns
f_cpu        12.5Mhz   10Mhz      8.3MHz   10Mhz     8.3MHz    6.6MHz
=========== ========= ========= ========= ========= ========= =========

.. _dram_banks::

Number of address lines and banks needed
========================================

Since, I don't think we could either afford or drive more than 32 memory chips on the bus, with up to 4 banks we could support the following memory sizes:

1-bit chips:

====== ======== ========= ======================= ================= =============== ============ ===================
Year   Capacity Word size Number of address lines Capacity per bank Number of banks Max capacity Number of RAM chips
====== ======== ========= ======================= ================= =============== ============ ===================
1978   64kbit   1         8                       128kByte          1               128kByte     16
1978   64kbit   1         8                       128kByte          2               256kByte     32*
1982   256kbit  1         9                       512kByte          1               512kByte     16
1982   256kbit  1         9                       512kByte          2               1MByte       32*
1986   1Mbit    1         10                      2MByte            1               2MByte       16
1986   1Mbit    1         10                      2MByte            2               4MByte       32*
1988   4Mbit    1         11                      8MByte            1               8MByte       16
1988   4Mbit    1         11                      8MByte            2               16MByte      32*
====== ======== ========= ======================= ================= =============== ============ ===================

4-bit chips:

====== ======== ========= ======================= ================= =============== ============ ===================
Year   Capacity Word size Number of address lines Capacity per bank Number of banks Max capacity Number of RAM chips
====== ======== ========= ======================= ================= =============== ============ ===================
1982   256kbit  4         8                       128kByte          1               128kByte     4
1982   256kbit  4         8                       128kByte          2               256kByte     8
1982   256kbit  4         8                       128kByte          4               512kByte     16
1986   1Mbit    4         9                       512kByte          1               512kByte     4
1986   1Mbit    4         9                       512kByte          2               1MByte       8
1988   4Mbit    4         10                      2MByte            1               1MByte       4
1986   1Mbit    4         9                       512kByte          4               2MByte       16
1988   4Mbit    4         10                      2MByte            2               4MByte       8
1991   16Mbit   4         11                      8MByte            1               8MByte       4
1991   16Mbit   4         11                      8MByte            2               16MByte      8
====== ======== ========= ======================= ================= =============== ============ ===================

Here we assume that we can't have 4 banks of the larger chips since we mux the address lines with the bank-selects.

This shows that at our introduction year ('84) we should have been able to support 0.5M in 4-bit configs and 1M in 1-bit configs.

For modern systems though, (where we have access to all the DRAM sizes) we should probably go with only supporting 4-bit variants as those can also span the full supported ranges.

4-banks work especially well with EDO-style 72-pin SIMM memories. The 2-bank versions would only be able to use one side of the SIMM, so dual-sided SIMMs would only work at half capacity. We should only need a single memory socket, where a 32MByte double-sided module would get us the full 16MByte capacity.


.. _eeprom::

EPROM
~~~~~

Timeline (from https://en.wikipedia.org/wiki/EPROM):

======    ========
Year      Capacity
======    ========
1975      2704
1975      2708
1977      2716
1979      2732
1981      2764 (https://timeline.intel.com/1981/a-new-era-for-eprom)
1982      27128 (https://timeline.intel.com/1982/the-eprom-evolution-continues)
?         27256
?         27512
1986      27010 (https://timeline.intel.com/1986/one-megabit-eprom)
======    ========

Interface
---------

To get to the EPROM, we would need to latch the first address cycle, and only enable nOE and nCE on the second address cycle, when the full address is available. We can use the first address cycle for some pre-decoding though.

.. _eeprom_timing:

Timing
------

Here's a typical datasheet: https://datasheet.octopart.com/D27256-2-Intel-datasheet-17852618.pdf

Access times are 250ns, though there are several speed-grades available.

By '91, CMOS EPROMs were available with access times roughly half of that: 120ns was the highest speed-grade.

At that time same-capacity (and speed) FLASH parts started to appear too - not 5V programmable parts though. They required ~10ns hold-times on data (relative to the rising edge of nWE), which is something that DRAMs didn't have.

To work with these slow devices, several wait-states need to be inserted (3 minimum). Below are single-beat accesses, but bursts work just as well since timing is solely derived from nCAS.
