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

def test_calculator_combinations(calculator):
    # Three possible transfocator combinations
    # Two possible prefocus lens choices
    assert len(calculator.combinations()) == 6
    assert len(calculator.combinations(include_prefocus=False)) == 3

def test_calculator_find_combinations(calculator):
    solution = calculator.find_solution(312.5)
    # Assert we found the accurate combination
    assert np.isclose(solution.image(0.0), 312.5, atol=0.1)
