############
# Standard #
############
import os
import subprocess
from collections import namedtuple
###############
# Third Party #
###############
import pytest
##########
# Module #
##########
from transfocate.lens import Lens, LensConnect
from transfocate.calculator import Calculator
from pcdsdevices.sim.pv import using_fake_epics_pv


################
# Mock Classes #
################
class FakeLens(object):

    image_from_obj = Lens.image_from_obj

    def __init__(self, radius, z, focus):
        self.radius = radius
        self.z = z
        self.focus = focus
        self.inserted = False

    def insert(self):
        self.inserted = True

    def remove(self):
        self.inserted = False


############
# Fixtures #
############

@pytest.fixture(scope='module')
@using_fake_epics_pv
def lens():
    l =  Lens("TST:TFS:LENS:01:", name='Lens')
    l._sig_radius._read_pv.put(500.0)
    l._sig_z._read_pv.put(100.0)
    l._sig_focus._read_pv.put(50.0)
    return l

@pytest.fixture(scope='module')
@using_fake_epics_pv
def lens_array():
    first = Lens("TST:TFS:LENS:01:", name='Lens 1')
    second = Lens("TST:TFS:LENS:02:", name='Lens 2')
    third = Lens("TST:TFS:LENS:03:", name='Lens 3')
    return LensConnect(first, second, third)


@pytest.fixture(scope='module')
def array():
    first  = FakeLens(500.0, 100.0, 50.0)
    second = FakeLens(500.0, 275.0, 25.0)
    return LensConnect(second, first)
