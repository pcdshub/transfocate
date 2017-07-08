############
# Standard #
############
import logging

###############
# Third Party #
###############
import pytest

##########
# Module #
##########
from transfocate.lens import Lens, LensConnect

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

############
# Fixtures #
############
@pytest.fixture(scope='module')
def lens():
    return Lens(500.0, 100.0, 50.0)

@pytest.fixture(scope='module')
def array():
    first  = Lens(500.0, 100.0, 50.0)
    second = Lens(500.0, 275.0, 25.0)
    return LensConnect(first, second)
