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
    #test with tfs[0] and xrt[0]
    transfocator.xrt_lenses[0].insert()
    transfocator.tfs_lenses[0].insert()
    assert transfocator.current_focus == 312.5
    
    #test with xrt[0] and tfs[0,1]
    transfocator.tfs_lenses[1].insert()
    assert np.isclose(300.4, transfocator.current_focus, atol=0.1)
    
    #test with no xrt and tfs[0,1,2]
    transfocator.xrt_lenses[0].remove()
    transfocator.tfs_lenses[2].insert()
    assert np.isclose(295.7, transfocator.current_focus, atol=0.1)
    
    #test with xrt[1] and tfs[1,3]
    transfocator.xrt_lenses[1].insert()
    transfocator.tfs_lenses[0].remove()
    transfocator.tfs_lenses[2].remove()
    transfocator.tfs_lenses[3].insert()
    assert np.isclose(318.5, transfocator.current_focus, atol=0.1)
    
    #test with xrt[1] and tfs[1] 
    transfocator.tfs_lenses[3].remove()
    assert np.isclose(367.9, transfocator.current_focus, atol=0.1)
    
    #test xrt[1] and tfs[0]
    transfocator.tfs_lenses[1].remove()
    transfocator.tfs_lenses[0].insert()
    assert np.isclose(305.35, transfocator.current_focus, atol=0.1)
    
    #test xrt[1] and tfs[0,1,2,3]
    transfocator.tfs_lenses[1].insert()
    transfocator.tfs_lenses[2].insert()
    transfocator.tfs_lenses[3].insert()
    assert np.isclose(356.48, transfocator.current_focus, atol=0.1)

def test_transfocator_find_best_combo(transfocator):
    #test with tfs[0] and xrt[0]
    assert transfocator.find_best_combo(312.5).nlens==2
    assert np.isclose(250.0, transfocator.find_best_combo(312.5).effective_radius, atol=0.1)
    assert np.isclose(312.5, transfocator.find_best_combo(312.5).image(0.0), atol=0.1)
    
    #test with xrt[0] and tfs[0,1]
    assert transfocator.find_best_combo(300.4, 2).nlens==3
    assert np.isclose(166.667, transfocator.find_best_combo(300.4, 2).effective_radius, atol=0.1)
    assert np.isclose(300.4, transfocator.find_best_combo(300.4, 2).image(0.0), atol=0.1)
    
    #test with xrt[1] and tfs[1,3]
    assert transfocator.find_best_combo(318.5).nlens==3
    assert np.isclose(96.77, transfocator.find_best_combo(318.5).effective_radius, atol=0.1)
    assert np.isclose(318.5, transfocator.find_best_combo(318.5).image(0.0), atol=0.1)
    
    #test with xrt[1] and tfs[1]
    assert transfocator.find_best_combo(367.9).nlens==2
    assert np.isclose(187.5, transfocator.find_best_combo(367.9).effective_radius,atol=0.1)
    assert np.isclose(367.9, transfocator.find_best_combo(367.9).image(0.0),atol=0.1)
    

    #test xrt[1] and tfs[0]
    assert transfocator.find_best_combo(305.35).nlens==2
    assert np.isclose(187.5, transfocator.find_best_combo(305.35).effective_radius, atol=0.1)
    assert np.isclose(305.35, transfocator.find_best_combo(305.35).image(0.0), atol=0.1)

    #test xrt[1] and tfs[0,1,2,3]
    assert transfocator.find_best_combo(356.48).nlens==5
    assert np.isclose(69.76, transfocator.find_best_combo(356.48).effective_radius, atol=0.1)
    assert np.isclose(356.48, transfocator.find_best_combo(356.48).image(0.0), atol=0.1)

def test_transfocator_focus_at(transfocator):
    #test with tfs[0] and xrt[0]
    transfocator.focus_at(312.5)
    assert [lens.inserted for lens in transfocator.xrt_lenses] == [True, False]
    assert [lens.inserted for lens in transfocator.tfs_lenses] == [True, False, False, False]
    
    #test with xrt[0] and tfs[0,1]
    transfocator.focus_at(300.4)
    assert [lens.inserted for lens in transfocator.xrt_lenses] == [True, False]
    assert [lens.inserted for lens in transfocator.tfs_lenses] == [True, True, False, False]

    #test with no xrt and tfs[0,1,2]
    #transfocator.focus_at(295.7)
    #assert [lens.inserted for lens in transfocator.xrt_lenses] == [False, False]
    #assert [lens.inserted for lens in transfocator.tfs_lenses] == [True, True, True, False]
    
    #test with xrt[1] and tfs[1,3]
    transfocator.focus_at(318.5)
    assert [lens.inserted for lens in transfocator.xrt_lenses] == [False, True]
    assert [lens.inserted for lens in transfocator.tfs_lenses] == [False, True, False, True]

    #test with xrt[1] and tfs[1]
    transfocator.focus_at(367.9)
    assert [lens.inserted for lens in transfocator.xrt_lenses] == [False, True]
    assert [lens.inserted for lens in transfocator.tfs_lenses] == [False, True, False, False]
    
    #test xrt[1] and tfs[0]
    transfocator.focus_at(305.35)
    assert [lens.inserted for lens in transfocator.xrt_lenses] == [False, True]
    assert [lens.inserted for lens in transfocator.tfs_lenses] == [True, False, False, False]
    
    #test xrt[1] and tfs[0,1,2,3]
    transfocator.focus_at(356.48)
    assert [lens.inserted for lens in transfocator.xrt_lenses] == [False, True]
    assert [lens.inserted for lens in transfocator.tfs_lenses] == [True, True, True, True]


