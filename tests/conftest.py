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
import epics
import pytest
##########
# Module #
##########
from .server import launch_server
from transfocate.lens import Lens, LensConnect
from transfocate.calculator import Calculator

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
def lens():
    return Lens("TST:TFS:LENS:01:")

@pytest.fixture(scope='module')
def array():
    first  = FakeLens(500.0, 100.0, 50.0)
    second = FakeLens(500.0, 275.0, 25.0)
    return LensConnect(second, first)

@pytest.fixture(scope='session', autouse=True)
def pyioc():
    #Create full path to server file
    server = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'server.py')
    proc = subprocess.Popen(['python', server])
    yield
    logging.debug("Disconnecting EPICS variables")
    epics.ca.destroy_context()
    logging.debug("Killing Python IOC thread ...")
    proc.kill()


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
