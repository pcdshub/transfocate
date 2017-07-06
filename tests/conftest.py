############
# Standard #
############

###############
# Third Party #
###############
import pytest

##########
# Module #
##########
from transfocate.lens import Lens, LensConnect


@pytest.fixture(scope='module')
def lens():
    return Lens(500.0, 100.0, 50.0)


@pytest.fixture(scope='module')
def array():
    first  = Lens(500.0, 100.0, 50.0)
    second = Lens(500.0, 275.0, 25.0)
    return LensConnect(first, second)
