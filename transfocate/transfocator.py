import math
import logging

from pcdsdevices.device_types import IMS
from ophyd import Device, EpicsSignalRO, Component, FormattedComponent, EpicsSignal
from ophyd.status import wait as status_wait

from .lens import Lens, LensConnect
from .calculator import Calculator
from functools import wraps

logger = logging.getLogger(__name__)


class Transfocator(Device):
    """
    Class to represent the MFX Transfocator
    """
    # Define EPICS signals
    xrt_limit = Component(EpicsSignalRO, ":XRT_ONLY")
    tfs_limit = Component(EpicsSignalRO, ":MFX_ONLY")
    faulted = Component(EpicsSignalRO, ":BEAM:FAULTED")

    # XRT Lenses
    prefocus_top = Component(Lens, ":DIA:03")
    prefocus_mid = Component(Lens, ":DIA:02")
    prefocus_bot = Component(Lens, ":DIA:01")

    # TFS Lenses
    tfs_02 = Component(Lens, ":TFS:02")
    tfs_03 = Component(Lens, ":TFS:03")
    tfs_04 = Component(Lens, ":TFS:04")
    tfs_05 = Component(Lens, ":TFS:05")
    tfs_06 = Component(Lens, ":TFS:06")
    tfs_07 = Component(Lens, ":TFS:07")
    tfs_08 = Component(Lens, ":TFS:08")
    tfs_09 = Component(Lens, ":TFS:09")
    tfs_10 = Component(Lens, ":TFS:10")

    # Requested energy
    req_energy = Component(EpicsSignal, ":BEAM:REQ_ENERGY")

    # Actual beam energy
    beam_energy = Component(EpicsSignal, ":BEAM:ENERGY")

    # Translation
    translation = FormattedComponent(IMS, "MFX:TFS:MMS:21")

    def __init__(self, prefix, *, nominal_sample=399.88103, **kwargs):
        self.nominal_sample = nominal_sample
        super().__init__(prefix, **kwargs)

    @property
    def lenses(self):
        """
        Component lenses
        """
        return [getattr(self, dev) for dev in self._sub_devices
                if isinstance(getattr(self, dev), Lens)]

    @property
    def xrt_lenses(self):
        """
        Lenses in the XRT
        """
        return [lens for lens in self.lenses if 'DIA' in lens.prefix]

    @property
    def tfs_lenses(self):
        """
        Transfocator lenses
        """
        return [lens for lens in self.lenses if 'TFS' in lens.prefix]

    @property
    def current_focus(self):
        """
        The distance from the focus of the Transfocator to nominal_sample

        Note
        ----
        If no lenses are inserted this will retun NaN
        """
        # Find inserted lenses
        inserted = [lens for lens in self.lenses if lens.inserted]
        # Check that we have any inserted lenses at all
        if not inserted:
            logger.warning("No lenses are currently inserted")
            return math.nan
        # Calculate the image from this set of lenses
        return LensConnect(*inserted).image(0.0) - self.nominal_sample

    def find_best_combo(self, target=None, show=True, energy=None,
                        abs_tol=5.0, **kwargs):
        """
        Calculate the best lens array to hit the nominal sample point

        Parameters
        ----------
        target : float, optional
            The target image of the lens array. By default this is
            `nominal_sample`

        show : bool, optional
            Print a table of the of the calculated lens combination

        energy : float, optional
            requested beam energy (in eV) to be used for calculation.
            By default this is 'None' and the current beam energy is
            used

        abs_tol : float, optional
            absolute tolerance (in eV) for which beam energy can change
            during calculation without returning error

        kwargs:
            Passed to :meth:`.Calculator.find_solution`
        """
        if energy:
            self.req_energy.put(energy)
            requested = True
        else:
            requested = False

        target = target or self.nominal_sample
        # Only included allowed XRT lenses
        xrt_limit = self.xrt_limit.get()
        allowed_xrt = [lens for lens in self.xrt_lenses
                       if lens.radius >= xrt_limit]
        # Warn users if no XRT lenses are over the required radius
        if not allowed_xrt:
            logger.warning("Can not find a prefocusing lens that meets the "
                           "safety requirements")
        # Create a calculator
        # mutate calc.find_solution to check constant energy
        # Return the solution
        if requested:
            # Checking all xrt lenses
            calc = Calculator(self.xrt_lenses, self.tfs_lenses)
            find_solution_const_energy = constant_energy(calc.find_solution,
                                                         self, 'req_energy',
                                                         abs_tol)
        else:
            # Checking only xrt_lenses producing foci within xrt_limit
            calc = Calculator(allowed_xrt, self.tfs_lenses)
            find_solution_const_energy = constant_energy(calc.find_solution,
                                                         self, 'beam_energy',
                                                         abs_tol)
        combo = find_solution_const_energy(target, requested=requested,
                                           **kwargs)
        if combo:
            combo.show_info()
        else:
            logger.error("Unable to find a valid solution for target")
        return combo

    def set(self, value, **kwargs):
        """
        Set the Transfocator focus

        Parameters
        """
        return self.focus_at(value=value, **kwargs)

    def focus_at(self, value=None, wait=False, timeout=None, **kwargs):
        """
        Calculate a combination and insert the lenses

        Parameters
        ----------
        value: float, optional
            Chosen focal plane. Nominal sample by default

        wait : bool, optional
            Wait for the motion of the transfocator to complete

        timeout: float, optional
            Timeout for motion

        kwargs:
            All passed to :meth:`.find_best_combo`

        Returns
        -------
        StateStatus
            Status that represents whether the move is complete
        """
        # Find the best combination of lenses to match the target image
        plane = value or self.nominal_sample
        best_combo = self.find_best_combo(target=plane, **kwargs)
        # Collect status to combine
        statuses = list()
        # Only tell one XRT lens to insert
        prefocused = False
        for lens in self.xrt_lenses:
            if lens in best_combo.lenses:
                statuses.append(lens.insert(timeout=timeout))
                prefocused = True
                break
        # If we have no XRT lenses one remove will do
        if not prefocused:
            statuses.append(self.xrt_lenses[0].remove(timeout=timeout))
        # Ensure all Transfocator lenses are correct
        for lens in self.tfs_lenses:
            if lens in best_combo.lenses:
                statuses.append(lens.insert(timeout=timeout))
            else:
                statuses.append(lens.remove(timeout=timeout))
        # Conglomerate all status objects
        status = statuses.pop(0)
        for st in statuses:
            status = status & st
        # Wait if necessary
        if wait:
            status_wait(status, timeout=timeout)
        return status


