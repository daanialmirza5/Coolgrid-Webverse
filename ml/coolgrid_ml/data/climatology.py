"""Shared seasonal weather climatology used by both the demo providers (to
generate historical observations) and the forecaster (to project future
weather deterministically). Loosely shaped on Pune's hot (Mar-Jun), monsoon
(Jun-Sep), and mild winter (Oct-Feb) pattern -- a simplified sinusoidal
approximation, not a calibrated meteorological model.
"""

from __future__ import annotations

import numpy as np

MONSOON_START_DOY = 152
MONSOON_END_DOY = 273


def seasonal_air_temp(day_of_year: int) -> float:
    phase = 2 * np.pi * (day_of_year - 110) / 365.0
    return 27.5 + 6.0 * np.cos(phase)


def seasonal_humidity(day_of_year: int) -> float:
    if MONSOON_START_DOY <= day_of_year <= MONSOON_END_DOY:
        return 78.0
    phase = 2 * np.pi * (day_of_year - 110) / 365.0
    return 45.0 - 10.0 * np.cos(phase)


def seasonal_radiation(day_of_year: int) -> float:
    if MONSOON_START_DOY <= day_of_year <= MONSOON_END_DOY:
        return 480.0
    phase = 2 * np.pi * (day_of_year - 172) / 365.0
    return 640.0 + 90.0 * np.cos(phase)


def seasonal_wind(day_of_year: int) -> float:
    return 3.2 if MONSOON_START_DOY <= day_of_year <= MONSOON_END_DOY else 2.2
