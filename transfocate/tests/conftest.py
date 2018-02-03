############
# Standard #
############
import os
import logging
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


#################
# Logging Setup #
#################
#Enable the logging level to be set from the command line
def pytest_addoption(parser):
    parser.addoption("--log", action="store", default="INFO",
                     help="Set the level of the log")
    parser.addoption("--logfile", action="store", default=None,
                     help="Write the log output to specified file path")

#Create a fixture to automatically instantiate logging setup
@pytest.fixture(scope='session', autouse=True)
def set_level(pytestconfig):
    #Read user input logging level
    log_level = getattr(logging, pytestconfig.getoption('--log'), None)

    #Report invalid logging level
    if not isinstance(log_level, int):
        raise ValueError("Invalid log level : {}".format(log_level))

    #Create basic configuration
    logging.basicConfig(level=log_level,
                        filename=pytestconfig.getoption('--logfile'))

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
    l.sig_radius._read_pv.put(500.0)
    l.sig_z._read_pv.put(100.0)
    l.sig_focus._read_pv.put(50.0)
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


@pytest.fixture(scope='module')
def calculator():
    #Define prefocus lenses
    prefocus = [FakeLens(500., 100.0, 50.),
                FakeLens(300., 100.0, 25.)]
    #Define transfocator
    tfs = [FakeLens(500., 275., 25.),
           FakeLens(500., 280., 55.)]
    #Define Calculator
    return Calculator(xrt_lenses = prefocus,
                      tfs_lenses = tfs,
                      xrt_limit  = 400,
                      tfs_limit  = 750)
