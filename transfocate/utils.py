import numpy as np
from pathlib import Path

# Lens data and constants
eRad = 2.81704E-13 # Classical radius of an electron in cm
p_be = 1.85        # Density of Be at room temperature in cm
m_be = 9.0121831   # Standard atomic weight
NA = 6.02212E23    # Avogadro's Constant
Be_refr = np.loadtxt(f'{Path(__file__).parent}/data/Be.csv', skiprows=1, delimiter=',')

# Prefocus energy range. Should probably be in a file under data
# format: (E_min, E_max): (xrt_lens_idx, lens_radius)
MFX_prefocus_energy_range = {
    (0,7000):(None,None),
    (7000,10000):(2,750),
    (10000,12000):(1,428)
}


def focal_length(radius, energy, N=1):
    """
    Calculate the focal length of a Beryllium lens
    Ref: HR Beguiristain et al. OPTICS LETTERS, Vol. 27, No. 9 (2002)

    Steps:
    1) Interpolate energy to find f1 and f2
    2) Get real aprt index of refraction delta
    3) f = R / (2N*delta)
    """
    # Step 1
    idx = find_nearest(Be_refr[:,0], energy)
    if energy > Be_refr[idx,0]:
        E = [Be_refr[idx,0], Be_refr[idx+1,0]]
        f1 = [Be_refr[idx,1], Be_refr[idx+1,1]]
        f2 = [Be_refr[idx,2], Be_refr[idx+1,2]]
    else:
        E = [Be_refr[idx-1,0], Be_refr[idx,0]]
        f1 = [Be_refr[idx-1,1], Be_refr[idx,1]]
        f2 = [Be_refr[idx-1,2], Be_refr[idx,2]]
    f1 = np.interp(energy, E, f1)
    f2 = np.interp(energy, E, f2)

    # Step 2
    f = f1+f2*1j
    f = f*p_be*NA/m_be
    wavelength = (12389.4/energy)*1E-08 #m
    delta = (eRad * wavelength**2 * f / (2*np.pi)).real
    
    # Step 3
    return radius*1e-6/2/N/delta


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx