###############
# Third Party #
###############
import pytest
##########
# Module #
##########
from transfocate.lens import Lens, LensConnect
from ophyd.sim import make_fake_device

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


SynLens = make_fake_device(Lens)
############
# Fixtures #
############

@pytest.fixture(scope='module')
def lens():
    lens = SynLens("TST:TFS:LENS:01:", name='Lens')
    lens._sig_radius.sim_put(500.0)
    lens._sig_z.sim_put(100.0)
    lens._sig_focus.sim_put(50.0)
    return lens


@pytest.fixture(scope='module')
def lens_array():
    first = SynLens("TST:TFS:LENS:01:", name='Lens 1')
    second = SynLens("TST:TFS:LENS:02:", name='Lens 2')
    third = SynLens("TST:TFS:LENS:03:", name='Lens 3')
    return LensConnect(first, second, third)


@pytest.fixture(scope='module')
def array():
    first = FakeLens(500.0, 100.0, 50.0)
    second = FakeLens(500.0, 275.0, 25.0)
    return LensConnect(second, first)
