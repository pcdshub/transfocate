import time

import bluesky
import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
import databroker

import ophyd
from ophyd import Component as Cpt
from ophyd import EpicsSignal, EpicsSignalRO

import transfocate


class StageHelperMixin:
    def stage(self, *args, **kwargs):
        ret = super().stage(*args, **kwargs)
        # A delay for CA links to get reconfigured
        time.sleep(0.05)
        self._stage_unstage_hook()
        return ret

    def unstage(self, *args, **kwargs):
        ret = super().unstage(*args, **kwargs)
        # A delay for CA links to get reconfigured
        time.sleep(0.05)
        self._stage_unstage_hook()
        return ret


class InputLinkOverrideHelper(StageHelperMixin, ophyd.Device):
    """
    Helper Device for overriding a record's input link during a bluesky scan.
    """
    # TODO output_link variant for ATEF?
    input_link = Cpt(EpicsSignal, ".INP$", kind="config", string=True)
    proc = Cpt(EpicsSignal, ".PROC", kind="omitted")
    # TODO: generalizing fails with `string=True` here:
    value = Cpt(EpicsSignal, "", kind="normal")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs = {
            # Disable the input link entirely:
            "input_link": "",
        }

    def _stage_unstage_hook(self):
        """Poke record after switching its INP field."""
        self.proc.put(1)


class OutputModeSelectOverrideHelper(StageHelperMixin, ophyd.Device):
    """
    Helper Device for overriding a record's OMSL during a bluesky scan.
    """
    omsl = Cpt(EpicsSignal, ".OMSL", kind="config", string=True)
    proc = Cpt(EpicsSignal, ".PROC", kind="omitted")
    value = Cpt(EpicsSignal, "", kind="normal")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs = {
            # Disable closed_loop when staging:
            "omsl": "supervisory",
        }

    def _stage_unstage_hook(self):
        """Poke record after switching its OMSL."""
        self.proc.put(1)


class LensCheckout(ophyd.Device):
    state_omsl = Cpt(OutputModeSelectOverrideHelper, ":STATE")
    state = Cpt(EpicsSignal, ":STATE", kind="normal")  # , string=True)

    known_omsl = Cpt(OutputModeSelectOverrideHelper, ":SAFE")
    known = Cpt(EpicsSignal, ":SAFE", kind="normal", string=True)


class LensInterlockCheckout(ophyd.Device):
    bypass = Cpt(
        EpicsSignal,
        ":BYPASS:STATUS", write_pv=":BYPASS:SET",
        doc="Bypass in use?",
    )
    energy = Cpt(
        EpicsSignal,
        ":PLC:ENERGY_RBV",
        write_pv=":BYPASS:ENERGY",  # <-- note bypass PV
        kind="normal", auto_monitor=False
    )
    plc_cycles = Cpt(EpicsSignalRO, ":PLC:CYCLE", kind="normal")
    update_seq = Cpt(EpicsSignalRO, ":PLC:UPDATE_SEQ", kind="normal")

    # XRT Lenses
    xrt_03 = Cpt(LensCheckout, ":DIA:03")
    xrt_02 = Cpt(LensCheckout, ":DIA:02")
    xrt_01 = Cpt(LensCheckout, ":DIA:01")

    # TFS Lenses
    tfs_02 = Cpt(LensCheckout, ":TFS:02")
    tfs_03 = Cpt(LensCheckout, ":TFS:03")
    tfs_04 = Cpt(LensCheckout, ":TFS:04")
    tfs_05 = Cpt(LensCheckout, ":TFS:05")
    tfs_06 = Cpt(LensCheckout, ":TFS:06")
    tfs_07 = Cpt(LensCheckout, ":TFS:07")
    tfs_08 = Cpt(LensCheckout, ":TFS:08")
    tfs_09 = Cpt(LensCheckout, ":TFS:09")
    tfs_10 = Cpt(LensCheckout, ":TFS:10")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs = {
            # Set the bypass during scans
            "bypass": 1,
        }

    @property
    def lenses(self):
        """
        Component lenses
        """
        return [getattr(self, dev) for dev in self._sub_devices
                if isinstance(getattr(self, dev), LensCheckout)]

    @property
    def xrt_lenses(self):
        """Pre-focusing lenses in the XRT."""
        return [lens for lens in self.lenses if 'DIA' in lens.prefix]

    @property
    def tfs_lenses(self):
        """Transfocator lenses."""
        return [lens for lens in self.lenses if 'TFS' in lens.prefix]

    def set_lens_state(self, xrt, tfs):
        """Bluesky plan - set lens state."""
        xrt_lenses = {
            0: [0, 0, 0],
            1: [0, 0, 1],
            2: [0, 1, 0],
            3: [1, 0, 0],
        }
        for lens, state in zip(self.xrt_lenses, xrt_lenses[xrt]):
            yield from bps.mv(lens.state, state)

        for lens, state in zip(self.tfs_lenses, tfs):
            yield from bps.mv(lens.state, state)

        yield from bps.wait()
        yield from bps.sleep(0.5)


