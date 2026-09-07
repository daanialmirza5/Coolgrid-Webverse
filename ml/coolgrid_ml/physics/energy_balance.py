"""Simplified surface energy balance model.

This is a deliberately lightweight, bulk-parameter approximation of the
classic surface energy balance (Oke, 1982):

    Rn = H + LE + G

where Rn is net radiation, H is sensible heat flux, LE is latent heat flux
(evapotranspiration-driven cooling), and G is ground heat storage. Surface
temperature is then related to the sensible heat flux through a bulk
aerodynamic resistance formula:

    H = rho * cp * Ch * u * (Ts - Ta)  =>  Ts = Ta + H / (rho * cp * Ch * u)

ASSUMPTIONS (documented, not empirically validated against ground truth):
  - Net longwave loss is approximated as a fixed fraction of incoming
    shortwave radiation rather than modeled from emissivity/sky temperature.
  - Evapotranspiration availability is approximated from vegetation/water
    cover fraction and relative humidity rather than soil moisture or LAI.
  - Ground heat storage is approximated from built-up density and albedo
    rather than material thermal admittance.
  - The bulk heat transfer coefficient Ch is held constant; real values vary
    with surface roughness and atmospheric stability.

This model exists to (a) give CoolGrid's synthetic demo dataset physically
plausible internal relationships (more vegetation/water/albedo -> cooler;
more built-up/less wind -> hotter) and (b) act as a physics-informed
constraint that pulls learned predictions back toward physically sane
values (see `physics/pinn.py` and `prediction/forecaster.py`). It is NOT a
peer-reviewed, calibrated energy balance model and must not be presented as
one.
"""

from __future__ import annotations

from dataclasses import dataclass

# Bulk physical constants (typical near-surface air values).
AIR_DENSITY_KG_M3 = 1.2
SPECIFIC_HEAT_AIR_J_KGK = 1005.0
BULK_TRANSFER_COEFF = 0.009
NET_LONGWAVE_LOSS_FRACTION = 0.22  # fraction of incoming shortwave lost as net longwave
PRIESTLEY_TAYLOR_ALPHA = 1.26
MIN_WIND_MS = 0.5

# The bulk aerodynamic formula below is unstable at low wind speed (offset
# blows up as u -> 0). Real satellite-observed LST-minus-air-temperature
# offsets for even the hottest dry impervious surfaces rarely exceed ~20C,
# so the offset is clamped to that documented realistic band rather than
# left to diverge -- a deliberate bound on a simplified model, not a fitted
# physical constant.
MAX_SURFACE_OFFSET_C = 26.0
MIN_SURFACE_OFFSET_C = -3.0
CANYON_WIND_REDUCTION_MAX = 0.2  # max fractional wind-speed reduction from urban canyon drag


@dataclass
class EnergyBalanceEstimate:
    net_radiation_wm2: float
    latent_heat_flux_wm2: float
    ground_storage_flux_wm2: float
    sensible_heat_flux_wm2: float
    surface_air_offset_c: float
    lst_celsius: float


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def estimate_lst(
    air_temp_c: float,
    shortwave_wm2: float,
    albedo: float,
    green_space_pct: float,
    water_body_pct: float,
    built_up_density: float,
    humidity_pct: float,
    wind_speed_ms: float,
) -> EnergyBalanceEstimate:
    """Estimate land surface temperature from a simplified bulk energy balance.

    Args:
        air_temp_c: Ambient near-surface air temperature in degrees Celsius.
        shortwave_wm2: Downwelling solar shortwave radiation in W/m^2.
        albedo: Surface reflectance coefficient [0.02, 0.90].
        green_space_pct: Percentage of ward area covered by vegetation [0, 100].
        water_body_pct: Percentage of ward area covered by open water [0, 100].
        built_up_density: Fraction of ward area covered by impervious/built structures [0.0, 1.0].
        humidity_pct: Relative humidity percentage [0, 100].
        wind_speed_ms: 10m wind speed in m/s.

    Returns:
        EnergyBalanceEstimate dataclass containing radiation, flux components, and estimated LST.
    """

    shortwave_wm2 = max(shortwave_wm2, 0.0)
    albedo = _clamp(albedo, 0.02, 0.9)

    net_radiation = shortwave_wm2 * (1 - albedo) * (1 - NET_LONGWAVE_LOSS_FRACTION)

    veg_fraction = _clamp(green_space_pct / 100.0, 0.0, 1.0)
    water_fraction = _clamp(water_body_pct / 100.0, 0.0, 1.0)
    et_fraction = _clamp(veg_fraction * 0.85 + water_fraction * 1.15, 0.0, 1.15)
    moisture_availability = 0.35 + 0.65 * _clamp(humidity_pct / 100.0, 0.0, 1.0)
    latent_heat_flux = net_radiation * et_fraction * moisture_availability * (
        PRIESTLEY_TAYLOR_ALPHA / 1.4
    )
    latent_heat_flux = _clamp(latent_heat_flux, 0.0, net_radiation) if net_radiation > 0 else 0.0

    # Ground heat storage (G) is reported as a diagnostic -- the fraction of
    # net radiation banked into urban thermal mass, relevant to nighttime
    # heat retention -- but is NOT subtracted from the daytime sensible heat
    # flux. Subtracting it would (incorrectly, for a *skin-temperature*
    # estimate) make higher built-up density LOWER daytime LST, the opposite
    # of the observed urban heat island effect: low-conductivity impervious
    # materials heat up *more* at the surface precisely because they don't
    # readily conduct absorbed energy away.
    storage_fraction = _clamp(0.08 + 0.35 * built_up_density - 0.25 * albedo, 0.0, 0.55)
    ground_storage_flux = net_radiation * storage_fraction

    sensible_heat_flux = max(net_radiation - latent_heat_flux, -20.0)

    # Dense built environments reduce near-surface wind speed and turbulent
    # mixing (urban canyon / building drag effect), which weakens convective
    # heat removal from the surface -- this is what gives built-up density an
    # LST effect of its own, distinct from the albedo/vegetation it usually
    # correlates with.
    canyon_wind_reduction = 1.0 - CANYON_WIND_REDUCTION_MAX * _clamp(built_up_density, 0.0, 1.0)
    wind_eff = max(wind_speed_ms * canyon_wind_reduction, MIN_WIND_MS)
    denom = AIR_DENSITY_KG_M3 * SPECIFIC_HEAT_AIR_J_KGK * BULK_TRANSFER_COEFF * wind_eff
    surface_air_offset = _clamp(sensible_heat_flux / denom, MIN_SURFACE_OFFSET_C, MAX_SURFACE_OFFSET_C)

    lst = air_temp_c + surface_air_offset

    return EnergyBalanceEstimate(
        net_radiation_wm2=round(net_radiation, 2),
        latent_heat_flux_wm2=round(latent_heat_flux, 2),
        ground_storage_flux_wm2=round(ground_storage_flux, 2),
        sensible_heat_flux_wm2=round(sensible_heat_flux, 2),
        surface_air_offset_c=round(surface_air_offset, 3),
        lst_celsius=round(lst, 2),
    )
