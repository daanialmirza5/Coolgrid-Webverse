from coolgrid_ml.physics.energy_balance import estimate_lst


def test_more_vegetation_cools():
    hot = estimate_lst(
        air_temp_c=32, shortwave_wm2=650, albedo=0.12, green_space_pct=5,
        water_body_pct=0, built_up_density=0.8, humidity_pct=40, wind_speed_ms=2.0,
    )
    cool = estimate_lst(
        air_temp_c=32, shortwave_wm2=650, albedo=0.12, green_space_pct=60,
        water_body_pct=0, built_up_density=0.8, humidity_pct=40, wind_speed_ms=2.0,
    )
    assert cool.lst_celsius < hot.lst_celsius


def test_higher_albedo_cools():
    low_albedo = estimate_lst(
        air_temp_c=32, shortwave_wm2=650, albedo=0.10, green_space_pct=10,
        water_body_pct=0, built_up_density=0.7, humidity_pct=40, wind_speed_ms=2.0,
    )
    high_albedo = estimate_lst(
        air_temp_c=32, shortwave_wm2=650, albedo=0.45, green_space_pct=10,
        water_body_pct=0, built_up_density=0.7, humidity_pct=40, wind_speed_ms=2.0,
    )
    assert high_albedo.lst_celsius < low_albedo.lst_celsius


def test_more_built_up_heats():
    low_bud = estimate_lst(
        air_temp_c=32, shortwave_wm2=650, albedo=0.18, green_space_pct=20,
        water_body_pct=2, built_up_density=0.15, humidity_pct=40, wind_speed_ms=2.0,
    )
    high_bud = estimate_lst(
        air_temp_c=32, shortwave_wm2=650, albedo=0.18, green_space_pct=20,
        water_body_pct=2, built_up_density=0.85, humidity_pct=40, wind_speed_ms=2.0,
    )
    assert high_bud.lst_celsius > low_bud.lst_celsius


def test_lst_stays_within_physically_plausible_bounds_even_at_low_wind():
    est = estimate_lst(
        air_temp_c=35, shortwave_wm2=700, albedo=0.08, green_space_pct=0,
        water_body_pct=0, built_up_density=0.95, humidity_pct=20, wind_speed_ms=0.3,
    )
    assert 35 <= est.lst_celsius <= 65
