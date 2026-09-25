# Four physical-model qualifications, measured rather than argued

**Status:** Accepted. Un-numbered study: it changed no `Config` field, no
default, no prior, no persisted production artifact and no published
probability. What it changed is four statements the thesis made about the
implemented physics, three of which were false and one of which was offered as
corroboration it does not supply.

> **Re-based under ADR-0054, 2026-09-25.** The evidence this note reads was regenerated on the re-based
> matrix d70 (0.70 / 0.53 / 0.26 / 0.70 mm became 0.90 / 0.65 / 0.74 /
> 0.75 mm at KP 57.4 / 58.8 / 60.0 / 62.0; bulk unchanged). The committed
> JSON is the re-based record. Where the prose below quotes a matrix-reading
> number it is the pre-rebase value, kept as written; the re-based values are
> in the JSON, tabulated in `bimodal-foundation-d70-study.md` Part 3 and in
> the dated addenda of `docs/phase2_report.md` and `docs/phase3_report.md`.

**Date:** 2026-09-16
**Driver:** `scripts/physical_model_qualifications.py` (`--part all`)
**Evidence:** `physical-model-qualifications-study.json` beside this note
**Tests:** `tests/test_physical_model_qualifications.py` (17 analytic checks)
**Parents:** ADR-0008 (the uplift/heave collapse), ADR-0028 and ADR-0052 (the
two head conventions and the declined foreland credit), ADR-0042 decision 9
(the scour erodibility conversion), ADR-0047 (the seepage-length convention)

---

## 1. What this closes

An independent examiner review of 2026-09-12 raised two findings and a register
of local physical-model statements. The two findings are its F7 (the foreland
and the gradient argument) and F8 (the scour explanation). This note is the
measurement behind their disposition and behind the related statements. It does
not adopt the review's numbers, its probe or its reasoning: every quantity below
was derived independently and then computed through the engine's own kernels,
and one of the four outcomes goes further than the review claimed while another
goes less far.

## 2. The 1998 exit gradients do not select a seepage-length convention

**The withdrawn argument.** Appendix B carried a back-calculation cross-check:
at KP 60.0 an under-levee path of order 35 m with a design head of about 3 m was
said to be "consistent with" the reported local vertical exit gradient
`i_v = 0.50`, while a several-hundred-metre path beneath the 600 m foreshore
"would imply an average gradient near 0.005, which is incapable of producing the
observed local exit gradient".

**Why it fails.** The two quantities compared are not the same kind of object.
`i_v` is a *local vertical* gradient: a head difference across the blanket
divided by the blanket thickness. The 0.005 is an *average horizontal* gradient
along the path. A long path with a small average gradient can still produce a
large local exit gradient, because exit gradients concentrate; the tabulated
values are in fact OYO's own finite-element maxima at the landside toe, from a
schematization with a continuous cohesive blanket over the whole domain
including the foreshore.

**What the measurement says.** Within the adopted leakage-length translation the
local vertical exit gradient is `i_v = r_e (H - z_toe) / D_bl`, with
`r_e = lambda_in / (lambda_out_eff + L + lambda_in)`. Evaluated at each section's
prior means and its own 1998 design level, once at the surveyed under-levee `L`
and once at `L + B_f`:

| KP | head 1998 [m] | `r_e` at `L` | `r_e` at `L+B_f` | `i_v` under-levee | `i_v` spanning | `i_v` reported | under/reported | spanning/reported |
|---|---|---|---|---|---|---|---|---|
| 57.4 | 1.21 | 0.438 | 0.236 | 0.663 | 0.357 | 0.040 | 16.57 | 8.93 |
| 58.8 | 2.83 | 0.436 | 0.197 | 1.452 | 0.655 | 1.300 | 1.12 | 0.50 |
| 60.0 | 3.06 | 0.417 | 0.108 | 1.501 | 0.389 | 0.500 | 3.00 | 0.78 |
| 62.0 | 1.78 | 0.351 | 0.251 | 1.390 | 0.993 | 0.970 | 1.43 | 1.02 |

Neither convention reproduces the tabulated values, and **at three of the four
sections the foreshore-spanning path is the closer of the two**. At KP 60.0, the
very section the withdrawn argument reasoned from, the adopted convention
over-predicts by 3.00 and the alternative under-predicts by 1.29. The mean
absolute log error is 1.095 for the under-levee convention against 0.788 for the
spanning one. The comparison therefore does not corroborate the adopted
convention; if anything it leans the other way, and it should not be quoted in
either direction.

