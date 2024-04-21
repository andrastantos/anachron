External bus timing
===================

DRAM access timing
------------------

The bus support DDR accesses to DRAM. The first half of a clock-cycle, lower byte, the second half of the clock cycle the upper byte is accessed. Long bursts within a 512-byte page are supported by keeping `n_ras_a/b` low while toggling `n_cas_0/1`. At either end of the burst, some overhead (one cycle each) needs to be paid to return the bus to it's idle state and allow for the DRAM chip to meet pre-charge timing.

.. wavedrom::

    {
        head:{
            text:'8-byte burst DRAM access cycle',
        },
        signal: [
            {name: 'clk',       wave: 'p......', period: 2},
            {name: 'n_ras_a/b', wave: '1.0.........1.'},
            {name: 'n_nren',    wave: '1.............'},
            {name: 'n_cas_0',   wave: '1..01010101...'},
            {name: 'n_cas_1',   wave: '1...01010101..'},
            {name: 'a[10:0]',   wave: 'x.==.=.=.=.x..', data: ['row', 'col0', 'col1', 'col2', 'col3']},
            ["read",
            {name: 'n_we',      wave: 'x.1.........x.'},
            {name: 'd[7:0]',    wave: 'x...23456789x.', phase: 0.3, data: ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7']},
            ],
            ["write",
            {name: 'n_we',      wave: 'x.0.........x.'},
            {name: 'd[7:0]',    wave: 'x..23456789x..', data: ['w0', 'w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7']},
            ],
        ],
    }

.. wavedrom::

    {
        head:{
            text:'Two back-to-back 2-byte burst DRAM access cycles',
        },
        signal: [
            {name: 'clk',       wave: 'p......', period: 2},
            {name: 'n_ras_a/b', wave: '1.0...1.0...1.'},
            {name: 'n_nren',    wave: '1.............'},
            {name: 'n_cas_0',   wave: '1..01....01...'},
            {name: 'n_cas_1',   wave: '1...01....01..'},
            {name: 'a[10:0]',   wave: 'x.==.x..==.x..', data: ['row0', 'col0', 'row1', 'col1']},
            ["read",
            {name: 'n_we',      wave: 'x.1...x.1...x.'},
            {name: 'd[7:0]',    wave: 'x...23x...45x.', phase: 0.3, data: ['r0', 'r1', 'r2', 'r3']},
            ],
            ["write",
            {name: 'n_we',      wave: 'x.0...x.0...x.'},
            {name: 'd[7:0]',    wave: 'x..23x...45x..', data: ['w0', 'w1', 'w2', 'w3']},
            ],
        ],
    }

.. wavedrom::

    {
        head:{
            text:'DRAM refresh cycle',
        },
        signal: [
            {name: 'clk',       wave: 'p..', period: 2},
            {name: 'n_ras_a',   wave: '1.0.1.'},
            {name: 'n_ras_b',   wave: '1.0.1.'},
            {name: 'n_nren',    wave: '1.....'},
            {name: 'n_cas_0',   wave: '1.....'},
            {name: 'n_cas_1',   wave: '1.....'},
            {name: 'a[10:0]',   wave: 'x.=.x.', data: ['row']},
            {name: 'n_we',      wave: 'x.1.x.'},
            {name: 'd[7:0]',    wave: 'x.....'},
        ]
    }

.. note:: Refresh cycles assert both n_ras_a and n_ras_b at the same time. Other cycles assert either of the two, but not both.

.. note:: These timing diagrams aren't really compatible with fast-page-mode memories. The more precise way of saying this is that these timings don't allow us to take advantage of FPM access cycles. We would need to delay both `n_cas_0/1` signals by half a clock-cycle to make FPM work. That would probably result in an extra clock cycle of latency on reads. It would however allow us to double the clock speed.

Non-DRAM access timing
----------------------

For non-DRAM accesses, the waveforms are different in several ways:

1. No bursts are supported
2. Select signals are slowed down
3. External and internal wait-states can be inserted

.. wavedrom::

    {
        head:{
            text:'Back-to-back non-DRAM cycles to even and odd addresses; no wait states',
        },
        signal: [
            {name: 'clk',       wave: 'p......', period: 2},
            {name: 'n_ras_a/b', wave: '1.............'},
            {name: 'n_nren',    wave: '1.0...1.0...1.'},
            {name: 'n_cas_0',   wave: '1...0.1.......'},
            {name: 'n_cas_1',   wave: '1.........0.1.'},
            {name: 'a[10:0]',   wave: 'x.==...x==...x', data: ['row0', 'col0', 'row1', 'col1']},
            ["read",
            {name: 'n_we',      wave: 'x.1....x1....x'},
            {name: 'd[7:0]',    wave: 'x.....2x....3x', phase: 0.3, data: ['r0', 'r1']},
            ],
            ["write",
            {name: 'n_we',      wave: 'x.0....x0....x'},
            {name: 'd[7:0]',    wave: 'x..2...x.3...x', data: ['w0', 'w1']},
            ],
            {name: 'n_wait',    wave: 'x...1.x...1.x.'}
        ],
    }

.. wavedrom::

    {
        head:{
            text:'non-DRAM cycle; 2 internal wait states',
        },
        signal: [
            {name: 'clk',       wave: 'p.....', period: 2},
            {name: 'n_ras_a/b', wave: '1...........'},
            {name: 'n_nren',    wave: '1.0.......1.'},
            {name: 'n_cas_0/1', wave: '1...0.....1.'},
            {name: 'a[10:0]',   wave: 'x.==.......x', data: ['row', 'col']},
            ["read",
            {name: 'n_we',      wave: 'x.1........x'},
            {name: 'd[7:0]',    wave: 'x.........2x', phase: 0.3, data: ['r']},
            ],
            ["write",
            {name: 'n_we',      wave: 'x.0........x'},
            {name: 'd[7:0]',    wave: 'x..2.......x', data: ['w']},
            ],
            {name: 'n_wait',    wave: 'x.......1.x.'}
        ],
    }

.. wavedrom::

    {
        head:{
            text:'non-DRAM cycle; 1 internal, 1 external wait states',
        },
        signal: [
            {name: 'clk',       wave: 'p.....', period: 2},
            {name: 'n_ras_a/b', wave: '1...........'},
            {name: 'n_nren',    wave: '1.0.......1.'},
            {name: 'n_cas_0/1', wave: '1...0.....1.'},
            {name: 'a[10:0]',   wave: 'x.==.......x', data: ['row', 'col']},
            ["read",
            {name: 'n_we',      wave: 'x.1........x'},
            {name: 'd[7:0]',    wave: 'x.........2x', phase: 0.3, data: ['r']},
            ],
            ["write",
            {name: 'n_we',      wave: 'x.0........x'},
            {name: 'd[7:0]',    wave: 'x..2.......x', data: ['w']},
            ],
            {name: 'n_wait',    wave: 'x.....0.1.x.'}
        ],
    }

.. note:: These timings don't really support external devices with non-0 data hold-time requirements. Maybe we can delay turning off data-bus drivers by half a cycle?

DMA access timing
-----------------

DMA accesses follow the timing of non-DRAM accesses, but select DRAM instead of non-DRAM devices as their targets. Just like non-DRAM accesses, only non-burst, 8-bit accesses are supported.

.. TODO:: These timings are incorrect! n_cas needs to be delayed until data is ready on the data-bus, as it gets latched in the falling edge. This probably means that n_cas will have to go down for the last half-cycle of the DMA, after n_wait is sampled high.

.. wavedrom::

    {
        head:{
            text:'DMA cycle; 1 internal, 1 external wait states, active high request',
        },
        signal: [
            {name: 'clk',       wave: 'p.......', period: 2},
            {name: 'n_ras_a/b', wave: 'x..|1.0.......1.'},
            {name: 'n_nren',    wave: 'x..|1...........'},
            {name: 'n_cas_0/1', wave: 'x..|1...0.....1.'},
            {name: 'a[10:0]',   wave: 'x..|..==.......x', data: ['row', 'col']},
            {name: 'n_we',      wave: 'x..|..=........x'},
            {name: 'd[7:0]',    wave: 'x..|..z........x'},
            {name: 'n_wait',    wave: 'x..|......0.1.x.'},
            ["DMA signals",
            {name: 'dreq_X',    wave: 'x.1|..=.........'},
            {name: 'n_dack_X',  wave: '1..|..0.......1.'},
            {name: 'tc',        wave: 'x..|..=.......x.'},
            ]
        ],
    }

.. wavedrom::

    {
        head:{
            text:'DMA cycle; no wait states, active high request',
        },
        signal: [
            {name: 'clk',       wave: 'p.....', period: 2},
            {name: 'n_ras_a/b', wave: 'x..|1.0...1.'},
            {name: 'n_nren',    wave: 'x..|1.......'},
            {name: 'n_cas_0/1', wave: 'x..|1...0.1.'},
            {name: 'a[10:0]',   wave: 'x..|..==...x', data: ['row', 'col']},
            {name: 'n_we',      wave: 'x..|..=....x'},
            {name: 'd[7:0]',    wave: 'x..|..z....x'},
            {name: 'n_wait',    wave: 'x..|....1.x.'},
            ["DMA signals",
            {name: 'dreq_X',    wave: 'x1.|..=.....'},
            {name: 'n_dack_X',  wave: '1..|..0...1.'},
            {name: 'tc',        wave: 'x..|..=...x.'},
            ]
        ],
    }

.. wavedrom::

    {
        head:{
            text:'Bus master request-grant cycle, active high request',
        },
        signal: [
            {name: 'clk',       wave: 'p......', period: 2},
            {name: 'n_ras_a/b', wave: 'x..|1.z|..1.x.'},
            {name: 'n_nren',    wave: 'x..|1.z|..1.x.'},
            {name: 'n_cas_0/1', wave: 'x..|1.z|..1.x.'},
            {name: 'a[10:0]',   wave: 'x..|..z|..x...'},
            {name: 'n_we',      wave: 'x..|..z|..x...'},
            {name: 'd[7:0]',    wave: 'x..|..z|..x...'},
            {name: 'n_wait',    wave: 'x..|...|......'},
            ["DMA signals",
            {name: 'dreq_X',    wave: 'x1.|...|0.....'},
            {name: 'n_dack_X',  wave: '1..|..0|..1...'},
            {name: 'tc',        wave: 'x..|...|......'},
            ]
        ],
    }

