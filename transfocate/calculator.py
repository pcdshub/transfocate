

import numpy as np
import itertools
import logging
from transfocate.lens import Lens
from transfocate.lens import LensConnect


logger = logging.getLogger(__name__)

class TransfocatorCombo(object):
    """Class creates and keeps track of the lens array lists and calculates the
    image of the combined xrt/tfs beryllium lens array

    Attributes
    ----------
    xrt : list
        A list of the xrt lenses with all the attributes of the LensConnect
        class
    tfs : list
        A list of the tfs lenses with all the attributes of the LensConnect
        class
    """
    def __init__(self, xrt, tfs):
        self.xrt=LensConnect(xrt)
        self.tfs=LensConnect(*tfs)

    def image(self, z_obj):
        """Method calculates the image of the combined tfs and xrt lens array
        
        Returns
        -------
        float
            Returns the image of the xrt/tfs lens array
        """
        xrt_image=self.xrt.image(z_obj)
        total_image=self.tfs.image(xrt_image)
        logger.debug("the xrt image of the array is %s and the image of the combined xrt/tfs array is %s" %(xrt_image,total_image))
        return total_image


class Calculator(object):
    """Class for the transfocator beryllium lens calculator.

    Attributes
    ----------
    xrt_lenses : list
        A list of the xrt prefocus lenses
    tfs_lenses : list
        A list of the beryllium transfocator lenses
    xrt_limit : float 
        The hard limit i.e. minimum effective radius that the xrt lens array can safely
        have
    tfs : float
        The hard limit i.e. maximum effective radius that tfs lense array can
        safely have
    """

    def __init__(self, xrt_lenses, tfs_lenses, xrt_limit=None, tfs_limit=None):
        self.xrt_lenses=xrt_lenses
        self.tfs_lenses=tfs_lenses
        self.xrt_limit=xrt_limit
        self.tfs_limit=tfs_limit

    @property
    def combinations(self):
        """Method calculates and returns all possible combinations of the xrt
        and tfs lense arrays

        Returns
        -------
        list
            Returns a list of all possible combinations of the xrt and tfs
            lense arrays
        """
        
        all_combo=[]
        prefocus_combo=self.xrt_lenses
        tfs_combo=[]
        for i in range(len(self.tfs_lenses)+1):
            z=list(itertools.combinations(self.tfs_lenses,i))
            for index in range(len(z)):
                tfs_combo.append(z[index])
            logger.debug("length of the tfs combinations array %s"%(len(tfs_combo)))
        for prefocus in prefocus_combo:
            for combo in tfs_combo:
                all_combo.append(TransfocatorCombo(prefocus,combo))
        logger.debug("Length of the list of all combinations %s"%(len(all_combo)))
        return all_combo 
        
    def find_combinations(self, target_image, z_obj=0.0, num_sol=1):
        """Method finds all possible xrt/tfs lens combinations and calculates the xrt/tfs lens arrays with the smallest error
        from the user's desired setting (i.e. the image of the lens array is
        closest to the target image of the array the user requires.

        Parameters
        ----------
        target_image : float
            The deasired image of the lens array
        z_obj : float
            location of the lens object along the beam pipline in meters (m)
        num_sol : int
            The desired number of solutions that are closest to the
            target_image (i.e. the solutions with the smallest error)
        
        Returns
        -------
        array
            Returns an array of lens combinations with the closest possible
            image to the target_image

        Note
        ----
        This mehtod does not currently take into account the case in which
        there is no tfs or xrt arrays.

        """
        image_diff=[]
        closest_sols=[]
            
        for combo in self.combinations:
            if combo.xrt.effective_radius>self.xrt_limit and combo.tfs.effective_radius<self.tfs_limit:
                diff=np.abs(combo.image(z_obj)-target_image)
                logger.debug("Found a combination with image {} "
                             "from target {}.".format(diff, target_image))
                image_diff.append(diff)
            else:
                logger.debug("Dropping combination that does not meet radius "
                             "requirements")
        index=np.argsort(image_diff)
        combos = np.asarray(self.combinations)
        sorted_combos = combos[index]
        final_sols=[]
        return sorted_combos