def sweep_energy_plan(tfs, checkout, xrt_lens, num_steps):
    yield from bps.open_run()
    yield from bps.stage(checkout)
    yield from bps.stage(tfs)

    tfs_lens_combinations = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],  # 0.00
        [1, 1, 1, 1, 1, 1, 1, 1, 1],  # 10.17
        # [0, 1, 1, 1, 1, 1, 1, 1, 1],  # 10.38
        # [1, 0, 1, 1, 1, 1, 1, 1, 1],  # 10.53
        # [1, 1, 0, 1, 1, 1, 1, 1, 1],  # 10.60
        # [1, 1, 1, 0, 1, 1, 1, 1, 1],  # 10.71
        # [0, 0, 1, 1, 1, 1, 1, 1, 1],  # 10.75
        # [0, 1, 0, 1, 1, 1, 1, 1, 1],  # 10.83
        # [0, 1, 1, 0, 1, 1, 1, 1, 1],  # 10.95
        # [1, 0, 0, 1, 1, 1, 1, 1, 1],  # 10.99
        # [1, 1, 1, 1, 0, 1, 1, 1, 1],  # 11.07
        # [1, 0, 1, 0, 1, 1, 1, 1, 1],  # 11.11
        # [1, 1, 0, 0, 1, 1, 1, 1, 1],  # 11.19
        # [0, 0, 0, 1, 1, 1, 1, 1, 1],  # 11.24
        # [0, 1, 1, 1, 0, 1, 1, 1, 1],  # 11.32
        # [0, 0, 1, 0, 1, 1, 1, 1, 1],  # 11.36
        # [0, 1, 0, 0, 1, 1, 1, 1, 1],  # 11.45
        # [1, 0, 1, 1, 0, 1, 1, 1, 1],  # 11.49
        # [1, 1, 0, 1, 0, 1, 1, 1, 1],  # 11.58
        # [1, 0, 0, 0, 1, 1, 1, 1, 1],  # 11.63
        # [1, 1, 1, 0, 0, 1, 1, 1, 1],  # 11.72
        # [0, 0, 1, 1, 0, 1, 1, 1, 1],  # 11.76
        # [0, 1, 0, 1, 0, 1, 1, 1, 1],  # 11.86
        # [0, 0, 0, 0, 1, 1, 1, 1, 1],  # 11.90
        # [0, 1, 1, 0, 0, 1, 1, 1, 1],  # 12.00
        # [1, 0, 0, 1, 0, 1, 1, 1, 1],  # 12.05
        # [1, 1, 1, 1, 1, 0, 1, 1, 1],  # 12.15
        # [1, 0, 1, 0, 0, 1, 1, 1, 1],  # 12.20
        # [1, 1, 0, 0, 0, 1, 1, 1, 1],  # 12.30
        # [0, 0, 0, 1, 0, 1, 1, 1, 1],  # 12.35
        # [0, 1, 1, 1, 1, 0, 1, 1, 1],  # 12.45
        # [0, 0, 1, 0, 0, 1, 1, 1, 1],  # 12.50
        # [0, 1, 0, 0, 0, 1, 1, 1, 1],  # 12.61
        # [1, 0, 1, 1, 1, 0, 1, 1, 1],  # 12.66
        # [1, 1, 1, 1, 1, 1, 1, 1, 0],  # 12.77
        # [1, 0, 0, 0, 0, 1, 1, 1, 1],  # 12.82
        # [1, 1, 1, 0, 1, 0, 1, 1, 1],  # 12.93
        # [0, 0, 1, 1, 1, 0, 1, 1, 1],  # 12.99
        # [0, 1, 1, 1, 1, 1, 1, 1, 0],  # 13.10
        # [0, 0, 0, 0, 0, 1, 1, 1, 1],  # 13.16
        # [0, 1, 1, 0, 1, 0, 1, 1, 1],  # 13.27
        # [1, 0, 1, 1, 1, 1, 1, 1, 0],  # 13.33
        # [1, 1, 1, 1, 0, 0, 1, 1, 1],  # 13.45
        # [1, 0, 1, 0, 1, 0, 1, 1, 1],  # 13.51
        # [1, 1, 1, 0, 1, 1, 1, 1, 0],  # 13.64
        # [0, 0, 1, 1, 1, 1, 1, 1, 0],  # 13.70
        # [0, 1, 1, 1, 0, 0, 1, 1, 1],  # 13.82
        # [0, 1, 0, 1, 1, 1, 1, 1, 0],  # 13.82
        # [0, 0, 1, 0, 1, 0, 1, 1, 1],  # 13.89
        # [0, 1, 1, 0, 1, 1, 1, 1, 0],  # 14.02
        # [1, 0, 1, 1, 0, 0, 1, 1, 1],  # 14.08
        # [1, 1, 1, 1, 0, 1, 1, 1, 0],  # 14.22
        # [1, 0, 1, 0, 1, 1, 1, 1, 0],  # 14.29
        # [1, 1, 1, 0, 0, 0, 1, 1, 1],  # 14.42
        # [0, 0, 1, 1, 0, 0, 1, 1, 1],  # 14.49
        # [0, 1, 1, 1, 0, 1, 1, 1, 0],  # 14.63
        # [0, 0, 1, 0, 1, 1, 1, 1, 0],  # 14.71
        # [0, 1, 1, 0, 0, 0, 1, 1, 1],  # 14.85
        # [1, 0, 1, 1, 0, 1, 1, 1, 0],  # 14.93
        # [1, 1, 0, 1, 0, 1, 1, 1, 0],  # 15.08
        # [1, 0, 1, 0, 0, 0, 1, 1, 1],  # 15.15
        # [1, 1, 1, 0, 0, 1, 1, 1, 0],  # 15.31
        # [0, 0, 1, 1, 0, 1, 1, 1, 0],  # 15.38
        # [0, 1, 0, 1, 0, 1, 1, 1, 0],  # 15.54
        # [0, 0, 1, 0, 0, 0, 1, 1, 1],  # 15.62
        # [0, 1, 1, 0, 0, 1, 1, 1, 0],  # 15.79
        # [1, 0, 0, 1, 0, 1, 1, 1, 0],  # 15.87
        # [1, 1, 1, 1, 1, 0, 1, 1, 0],  # 16.04
        # [1, 0, 1, 0, 0, 1, 1, 1, 0],  # 16.13
        # [1, 1, 0, 0, 0, 1, 1, 1, 0],  # 16.30
        # [0, 0, 0, 1, 0, 1, 1, 1, 0],  # 16.39
        # [0, 1, 1, 1, 1, 0, 1, 1, 0],  # 16.57
        # [0, 0, 1, 0, 0, 1, 1, 1, 0],  # 16.67
        # [0, 1, 0, 0, 0, 1, 1, 1, 0],  # 16.85
        # [1, 0, 1, 1, 1, 0, 1, 1, 0],  # 16.95
        # [1, 1, 1, 1, 1, 1, 1, 0, 0],  # 17.14
        # [1, 0, 0, 0, 0, 1, 1, 1, 0],  # 17.24
        # [1, 1, 1, 0, 1, 0, 1, 1, 0],  # 17.44
        # [0, 0, 1, 1, 1, 0, 1, 1, 0],  # 17.54
        # [0, 1, 1, 1, 1, 1, 1, 0, 0],  # 17.75
        # [0, 0, 0, 0, 0, 1, 1, 1, 0],  # 17.86
        # [0, 1, 1, 0, 1, 0, 1, 1, 0],  # 18.07
        # [1, 0, 1, 1, 1, 1, 1, 0, 0],  # 18.18
        # [1, 1, 1, 1, 0, 0, 1, 1, 0],  # 18.40
        # [1, 0, 1, 0, 1, 0, 1, 1, 0],  # 18.52
        # [1, 1, 1, 0, 1, 1, 1, 0, 0],  # 18.75
        # [0, 0, 1, 1, 1, 1, 1, 0, 0],  # 18.87
        # [0, 1, 1, 1, 0, 0, 1, 1, 0],  # 19.11
        # [0, 1, 0, 1, 1, 1, 1, 0, 0],  # 19.11
        # [0, 0, 1, 0, 1, 0, 1, 1, 0],  # 19.23
        # [0, 1, 1, 0, 1, 1, 1, 0, 0],  # 19.48
        # [1, 0, 1, 1, 0, 0, 1, 1, 0],  # 19.61
        # [1, 1, 1, 1, 0, 1, 1, 0, 0],  # 19.87
        [1, 0, 1, 0, 1, 1, 1, 0, 0],  # 20.00
        # [1, 1, 1, 0, 0, 0, 1, 1, 0],  # 20.27
        # [0, 0, 1, 1, 0, 0, 1, 1, 0],  # 20.41
        # [0, 1, 1, 1, 0, 1, 1, 0, 0],  # 20.69
        # [0, 0, 1, 0, 1, 1, 1, 0, 0],  # 20.83
        # [0, 1, 1, 0, 0, 0, 1, 1, 0],  # 21.13
        # [1, 0, 1, 1, 0, 1, 1, 0, 0],  # 21.28
        # [1, 1, 0, 1, 0, 1, 1, 0, 0],  # 21.58
        # [1, 0, 1, 0, 0, 0, 1, 1, 0],  # 21.74
        # [1, 1, 1, 0, 0, 1, 1, 0, 0],  # 22.06
        # [0, 0, 1, 1, 0, 1, 1, 0, 0],  # 22.22
        # [0, 1, 0, 1, 0, 1, 1, 0, 0],  # 22.56
        # [0, 0, 1, 0, 0, 0, 1, 1, 0],  # 22.73
        # [0, 1, 1, 0, 0, 1, 1, 0, 0],  # 23.08
        # [1, 0, 0, 1, 0, 1, 1, 0, 0],  # 23.26
        # [1, 1, 1, 1, 1, 0, 1, 0, 0],  # 23.62
        # [1, 0, 1, 0, 0, 1, 1, 0, 0],  # 23.81
        # [1, 1, 0, 0, 0, 1, 1, 0, 0],  # 24.19
        # [0, 0, 0, 1, 0, 1, 1, 0, 0],  # 24.39
        # [0, 1, 1, 1, 1, 0, 1, 0, 0],  # 24.79
        # [0, 0, 1, 0, 0, 1, 1, 0, 0],  # 25.00
        # [0, 1, 0, 0, 0, 1, 1, 0, 0],  # 25.42
        # [1, 0, 1, 1, 1, 0, 1, 0, 0],  # 25.64
        # [1, 1, 1, 1, 1, 1, 0, 0, 0],  # 26.09
        # [1, 0, 0, 0, 0, 1, 1, 0, 0],  # 26.32
        # [1, 1, 1, 0, 1, 0, 1, 0, 0],  # 26.79
        # [0, 0, 1, 1, 1, 0, 1, 0, 0],  # 27.03
        # [0, 1, 1, 1, 1, 1, 0, 0, 0],  # 27.52
        # [0, 1, 0, 1, 1, 0, 1, 0, 0],  # 27.52
        # [0, 0, 0, 0, 0, 1, 1, 0, 0],  # 27.78
        # [0, 1, 1, 0, 1, 0, 1, 0, 0],  # 28.30
        # [1, 0, 1, 1, 1, 1, 0, 0, 0],  # 28.57
        # [1, 1, 1, 1, 0, 0, 1, 0, 0],  # 29.13
        # [1, 0, 1, 0, 1, 0, 1, 0, 0],  # 29.41
        [1, 1, 1, 0, 1, 1, 0, 0, 0],  # 30.00
        # [0, 0, 1, 1, 1, 1, 0, 0, 0],  # 30.30
        # [0, 1, 1, 1, 0, 0, 1, 0, 0],  # 30.93
        # [0, 1, 0, 1, 1, 1, 0, 0, 0],  # 30.93
        # [0, 0, 1, 0, 1, 0, 1, 0, 0],  # 31.25
        # [0, 1, 1, 0, 1, 1, 0, 0, 0],  # 31.91
        # [1, 0, 1, 1, 0, 0, 1, 0, 0],  # 32.26
        # [1, 1, 1, 1, 0, 1, 0, 0, 0],  # 32.97
        # [1, 0, 1, 0, 1, 1, 0, 0, 0],  # 33.33
        # [1, 1, 1, 0, 0, 0, 1, 0, 0],  # 34.09
        # [0, 0, 1, 1, 0, 0, 1, 0, 0],  # 34.48
        # [0, 1, 1, 1, 0, 1, 0, 0, 0],  # 35.29
        # [0, 0, 1, 0, 1, 1, 0, 0, 0],  # 35.71
        # [0, 1, 1, 0, 0, 0, 1, 0, 0],  # 36.59
        # [1, 0, 1, 1, 0, 1, 0, 0, 0],  # 37.04
        # [1, 1, 0, 1, 0, 1, 0, 0, 0],  # 37.97
        # [1, 0, 1, 0, 0, 0, 1, 0, 0],  # 38.46
        # [1, 1, 1, 0, 0, 1, 0, 0, 0],  # 39.47
        [0, 0, 1, 1, 0, 1, 0, 0, 0],  # 40.00
        # [0, 1, 0, 1, 0, 1, 0, 0, 0],  # 41.10
        # [0, 0, 1, 0, 0, 0, 1, 0, 0],  # 41.67
        # [0, 1, 1, 0, 0, 1, 0, 0, 0],  # 42.86
        # [1, 0, 0, 1, 0, 1, 0, 0, 0],  # 43.48
        # [1, 1, 1, 1, 1, 0, 0, 0, 0],  # 44.78
        # [1, 0, 1, 0, 0, 1, 0, 0, 0],  # 45.45
        # [1, 1, 0, 0, 0, 1, 0, 0, 0],  # 46.87
        # [0, 0, 0, 1, 0, 1, 0, 0, 0],  # 47.62
        # [0, 1, 1, 1, 1, 0, 0, 0, 0],  # 49.18
        [0, 0, 1, 0, 0, 1, 0, 0, 0],  # 50.00
        # [0, 1, 0, 0, 0, 1, 0, 0, 0],  # 51.72
        # [1, 0, 1, 1, 1, 0, 0, 0, 0],  # 52.63
        # [1, 1, 0, 1, 1, 0, 0, 0, 0],  # 54.55
        # [1, 0, 0, 0, 0, 1, 0, 0, 0],  # 55.56
        # [1, 1, 1, 0, 1, 0, 0, 0, 0],  # 57.69
        # [0, 0, 1, 1, 1, 0, 0, 0, 0],  # 58.82
        # [0, 1, 0, 1, 1, 0, 0, 0, 0],  # 61.22
        # [0, 0, 0, 0, 0, 1, 0, 0, 0],  # 62.50
        # [0, 1, 1, 0, 1, 0, 0, 0, 0],  # 65.22
        # [1, 0, 0, 1, 1, 0, 0, 0, 0],  # 66.67
        # [1, 1, 1, 1, 0, 0, 0, 0, 0],  # 69.77
        # [1, 0, 1, 0, 1, 0, 0, 0, 0],  # 71.43
        # [1, 1, 0, 0, 1, 0, 0, 0, 0],  # 75.00
        # [0, 0, 0, 1, 1, 0, 0, 0, 0],  # 76.92
        [0, 1, 1, 1, 0, 0, 0, 0, 0],  # 81.08
        # [0, 0, 1, 0, 1, 0, 0, 0, 0],  # 83.33
        # [0, 1, 0, 0, 1, 0, 0, 0, 0],  # 88.24
        # [1, 0, 1, 1, 0, 0, 0, 0, 0],  # 90.91
        # [1, 1, 0, 1, 0, 0, 0, 0, 0],  # 96.77
        [1, 0, 0, 0, 1, 0, 0, 0, 0],  # 100.00
        # [1, 1, 1, 0, 0, 0, 0, 0, 0],  # 107.14
        # [0, 0, 1, 1, 0, 0, 0, 0, 0],  # 111.11
        # [0, 1, 0, 1, 0, 0, 0, 0, 0],  # 120.00
        # [0, 0, 0, 0, 1, 0, 0, 0, 0],  # 125.00
        # [0, 1, 1, 0, 0, 0, 0, 0, 0],  # 136.36
        # [1, 0, 0, 1, 0, 0, 0, 0, 0],  # 142.86
        # [1, 0, 1, 0, 0, 0, 0, 0, 0],  # 166.67
        # [1, 1, 0, 0, 0, 0, 0, 0, 0],  # 187.50
        [0, 0, 0, 1, 0, 0, 0, 0, 0],  # 200.00
        [0, 0, 1, 0, 0, 0, 0, 0, 0],  # 250.00
        [0, 1, 0, 0, 0, 0, 0, 0, 0],  # 300.00
        [1, 0, 0, 0, 0, 0, 0, 0, 0],  # 500.00
    ]
    for tfs_lens_combo in tfs_lens_combinations:
        # Put us at the beginning of the range prior to lens insertion
        # (TODO: This being required may indicate a bug at fast rates...)
        yield from bps.mv(checkout.energy, 0.0)

        yield from checkout.set_lens_state(xrt_lens, tfs_lens_combo)
        yield from bpp.stub_wrapper(bp.grid_scan(
            [tfs, checkout],
            checkout.energy, 0, 38000, num_steps,
            # snake_axes=False,
        ))

    yield from bps.close_run()
