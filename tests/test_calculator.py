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
    prefocus = [Lens(500., 125.0, 100.),
                Lens(500., 145.0, 200.)]
    #Define transfocator
    tfs = [Lens(500., 100., 50.),
           Lens(500., 275., 25.)]
    #Define Calculator
    return Calculator(xrt_lenses = prefocus,
                      tfs_lenses = tfs,
                      xrt_limit  = 75,
                      tfs_limit  = 18)

def test_calculator_combinations(calculator):
    #Eight possible transfocator combinations
    #Three possible prefocus lens choices
    assert len(calculator.combinations) == 24

def test_calculator_find_combinations(calculator):
    solutions = calculator.find_combinations(312.5, num_sol=1)
    #Assert we found the accurate combination
    assert np.isclose(solutions[0].image(0.0), 312.5, atol=0.1)
