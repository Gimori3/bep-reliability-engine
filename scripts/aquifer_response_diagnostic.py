"""ADR-0032 Part 2 — the aquifer-response diagnostic (M4 instantaneous-vs-lag gate).

Executes the pre-registered ADR-0032 diagnostic against the real data. It does
**not** re-decide any pre-registered quantity: the specific-storage range, the
threshold Pi* on tau_aq / T_rise, the T_rise-as-primary-denominator convention,
and the governing-section list are imported from the package
(``hydraulics.AQUIFER_RESPONSE_*``) — the single source of truth shared with the
production-run metadata block — and applied unchanged.

For each governing section it:

1. draws the production LHS prior (the same call ``run._sample_prior`` makes) and
   computes the stochastic tau_aq = S_s * D_aq * D_bl / k_bl across all N rows,
   at the decision-driver S_s (upper bound);
2. characterizes the flood duration from the pinned canonical d4PDF event and a
   representative spread of HPB members, via ``hydrographs.flood_timescales``,
   at the node's own Eq. 4.19 rating;
3. forms Pi = tau_aq / T_rise (Check A) and the Nyquist native-resolution ratio
   (Check B) through ``hydraulics.aquifer_response_diagnostic``, and prints a
   per-section and an overall verdict.

Run:  python scripts/aquifer_response_diagnostic.py
Optional:  --members 150   (size of the representative d4PDF spread)
           --no-plot       (skip the figure)

Companion note: docs/decisions/adr0032-aquifer-response-diagnostic.md.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from bep_reliability_engine.config import Config
from bep_reliability_engine.hydraulics import (
    AQUIFER_RESPONSE_PI_THRESHOLD,
    AQUIFER_RESPONSE_SS_DRIVER_PER_M,
    AQUIFER_RESPONSE_SS_RANGE_PER_M,
    aquifer_response_diagnostic,
    aquifer_response_time,
)
from bep_reliability_engine.hydrographs import (
    build_hydrograph_record,
    flood_timescales,
    load_rating_coefficients,
    parse_member_header,
    rating_curve_path,
    read_discharge_ensemble,
    resolve_band_workbook,
    resolve_discharge_source_kp,
)
from bep_reliability_engine.run import _sample_prior

REPO = Path(__file__).resolve().parents[1]

# Pre-registered ADR-0032 constants — imported, never redefined (no drift).
S_S_LOWER, S_S_UPPER = AQUIFER_RESPONSE_SS_RANGE_PER_M
S_S_DRIVER = AQUIFER_RESPONSE_SS_DRIVER_PER_M
PI_THRESHOLD = AQUIFER_RESPONSE_PI_THRESHOLD
GOVERNING = {  # section -> config (matrix interpretation; tau_aq is d70-free)
    "KP58.8": "configs/kp58_8_historical_matrix.yaml",
    "KP60.0": "configs/kp60_0_historical_matrix.yaml",
}
CANONICAL_EVENT = "HPB_m064_1987"  # the production compound event (ADR-0020)


def load_flood_population(
    data_root: Path, river: str, kp: float, n_members: int
) -> tuple[list[dict], dict, float, str]:
    """Flood timescales for a representative HPB spread + the pinned canonical event.

    Returns ``(spread_metrics, canonical_metrics, dt_s, workbook_tag)``. The
    representative spread is stratified across peak-discharge magnitude so it
    spans flat members and the flashiest floods rather than over-weighting the
    common small events.
    """
    info = parse_member_header(CANONICAL_EVENT)
    a_kp, b_kp = load_rating_coefficients(rating_curve_path(data_root, river))[kp]
    workbook = resolve_band_workbook(
        data_root, river=river, kp=kp, scenario=str(info["scenario"])
    )
    _, proxied = resolve_discharge_source_kp(kp)
    time_hours, members = read_discharge_ensemble(workbook)

    def stage_of(name: str) -> np.ndarray:
        return build_hydrograph_record(
            time_hours,
            members[name],
            a_kp=a_kp,
            b_kp=b_kp,
            scenario=str(info["scenario"]),
            event_id=name,
        ).h

    names = list(members)
    peaks = np.array([float(np.max(members[n])) for n in names])
    order = np.argsort(peaks)
    picks = np.unique(np.linspace(0, len(names) - 1, n_members).astype(int))
    spread: list[dict] = []
    for i in picks:
        try:
            m = flood_timescales(stage_of(names[order[i]]), 3600.0)
        except ValueError:
            continue  # constant (flat) member — no peak
        if m["amplitude_m"] > 0.5:  # ignore essentially flat members
            spread.append(m)

    canon = flood_timescales(stage_of(CANONICAL_EVENT), 3600.0)
    tag = workbook.name + (f" (Q proxied from {proxied})" if proxied else "")
    return spread, canon, 3600.0, tag


def _fmt(seconds: float) -> str:
    return f"{seconds:8.0f} s ({seconds / 3600.0:5.2f} h)"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--members", type=int, default=150)
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()

    data_root = REPO / "data" / "raw"
    river = "Tokachi"

    print("=" * 78)
    print("ADR-0032 Part 2 - aquifer-response diagnostic")
    print(
        f"  S_s range [{S_S_LOWER:.0e}, {S_S_UPPER:.0e}] 1/m; driver = "
        f"{S_S_DRIVER:.0e} (upper bound)"
    )
    print(
        f"  Pi* = {PI_THRESHOLD} on tau_aq / T_rise; governing = " f"{list(GOVERNING)}"
    )
    print("=" * 78)

    spreads: dict[str, list[dict]] = {}
    blocks: dict[str, dict] = {}
    for section, cfg_path in GOVERNING.items():
        kp = float(section.replace("KP", ""))
        spread, canon, native_dt, tag = load_flood_population(
            data_root, river, kp, args.members
        )
        spreads[section] = spread
        t_rise = np.array([m["rising_limb_s"] for m in spread])
        t_plat = np.array([m["plateau_s"] for m in spread])
        t_rise_med = float(np.median(t_rise))
        t_rise_flashy = float(np.percentile(t_rise, 10))
        t_plat_med = float(np.median(t_plat))

        config = Config.from_yaml(REPO / cfg_path)
        theta = _sample_prior(config)
        specs = {m.name: m for m in config.priors.to_marginal_specs()}
        # Pre-registered analytic verdict at the MEDIAN representative T_rise.
        block = aquifer_response_diagnostic(
            segment_id=config.segment_id,
            d_aq_mean_m=specs["D_aq"].mean,
            d_bl_mean_m=specs["D_bl"].mean,
            k_bl_mean_mps=specs["k_bl"].mean,
            d_aq_cov=specs["D_aq"].cov,
            d_bl_cov=specs["D_bl"].cov,
            k_bl_cov=specs["k_bl"].cov,
            t_rise_s=t_rise_med,
            t_plateau_s=t_plat_med,
            native_dt_s=native_dt,
        )
        blocks[section] = block
        tau_sample = aquifer_response_time(
            theta.column("D_aq"),
            theta.column("D_bl"),
            theta.column("k_bl"),
            S_S_DRIVER,
        )
        p50, p90, p99, mx = np.percentile(tau_sample, [50, 90, 99, 100])
        # Worst plausible conjunction: sample p99 over the flashiest T_rise.
        pi_stress = float(p99 / t_rise_flashy)

        print(f"\n--- {section}  ({tag}) ---")
        print(f"  representative spread: {len(spread)} HPB members with a real peak")
        print(
            f"  canonical {CANONICAL_EVENT}: rise(10%->peak) "
            f"{_fmt(canon['rising_limb_s'])}, plateau {_fmt(canon['plateau_s'])}, "
            f"FWHM {_fmt(canon['fwhm_s'])}"
        )
        print(
            f"  T_rise onset->peak   median {_fmt(t_rise_med)}, "
            f"10th-pct {_fmt(t_rise_flashy)}"
        )
        print(f"  T_plateau (>=90%)    median {_fmt(t_plat_med)}")
        print(f"  tau_aq @S_s={S_S_DRIVER:.0e} (driver):")
        print(f"    central (prior means)  {_fmt(block['tau_aq_central_s'])}")
        print(f"    90th-pct-tau corner    {_fmt(block['tau_aq_corner90_s'])}")
        print(
            f"    sample p50/p90/p99/max {p50:.0f} / {p90:.0f} / {p99:.0f} "
            f"/ {mx:.0f} s"
        )
        print(
            f"  Pi = tau_aq / T_rise:  central {block['pi_central']:.3f}, "
            f"corner90 {block['pi_corner90']:.3f}, stress(p99/flashy) "
            f"{pi_stress:.3f}   [Pi* = {PI_THRESHOLD}]"
        )
        check_a = (
            "PASS (instantaneous)"
            if block["check_a_instantaneous_justified"]
            else "FAIL (activate lag)"
        )
        print(f"  Check A (central Pi <= Pi*): {check_a}")
        print(
            f"  Check B (native dt {native_dt:.0f}s <= T_feature/2): "
            f"{'PASS' if block['check_b_native_resolves'] else 'INSUFFICIENT'} "
            f"(T_feature={min(t_plat_med, t_rise_med):.0f}s)"
        )

    # --- overall verdict ------------------------------------------------------
    all_a = all(b["check_a_instantaneous_justified"] for b in blocks.values())
    corner_trips = any(b["pi_corner90"] > PI_THRESHOLD for b in blocks.values())
    all_b = all(b["check_b_native_resolves"] for b in blocks.values())
    print("\n" + "=" * 78)
    print("OVERALL VERDICT")
    if all_a and not corner_trips:
        print("  Check A: instantaneous default JUSTIFIED at every governing section")
        print("  (central Pi and the 90th-pct-tau corner both below Pi*).")
    elif all_a and corner_trips:
        print("  Check A: central Pi below Pi* everywhere, BUT the 90th-pct-tau corner")
        print("  exceeds Pi* somewhere -> ADR-0032 secondary (grey-zone) rule applies.")
    else:
        print("  Check A: a governing section EXCEEDS Pi* -> ACTIVATE LAG globally.")
    print(
        "  Check B: "
        + (
            "native resolution adequate at every section."
            if all_b
            else "native resolution marginal/insufficient."
        )
    )
    print("=" * 78)

    if not args.no_plot:
        _plot(spreads, blocks)


def _plot(spreads: dict[str, list[dict]], blocks: dict[str, dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    colors = {"KP58.8": "#1b6ca8", "KP60.0": "#c8553d"}
    for section, spread in spreads.items():
        rise_h = np.array([m["rising_limb_s"] for m in spread]) / 3600.0
        axes[0].hist(
            rise_h,
            bins=np.arange(0, rise_h.max() + 2) - 0.5,
            alpha=0.55,
            label=section,
            color=colors[section],
        )
    axes[0].axvline(
        1.5,
        color="k",
        ls=":",
        lw=1,
        label="~1.5 h plateau (flashy-river expectation)",
    )
    axes[0].set_xlabel("T_rise (10%->peak) [h]")
    axes[0].set_ylabel("d4PDF members")
    axes[0].set_title("Flood rising-limb time (native hourly grid)")
    axes[0].legend(fontsize=8)

    labels = list(blocks)
    x = np.arange(len(labels))
    axes[1].bar(
        x - 0.2,
        [blocks[s]["pi_central"] for s in labels],
        0.35,
        label="central θ",
        color="#4c9f70",
    )
    axes[1].bar(
        x + 0.2,
        [blocks[s]["pi_corner90"] for s in labels],
        0.35,
        label="90th-pct-τ corner",
        color="#e0a458",
    )
    axes[1].axhline(
        PI_THRESHOLD, color="r", ls="--", lw=1.2, label=f"Pi* = {PI_THRESHOLD}"
    )
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels)
    axes[1].set_ylabel("Pi = tau_aq / T_rise")
    axes[1].set_title(f"Time-constant ratio at S_s = {S_S_DRIVER:.0e} 1/m")
    axes[1].legend(fontsize=8)

    fig.tight_layout()
    out = REPO / "docs" / "figures" / "adr0032_aquifer_response.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    print(f"\nfigure -> {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
