import numpy as np
import periodictable as pt

# Constants
eRad = pt.core.constants.electron_radius * 100  # Classical radius of an electron [cm]
p_be = pt.Be.density  # Density of Be at room temperature [g/cm^3]
m_be = pt.Be.mass  # Standard atomic weight
NA = pt.core.constants.avogadro_number  # Avogadro's Constant


# Prefocus energy range. Should probably be in a file under data
# format: (E_min, E_max): (xrt_lens_idx, lens_radius)
MFX_prefocus_energy_range = {
    (0, 7000): (None, None),
    (7000, 10000): (2, 750),
    (10000, 12000): (1, 428),
    (12000, 16000): (0, 333)
}


def focal_length(radius, energy, N=1):
    """
    Calculate the focal length of a Beryllium lens
    Ref: HR Beguiristain et al. OPTICS LETTERS, Vol. 27, No. 9 (2002)

    Probably want to use pcdscalc instead eventually
    """
    # Get scattering factors
    f1, f2 = pt.Be.xray.scattering_factors(energy=energy/1000)

    # Calculate delta (refraction index)
    f = f1+f2*1j
    f = f*p_be*NA/m_be
    wavelength = (12389.4/energy)*1E-08  # [cm]
    delta = (eRad * wavelength**2 * f / (2*np.pi)).real
    # delta = be_calcs.get_delta(energy/1000, 'Be', p_be) # too slow

    # f = R / (2N*delta)
    return radius*1e-6/2/N/delta
