import ophyd
import bluesky
import databroker
import time
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky.callbacks import LiveTable

from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO


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
    energy_input = Cpt(InputLinkOverrideHelper, ":BEAM:ENERGY")
    energy = Cpt(EpicsSignal, ":PLC:ENERGY_RBV", write_pv=":BEAM:ENERGY", kind="normal")
    plc_cycles = Cpt(EpicsSignalRO, ":PLC:CYCLE", kind="normal")

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
        for lens, state in zip(self.xrt_lenses, xrt):
            yield from bps.mv(lens.state, state)

        for lens, state in zip(self.tfs_lenses, tfs):
            yield from bps.mv(lens.state, state)

        yield from bps.wait()


def _wait_cycles(checkout, num_cycles):
    """
    Wait for a number of PLC cycles to elapse before continuing.
    """
    start_cycles = checkout.plc_cycles.get()

    def is_done():
        elapsed = checkout.plc_cycles.get() - start_cycles
        if elapsed < 0:
            elapsed += 65535
        return elapsed > num_cycles

    while not is_done():
        yield from bps.sleep(0.05)
        

def test_plan(tfs, checkout):
    yield from bps.open_run()
    yield from bps.stage(checkout)
    yield from bps.stage(tfs)
    yield from checkout.set_lens_state(
        xrt=[1, 0, 0],
        tfs=[0, 0, 0, 0, 0, 0, 0, 0, 1],
    )
    yield from bpp.stub_wrapper(bp.grid_scan(
        [tfs, checkout],
        checkout.energy, 0, 38000, 50, 
        snake_axes=False,
    ))
    yield from bps.close_run()


if __name__ == "__main__":
    import transfocate
    tfs = transfocate.Transfocator("MFX:LENS", name="tfs")
    checkout = LensInterlockCheckout("MFX:LENS", name="checkout")
    db = databroker.Broker.named('temp')
    RE = bluesky.RunEngine({})
    RE.subscribe(db.insert)
    fields = [
        'checkout_energy',
        'tfs_interlock_limits_low',
        'tfs_interlock_limits_high',
        'tfs_interlock_faulted',
        'tfs_interlock_state_fault',
        'tfs_interlock_limit_fault',
        'tfs_tfs_radius',
        'tfs_xrt_radius',
    ]
    tfs.wait_for_connection()
    checkout.wait_for_connection()
    # from bluesky.callbacks.best_effort import BestEffortCallback
    # bec = BestEffortCallback()
    # RE.subscribe(bec)
