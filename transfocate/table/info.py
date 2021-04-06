import logging
import os
import pathlib

import pandas as pd

logger = logging.getLogger(__name__)

MODULE_PATH = pathlib.Path(__file__).parent.resolve()

EXCEL_SHEET = "Results"
ROW_START = 16
REGIONS = {
    "NO_LENS": {"usecols": "B:D"},
    "LENS3_333": {"usecols": "F:H"},
    "LENS2_428": {"usecols": "J:L"},
    "LENS1_750": {"usecols": "N:P"},
}

# Lens information
# Radii in micron:
xrt_lenses_radii = [750.0, 428.6, 333.3]
tfs_lens_radii = [
    # 0.0,
    500.0,
    300.0,
    250.0,
    200.0,
    125.0,
    62.5,
    50.0,
    50.0,
    50.0,
]


# Min effective radius is when all lenses are inserted:
MIN_RADIUS = 1 / sum(1 / radius for radius in tfs_lens_radii)
# Max radius is when the largest is inserted:
MAX_RADIUS = max(tfs_lens_radii)

# In these ranges, a transfocator lens MUST be inserted
REQUIRES_LENS_RANGE = {
    0: None,
    3: (9.50e3, 11.11e3),
    2: (8.28e3, 10.02e3),
    1: (5.96e3, 8.02e3),
}

MIN_ENERGY = {
    0: 0.0,
    3: 9.50e3,
    2: 8.28e3,
    1: 5.96e3,
}


def read_spreadsheet(spreadsheet=None):
    if spreadsheet is None:
        spreadsheet = SPREADSHEET

    for name, read_kw in REGIONS.items():
        df = pd.read_excel(
            spreadsheet,
            engine="openpyxl",
            sheet_name=EXCEL_SHEET,
            skiprows=ROW_START - 1,
            header=None,
            **read_kw
        )
        df.columns = ["energy", "trip_min", "trip_max"]
        df.energy *= 1e3  # keV -> eV
        df = df.dropna()
        df = df.set_index(df.energy)
        df.loc[df.trip_max > 1e4, "trip_max"] = 1e4
        yield name, df


# Configuration for reading the spreadsheet:
try:
    SPREADSHEET = pathlib.Path(os.environ["TRANSFOCATOR_SPREADSHEET"])
except KeyError:
    SPREADSHEET = MODULE_PATH / "MFX_EnergyLensInterlock_Tables_Transposed.xlsx"

if not SPREADSHEET.exists():
    logger.error("Table not available (``TRANSFOCATOR_SPREADSHEET``): %s", SPREADSHEET)
data = dict(read_spreadsheet())
