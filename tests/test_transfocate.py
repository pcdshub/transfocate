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
from transfocate.transfocate import Transfocator

@pytest.fixture(scope='function')
def transfocator():
    #Prefocus lenses
    prefocus = [FakeLens(500., 100.0, 50.),
                FakeLens(300., 100.0, 25.)]

    #Define transfocator
    tfs = [FakeLens(500., 275., 25.),
           FakeLens(500., 280., 55.)]

    return Transfocator("TST:TFS:LENS:",
                        xrt_lenses=prefocus,
                        tfs_lenses=tfs)


def test_transfocator_current_focus(transfocator):
    transfocator.xrt_lenses[1].insert()
    transfocator.tfs_lenses[0].insert()
    assert transfocator.current_focus == 312.5


def test_transfocator_focus_at(transfocator):
    transfocator.focus_at(312.5)
    assert [lens.inserted for lens in transfocator.xrt_lenses] == [False, True]
    assert [lens.inserted for lens in transfocator.tfs_lenses] == [True,  False]
