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
from transfocate.lens       import Lens
from transfocate.calculator import Calculator

@pytest.fixture(scope='module')
def calculator():
    #Define prefocus lenses
    prefocus = [Lens(300, 100, 100),
                Lens(200, 100, 50)]
    #Define transfocator
    tfs = [Lens(300, 200, 25),
           Lens(200, 100, 20)]
    #Define Calculator
    return Calculator(xrt_lenses = prefocus,
                      tfs_lenses = tfs,
                      xrt_limit  = 75,
                      tfs_limit  = 18)


def test_calculator_combinations(calculator):
    #Eight possible transfocator combinations
    #Three possible prefocus lens choices
    assert len(calculator.combinations) == 24
