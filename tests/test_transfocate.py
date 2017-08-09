############
# Standard #
############
import logging

###############
# Third Party #
###############
import pytest

##########
# Module #
##########
from .conftest import FakeLens
from transfocate.transfocator import Transfocator
import numpy as np

@pytest.fixture(scope='function')
def transfocator():
    #Prefocus lenses
    prefocus = [FakeLens(500., 100.0, 50.),
                FakeLens(300., 100.0, 25.)]

    #Define transfocator
    tfs = [FakeLens(500., 275., 25.),
           FakeLens(500., 280., 55.),
           FakeLens(500., 300., 75.),
           FakeLens(200., 310., 10.)]

    return Transfocator("TST:TFS:LENS:",
                        xrt_lenses=prefocus,
                        tfs_lenses=tfs)


def test_transfocator_current_focus(transfocator):
    transfocator.xrt_lenses[0].insert()
    transfocator.tfs_lenses[0].insert()
    assert transfocator.current_focus == 312.5
    
    transfocator.tfs_lenses[1].insert()
    assert np.isclose(300.4, transfocator.current_focus, atol=0.1)
    
    transfocator.xrt_lenses[0].remove()
    transfocator.tfs_lenses[2].insert()
    assert np.isclose(295.7, transfocator.current_focus, atol=0.1)
    
    transfocator.xrt_lenses[1].insert()
    transfocator.tfs_lenses[0].remove()
    transfocator.tfs_lenses[2].remove()
    transfocator.tfs_lenses[3].insert()
    assert np.isclose(318.5, transfocator.current_focus, atol=0.1)

    transfocator.tfs_lenses[3].remove()
    assert np.isclose(367.9, transfocator.current_focus, atol=0.1)
   
def test_transfocator_find_best_combo(transfocator):
    assert transfocator.find_best_combo(312.5).nlens==2
    assert np.isclose(250.0, transfocator.find_best_combo(312.5).effective_radius, atol=0.1)
    assert np.isclose(312.5, transfocator.find_best_combo(312.5).image(0.0), atol=0.1)
    
    #assert transfocator.find_best_combo(300.4).nlens==3
    #assert np.isclose(166.667, transfocator.find_best_combo(300.4).effective_radius, atol=0.1)
    assert np.isclose(300.4, transfocator.find_best_combo(300.4).image(0.0), atol=0.1)

def test_transfocator_focus_at(transfocator):
    transfocator.focus_at(312.5)
    assert [lens.inserted for lens in transfocator.xrt_lenses] == [True, False]
    assert [lens.inserted for lens in transfocator.tfs_lenses] == [True, False, False, False]
    
    transfocator.focus_at(300.4)
    assert [lens.inserted for lens in transfocator.xrt_lenses] == [True, False]
    assert [lens.inserted for lens in transfocator.tfs_lenses] == [True, True, True, False]

    transfocator.focus_at(295.7)
    assert [lens.inserted for lens in transfocator.xrt_lenses] == [True, False]
    assert [lens.inserted for lens in transfocator.tfs_lenses] == [True, True, True, False]
    
