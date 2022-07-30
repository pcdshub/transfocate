import numpy as np
import transfocate.offline_calculator as calc
import transfocate.transfocator as tf
import transfocate.lens as ll
from importlib import reload
reload(calc)
reload(ll)
reload(tf)


print('TEST CALCULATOR\n')

energy = 9500

tfs = tf.Transfocator(prefix='MFX:LENS', name='MFX Transfocator')

c = calc.TFS_Calculator(tfs_lenses=tfs.tfs_lenses, prefocus_lenses=tfs.xrt_lenses)

# radii = [500,500,250,250,50,50]
# zs = [390, 390.2, 390.4, 390.6, 390.8, 391, 391.2]
# lenses = [ll.LensBase(radius=r, z_position=z) for r,z in zip(radii,zs)]
# c = calc.TFS_Calculator(tfs_lenses=lenses, prefocus_lenses=tfs.xrt_lenses)

target = 399.88103
energy = 9500

combo, diff = c.find_solution(target, energy, n=4)
combo.show_info()
print(f'Difference to desired focus: {diff}')
