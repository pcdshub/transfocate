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
import numpy as np
import prettytable
from ophyd import EpicsSignalRO
from ophyd import FormattedComponent as FC
from pcdsdevices.inout import InOutRecordPositioner

##########
# Module #
##########

logger = logging.getLogger(__name__)


class Lens(InOutRecordPositioner):
    """
    Data structure for basic Lens object
    """
    _sig_radius = FC(EpicsSignalRO, "{self.prefix_lens}:RADIUS",
                     auto_monitor=True)
    _sig_z = FC(EpicsSignalRO, "{self.prefix_lens}:Z",
                auto_monitor=True)
    _sig_focus = FC(EpicsSignalRO, "{self.prefix_lens}:FOCUS",
                    auto_monitor=True)
    # Default configuration attributes. Read attributes are set correctly by
    # InOutRecordPositioner
    _default_configuration_attrs = ['_sig_radius', '_sig_z']

    def __init__(self, prefix, prefix_lens, **kwargs):
        self.prefix_lens = prefix_lens
        super().__init__(prefix, **kwargs)

    @property
    def radius(self):
        """
        Method converts the EPICS lens radius signal into a float that can be
        used for calculations.

        Returns
        -------
        float
            Returns the radius of the lens
        """
        return self._sig_radius.value

    @property
    def z(self):
        """
        Method converts the z position EPICS signal into a float.

        Returns
        -------
        float
            Returns the z position of the lens in meters along the beamline
        """
        return self._sig_z.value

    @property
    def focus(self):
        """
        Method converts the EPICS focal length signal of the lens into a float

        Returns
        -------
        float
            Returns the focal length of the lens in meters
        """
        return self._sig_focus.value

    def image_from_obj(self, z_obj):
        """
        Method calculates the image distance in meters along the beam pipeline
        from a point of origin given the focal length of the lens, location of
        lens, and location of object.

        Parameters
        ----------
        z_obj
            Location of object along the beamline in meters (m)

        Returns
        -------
        image
            Returns the distance z_im of the image along the beam pipeline from
            a point of origin in meters (m)
        Note
        ----
        If the location of the object (z_obj) is equal to the focal length of
        the lens, this function will return infinity.
        """
        # Check if the lens object is at the focal length
        # If this happens, then the image location will be infinity.
        # Note, this should not effect the recursive calculations that occur
        # later in the code
        if z_obj == self.focus:
            return np.inf
        # Find the object location for the lens
        obj = self.z - z_obj
        # Calculate the location of the focal plane
        plane = 1/(1/self.focus - 1/obj)
        # Find the position in accelerator coordinates
        return plane + self.z


class LensConnect:
    """
    Data structure for a basic system of lenses
    """
    def __init__(self, *args):
        """
        Parameters
        ----------
        args
            Variable length argument list of the lenses in the system, their
            radii, z position, and focal length.
        """
        self.lenses = sorted(args, key=lambda lens: lens.z)

    @property
    def effective_radius(self):
        """
        Method calculates the effective radius of the lens array

        Returns
        -------
        float
            returns the effective radius of the lens array.
        """
        if not self.lenses:
            return 0.0
        return 1/np.sum(np.reciprocal([float(l.radius) for l in self.lenses]))

    def image(self, z_obj):
        """
        Method recursively calculates the z location of the image of a system
        of lenses and returns it in meters (m)

        Parameters
        ----------
        z_obj
            Location of the object along the beam pipline from a designated
            point of origin in meters (m)

        Returns
        -------
        float
            returns the location z of a system of lenses in meters (m).
        """
        # Set the initial image as the z object
        image = z_obj
        # Determine the final output by looping through lenses
        for lens in self.lenses:
            image = lens.image_from_obj(image)
        return image

    @property
    def nlens(self):
        """
        Method calculates the total number of lenses in the Lens array.

        Returns
        -------
        int
            Returns the total number of lenses in the array.
        """
        return len(self.lenses)

    def _info(self):
        """
        Create a table with lens information
        """
        # Create initial table
        pt = prettytable.PrettyTable(['Prefix', 'Radius', 'Z'])
        # Adjust table settings
        pt.align = 'l'
        pt.float_format = '8.5'
        for lens in self.lenses:
            pt.add_row([lens.prefix, lens.radius, lens.z])
        return pt

    def show_info(self):
        """
        Show a table of information on the lens
        """
        print(self._info())
