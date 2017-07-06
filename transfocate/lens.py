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
	
		


