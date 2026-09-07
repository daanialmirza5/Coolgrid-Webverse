from coolgrid_ml.data.city_grid import generate_city, GRID_COLS, GRID_ROWS
from coolgrid_ml.data.dataset import build_training_dataset, FEATURE_COLUMNS


def test_generate_city_deterministic():
    a = generate_city(seed=42)
    b = generate_city(seed=42)
    assert [w.ward_id for w in a] == [w.ward_id for w in b]
    assert [w.built_up_density for w in a] == [w.built_up_density for w in b]
    assert len(a) == GRID_COLS * GRID_ROWS


def test_ward_polygons_are_closed_rings():
    wards = generate_city(seed=42)
    for w in wards:
        assert w.polygon[0] == w.polygon[-1]
        assert len(w.polygon) == 5


def test_build_training_dataset_has_expected_columns():
    df = build_training_dataset(n_days=15, sample_stride=5, seed=1)
    for col in FEATURE_COLUMNS + ["lst_celsius", "ward_id"]:
        assert col in df.columns
    assert len(df) > 0
    assert df["lst_celsius"].between(-10, 70).all()
