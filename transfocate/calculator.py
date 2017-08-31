

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
    #define TransfocatorCombo attributes
    #Note: onely one xrt can be entered for this but multiple tfs lenses can be
    #entered
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
        #
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
    #Define calculator variables
    #There are not xtr or tfs limits unless they are set by the signals
    def __init__(self, xrt_lenses, tfs_lenses, xrt_limit=None, tfs_limit=None):
        self.xrt_lenses=xrt_lenses
        self.tfs_lenses=tfs_lenses
        self.xrt_limit=xrt_limit
        self.tfs_limit=tfs_limit

    @property
    def combinations(self):
        #Note: all lens arrays will consist of one prefocus lens and an array
        #of tfs lenses
        
        """Method calculates and returns all possible combinations of the xrt
        and tfs lense arrays

        Returns
        -------
        list
            Returns a list of all possible combinations of the xrt and tfs
            lense arrays
        """
        
        #create empty lists for all possible xrt and tfs combos and all possible tfs combos
        #xrt lenses put into prefocus
        all_combo=[]
        prefocus_combo=self.xrt_lenses
        tfs_combo=[]

        #loop through tfs lenses from i=0 to i=length of tfs list +1
        for i in range(len(self.tfs_lenses)+1):
            #create a list z of all possile tfs lens combinations using
            #itertools
            z=list(itertools.combinations(self.tfs_lenses,i))
            #loop through the combinations in z from index=0 to index= length
            #of z 
            for index in range(len(z)):
                #append the combinations into tfs_combo
                #if len(z.lens)<=4:
                tfs_combo.append(z[index])
            logger.debug("length of the tfs combinations array %s"%(len(tfs_combo)))
       
        #loop through all the prefocus lenses
        for prefocus in prefocus_combo:
            #loop through the combinations of tfs and prefocus lenses
            for combo in tfs_combo:
                #add the lens combinations as TransfocatorCombos so that we are
                #keeping track of lists of lenses instead of lists of lists
                all_combo.append(TransfocatorCombo(prefocus,combo))
        
        logger.debug("Length of the list of all combinations %s"%(len(all_combo)))
        return all_combo 
        
    def find_combinations(self, target_image, n=4, z_obj=0.0, use_limits=True):
        """Method finds all possible xrt/tfs lens combinations and calculates the xrt/tfs lens arrays with the smallest error
        from the user's desired setting (i.e. the image of the lens array is
        closest to the target image of the array the user requires.

        Parameters
        ----------
        target_image : float
            The deasired image of the lens array
        n : int
            The maximum number of lenses in the array. If unspecified by the
            user, it will be set to 4.  Note: this does not take the xrt lens
            into account; however, there will always be at least 1 prefocus
            lens in the beam so we only need to worry about the tfs lens
            arrays.
        z_obj : float
            location of the lens object along the beam pipline in meters (m)
        
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
        #create list of the image differences
        image_diff=[]
        #create list for the solutions with images closest to the target
        #image(i.e. with the lowest error
        closest_sols=[]
        
        #loop through all possible tfs/xrt combinations
        for combo in self.combinations:
            logger.debug("number of allowed lenses: %s"%n)

            #check if the effective radius of the array is less than the tfs
            #safety limit and greater than the xrt safety limit
            #also check to see if the number of lenses in the array is less
            #than or equal to the efficiency limit
            #if it is more than n, the array is disregarded
            if combo.tfs.nlens<=n:
                if use_limits==True and combo.xrt.effective_radius>self.xrt_limit and combo.tfs.effective_radius<self.tfs_limit:
                    #take the difference between the array image and the target
                    #image
                    diff=np.abs(combo.image(z_obj)-target_image)
                    logger.info("Found a combination with image {}, and difference {} "
                                "from target {}.".format(combo.image(z_obj), diff, target_image))
                    #add the difference to the end of image diff
                    image_diff.append(diff)
            
                elif use_limits==False:
                    diff=np.abs(combo.image(z_obj)-target_image)
                    image_diff.append(diff)
                
                else:
                    logger.debug("Dropping combination that does not meet radius "
                                "requirements")
            else:
                x=combo.tfs.nlens-n
                #logger.debug("dropped combo that had %s lenses over limit "
                #             "%s"%combo.tfs.nlens, n)
        #sort the list based from lowest image diff to highest
        #note: argsort sorts so that the index list is a list if indeces in
        #order of their coresponding values in image diff
        index=np.argsort(image_diff)
        #make an array out of the combinations list
        combos = np.asarray(self.combinations)
        #make the sorted list where the lens combos are sorted based on
        #smallest error
        sorted_combos = combos[index]
        return sorted_combos
