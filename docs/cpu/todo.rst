Todo
====

Toolchain
---------

.. todo:: We'll need to make sure we use sign-extend loads appropriately: apparently Moxie didn't have sign-extend loads

.. todo:: brew.opt needs to be updated to actually generate mfloat and mno-float options.

.. todo:: add floating point instructions (probably for something like fastmath only)

.. todo:: figure out if we really need 'upper' version of multiplies and how to efficiently use them. Right now 64-bit multiplies are borken, I think.

.. todo::
   we probably want to control register allocation order. Some comment from code::

      /* The order in which registers should be allocated.
         It is better to use the registers the caller need not save.
         Allocate r0 through r3 in reverse order since r3 is least likely
         to contain a function parameter; in addition results are returned
         in r0.  It is quite good to use lr since other calls may clobber
         it anyway.  */
      #define REG_ALLOC_ORDER						\

.. todo::
   we should use this::

      CALL_REALLY_USED_REGISTERS instead of CALL_USED_REGISTERS -> that's legacy.

.. todo::
   there's a GCC macro: :code:`__REGISTER_PREFIX__`. If there's a GAS equivalent, maybe we can coerce GAS expression parser to stop at register names? I actually think this is outdated. I have a completely re-written parser at this point which doesn't depend on the demented GAS expression parser. It identifies expression boundaries on its own and calls the GAS parser for only the appropriate segments.

.. todo:: we need a predefined macro for -msoft-float

