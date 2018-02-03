############
# Standard #
############

###############
# Third Party #
###############
import numpy as np

##########
# Module #
##########
from pcdsdevices.sim.pv import using_fake_epics_pv

@using_fake_epics_pv
def test_lens_properties(lens):
    assert np.isclose(500.0, lens.radius, atol=0.1)
    assert np.isclose(100.0, lens.z,      atol=0.1)
    assert np.isclose(50.0,  lens.focus,  atol=0.1)

@using_fake_epics_pv
def test_image_from_obj(lens):
    #Real image
    assert np.isclose(lens.image_from_obj(0.0),  200.0, atol=0.1)
    #Imaginary image
    lens.state._read_pv.put(0)
    assert lens.inserted == False
    lens.state._read_pv.put(1)
    assert lens.inserted == True

@using_fake_epics_pv
def test_lens_motion(lens):
    lens.insert()
    assert lens.in_signal.value == 1
    lens.remove()
    assert lens.out_signal.value == 1

def test_lens_connect_effective_radius(array):
    assert np.isclose(array.effective_radius, 250, atol=0.1)

def test_lens_connect_image(array):
    assert np.isclose(array.image(0.0),  312.5,   atol=0.1)
    assert np.isclose(array.image(75.0), 303.125, atol=0.1)
    assert np.isclose(array.image(80.0), 303.409, atol=0.1)
    assert np.isclose(array.image(125.0), 304.6875, atol=0.1)

def test_number_of_lenses(array):
    assert array.nlens== 2