**The argument also proves too much.** The modelled *horizontal* gradient at the
toe, `r_e (H - z_toe) / lambda_in`, is 0.0052, 0.0106, 0.0146 and 0.0161 along
the reach, against tabulated horizontal gradients of 0.050, 0.620 and 0.400 at
the three sections that report one: a factor of ten to sixty low. The adopted
convention's own average gradient is thus the same order as the 0.005 the
withdrawn argument called "incapable", so applying that argument consistently
would refute the convention it was written to defend.

**What survives.** The under-levee convention itself is untouched. It is
Sellmeijer's own calibration geometry, ADR-0047 fixed the rule for adopting or
holding it, and ADR-0052 measured what declining the permissive foreland credit
is worth. TR Zandmeevoerende Wellen (1999) §4.4.2 was re-read verbatim from
`docs/references/tr-15_technischrapportzandmeevoerendewellen.pdf` (PDF page 43,
printed page 44) this session and still says *mag*: the credit is permitted, not
required. What does not survive is the gradient back-calculation offered as
independent corroboration.

The one thing the tabulated gradients still show is that their variation does
not follow foreshore width, so they supply no evidence of foreshore control
either. That reading is retained.

## 3. The critical head is sublinear in the seepage length

`H_c = L F_r F_s F_g`. `F_r` is free of `L`; `F_s` carries `L^(-1/3)` at the
production `alpha = -1/3`; and `F_g = 0.91 (D_aq/L)^(0.28/((D_aq/L)^2.8 - 1) +
0.04)` rises with `L`, tending to `L^0.24` for `D_aq/L << 1`. The exponent is
therefore near `1 - 1/3 + 0.24 = 0.907` analytically, and measured through M6:

| KP | `D_aq/L` | local `dlnH_c/dlnL` | secant over `L -> L + lambda_out_eff` | `H_c/L` at `L` | `H_c/L` credited |
|---|---|---|---|---|---|
| 57.4 | 0.212 | 0.894 | 0.903 | 0.0616 | 0.0539 |
| 58.8 | 0.229 | 0.892 | 0.902 | 0.0609 | 0.0528 |
| 60.0 | 0.259 | 0.888 | 0.900 | 0.0562 | 0.0496 |
| 62.0 | 0.250 | 0.889 | 0.896 | 0.0804 | 0.0757 |

So `H_c` **rises** with `L` and the critical **gradient** `H_c/L` falls, as
`L^-0.11`. Two thesis statements were wrong on this and are corrected: that `L`
enters `H_c` "linearly", and that "the static model predicts decreasing piping
resistance as seepage length `L` increases". The second is true only of the
gradient, and the distinction matters because it is the sentence that contrasts
Sellmeijer with the Shields-Darcy scale argument.

The `kappa` column of this part reproduces ADR-0052's prior-mean table exactly
(3.481 / 3.734 / 3.099 / 1.683), which is the cross-check the measurement was
gated on.

## 4. KP 62.0's static displacement is mostly soil, not geometry

Chapter 6 attributed the displacement of KP 62.0's curves from the other three
to "two geometric properties", the longest seepage path and the thinnest
blanket. Measured on the persisted production theta matrices, with each
section's own sampled `L` from its config seed:

| KP | nominal `L` [m] | median `H_c` [m] | median `H_c` with `L` rescaled to 40 m | length factor |
|---|---|---|---|---|
| 57.4 | 33.0 | 2.036 | 2.418 | 1.188 |
| 58.8 | 35.0 | 2.139 | 2.409 | 1.127 |
| 60.0 | 34.8 | 1.980 | 2.241 | 1.132 |
| 62.0 | 40.0 | 3.217 | 3.217 | 1.000 |

KP 62.0's median critical head stands 1.50 to 1.62 times the other three. Give
them its 40 m path and 1.33 to 1.44 of that remains, so **the seepage path
accounts for 26 to 38 per cent of the elevation in log terms** and the balance
is the coarse matrix diameter transferred to this section combined with the
basin's lowest aquifer conductivity, `H_c` scaling as about
`d_70^0.4 k_aq^(-1/3)`.

The second "geometric property" is worse than incomplete. The crack-resistance
decrement `0.3 D_bl` belongs to the transient driver alone (ADR-0028), so it
cannot enter a static-branch displacement at all; and its direction is the
reverse of the one claimed. A thinner blanket means a *smaller* subtraction,
hence *more* transient driving head, hence a leftward shift, whereas KP 62.0's
transient branch is displaced right by a further 0.4 m. That further
displacement is the traversal requirement, which strengthens with the longest
path and the slowest rate.

