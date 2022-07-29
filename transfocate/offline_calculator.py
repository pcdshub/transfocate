import itertools
import logging
from pathlib import Path
from unittest import skip
import wave

import numpy as np

from transfocate.lens import LensConnect


logger = logging.getLogger(__name__)

# Lens data and constants
eRad = 2.81704E-13 # Classical radius of an electron in cm
p_be = 1.85        # Density of Be at room temperature in cm
m_be = 9.0121831   # Standard atomic weight
NA = 6.02212E23    # Avogadro's Constant
Be_refr = np.loadtxt(f'{Path(__file__).parent}/data/Be.csv', skiprows=1, delimiter=',')

# Prefocus energy range
# format: (E_min, E_max): (xrt_lens_idx, lens_radius)
prefocus_energy_range = {
    (0,7000):(None,None),
    (7000,10000):(2,750),
    (10000,12000):(1,428)
}


def focal_length(lens, energy, N=1):
    """
    Calculate the focal length of a Beryllium lens
    Ref: HR Beguiristain et al. OPTICS LETTERS, Vol. 27, No. 9 (2002)

    Steps:
    1) Interpolate energy to find f1 and f2
    2) Get real aprt index of refraction delta
    3) f = R / (2N*delta)
    """
    # Step 1
    idx = find_nearest(Be_refr[:,0], energy)
    if energy > Be_refr[idx,0]:
        E = [Be_refr[idx,0], Be_refr[idx+1,0]]
        f1 = [Be_refr[idx,1], Be_refr[idx+1,1]]
        f2 = [Be_refr[idx,2], Be_refr[idx+1,2]]
    else:
        E = [Be_refr[idx-1,0], Be_refr[idx,0]]
        f1 = [Be_refr[idx-1,1], Be_refr[idx,1]]
        f2 = [Be_refr[idx-1,2], Be_refr[idx,2]]
    f1 = np.interp(energy, E, f1)
    f2 = np.interp(energy, E, f2)

    # Step 2
    f = f1+f2*1j
    f = f*p_be*NA/m_be
    wavelength = (12389.4/energy)*1E-08 #m
    delta = (eRad * wavelength**2 * f / (2*np.pi)).real
    
    # Step 3
    # R = lens._sig_radius.get()
    R = 500
    return R*1e-6/2/N/delta


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx


class TFS_Calculator(object):
    def __init__(self, xrt_lenses=None, tfs_lenses=None):
        self.xrt_lenses = xrt_lenses
        self.tfs_lenses = tfs_lenses
        if tfs_lenses is not None:
            self.combos = self.combinations()
        return


    def combinations(self, include_prefocus=False):
        """
        All possible combinations of the given lenses

        Parameters
        ----------
        include_prefocus : bool
            Use only combinations that include a prefocusing lens. If False,
            only combinations of Transfocator lenses are returned

        Returns
        -------
        combos: list
            List of LensConnect objects
        """
        combos = list()
        tfs_combos = list()
        # Warn operators if we received no transfocator lenses
        if include_prefocus and not self.xrt_lenses:
            logger.warning("No XRT lens given to calculator, but prefocusing "
                           "was requested")
            include_prefocus = False
        # Initially only consider transfocator lenses
        for i in range(1, len(self.tfs_lenses)+1):
            list_combos = list(itertools.combinations(self.tfs_lenses, i))
            # Create LensConnect objects from all of our possible combinations
            tfs_combos.extend([LensConnect(*combo) for combo in list_combos])
        logger.debug("Found %s combinations of Transfocator lenses",
                     len(tfs_combos))
        
        """ 
        In practice the prefocus are generally fixed for a given energy. Keeping 
        it in case we want it again in the future.
        """
        # If we don't want to prefocus return only Transfocator lenses
        if not include_prefocus:
            return tfs_combos
        
        # Loop through all the prefocusing lenses
        for prefocus in self.xrt_lenses:
            c = LensConnect(prefocus)
            for combo in tfs_combos:
                # Create combinations of prefocusing and transfocating lenses
                combos.append(LensConnect.connect(c, combo))
        logger.debug("Found %s total combinations of lenses", len(combos))
        return combos


    def get_pre_focus_lens(self, energy):
        for e_range, lens in prefocus_energy_range.items():
            if energy>=e_range[0] and energy<e_range[1]:
                pre_focus_lens_idx = lens[0]
                break
        if pre_focus_lens_idx is None:
            pre_focus_lens = None
        else:
            pre_focus_lens = self.xrt_lenses[pre_focus_lens_idx]
        return pre_focus_lens


    def get_combo_image(self, combo, z_obj=0.0):
        return combo.image(z_obj)

    
    def find_solution(self, target, energy, n=4, z_obj=0.0):
        """
        Find a combination to reach a specific focus

        Parameters
        ----------
        target: float
            The desired position of the focal plane in accelerator coordinates

        n : int, optional
            The maximum number of lenses in a valid combination. This saves
            time by avoiding calculating the focal plane of combinations with a
            large number of lenses

        z_obj : float, optional
            The source point of the beam

        Returns
        -------
        array: LensConnect
            An array of lens combinations with the closest possible image to
            the target_image
        
        Steps:
        1) find the right pre-focussing lens. These are pre-defined based on the 
        photon energy (see prefocus_energy_range). and add it to the combos
        2) Calculate the focus and the difference to the target for each TFS lens
        combination
        3) Pick the smaller difference
        """
        # Step 1
        pre_focus_lens = self.get_pre_focus_lens(energy)
        if pre_focus_lens is None:
            combos = self.combos
        else:
            combos = []
            for combo in self.combos:
                c = LensConnect(pre_focus_lens)
                lens_combo = LensConnect.connect(c, combo)
                combos.append(lens_combo)                

        # Step 2
        diff = []
        for ii, combo in enumerate(self.combos):
            if combo.nlens > n:
                continue
            image = combo.image(z_obj)
            diff.append(np.abs(image - target))
        
        # Step 3
        solution = combos[np.argmin(diff)]
        return solution, np.min(diff)

