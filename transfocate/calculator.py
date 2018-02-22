import itertools
import logging

import numpy as np

from transfocate.lens import LensConnect


logger = logging.getLogger(__name__)


class Calculator:
    """
    Class for the transfocator beryllium lens calculator.

    Parameters
    ----------
    xrt_lenses : list
        A list of the xrt prefocus lenses

    tfs_lenses : list
        A list of the transfocator lenses
    """
    def __init__(self, xrt_lenses, tfs_lenses):
        self.xrt_lenses = xrt_lenses
        self.tfs_lenses = tfs_lenses

    def combinations(self, include_prefocus=True):
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

    def find_solution(self, target, n=4, z_obj=0.0,
                      include_prefocus=True):
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

        include_prefocus: bool, optional
            Use only combinations that include a prefocusing lens. If False,
            only combinations of Transfocator lenses are returned

        Returns
        -------
        array: LensConnect
            An array of lens combinations with the closest possible image to
            the target_image
        """
        solution = None
        solution_diff = np.inf
        # Loop through all possible tfs/xrt combinations
        for combo in self.combinations(include_prefocus=include_prefocus):
            # Check to see if the number of lenses is less than the limit
            if combo.nlens <= n:
                try:
                    image = combo.image(z_obj)
                    diff = np.abs(image - target)
                except Exception as exc:
                    logger.exception("Unable to calculate image position")
                    diff = np.inf
                # See if we have found a better solution
                if diff < solution_diff:
                    logger.debug("Found a combination with image %s, %s "
                                 "from target %s", image, diff, target)
                    solution = combo
                    solution_diff = diff
        logger.info("Result found with a focal plane {} from the requested "
                    "position".format(solution_diff))
        return solution
