import numpy as np
import transfocate.offline_calculator as calc
from transfocate.transfocator import Transfocator
from importlib import reload
reload(calc)


print('TEST CALCULATOR\n')

energy = 9500

tfs = Transfocator(prefix='MFX:LENS', name='MFX Transfocator')

c = calc.TFS_Calculator(xrt_lenses=tfs.xrt_lenses, tfs_lenses=tfs.tfs_lenses)

target = 399
energy = 9500

diff = c.find_solution(target, energy)
