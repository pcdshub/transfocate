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
        """
        Method calculates the image distance in meters along the beam
        pipeline given the focal length of the lens, location of lens, and location of
        object.

        Parameters
        ----------
        z_obj
            Location of object along the beamline in meters (m)

        Returns
        -------
        float
            Returns the distance z_im of the image along the beam pipeline in
            meters (m)
        """
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
    def __init__(self, *args, **kwargs):
        self.saved=args
    
    @property
    def effective_radius(self):

    def image(self, z_obj):
        image=z_obj
        for lens in self.lenses:
            image=image_from_obj(image)
