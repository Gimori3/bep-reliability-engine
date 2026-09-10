"""Redrawing a persisted study must not start another physical experiment."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def test_tail_figures_only_uses_record_without_loading_physics(monkeypatch, tmp_path):
    import tail_variance_study as driver

    record = {"levels": [{"sentinel": 1}], "n_study": 123, "n_replicates": 7}
    evidence = tmp_path / "evidence.json"
    original = json.dumps(record).encode()
    evidence.write_bytes(original)
    monkeypatch.setattr(driver, "OUTPUT_JSON", evidence)
    monkeypatch.setattr(sys, "argv", ["tail_variance_study", "--figures-only"])

    def forbidden(*args, **kwargs):
        raise AssertionError("A redraw must not load or evaluate a new experiment")

    monkeypatch.setattr(driver.Config, "from_yaml", forbidden)
    monkeypatch.setattr(driver, "evaluate_batch", forbidden)
    plotted = []
    monkeypatch.setattr(driver, "_plot", lambda *args: plotted.append(args))
    driver.main()
    assert plotted == [(record["levels"], 123, 7)]
    assert evidence.read_bytes() == original


def test_cross_section_drawing_inputs_match_the_production_record():
    import generate_annotated_cross_section as drawing

    record = yaml.safe_load(
        (drawing.REPO / "configs/kp62_0_historical_matrix.yaml").read_text()
    )
    for name in ("k_aq", "D_aq", "D_bl", "k_bl"):
        assert getattr(drawing, name.upper()) == record["priors"][name]["mean"]
    for drawn, key in (
        (drawing.L, "L"),
        (drawing.B_F, "foreshore_width"),
        (drawing.Z_TOE, "z_toe"),
        (drawing.HWL, "HWL"),
        (drawing.D_FORE, "D_fore"),
        (drawing.K_FORE, "k_fore"),
    ):
        assert drawn == record["geometry"][key]


def test_package_fragility_type_matches_the_driver_house_style():
    import _figstyle

    from bayesian_reliability_updating import plots

    assert plots._FRAGILITY_PRINT_PT == _figstyle.PRINT_PT


def test_persisted_update_reads_datum_and_peak_from_its_own_sidecars(
    monkeypatch, tmp_path
):
    import plot_persisted_fragility_update as driver

    stem = "tokachi_kp58.8_historical_matrix"
    saved = tmp_path / "results/phase2" / f"{stem}_posterior.json"
    saved.parent.mkdir(parents=True)
    parent = tmp_path / "results/different_parent.json"
    record = {
        "phase1": {"path": "results/different_parent.h5"},
        "phase2": {"event_chain": [{"record": {"peak_m_msl": 43.125}}]},
    }
    saved.write_text(json.dumps(record))
    parent.write_text(json.dumps({"config": {"geometry": {"z_toe": 37.625}}}))
    preserved = {p: p.read_bytes() for p in (saved, parent)}
    posterior = SimpleNamespace(
        fragility=SimpleNamespace(conditioning_grid=[38.0, 44.0]),
        P_f_trans_prior_raw=[0.0, 0.1],
        P_f_static_prior_raw=[0.0, 0.3],
    )
    monkeypatch.setattr(driver, "REPO", tmp_path)
    loaded = []

    def load(path):
        loaded.append(path)
        return posterior

    monkeypatch.setattr(driver.PosteriorResult, "load", load)
    calls = []
    monkeypatch.setattr(
        driver.plots, "plot_fragility_update", lambda *a, **kw: calls.append((a, kw))
    )
    driver.redraw("kp58_8")
    assert loaded == [saved.with_suffix(".h5")]
    args, kwargs = calls[0]
    assert args[:4] == (
        [38.0, 44.0],
        [0.0, 0.1],
        [0.0, 0.3],
        posterior.fragility,
    )
    assert kwargs["z_toe_m"] == 37.625
    assert kwargs["event_peak_m"] == 43.125
    assert (
        kwargs["publication_path"].name == "phase2_fragility_update_kp58_8_matrix.png"
    )
    assert all(p.read_bytes() == data for p, data in preserved.items())
