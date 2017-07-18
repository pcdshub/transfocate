"""
Basic Lens object handling
"""
############
# Standard #
############
import logging
###############
# Third Party #
###############


##########
# Module #
##########

class Lens(object):
    """
    Data structure for basic Lens object
    """
    def __init__(self, radius, z, focus):
        """
        Parameters
        ----------
        radius : float
            Radius of beryllium lens measured in microns (um). Affects focus of lens  
        z : float
            Lens position along beam pipelin measure in meters (m).
        focus : float
            Focal length of lens in meters (m). Is a function of radius
        """
        self.radius=radius
        self.z=z
        self.focus=focus

    def image_from_obj(self, z_obj):
        """
        Method calculates the image distance in meters along the beam
        pipeline from a point of origin given the focal length of the lens, location of lens, and location of
        object.

        Parameters
        ----------
        z_obj
            Location of object along the beamline in meters (m)

        Returns
        -------
        float
            Returns the distance z_im of the image along the beam pipeline from
            a point of origin in meters (m)
        Note
        ----
        If the location of the object (z_obj) is equal to the focal length of
        the lens, this function will return infinity.
        """
        if z_obj==self.focus:
            return np.inf
        o=self.z-z_obj
        #print (o)
        i_inv=(1/self.focus)-(1/o)
        #print (i_inv)
        i=1/i_inv
        #print (i)
        z_im=i+self.z
        #print (z_im)
        return z_im

class LensConnect(object):
    """
    Data structure for a basic system of lenses
    """
    
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args
            Variable length argument list of the lenses in the system, their radii,
            z position, and focal length.
        **kwargs
            Arbitraty keyword argumens.
        """
        self.lenses=args

    @property
    def effective_radius(self):
        """
        Method calculates the effective radius of the lens array

        Returns
        -------
        float
            returns the effective radius of the lens array.
        """
       # print(self.lenses)
        if not self.lenses or len(self.lenses)==0:
            return 0

        else:
            collect=0
            #print(len(self.lenses))
            for lens in self.lenses:
                collect+=(1/lens.radius)
                #print (lens.radius)
                #print (lens.radius)
                #print(collect)
                #print (len(self.lenses))
            #print (collect)
            return 1/collect

    def image(self, z_obj):
        """
        Method recursively calculates the z location of the image of a system of
        lenses and returns it in meters (m)
    
        Parameters
        ----------
        z_obj
            Location of the object along the beam pipline from a designated point
            of origin in meters (m)
        
        Returns
        -------
        float
            returns the location z of a system of lenses in meters (m).
        """
        image=z_obj
        lens_list=self.z_based_sort
        for lens in lens_list:
            #print (image)
            image=lens.image_from_obj(image)
            #print (image)
        return image

    @property
    def z_based_sort(self):
        """
        Method sorts the array of lenses into a new list based on their z
        position along the beamline.  Lenses are sorted in ascending order.

        Returns
        -------
        list
            Returns the sorted list of lenses 
        """
        sorted_lenses=sorted(self.lenses, key=lambda lens: lens.z)
        #for lens in sorted_lenses:
            #print (lens.z)
        return sorted_lenses

    def nlens(self):
        """
        Method calculates the total number of lenses in the Lens array.

        Returns
        -------
        int
            Returns the total number of lenses in the array.
        """
        return len(self.lenses)
