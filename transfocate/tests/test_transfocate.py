import logging

import pytest
import numpy as np
from pcdsdevices.sim.pv import using_fake_epics_pv

from transfocate.transfocator import Transfocator

logger = logging.getLogger(__name__)


# Utility functions for manipulating simulated lenses
def insert(lens):
    lens._removed._read_pv.put(0)
    lens._inserted._read_pv.put(1)


def remove(lens):
    lens._removed._read_pv.put(1)
    lens._inserted._read_pv.put(0)


@pytest.fixture(scope='function')
@using_fake_epics_pv
def transfocator():
    # Create our base transfocator
    trans = Transfocator("TST:LENS",
                         name='Transfocator')
    # Set all the lens values to ridiculous values and out
    for lens in trans.xrt_lenses:
        lens._sig_z._read_pv.put(100.0)
        lens._sig_focus._read_pv.put(1000.0)
        remove(lens)
    for lens, z in zip(trans.tfs_lenses,
                       np.linspace(250, 260, len(trans.tfs_lenses))):
        lens._sig_z._read_pv.put(z)
        lens._sig_focus._read_pv.put(1000.0)
        remove(lens)
    # Give two reasonable values so we can test calculations
    trans.prefocus_bot._sig_focus._read_pv.put(50.0)
    trans.tfs_02._sig_z._read_pv.put(275.)
    trans.tfs_02._sig_focus._read_pv.put(25.)
    # Use a nominal sample position
    trans.nominal_sample = 300.0
    # Set a reasonable limit
    trans.xrt_limit._read_pv.put(-1.0)
    return trans


@using_fake_epics_pv
def test_transfocator_current_focus(transfocator):
    assert np.isnan(transfocator.current_focus)
    insert(transfocator.prefocus_bot)
    insert(transfocator.tfs_02)
    assert transfocator.tfs_02.inserted
    assert transfocator.prefocus_bot.inserted
    assert transfocator.current_focus == 12.5


@using_fake_epics_pv
def test_transfocator_find_best_combo(transfocator):
    # A solution with a prefocus
    combo = transfocator.find_best_combo(312.5)
    assert combo.nlens == 2
    assert np.isclose(312.5, combo.image(0.0), atol=0.1)
    # A solution where there are no valid prefocus
    transfocator.xrt_limit._read_pv.put(1500.)
    combo = transfocator.find_best_combo(target=302.5)
    assert combo.nlens == 1
    assert np.isclose(302.5, combo.image(0.0), atol=0.1)


@using_fake_epics_pv
def test_transfocator_focus_at(transfocator):
    #test with tfs[0] and xrt[0]
    # Insert Transfocator lenses so we can test that they are properly removed
    for lens in transfocator.tfs_lenses:
        insert(lens)
    transfocator.focus_at(value=312.5, wait=False)
    assert transfocator.prefocus_bot._insert._write_pv.get() == 1
    assert transfocator.tfs_02._insert._write_pv.get() == 1
    for lens in transfocator.tfs_lenses:
        if lens != transfocator.tfs_02:
            assert lens._remove._write_pv.get() == 1