The same chapter separately claimed the decrement "is therefore largest at
KP 57.4 and smallest at KP 62.0" and that the observed ordering is "exactly the
reverse". The decrements are 0.240, 0.255, 0.255 and 0.135 m, so KP 57.4 is
third of four, not largest, and the median offsets are 0.74, 0.88, 1.20 and
1.49 m, which is not the reverse of anything. The conclusion the passage draws
survives and is restated exactly: the section with much the smallest decrement
carries much the largest offset, so the decrement is not what orders them.

## 5. The scour law engages; its breach criterion does not

**The withdrawn explanation.** Chapter 7 explained the exactly-zero fluvial
scour result by a threshold the loading never reaches: "critical bed shear
stress of roughly 51 Pa exceeds high-water-bed sheet-flow shear throughout the
loading range. The mechanism therefore never engages."

**Why it fails.** The ADR-0042 decision-9 correction divides the erodibility
coefficient `k` by 105.56; it is the *rate* coefficient. The critical shear
`tau_c` is converted separately and correctly, and it is not a constant: it is
drawn Normal with mean `1.058 psf x 47.8803 = 50.66 Pa` and coefficient of
variation 0.560, resampled positive.

**What the measurement says.** Reproducing the committed surface-curve
generation exactly (same segment inputs, canonical event `HPB_m064_1987`, level
ladder, seeds and `N_MC = 10 000`) and reporting activation, accumulation and
criterion separately instead of the failure fraction:

| quantity | value |
|---|---|
| peak bed shear over the ladder | 25.4 to 108.1 Pa, median 47.4 |
| segments where the law activates | **114 of 114** |
| fraction of draws activated | 0.152 to 0.978, median 0.436 |
| accumulated depth, most erodible draw | 0.32 to 3.16 m, median 1.33 |
| accumulated depth, mean over draws | 0.011 to 0.462 m |
| accumulated depth under the as-received `k` | up to 353 m |
| levee width the depth must consume | 7.0 m at the crest, 13.5 to 23.0 m at floodplain level |
| largest depth-to-width ratio anywhere | 0.451 |

The law engages everywhere, at a substantial share of draws, and removes up to
about three metres of material. What never happens is that the accumulated depth
reaches the width: the worst case anywhere consumes 45 per cent of it. Under the
as-received conversion the same integral reaches 353 m, which is why that
conversion produced failures.

Appendix H already gave the structurally correct account ("insufficient
accumulated scour"), but its magnitude was also short: "far less than a meter"
is true of the mean draw and not of the tail, and the effective width is 7 to 23
metres rather than "tens of metres". Both are corrected.

**What this does not license.** It says nothing about whether physical surface
erosion is harmless here. Lateral bank retreat by channel migration is a
separate mechanism, is not in the model set, and is the one with the strongest
claim to having caused failure in this basin. Chapter 3 had said that pathway
"enters the integrated framework through the pre-calculated scour fragility",
which contradicted Chapters 1, 7, 8, 9 and the Summary; it is corrected to match
them.

## 6. What changed, and what did not

**Unchanged:** every `Config` field and default, every prior, the canonical
event, all eight production sweeps, all Phase 2 posteriors, every Phase 3
annual number and mechanism share, and every figure. No kernel was edited. The
two new engine files are a driver and a test module, neither imported by any
production path.

**Changed, thesis side:** Chapter 2 (the critical-gradient statement, the
positive part in the rate equation, the conditions on the duration heuristic),
Chapter 3 (the uplift/heave thickness scaling, the `L` dependence of `H_c`, the
bank-retreat attribution, the conductivity-bracket wording), Chapter 6 (what
displaces KP 62.0, and the crack-decrement ordering), Chapter 7 (the scour
explanation), Chapter 8 (the scope of the zero-recovery conservatism, and one
"proportionally"), Appendix B (the withdrawn back-calculation, the two-soil
evidence scope, the mislabelled particle-weight dispersion), Appendix F (the
Tokoro breach label), Appendix H (the scour magnitudes) and Appendix I (the
"bracket the truth" claim).

**A point of method worth keeping.** Three of the four corrections here were
invisible to the test suite and to every numerical gate, because none of them is
a computed quantity: they are statements *about* computed quantities. The gate
that would have caught them is the one applied in `tests/test_physical_model_qualifications.py`,
which asserts the sign and the scaling of each relation the prose claims, rather
than the value of any result.
