

import numpy as np
from transfocate.lens import Lens
from transfocate.lens import LensConnect
from transfocate.calculator import Calculator
from transfocate.calculator import TransfocatorCombo
import logging 
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import Component
from ophyd.utils import set_and_wait 

class Transfocator(Device):
    #define the EPICS signals
    xrt_limit = Component(EpicsSignalRO, "XRT_ONLY")
    tfs_limit = Component(EpicsSignalRO, "MFX_ONLY")
    faulted = Component(EpicsSignalRO, "BEAM:FAULTED")

    def __init__(self, prefix, xrt_lenses, tfs_lenses, **kwargs):
        #define user-entered parameters
        self.prefix=prefix
        self.xrt_lenses=xrt_lenses
        self.tfs_lenses=tfs_lenses
        super().__init__(prefix, **kwargs)


    @property
    def current_focus(self):
        #makeing a list of lenses already in the transfocator, looping through
        #and adding them to the list if they are
        already_in=[]
        for lens in self.xrt_lenses:
            if lens.inserted:
                already_in.append(lens)
        for lens in self.tfs_lenses:
            if lens.inserted==True:
                already_in.append(lens)
        #makr the list of already-inserted lenses a LensCOnnect 
        already_in=LensConnect(*already_in)
        #get the current focal length/image
        focus=already_in.image(0.0)
        print (focus)
        return focus

    def focus_at(self, i, obj=0.0):
        #remove all the lenses so there is a clean slate
        for lens in self.xrt_lenses:
            lens.remove()
        for lens in self.tfs_lenses:
            lens.remove()
        calc=Calculator(self.xrt_lenses, self.tfs_lenses, self.xrt_limit.value, self.tfs_limit.value)
        best_combo = calc.find_combinations(i, obj, num_sol=1)[0]
        print (type(best_combo))
        print (best_combo)
        for lens in best_combo.xrt.lenses:
            lens.insert()
            print("lens inserted")
        for lens in best_combo.tfs.lenses:
            lens.insert()
