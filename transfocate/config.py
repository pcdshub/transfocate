from transfocate.lens import Lens
from transfocate.lens import LensConnect
from transfocate.calculator import Calculator
from transfocate.calculator import TransfocatorCombo
from transfocate.transfocator import Transfocator

prefocus=[Lens("MFX:LENS:DIA:01:", name='6K70'),
          Lens("MFX:LENS:DIA:02:", name='7K50'),
          Lens("MFX:LENS:DIA:03:", name='9K45')]

tfs=[Lens("MFX:LENS:TFS:02:", name='lens_2'),
     Lens("MFX:LENS:TFS:03:", name='lens_3'),
     Lens("MFX:LENS:TFS:04:", name='lens_4'),
     Lens("MFX:LENS:TFS:05:", name='lens_5'),
     Lens("MFX:LENS:TFS:06:", name='lens_6'),
     Lens("MFX:LENS:TFS:07:", name='lens_6'),
     Lens("MFX:LENS:TFS:08:", name='lens_7'),
     Lens("MFX:LENS:TFS:09:", name='lens_8'),
     Lens("MFX:LENS:TFS:10:", name='lens_9')]

mfx_transfocator=Transfocator("MFX:LENS:", prefocus, tfs,
                              name='mfx_transfocator')
mfx_transfocator.nominal_sample = 378.9016
