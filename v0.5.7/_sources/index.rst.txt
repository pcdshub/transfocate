Transfocate
===========

The Transfocator is a tunable apparatus that focuses X-rays through the
application of compound refractive Beryllium lenses.  Normally, to operate the
Transfocator, users must know the location of lenses within the device and
their information, perform the math necessary to calculate the ideal focal
length, and apply the lenses manually.  This code automates this entire process
and requires only the sample location to calculate the optimal combination of
prefocusing and Transfocator lenses.  Additionally, this code automatically
takes hutch safety limits into account when applying lenses and will not apply
a lens array with an effective radius that is outside the safety limits.

Users will interact with the Transfocator Calculator database through :class:
`.Transfocator` That will handle the information for individual
lenses and systems of lenses, perform operations to find combinations, and
apply appropriate lens systems. Information for the lenses include the radius,
focal length, and z position along the beam and are all EPICS Read Only
signals.  Additionally, all units of length are measured in meters.

Creating a New Transfocator
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The lens arrays in Transfocator will be handled as :class:`.LensConnect` to
provide more functionality. The examples below use a simulated model so the
tutorial does not affect the real Transfocator in MFX.


.. ipython:: python

    import transfocate

    import transfocate.tests

    mfx_transfocator = transfocate.tests.transfocator


Manipulating Lenses
^^^^^^^^^^^^^^^^^^^
All of the lenses are sub-components of the Transfocator object. You can
manipulate them by:

.. ipython:: python

    mfx_transfocator.prefocus_bot.insert()

    mfx_transfocator.tfs_04.insert()

You may also want to set the value of the ``nominal_sample`` this is the
location that we believe the interaction point to be. In practice it varies
based on the location of the sample table and the instrumentation on the table
itself.

.. ipython:: python

    mfx_transfocator.nominal_sample


Finding and Applying Optimal Combination
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
First, you may want to find the current focus of the lenses inserted in the
Transfocator. To do this, use :meth:`.Transfocator.current_focus`

.. ipython:: python

    mfx_transfocator.current_focus


This command will find the difference between the current focus of the
Transfocator and the position we have saved as `nominal_sample`.  This may be
helpful if you want to see which lenses are currently inserted in the beamline
or to make sure that your previous settings have not been tampered with.

To find your optimal array of lenses, use :meth:`.Transfocator.find_best_combo`
and to find and apply your desired array of lenses, use
:meth:`.Transfocator.focus_at`. By default this will try and place the focal
plane to the interaction point, but you can adjust this using the ``target``
keyword. The command also supports all of the keywords to ignore prefocusing
lenses, change the source point, that are present in
:meth:`.Calculator.find_solution`.

.. ipython:: python

    combo = mfx_transfocator.find_best_combo()


.. toctree::
   :maxdepth: 1
   :caption: Contents:
   :hidden:

   lens.rst
   calculator.rst
   transfocator.rst