class TransfocatorEnergyInterrupt(Exception):
    """
    Custom exception returned when input beam energy (user defined
    or current measured value) changes significantly during
    calculation
    """
    pass


def constant_energy(func, transfocator_obj, energy_type, tolerance):
    """
    Ensures that requested energy does not change during calculation

    Parameters:
    transfocator_obj: transfocate.transfocator.Transfocator object

    energy_type: string
        input string specifying 'req_energy' or 'beam_energy'
        to be monitored during calculation

    tolerance: float
        energy (in eV) for which current beam energy can change during
        calculation and still assumed constant
    """
    @wraps(func)
    def with_constant_energy(*args, **kwargs):
        try:
            energy_signal = getattr(transfocator_obj, energy_type)
        except Exception as e:
            raise AttributeError("input 'energy_type' not defined") from e
        energy_before = energy_signal.get()
        logger.debug('Energy before the method %s' % energy_before)
        result = func(*args, **kwargs)
        energy_after = energy_signal.get()
        logger.debug('Energy after the method %s' % energy_after)
        delta_energy = abs(energy_after - energy_before)
        if not math.isclose(energy_before, energy_after, abs_tol=tolerance):
            raise TransfocatorEnergyInterrupt("The beam energy changed by %s eV"
                                              "during the calculation" % delta_energy)
        return result
    return with_constant_energy
