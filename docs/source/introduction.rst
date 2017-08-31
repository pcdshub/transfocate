.. _introduction_label:

Introduction
************
In the MFX experimentation hutch, the Transfocator is a tunable apparatus that
focuses X-rays through the application of compound refractive Beryllium lenses.
Normally, to operate the Transfocator, users must know the location of lenses
within the device and their information, perform the math necessary to
calculate the ideal focal length, and apply the lenses manually.  This code
automates this entire process and requires only the sample location to
calculate the optimal combniation of xrt and tfs lenses.  Additionally, this
code automatically takes hutch safety limits into account when applying lenses
and will not apply a lens array with a an effective radius that is outside the
safety limits.

Users will interact with the Transfocator Calculator database through :class:
`transfocate.Transfocator` That will handle the information for individual
lenses and systems of lenses, perform operations to find combinations, and
apply appropriate lens systems. Information for the lenses include the radius,
focal length, and z position along the beam and are all EPICS Read Only
signals.  Additionally, all units of length are measured in meters.

Creating a New Transfocator
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The lens arrays in Transfocator will be handled as :class:`.LensConnect` to provide
more functionality. The examples below use a simulation called ``transfocaotr``
from the testsso the tutorial does not affect the real Transfocator in MFX.


.. ipython:: python
    
    import transfocate 
    
    import transfocate.tests
    


    mfx_transfocator=transfocate.tests.transfocator()



Finding and Applying Optimal Combination
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Although the functions opperate separately in `transfocate.Transfocator`, only
one function has to be called to both calculate the optimal combination of xrt
and tfs lenses to match a target image and apply those lenses in the beamline.

First, you may want to fing the current focus of the lenses inserted in the
Transfocator. To do this, use :meth:`.Transfocator.current_focus`

.. ipython:: python

    mfx_transfocator.current_focus


This command will find the current focus of the Transfocator.  This may be
helpful if you want to see which lenses are currently inserted in the beamline
or to make sure that your previous settings have not been tampered with.  

To find your optimal array of lenses, use :meth:`.Transfocator.find_best_combo` and to find and apply your desired array of lenses, use :meth:`.Transfocator.focus_at`.

.. ipython:: python

    combo=mfx_transfocator.find_best_combo(312.5, 0.0)

    mfx_transfocator.focus_at(312.5, 0.0)


As entered, this command will return all possible combinations of the lenses
whose focal length will be 300.4 and whose length is 3 lenses or less and whose
image object distance is 0 meters.  Unless altered in this step, the onject
will always be set to 0.0 and the max number of tfs lenses will be 4. Remember
we assume there will always be 1 prefocus lens, so this amounts to a ax total
of 5 lenses which is ideally, the most that will ever be required.
After finding the optimal lens combination, this command will automatically
trigger EPICS signals to insert and remove the appropriate lenses.

Note: To find information on the lens array, you must use
:meth:`.Transfocator.find_best_combo` because this method returns a LensConnect
type.

Accessing Lens Information
^^^^^^^^^^^^^^^^^^^^^^^^^^
After you have found your optimal combination, you may want to get access to
some of the lens information. Because the arrays are saved as
:class:`.LensConnect`, this information and several operations are easily
accessible.  

When handleing the lens arrays, you may want to see a readout of the properties
of each lens in the array.  To view a readout of information for each lens, use
:meth:`.LensConnect.show_info`

.. ipython:: python

    combo.show_info()


This command will print the radius, z position, and focus of each lens.

Additionally, you amy want to find the number of lenses in your array.  To do
this, use :meth:`.LensConnect.nlens`

.. ipython:: python
    
    combo.nlens

This command will return and print the number of lenses currently in the array

Finally, you may want to see the effective radius of your array to see how it
sits within hutch safety limits.  To do this, use
:meth:`.LensConnect.effective_radius`

.. ipython:: python

    combo.effective_radius
