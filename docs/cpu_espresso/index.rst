.. Espresso Processor documentation master file, created by
   sphinx-quickstart on Thu Dec  8 13:25:35 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Espresso Processor
======================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction
   uarch
   exceptions
   address_translation
   boot
   dma
   event_counters
   memory
   clock
   pinout
   external_bus_timing
   csr_summary
   unimplemented_features
   dram_history
   eprom_history
   roadmap
   software
   synthesis_results
   todo
   debug_sessions/index

Todos
=====

.. todolist::


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Change requests
===============

1. Need to add in support for nWAIT handshake with Disco (including for refresh and DMA cycles)
2. Need to add ability to 'queue' refreshes in case they're held up by arbitration.
3. I think I want push/pull instructions for fast context switches

