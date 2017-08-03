from transfocate.lens import Lens
from transfocate.lens import LensConnect
from transfocate.calculator import Calculator
from transfocate.calculator import TransfocatorCombo
from transfocate.transfocator import Transfocator

prefocus=[Lens("MFX:LENS:DIA:01:"), 
          Lens("MFX:LENS:DIA:02:"), 
          Lens("MFX:LENS:DIA:03:")]

tfs=[Lens("MFX:LENS:TFS:02:"), 
     Lens("MFX:LENS:TFS:03:"),
     Lens("MFX:LENS:TFS:04:"),
     Lens("MFX:LENS:TFS:05:"), 
     Lens("MFX:LENS:TFS:06:"), 
     Lens("MFX:LENS:TFS:07:"),
     Lens("MFX:LENS:TFS:08:"), 
     Lens("MFX:LENS:TFS:09:"), 
     Lens("MFX:LENS:TFS:10:")]

mfx_transfocator=Transfocator("MFX:LENS:", prefocus, tfs)
mfx_transfocator.nominal_sample = 378.9016
