import time

import matplotlib  # isort: skip

try:  # noqa
    matplotlib.use('Qt5Agg')  # noqa
except Exception:  # noqa
    ...  # noqa

import bluesky
import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
import databroker

import matplotlib.pyplot as plt
import ophyd
from bluesky.callbacks import LiveTable
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
    energy_input = Cpt(InputLinkOverrideHelper, ":BEAM:ENERGY")
    energy = Cpt(EpicsSignal, ":PLC:ENERGY_RBV", write_pv=":BEAM:ENERGY", kind="normal", auto_monitor=False)
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
        yield from bps.sleep(0.3)


def sweep_energy_plan(tfs, checkout, xrt_lens, num_steps=20):
    yield from bps.open_run()
    yield from bps.stage(checkout)
    yield from bps.stage(tfs)

    tfs_lens_combinations = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 1],
        [1, 1, 1, 1, 1, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    for tfs_lens_combo in tfs_lens_combinations:
        yield from checkout.set_lens_state(xrt_lens, tfs_lens_combo)
        yield from bpp.stub_wrapper(bp.grid_scan(
            [tfs, checkout],
            checkout.energy, 0, 38000, num_steps, 
            # snake_axes=False,
        ))

    yield from bps.close_run()


def plot_sweep_energy(dbi):
    """Plot the databroker results from a `sweep_energy_plan`."""
    df = dbi.table()
    df = df.set_index(df.energy)

    fig, ax = plt.subplots(constrained_layout=True, figsize=(12, 10))
    ax.set_yscale('log')

    ax.scatter(df.energy, df.trip_high, label='Trip high', color='black', marker='v')
    ax.scatter(df.energy, df.trip_low, label='Trip low', color='black', marker='^')
    
    when_faulted = df.where(df.faulted == 1).dropna()
    ax.scatter(when_faulted.index, when_faulted.tfs_radius, color='red', marker='x')
    
    ax.set_ylim(1, 1e4)
    
    xrt_radius, *_ = list(df.xrt_radius)
    ax.set_title(f'xrt_radius = {xrt_radius:.2f}')
    return fig


if __name__ == "__main__":
    plt.ion()
    tfs = transfocate.Transfocator("MFX:LENS", name="tfs")
    checkout = LensInterlockCheckout("MFX:LENS", name="checkout")
    db = databroker.Broker.named('temp')
    RE = bluesky.RunEngine({})
    RE.subscribe(db.insert)
    tfs.interlock.limits.low.name = 'trip_low'
    tfs.interlock.limits.high.name = 'trip_high'
    tfs.interlock.faulted.name = 'faulted'
    tfs.interlock.state_fault.name = 'state_fault'
    tfs.interlock.violated_fault.name = 'violated'
    tfs.interlock.min_fault.name = 'min_fault'
    tfs.interlock.lens_required_fault.name = 'lens_required_fault'
    tfs.interlock.table_fault.name = 'table_fault'
    checkout.energy.name = 'energy'
    tfs.tfs_radius.name = 'tfs_radius'
    tfs.xrt_radius.name = 'xrt_radius'

    fields = [
        'energy',

        'trip_low',
        'trip_high',

        'faulted',
        'state_fault',
        'violated',
        'min_fault',
        'lens_required_fault',
        'table_fault',

        'tfs_radius',
        'xrt_radius',
    ]
    tfs.wait_for_connection()
    checkout.wait_for_connection()
   
    for xrt_lens in [3]: # [1, 2, 3]: 
        RE(sweep_energy_plan(tfs, checkout, xrt_lens), LiveTable(fields))
        plot_sweep_energy(db[-1])
