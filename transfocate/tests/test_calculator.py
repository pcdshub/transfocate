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
from transfocate.calculator import Calculator
from .conftest import FakeLens


@pytest.fixture(scope='function')
def calculator():
    # Prefocus lenses
    prefocus = [FakeLens(500., 100.0, 50.),
                FakeLens(300., 100.0, 25.)]

    # Define transfocator
    tfs = [FakeLens(500., 275., 25.),
           FakeLens(500., 280., 55.),
           FakeLens(500., 300., 75.),
           FakeLens(200., 310., 10.)]
    # Define Calculator
    return Calculator(xrt_lenses=prefocus, tfs_lenses=tfs)


def test_calculator_combinations(calculator):
    # Fifteen possible transfocator combinations
    # Two possible prefocus lens choices
    assert len(calculator.combinations()) == 30
    assert len(calculator.combinations(include_prefocus=False)) == 15


def test_calculator_find_combinations(calculator):
    # Test with tfs[0] and xrt[0]
    combo = calculator.find_solution(312.5)
    assert combo.nlens == 2
    assert np.isclose(250.0, combo.effective_radius, atol=0.1)
    assert np.isclose(312.5, combo.image(0.0), atol=0.1)

    # Test with xrt[1] and tfs[1,3]
    combo = calculator.find_solution(318.5)
    assert combo.nlens == 3
    assert np.isclose(96.77, combo.effective_radius, atol=0.1)
    assert np.isclose(318.5, combo.image(0.0), atol=0.1)

    # Test with xrt[1] and tfs[1]
    combo = calculator.find_solution(367.9)
    assert combo.nlens == 2
    assert np.isclose(187.5, combo.effective_radius, atol=0.1)
    assert np.isclose(367.9, combo.image(0.0), atol=0.1)

    # Test xrt[1] and tfs[0]
    combo = calculator.find_solution(305.35)
    assert combo.nlens == 2
    assert np.isclose(187.5, combo.effective_radius, atol=0.1)
    assert np.isclose(305.35, combo.image(0.0), atol=0.1)

    # Test xrt[1] and tfs[0,1,2,3]
    combo = calculator.find_solution(356.48, n=5)
    assert combo.nlens == 5
    assert np.isclose(69.76, combo.effective_radius, atol=0.1)
    assert np.isclose(356.48, combo.image(0.0), atol=0.1)
