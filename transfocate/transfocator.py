
import logging
import numpy as np
from transfocate.lens import Lens
from transfocate.lens import LensConnect
from transfocate.calculator import Calculator
from transfocate.calculator import TransfocatorCombo
import logging 
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import Component
from ophyd.utils import set_and_wait 

logger = logging.getLogger(__name__)

class Transfocator(Device):
    """Class to interface between the Transfocator and the calculator code

    Attributes
    ----------

    xrt_limit : EPICS Read Only signal
        The signal for the minimum effective radius that the xrt lens array can
        safely have
    tfs_limit : EPICS Read Only signal
        The signal for the maximum effective radius the tfs lens array can
        safely have
    faulted : EPICS Read Only signal
        This signal is triggered if one of the lens arrays is not in its
        inserted or removed position
    prefix : string
        The prefix for the whole transfocator
    xrt_lenses : list
        A list of the prefocus lenses
    tfs_lenses : list
        A list of the beryllium lens stack in the transfocator

    Note
    ----
    The xrt_limit, tfs_limit, and faulted variables are EPICS Read Only signals
    """
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
        """Method calculates the focus of the lenses array currently inserted
        in the transfocator

        Returns
        -------
        float
            Returns the current focus of the beryllium lens array already
            inserted in the transfocator.

        """
        #makeing a list of lenses already in the transfocator, looping through
        #and adding them to the list if they are
        already_in=[]
        for lens in self.xrt_lenses:
            if lens.inserted:
                already_in.append(lens)
        for lens in self.tfs_lenses:
            if lens.inserted==True:
                already_in.append(lens)
        logger.debug("There are %s lenses already inserted in the Transfocator"%(len(already_in)))
        #makr the list of already-inserted lenses a LensCOnnect of arbitrary length
        already_in=LensConnect(*already_in)
        #get the current focal length/image
        focus=already_in.image(0.0)
        logger.debug("The current focus of the inserted lenses is %s"%focus)
        return focus

    def find_best_combo(self, i, n=4, obj=0.0):
        """Method calculates the best lens array to meet the user's target
        image.

        Parameters
        ----------
        i : float
            The target image of the lens array
        n : int
            The maximum number of lenses in the array. Note: will automatically
            be set to 5 unless otherwise specified by the user.
        obj : float
            Location of the lens object along the beam pipeline measured in
            meters.  Parameter will be set to 0 unles otherwise specified by
            the user
        """
       
        #create a calculator 
        calc=Calculator(self.xrt_lenses, self.tfs_lenses, self.xrt_limit.value, self.tfs_limit.value)
        #create a list of all the possible combinations of the lenses in the
        #calculator and puts them in order with the array with the image
        #closest to the target image first and so on
        combos=calc.find_combinations(i, n, obj)
        
        #create a list for the best combination of lenses
        best_combo=[]
        #extend the list to add the xrt and tfs lenses as Lenses
        best_combo.extend(combos[0].xrt.lenses)
        best_combo.extend(combos[0].tfs.lenses)
        #instantiate the best combo as a LensConnect objet
        best_combo=LensConnect(*best_combo)
        return best_combo

    def focus_at(self, i, n=4, obj=0.0):
        """Method inserts the lenses in this array into the beam pipeline.

        Parameters
        ----------
        i : float
            The target image of the lens array (i.e. the image/focal length the
            user would ideally like to achieve
        n : int
            The maximum number od lenses in the array. Note: will automatically
            be set to 5 unless otherwise specified by the user
        obj : float
            Location of the lens object along the beam pipeline measured in
            meters.  Note: this parameter will be automatically set to 0 unless
            the user specifies otherwise.
        
        """
        
        #find the best combination of lenses to match the target image
        best_combo = self.find_best_combo(i, n, obj)
        
        #insert the lenses in the best combo LensConnect
        best_combo.apply_lenses()
        
        #loop through all the lenses and, if they are not in best_combo, remove
        #them.  If they are already removed, this should not affect them
        for lens in self.xrt_lenses:
            if lens not in best_combo.lenses:
                lens.remove()
        
        for lens in self.tfs_lenses:
            if lens not in best_combo.lenses:
                lens.remove()
        
        
