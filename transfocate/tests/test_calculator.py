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


def test_calculator_combinations(calculator):
    #Eight possible transfocator combinations
    #Three possible prefocus lens choices
    assert len(calculator.combinations) == 8

def test_calculator_find_combinations(calculator):
    solutions = calculator.find_combinations(312.5)
    #Assert we found the accurate combination
    assert np.isclose(solutions[0].image(0.0), 312.5, atol=0.1)
