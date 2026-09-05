"""Segment registry: the 200 m evaluation nodes and their BEP sources.

ADR-0038 decision 2. The nodes are the committed rating-curve KP grid
(``data/raw/rating_curves/HQrelation_{river}Riv_2017.csv``, 0.2 km spacing),
bounded to the thesis study reaches: Tokachi right bank KP 53.8-62.8 and
Satsunai left bank KP 3.2-16.6 (thesis §"Geographical Scope"). Each segment
optionally carries the OYO cross-section whose BEP fragility it inherits.

The default ``bep_source_policy='exact'`` assigns BEP curves only to the
four OYO sections' own segments; the borehole-free remainder carries
``bep_source=None`` — the honest data gap the thesis tiers as "bounded
extrapolation" territory. ``'nearest'`` (each segment inherits the nearest
OYO section within the same river/bank) exists for stamped sensitivity
exploration only.

.. warning::
   Under ``'nearest'`` a whole zone of segments shares one OYO section's BEP
   curve, so those segments are perfectly BEP-correlated by construction.
   Composing such a densely-populated reach as a series union of *independent*
   segments over-counts the independent failure opportunities by
   ``lambda_ac / segment_spacing`` (1.25 at the ADR-0037 primary; the length
   effect at reach scale). Route it through
   :func:`~system_integration.composition.length_effect_effective_count` /
   :func:`~system_integration.composition.reach_union` instead — never a naive
   independent product (seepage-length L study,
   ``docs/decisions/seepage-length-L-study.md`` §2).

Uemura's aggregation into Sections (Tokachi 1-5, Satsunai 1-4) is an
author-supplied table (ADR-0038 seam): ``load_section_table`` validates it;
until it arrives every result is reported per segment.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from bep_reliability_engine.hydrographs import (
    load_rating_coefficients,
    rating_curve_path,
)

__all__ = [
    "STUDY_REACHES",
    "OYO_BEP_SECTIONS",
    "KASUMI_TEI_CSV",
    "Segment",
    "SegmentRegistry",
    "build_registry",
    "load_kasumi_tei",
    "kasumi_tei_coincidences",
    "load_section_table",
]

# Thesis study reaches (inclusive KP bounds), per the Research Scope section.
STUDY_REACHES: dict[tuple[str, str], tuple[float, float]] = {
    ("Tokachi", "right"): (53.8, 62.8),
    ("Satsunai", "left"): (3.2, 16.6),
}

# The four confined OYO cross-sections with engine-derived BEP fragility
# (data/processed/tokachi_bep_inputs.csv; KP 63.4 excluded by default).
OYO_BEP_SECTIONS: tuple[tuple[str, str, float], ...] = (
    ("Tokachi", "right", 57.4),
    ("Tokachi", "right", 58.8),
    ("Tokachi", "right", 60.0),
    ("Tokachi", "right", 62.0),
)

_KP_TOL = 1e-6


@dataclass(frozen=True)
class Segment:
    """One 200 m evaluation segment.

    Attributes
    ----------
    river : str
        ``'Tokachi'`` or ``'Satsunai'``.
    bank : str
        ``'right'`` or ``'left'`` (fixed per river by the study scope).
    kp : float
        The segment's center node KP [km] on the 0.2 km rating grid.
    bep_source_kp : float or None
        KP of the OYO cross-section whose BEP fragility this segment
        inherits, or None when the segment has no defensible BEP curve
        (default ``'exact'`` policy for non-OYO segments).
    section_id : str or None
        Uemura section identifier once the author-supplied table is loaded;
        None until then.
    """

    river: str
    bank: str
    kp: float
    bep_source_kp: float | None = None
    section_id: str | None = None


@dataclass(frozen=True)
class SegmentRegistry:
    """The full study-reach segment set plus its provenance.

    Attributes
    ----------
    segments : tuple of Segment
        All segments, ordered by (river, kp).
    bep_source_policy : str
        ``'exact'`` (default) or ``'nearest'`` — stamped so downstream
        results can never silently mix policies.
    """

    segments: tuple[Segment, ...]
    bep_source_policy: str = "exact"
    _by_key: dict[tuple[str, float], Segment] = field(
        default_factory=dict, repr=False, compare=False
    )

    def __post_init__(self) -> None:  # populate the lookup (frozen dataclass)
        object.__setattr__(
            self,
            "_by_key",
            {(s.river, round(s.kp, 3)): s for s in self.segments},
        )

    def segment_at(self, river: str, kp: float) -> Segment:
        """Return the segment at (river, kp).

        Raises
        ------
        KeyError
            If no segment exists at that node.
        """
        try:
            return self._by_key[(river, round(kp, 3))]
        except KeyError:
            raise KeyError(
                f"no segment at {river} KP {kp:g}; the registry covers "
                f"{sorted(set(s.river for s in self.segments))} on the 0.2 km "
                "grid inside the study reaches."
            ) from None

    def bep_segments(self) -> tuple[Segment, ...]:
        """Segments that carry a BEP source (the composable subset)."""
        return tuple(s for s in self.segments if s.bep_source_kp is not None)


def build_registry(
    data_root: str | Path = "data/raw",
    *,
    bep_source_policy: str = "exact",
) -> SegmentRegistry:
    """Build the study-reach registry from the committed rating grid.

    Parameters
    ----------
    data_root : str or pathlib.Path
        Raw data root holding ``rating_curves/`` (the M3 convention).
    bep_source_policy : {'exact', 'nearest'}
        ``'exact'``: only the four OYO sections' own segments get a
        ``bep_source_kp``. ``'nearest'``: every segment inherits the nearest
        OYO section on its river/bank — sensitivity exploration only
        (ADR-0038 decision 2); the policy is stamped on the registry.

    Returns
    -------
    SegmentRegistry
        Segments ordered by (river, kp).

    Raises
    ------
    ValueError
        If the policy is unknown, a rating file lacks study-reach coverage,
        or an OYO section is missing from the grid.
    """
    if bep_source_policy not in ("exact", "nearest"):
        raise ValueError(
            f"unknown bep_source_policy {bep_source_policy!r}; expected "
            "'exact' or 'nearest' (ADR-0038 decision 2)."
        )

    segments: list[Segment] = []
    for (river, bank), (kp_lo, kp_hi) in STUDY_REACHES.items():
        coefficients = load_rating_coefficients(rating_curve_path(data_root, river))
        # The rating files carry a handful of off-grid gauge nodes (e.g.
        # Tokachi KP 56.73, the Obihiro gauge) alongside the 0.2 km survey
        # grid; the evaluation segments are the grid nodes only.
        kps = sorted(
            kp
            for kp in coefficients
            if kp_lo - _KP_TOL <= kp <= kp_hi + _KP_TOL
            and abs(kp / 0.2 - round(kp / 0.2)) <= 1e-6
        )
        if not kps:
            raise ValueError(
                f"rating file for the {river} has no KP nodes inside the "
                f"study reach [{kp_lo}, {kp_hi}] — wrong file or datum."
            )
        oyo_here = [okp for oriver, obank, okp in OYO_BEP_SECTIONS if oriver == river]
        for kp in kps:
            source: float | None = None
            if any(abs(kp - okp) <= _KP_TOL for okp in oyo_here):
                source = float(kp)
            elif bep_source_policy == "nearest" and oyo_here:
                source = min(oyo_here, key=lambda okp: abs(kp - okp))
            segments.append(
                Segment(river=river, bank=bank, kp=float(kp), bep_source_kp=source)
            )

    missing = [
        (river, kp)
        for river, _, kp in OYO_BEP_SECTIONS
        if not any(s.river == river and abs(s.kp - kp) <= _KP_TOL for s in segments)
    ]
    if missing:
        raise ValueError(
            f"OYO BEP sections missing from the rating grid: {missing!r} — "
            "the registry refuses a grid that cannot anchor the engine curves."
        )
    return SegmentRegistry(
        segments=tuple(segments), bep_source_policy=bep_source_policy
    )


def load_section_table(
    path: str | Path,
    registry: SegmentRegistry,
    *,
    allow_gaps: bool = False,
) -> SegmentRegistry:
    """Apply the Uemura section-aggregation table (seam).

    Expected CSV columns (exact names): ``river``, ``bank``, ``kp_from``,
    ``kp_to``, ``section_id`` — inclusive KP ranges per Uemura Section
    (Tokachi 1-5, Satsunai 1-4). This loader is the arrival contract
    (ADR-0038 decision 2); the committed reconstruction from Uemura's own
    SECTIONS.shp geometry is ADR-0043.

    Parameters
    ----------
    path : str or pathlib.Path
        The section table CSV.
    registry : SegmentRegistry
        The registry to annotate.
    allow_gaps : bool
        When False (default) every segment of a touched river/bank must be
        covered by some range (the strict anti-typo tiling check). When True
        (ADR-0043: Uemura's scheme legitimately covers only Satsunai KP
        3.2–7.0), uncovered segments keep ``section_id=None`` — an honest,
        visible gap.

    Returns
    -------
    SegmentRegistry
        A new registry whose segments carry ``section_id``.

    Raises
    ------
    ValueError
        On unknown rivers/banks, malformed or overlapping ranges, or (with
        ``allow_gaps=False``) segments left uncovered inside a touched
        river/bank.
    """
    path = Path(path)
    with open(path, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"river", "bank", "kp_from", "kp_to", "section_id"}
    if not rows or not required <= set(rows[0].keys()):
        raise ValueError(
            f"{path.name}: expected columns {sorted(required)} "
            f"(got {sorted(rows[0].keys()) if rows else 'no rows'})."
        )
    ranges: list[tuple[str, str, float, float, str]] = []
    for row in rows:
        river, bank = row["river"], row["bank"]
        if (river, bank) not in STUDY_REACHES:
            raise ValueError(
                f"{path.name}: unknown river/bank {(river, bank)!r}; expected "
                f"{sorted(STUDY_REACHES)}."
            )
        kp_from, kp_to = float(row["kp_from"]), float(row["kp_to"])
        if not kp_from < kp_to:
            raise ValueError(
                f"{path.name}: section {row['section_id']!r} has kp_from "
                f">= kp_to ({kp_from}, {kp_to})."
            )
        ranges.append((river, bank, kp_from, kp_to, row["section_id"]))

    for i, (river_a, bank_a, lo_a, hi_a, sid_a) in enumerate(ranges):
        for river_b, bank_b, lo_b, hi_b, sid_b in ranges[i + 1 :]:
            if (river_a, bank_a) == (river_b, bank_b) and (
                lo_a < hi_b - _KP_TOL and lo_b < hi_a - _KP_TOL
            ):
                raise ValueError(
                    f"{path.name}: sections {sid_a!r} and {sid_b!r} overlap "
                    f"on {river_a} {bank_a}."
                )

    touched = {(river, bank) for river, bank, *_ in ranges}
    annotated: list[Segment] = []
    for segment in registry.segments:
        section_id = segment.section_id
        for river, bank, lo, hi, sid in ranges:
            if (
                segment.river == river
                and segment.bank == bank
                and lo - _KP_TOL <= segment.kp <= hi + _KP_TOL
            ):
                section_id = sid
                break
        else:
            if (segment.river, segment.bank) in touched and not allow_gaps:
                raise ValueError(
                    f"{path.name}: segment {segment.river} KP {segment.kp:g} "
                    "is not covered by any section range — the table must "
                    "tile every reach it touches (pass allow_gaps=True for "
                    "a deliberately partial scheme, ADR-0043)."
                )
        annotated.append(
            Segment(
                river=segment.river,
                bank=segment.bank,
                kp=segment.kp,
                bep_source_kp=segment.bep_source_kp,
                section_id=section_id,
            )
        )
    return SegmentRegistry(
        segments=tuple(annotated), bep_source_policy=registry.bep_source_policy
    )


# Kasumi-tei (霞堤) registry: the open, discontinuous levees of the upper
# Tokachi system. Transcribed from the 霞堤一覧表 of 続十勝川治水史 (2023),
# PDF p. 268 (printed p. 246); see docs/tokachi_basin_document_review_2026-07-27.md
# and docs/tokachi_bep_inputs_provenance.md section 7.5.
KASUMI_TEI_CSV = Path("data/processed/kasumi_tei_locations.csv")


def load_kasumi_tei(
    csv_path: str | Path = KASUMI_TEI_CSV,
) -> tuple[tuple[str, str, str, float], ...]:
    """Load the kasumi-tei (open-levee) location register.

    A kasumi-tei is a deliberately discontinuous levee: the embankment is
    interrupted and the downstream end left open, with the next embankment
    overlapping it further inland. Floodwater enters the hinterland through
    the opening by design, and interior water drains out through it, so an
    opening is not a continuous barrier whose overtopping constitutes
    failure in the same sense as a continuous reach.

    This loader is informational and is *not* consulted by
    :func:`build_registry`; the production segment set and every persisted
    Phase 3 result are unchanged by its presence. It exists so that the
    coincidence check of :func:`kasumi_tei_coincidences` can be run, and
    re-run, whenever the study reaches are extended.

    Parameters
    ----------
    csv_path : str or pathlib.Path
        Register CSV with columns ``river``, ``bank``, ``name_ja``, ``kp_km``.

    Returns
    -------
    tuple of (str, str, str, float)
        ``(river, bank, name_ja, kp_km)`` rows, in file order.

    Notes
    -----
    The register covers the Tokachi, Satsunai and Otofuke rivers. Counts as
    of the 2023 source: 13 on the Tokachi, 13 on the Satsunai, 8 on the
    Otofuke. Only the Tokachi right bank and Satsunai left bank fall within
    the modelled study reaches (:data:`STUDY_REACHES`).
    """
    rows: list[tuple[str, str, str, float]] = []
    with Path(csv_path).open(newline="", encoding="utf-8") as handle:
        for record in csv.DictReader(handle):
            rows.append(
                (
                    record["river"],
                    record["bank"],
                    record["name_ja"],
                    float(record["kp_km"]),
                )
            )
    return tuple(rows)


def kasumi_tei_coincidences(
    registry: SegmentRegistry,
    csv_path: str | Path = KASUMI_TEI_CSV,
) -> tuple[tuple[Segment, str], ...]:
    """Report registry segments that coincide with a kasumi-tei opening.

    Parameters
    ----------
    registry : SegmentRegistry
        The segment set to test, typically from :func:`build_registry`.
    csv_path : str or pathlib.Path
        Kasumi-tei register, see :func:`load_kasumi_tei`.

    Returns
    -------
    tuple of (Segment, str)
        Each coinciding segment paired with the Japanese embankment name.
        Empty when no segment sits at an opening.

    Notes
    -----
    As of the 2026-07-28 check, exactly one of the 114 production segments
    coincides with an opening: Satsunai left bank KP 9.2 (愛国築堤). Under
    the production ``'exact'`` BEP-source policy that segment carries
    ``bep_source_kp=None``, so the BEP branch of the composition is
    unaffected; the coincidence bears only on its surface-mechanism terms.
    The Tokachi right-bank reach is clear, the nearest opening (KP 63.8,
    西帯広築堤) lying 1.0 km above the reach top at KP 62.8.

    The official 2019 bank-height table supplies a continuous planned
    high-water level and a design crest exactly 1.50 m above it through
    KP 9.2, so the design profile itself is not interrupted there; the
    register records the location of the kasumi-tei structure rather than a
    gap in the design crest. The two facts are recorded together because
    only the second is visible in the engine's own inputs.
    """
    openings = load_kasumi_tei(csv_path)
    index = {(river, bank, round(kp, 1)): name for river, bank, name, kp in openings}
    hits: list[tuple[Segment, str]] = []
    for segment in registry.segments:
        key = (segment.river, segment.bank, round(segment.kp, 1))
        if key in index:
            hits.append((segment, index[key]))
    return tuple(hits)
