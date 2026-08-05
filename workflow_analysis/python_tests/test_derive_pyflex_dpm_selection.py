import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "derive_pyflex_dpm_selection.py"
)
SPEC = importlib.util.spec_from_file_location("derive_pyflex_dpm_selection", SCRIPT_PATH)
derive_pyflex = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(derive_pyflex)


def test_uniform_config_totals_selects_lowest_sum():
    spm_data = {
        "store_conf": ["TMPFS 16n", "BeeGFS 8n", "BeeGFS 16n"],
        "single+tracks": [10.0, 1.0, 2.0],
        "tracks+stats": [8.0, 2.0, 3.0],
    }

    totals = derive_pyflex.uniform_config_totals(spm_data)

    assert totals[0] == {"config": "BeeGFS 8n", "spm_total": 3.0}
    assert [row["config"] for row in totals] == [
        "BeeGFS 8n",
        "BeeGFS 16n",
        "TMPFS 16n",
    ]


def test_per_pair_winners_can_differ_from_uniform_selection():
    spm_data = {
        "store_conf": ["BeeGFS 4n", "BeeGFS 8n", "BeeGFS 16n"],
        "idfea+single": [4.0, 3.0, 1.0],
        "single+tracks": [2.0, 1.0, 4.0],
    }

    winners = derive_pyflex.per_pair_winners(spm_data)

    assert winners == [
        {"pair": "idfea+single", "config": "BeeGFS 16n", "spm": 1.0},
        {"pair": "single+tracks", "config": "BeeGFS 8n", "spm": 1.0},
    ]


def test_loads_literal_spm_data_without_importing_plotting_module(tmp_path):
    source = tmp_path / "spm_figures_pyflex.py"
    source.write_text(
        """
def create_spm_data():
    spm_data = {
        "store_conf": ["TMPFS 16n", "BeeGFS 8n"],
        "pair_a": [10.0, 1.0],
        "pair_b": [5.0, 2.0],
    }
    return spm_data
""",
        encoding="utf-8",
    )

    result = derive_pyflex.derive_selection(source)

    assert result["selection"] == "BeeGFS 8n"
    assert result["uniform_config_totals"][0]["spm_total"] == pytest.approx(3.0)


def test_rejects_missing_store_conf():
    with pytest.raises(ValueError, match="store_conf"):
        derive_pyflex.uniform_config_totals({"pair": [1.0, 2.0]})


def test_rejects_pair_values_with_wrong_length():
    spm_data = {
        "store_conf": ["TMPFS 16n", "BeeGFS 8n"],
        "pair": [1.0],
    }

    with pytest.raises(ValueError, match="must match store_conf length"):
        derive_pyflex.uniform_config_totals(spm_data)


def test_rejects_missing_literal_assignment(tmp_path):
    source = tmp_path / "spm_figures_pyflex.py"
    source.write_text(
        """
def create_spm_data():
    spm_data = dict(store_conf=["TMPFS 16n"])
    return spm_data
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Literal assignment"):
        derive_pyflex.load_spm_data(source)


def test_real_pyflex_spm_data_selects_beegfs_8n_when_available():
    source = derive_pyflex.DEFAULT_SOURCE
    if not source.exists():
        pytest.skip(f"{source} is not available in this checkout")

    result = derive_pyflex.derive_selection(source)

    assert result["selection"] == "BeeGFS 8n"
    assert result["uniform_config_totals"][0]["spm_total"] == pytest.approx(
        5.408843953136396
    )
