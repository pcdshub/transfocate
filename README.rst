transfocate
===========
.. image:: https://travis-ci.org/pcdshub/transfocate.svg?branch=master
    :target: https://travis-ci.org/pcdshub/transfocate

* ophyd Devices for transfocator access in hutch-python
* Automated calculation of beryllium lens focusing optics for MFX Transfocator
* Automated checkout tools for verifying PLC interlock status
* Report generation for the latter

Note about RP
-------------

This module is not under Radiation Protection's defined scope for items which require
a permit to complete.

Note about the IOC
------------------

ioc-mfx-tfs-lens holds some important state for this ophyd support and calculations to work properly.
If you experience zero division exceptions when performing calculations, chances are that the IOC
has some invalid values stored.

Automated Checkout tools
=========================

These scripts use the IOC-defined bypass tools, meaning that no lenses will be
moved and photon energy does _not_ need to change.

** Do not run these scripts without permission from MFX. **

Performing a checkout
---------------------

First, load an IPython session with this module:

.. code-block:: bash

    $ source /reg/g/pcds/pyps/conda/pcds_conda
    $ ipython -i -m transfocate.automated_checkout

If the above times out, re-run the script.  It's ophyd related and will be
resolved eventually.  Otherwise, continue on.

Manual mode
-----------

To perform a scan for a single XRT lens, use:

.. code-block:: python

    >>> sweep_and_plot_xrt(xrt_lens, num_steps=100)

This will choose different combinations of TFS lenses to span the region, and
scan energy in 100 discrete steps.
To perform a scan for _all_ XRT lenses, use:

.. code-block:: python

    >>> sweep_and_plot_xrt_all(num_steps=100)

Per-lens data and plots will be saved to Excel and PNG/PDF files, respectively.
This can be combined into a full checkout report with the following:

.. code-block:: python

    >>> generate_report()

Automatic mode
---------------------

Automatic mode will perform ``sweep_and_plot_xrt_all()`` and
``generate_report()`` for you.

Report generation
---------------------

Report generation will use the files generated from the scan steps above.
It will only use existing files from the current directory.
It can be used on its own - after exiting the IPython session and reloading
it - without scanning again.

Now, you'll have the option to perform the steps automatically or manually.

Authors
=======

Teddy Rendahl, Taryn Imamura, Ken Lauer, and anyone else listed in `git blame`.
