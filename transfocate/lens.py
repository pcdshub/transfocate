"""
Basic Lens object handling
"""
############
# Standard #
############

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
        o=self.z-z_obj
        #print (o)
        i_inv=(1/self.focus)-(1/o)
        #print (i_inv)
        i=1/i_inv
        #print (i)
        z_im=i+self.z
        #print (z_im)
        return z_im


