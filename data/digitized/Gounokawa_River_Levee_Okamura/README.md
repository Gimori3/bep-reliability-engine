# Waseda companion dataset — Okamura et al. (2025), Gounokawa Shimohara levee

Source: Waseda University repository, doi:10.20556/0002006234
(https://waseda.repo.nii.ac.jp/records/2006234), the open companion dataset to
Okamura, Mori, Ishihara, Maeda et al. (2025), *Soils and Foundations* 65,
101656. Used by `scripts/validate_gounokawa_shimohara.py` (see
`docs/validation/gounokawa-shimohara-case.md`).

Committed here:

- `Fig5_...xlsx` — hourly Tanijugo water levels + hourly precipitation for the
  2018/2020/2021 events (the validation's loading input).
- `Fig11_...xlsx` — crest and hinterland ground-surface elevation profiles
  along the levee (pins z_toe at Location A).
- `Fig4_...xlsx` (x2) — annual maximum stages (source of the 1999 no-ejecta
  bound) and 24-h rainfall.

NOT committed (exceeds the repo's 500 KB pre-commit limit; retrieve from the
DOI above if needed):

- `Fig13_Elevation of the 2020 and 2021 event_OKAMURA Mitsu.xlsx` — the two
  5-cm UAV DEMs (JGD2011 zone III) of the Location A patch (~34 x 41 m). Not
  used by the validation harness (the patch cannot pin the seepage length L).

The dataset contains no grain-size or permeability data; those validation
inputs are digitized from the paper's figures and flagged READ-OFF in the
harness.
