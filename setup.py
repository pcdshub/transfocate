import versioneer
from setuptools import (setup, find_packages)


setup(name     = 'transfocate',
      version  = versioneer.get_version(),
      cmdclass = versioneer.get_cmdclass(),
      license  = 'BSD-like',
      author   = 'SLAC National Accelerator Laboratory',

      packages    = find_packages(),
      description = 'Automated Calculation of Transfocator Focusing Optics',
      include_package_data = True,
    )
