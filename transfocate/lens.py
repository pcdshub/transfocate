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
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import Component
from ophyd.utils import set_and_wait
logger = logging.getLogger(__name__)

##########
# Module #
##########

class Lens(Device):
    """
    Data structure for basic Lens object
    """
    
    """
    Parameters
    ----------
    sig_radius : EPICS Read Only signal
        Radius of beryllium lens measured in microns (um). Affects focus of lens  
    sig_z : EPICS Read Only signal
        Lens position along beam pipelin measure in meters (m).
    sig_focus : EPICS Read Only signal
        Focal length of lens in meters (m). Is a function of radius
    state : EPICS Read Only signal
        Position of the lens.  1 if it is inserted in the beamline and 0 if
        it is removed
    in_signal : EPICS signal
        Signal that triggers EPICS to insert the lens from the beamline
    out_signal : EPICS signal
        Signal that triggers EPICS to remove the lens from the beamline

    Note
    ----
    The variables radius, z, and focus are now EPICS signals for the lenses.
    """
    #defining the EPICS variables (note: these are the signals and not the
    #values of each variable)
    sig_radius=Component(EpicsSignalRO, "RADIUS")
    sig_z = Component(EpicsSignalRO, "Z")
    sig_focus = Component(EpicsSignalRO, "FOCUS")
    state = Component(EpicsSignalRO, "STATE") 
    in_signal = Component(EpicsSignal, "INSERT")
    out_signal = Component(EpicsSignal, "REMOVE")

    #z, radius, and focus properties: these convert the EPICS signal into a
    #value that can be interpreted by the other methods when the property is
    #called.  Otherwise, the signal itself would be inputted
    
    @property
    def radius(self):
        """
        Method converts the EPICS lens radius signal into a float that can be used for
        calculations.
        
        Returns
        -------
        float
            Returns the radius of the lens
        """
        return self.sig_radius.value
    
    @property 
    def z(self):
        """
        Method converts the z position EPICS signal into a float.
        
        Returns
        -------
        float
            Returns the z position of the lens in meters along the beamline
        """
        return self.sig_z.value
    
    @property
    def focus(self):
        """
        Method converts the EPICS focal length signal of the lens into a float
        
        Returns
        -------
        float
            Returns the focal length of the lens in meters 
        """
        return self.sig_focus.value

    @property
    def inserted(self):
        """
        Method checks if the lens is inserted in the beam pipeline or not

        Returns
        -------
        int
            Returns 1 if the lens in inserted in the beam pipeline and 0 if it
            has been removed.

        """
        #checks if the state value is 1 (inserted) or 0 (removed)
        if self.state.value==1:
            return True
        else:
            return False

    def insert(self):
        """
        Method sets the EPICS insert signal to 1 which triggers the motor to
        insert the lens from the beam pipeline
        """
        #Changes in_signal to 1 which causes the lense to be inserted
        self.in_signal.put(1)
    
    def remove(self):
        """
        Method sets the EPICS remove signal to 1 which triggers the motor to
        remove the lens from the beam pipeline
        """
        #changes out_signal to 1 which causes the lense to be removed
        self.out_signal.put(1)

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
        #check if the lens object is at the focal length.  
        #If this happens, then the image location will be infinity.
        #Note, this should not effect the recursive calculations that occur
        #later in the code
        if z_obj==self.focus:
            return np.inf
        #find the object location for the lens
        o=self.z-z_obj
        #calculate the inverse of i from the thin lens equation
        i_inv=(1/self.focus)-(1/o)
        #take the inverse of 1/i to get i
        i=1/i_inv
        #add the imsge to the lens z location aling the beam pipeline to get
        #the z position of the image
        z_im=i+self.z

        logger.debug("object measurement: %s i_invers: %s i: %s z image:%s"%(o, i_inv, i, z_im))
        
        return z_im


class LensConnect(Device):
    """
    Data structure for a basic system of lenses
    """
    #define the variables for lensconnect class
    #the lenses list can be a list of arbitrary length
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
        if not self.lenses or len(self.lenses)==0:
            return 0 #this method is only used if we impliment the option of No xrt/tfs lenses

        else:
            #set a collect variable to add the radii to
            collect=0
            #loop through the lenses in the array and add 1/radius to the
            #collect variable
            for lens in self.lenses:
                collect+=(1/lens.radius)
            logger.debug("lens radius: %s length of lens list: %s collect variable %s"%(lens.radius, len(self.lenses), collect)) 
            #take the inverse of collect to get the effective radius of the
            #lens array
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
        #set the initial image as the z object
        image=z_obj
        #call z_based_sort to put the lenses in order from closest to furthest
        #to the reference point on the beamline
        #save this sorted array into a list
        lens_list=self.z_based_sort
        #loop through the list and recursively calculate the image of the lens
        #array
        for lens in lens_list:
            image=lens.image_from_obj(image)
            logger.debug("image: %s" %(image))
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
        #define variable to count the number of lenses
        count=0
        #sort the lenses based on their z position
        sorted_lenses=sorted(self.lenses, key=lambda lens: lens.z)
        for lens in sorted_lenses:
            count +=1
            logger.debug("z position for lens number %s is %s" %(count,lens.z))
        return sorted_lenses
    
    @property
    def nlens(self):
        """
        Method calculates the total number of lenses in the Lens array.

        Returns
        -------
        int
            Returns the total number of lenses in the array.
        """
        logger.debug("number of lenses in list: %s" %(len(self.lenses)))
        #find the length of the list of lenses
        return len(self.lenses)
    
    def show_info(self):
        """
        Method prints the information for each lens in the LensConnect. Listed
        information includes: name, radius, and, z position
        """
        for lens in self.lenses:
            logging.info("name: %s radius: %s z-value: %s"%(lens.name, lens.radius, lens.z))
            print("name: %s radius: %s z-value: %s"%(lens.name, lens.radius, lens.z))

    def apply_lenses(self):
        """
        Method inserts the lenses in a LensConnect into the transfocator by
        setting the individual lens' insert EPICS signals to 1 which triggers
        them to be inserted into the beamline
        """
        #loop through lenses in the LensConnect
        for lens in self.lenses:
            #insert the lenses into the transfocator
            lens.insert()
            #logger.info("in signal value is %s"%(lens.in_signal.value))
