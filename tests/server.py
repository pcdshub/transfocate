"""
Python IOC used for mocking the Transfocator 
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############
from pypvserver import PypvServer, PyPV


##########
# Module #
##########

logger = logging.getLogger(__name__)

def launch_server():
    logger.debug("Creating the Python IOC Server")
    server = PypvServer('TST:')
    server.add_pv(PyPV("TFS:LENS:01:RADIUS",  500.0))
    server.add_pv(PyPV("TFS:LENS:01:Z",       100.0))
    server.add_pv(PyPV("TFS:LENS:01:FOCUS",   50.0))
    server.add_pv(PyPV("TFS:LENS:01:STATE",   0)) #0 Not In, 1 In
    server.add_pv(PyPV("TFS:LENS:01:INSERT",  0)) #Set to 1 for Insert
    server.add_pv(PyPV("TFS:LENS:01:REMOVE",  0)) #Set to 1 for Remove
    server.add_pv(PyPV("TFS:LENS:XRT_ONLY",  200.0))
    server.add_pv(PyPV("TFS:LENS:MFX_ONLY",  750.0))
    server.add_pv(PyPV("LENS:BEAM:FAULTED",  0))
    
    server.add_pv(PyPV("TFS:LENS:02:RADIUS",  250.0))
    server.add_pv(PyPV("TFS:LENS:02:Z",       150.0))
    server.add_pv(PyPV("TFS:LENS:02:FOCUS",   25.0))
    server.add_pv(PyPV("TFS:LENS:02:STATE",   0))
    server.add_pv(PyPV("TFS:LENS:02:INSERT",  0))
    server.add_pv(PyPV("TFS:LENS:02:REMOVE",  0))

    server.add_pv(PyPV("TFS:LENS:03:RADIUS",  300.0))
    server.add_pv(PyPV("TFS:LENS:03:Z",       100.0))
    server.add_pv(PyPV("TFS:LENS:03:FOCUS",   20.0))
    server.add_pv(PyPV("TFS:LENS:03:STATE",   0))
    server.add_pv(PyPV("TFS:LENS:03:INSERT",  0))
    server.add_pv(PyPV("TFS:LENS:03:REMOVE",  0))
   
    #Run until process aborts
    logger.debug("Running server ...")
    while True:
        pass

if __name__ == '__main__':
    launch_server()
