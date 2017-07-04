############
# Standard #
############

###############
# Third Party #
###############
import pytest
import numpy as np

##########
# Module #
##########
from transfocate.lens import Lens

def test_lens_properties():
    lens = Lens(500.0, 300.0, 50.0)
    assert np.isclose(500.0, lens.radius, atol=0.1)
    assert np.isclose(300.0, lens.z,      atol=0.1)
    assert np.isclose(50.0,  lens.focus,  atol=0.1)

