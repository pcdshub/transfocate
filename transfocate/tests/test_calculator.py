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
from .conftest import FakeLens
from transfocate.lens       import Lens
from transfocate.calculator import TransfocatorCombo


def test_calculator_combinations(calculator):
    #Eight possible transfocator combinations
    #Three possible prefocus lens choices
    assert len(calculator.combinations) == 8

def test_calculator_find_combinations(calculator):
    solutions = calculator.find_combinations(312.5, num_sol=1)
    #Assert we found the accurate combination
    assert np.isclose(solutions[0].image(0.0), 312.5, atol=0.1)

def test_transfocator_combo():
    #Define xrt and tfs lists
    xrt=FakeLens(300.0, 100., 25.)
    tfs=[FakeLens(500., 275., 25.),
         FakeLens(500., 280., 55.)]
    #Define TransfocatorCombo
    test_combo=TransfocatorCombo(xrt, tfs)
    assert np.isclose(test_combo.image(200.0), 297.18, atol=0.1)
