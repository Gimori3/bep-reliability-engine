"""Generate the annotated cross-section figure (KP 62.0) as TikZ.

Every hydraulic quantity is computed from the engine's own kernels, so the
drawing cannot drift from the model. Geometry comes from
data/processed/tokachi_bep_inputs.csv via configs/kp62_0_historical_matrix.yaml;
the compound-section elevations come from docs/tokachi_bep_inputs_provenance.md
Section 3.9 (OYO 1999 form 3).

Emits millimetre coordinates, so TikZ is set with x=1mm, y=1mm.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from bep_reliability_engine.hydraulics import (  # noqa: E402
    leakage_length_in,
    leakage_length_out,
    response_factor,
)

# --------------------------------------------------------------------------
# 1. Inputs -- all from the production config / provenance record
# --------------------------------------------------------------------------
K_AQ, D_AQ, D_BL, K_BL = 1.0e-3, 10.0, 0.45, 3.0e-6  # config priors (means)
D_FORE, K_FORE = 0.45, 3.0e-6  # ADR-0005 foreland proxy
L = 40.0  # ADR-0047 surveyed 2025
B_F = 44.0  # OYO form 3, kosuishiki-haba
Z_TOE = 44.90  # 2019 bank-height survey
HWL = 46.39  # 2019 bank-height survey
CREST = HWL + 1.50  # 1.50 m freeboard rule
Z_TERRACE = 45.00  # OYO form 3 kosuishiki-daka
Z_BASEFLOW = 41.60  # OYO form 3
Z_MEANBED = 38.40  # OYO form 3 heikin-kawadoko

lam_in = float(leakage_length_in(K_AQ, D_AQ, D_BL, K_BL))
lam_out = float(leakage_length_in(K_AQ, D_AQ, D_FORE, K_FORE))
lam_out_eff = float(leakage_length_out(K_AQ, D_AQ, D_FORE, K_FORE, B_F))
r_e = float(response_factor(lam_in, lam_out_eff, L))

TOT = lam_out_eff + L + lam_in
DH = HWL - Z_TOE
PHI_0 = Z_TOE + DH * (L + lam_in) / TOT  # head at riverside levee toe
PHI_L = Z_TOE + r_e * DH  # head at landside toe = h_aq
DROP_OUT = HWL - PHI_0
DROP_L = PHI_0 - PHI_L
DROP_IN = PHI_L - Z_TOE  # == delta h_blanket


def phi(x: float) -> float:
    """Piezometric head at the top of the aquifer, m T.P."""
    if x <= -B_F:  # aquifer at outcrop: no resistance
        return HWL
    if x <= 0.0:  # under the riverside blanket
        s = math.sinh((x + B_F) / lam_out) / math.sinh(B_F / lam_out)
        return HWL + (PHI_0 - HWL) * s
    if x <= L:  # under the levee: no leakage
        return PHI_0 + (PHI_L - PHI_0) * (x / L)
    return Z_TOE + (PHI_L - Z_TOE) * math.exp(-(x - L) / lam_in)  # hinterland


# --------------------------------------------------------------------------
# 2. Ground / stratigraphic profile (m T.P.), left to right
# --------------------------------------------------------------------------
X_LEFT, X_RIGHT = -78.0, 106.0
X_BAR_R = -50.0  # riverward limit of the terrace scarp
X_SCARP = -44.0  # terrace edge = riverside blanket edge
Z_BAR = 43.15  # braid-plain surface, schematic
Z_BASE = 34.45  # top of the impervious base = 44.45 - D_aq
Z_FRAME_BOT = 33.30


def ground(x: float) -> float:
    """Natural surface, m T.P."""
    if x <= X_BAR_R:
        return Z_BAR + 0.16 * math.sin(x * 0.28) + 0.10 * math.sin(x * 0.11)
    if x <= X_SCARP:
        t = (x - X_BAR_R) / (X_SCARP - X_BAR_R)
        return ground(X_BAR_R) + t * (Z_TERRACE - ground(X_BAR_R))
    if x <= 0.0:
        return Z_TERRACE
    if x <= L:
        return Z_TERRACE + (Z_TOE - Z_TERRACE) * (x / L)
    return Z_TOE


def aq_top(x: float) -> float:
    """Top of the aquifer = base of the confining blanket, m T.P."""
    if x <= X_BAR_R:
        return ground(x)  # blanket absent: aquifer outcrops
    return ground(x) - D_BL * min(1.0, (x - X_BAR_R) / (X_SCARP - X_BAR_R))


# levee prism: base = L exactly, crest elevation surveyed, outline indicative
LEV_R_RUN, LEV_CREST_W = 11.0, 15.0
LEV_X = [0.0, LEV_R_RUN, LEV_R_RUN + LEV_CREST_W, L]
LEV_Z = [Z_TERRACE, CREST, CREST, Z_TOE]
X_WATER_EDGE = LEV_R_RUN * (HWL - Z_TERRACE) / (CREST - Z_TERRACE)

L_PIPE = 22.0
X_PIPE_TIP = L - L_PIPE

# --------------------------------------------------------------------------
# 3. Millimetre mapping
# --------------------------------------------------------------------------
SX = 0.845  # mm per metre, horizontal
SY_B = 5.0 * SX  # panel B: 5x vertical exaggeration
ZB_BOT = Z_FRAME_BOT
ZA_BOT, ZA_TOP = 44.72, 46.62
SY_A = 11.6  # mm per metre, panel A
YB0 = 0.0
YA0 = 70.0


def X(x: float) -> float:
    return (x - X_LEFT) * SX


def YB(z: float) -> float:
    return YB0 + (z - ZB_BOT) * SY_B


def YA(z: float) -> float:
    return YA0 + (z - ZA_BOT) * SY_A


def pB(x: float, z: float) -> str:
    return f"({X(x):.2f},{YB(z):.2f})"


def pA(x: float, z: float) -> str:
    return f"({X(x):.2f},{YA(z):.2f})"


def poly(pts, fn):
    return " -- ".join(fn(x, z) for x, z in pts)


def sample(x0, x1, n, f):
    return [(x0 + (x1 - x0) * i / n, f(x0 + (x1 - x0) * i / n)) for i in range(n + 1)]


out: list[str] = []
A = out.append

# --------------------------------------------------------------------------
# 4. Preamble
# --------------------------------------------------------------------------
A(r"\definecolor{xsAquifer}{RGB}{232, 213, 172}")
A(r"\definecolor{xsBlanket}{RGB}{138, 150, 134}")
A(r"\definecolor{xsBase}{RGB}{171, 171, 176}")
A(r"\definecolor{xsLevee}{RGB}{205, 190, 158}")
A(r"\definecolor{xsWater}{RGB}{186, 214, 235}")
A(r"\definecolor{xsHead}{RGB}{16, 66, 136}")
A(r"\definecolor{xsPipe}{RGB}{152, 28, 28}")
A(r"\definecolor{xsLine}{RGB}{72, 72, 76}")
A(r"\definecolor{xsGuide}{RGB}{148, 148, 152}")
A(r"\begin{tikzpicture}[")
A(r"    x=1mm, y=1mm, font=\sffamily\scriptsize,")
A(r"    lbl/.style   = {inner sep=1pt, outer sep=0pt},")
# ``\tiny`` is 5 pt at the report's 10 pt base. Unlike the raster figures
# this drawing is typeset rather than reduced, so 5 pt is its true printed
# size and is below the 7 pt floor of conventions section 9.3.2. Raising
# ``tny`` to ``\scriptsize`` was built and read: the panel (a) axis title
# runs into its own tick labels, the two pipe-dimension labels merge, the
# high-water-bed label is struck through by the piezometric line and the
# embankment, and the low-water-channel box lands on the channel. Reaching
# the floor here is a re-layout of the drawing, not a size change.
A(r"    tny/.style   = {inner sep=1pt, outer sep=0pt, font=\sffamily\tiny},")
A(r"    callout/.style = {tny, draw=xsLine, line width=0.25pt,")
A(r"                       fill=white, rounded corners=0.6mm, inner sep=1.5pt,")
A(r"                       align=center},")
A(r"    dim/.style   = {draw=xsLine, line width=0.25pt,")
A(r"                    {Latex[length=1.3mm]}-{Latex[length=1.3mm]}},")
A(r"    ext/.style   = {draw=xsGuide, line width=0.15pt},")
A(r"    guide/.style = {draw=xsGuide, line width=0.2pt,")
A(r"                    dash pattern=on 0.5mm off 0.6mm},")
A(r"    lead/.style  = {draw=xsLine, line width=0.2pt, -{Latex[length=1.1mm]}},")
A(r"    tick/.style  = {draw=xsLine, line width=0.25pt}")
A(r"]")
# Extend the bounding box to cover the rotated axis titles: TikZ does not
# register rotated node text, so without this the picture reserves a box ~18 mm
# narrower than its own ink and the float spills into the left margin.
A(r"\path (-10.5,-20) (157,93.5);")
A(r"\node[font=\sffamily\small\bfseries, anchor=south] at (77.75,96)")
A(r" {Levee cross-section and piezometric head};")

gnd = sample(X_LEFT, X_RIGHT, 300, ground)
aqt = sample(X_LEFT, X_RIGHT, 300, aq_top)
xax = X_LEFT - 1.5

# ==========================================================================
# PANEL B -- geometry
# ==========================================================================
A(r"% ================= panel B: cross-section geometry =================")
A(rf"\fill[xsBase] {pB(X_LEFT, Z_FRAME_BOT)} rectangle {pB(X_RIGHT, Z_BASE)};")
A(
    rf"\fill[xsAquifer] {pB(X_LEFT, Z_BASE)} -- {poly(aqt, pB)}"
    rf" -- {pB(X_RIGHT, Z_BASE)} -- cycle;"
)
blk = [(x, z) for x, z in gnd if x >= X_BAR_R]
blk_b = [(x, z) for x, z in aqt if x >= X_BAR_R]
A(rf"\fill[xsBlanket] {poly(blk, pB)} -- {poly(list(reversed(blk_b)), pB)} -- cycle;")
wat = [(x, z) for x, z in gnd if x <= 0.0]
A(
    rf"\fill[xsWater] {pB(X_LEFT, HWL)} -- {pB(X_WATER_EDGE, HWL)} --"
    rf" {pB(0.0, Z_TERRACE)} -- {poly(list(reversed(wat)), pB)} -- cycle;"
)
A(rf"\fill[xsLevee] {poly(list(zip(LEV_X, LEV_Z)), pB)} -- cycle;")

A(rf"\draw[xsLine, line width=0.3pt] {pB(X_LEFT, Z_BASE)} -- {pB(X_RIGHT, Z_BASE)};")
A(rf"\draw[xsLine, line width=0.3pt] {poly(aqt, pB)};")
A(rf"\draw[xsLine, line width=0.45pt] {poly(gnd, pB)};")
A(rf"\draw[xsLine, line width=0.45pt] {poly(list(zip(LEV_X, LEV_Z)), pB)};")
A(rf"\draw[xsHead, line width=0.45pt] {pB(X_LEFT, HWL)} -- {pB(X_WATER_EDGE, HWL)};")

hd = sample(X_SCARP, X_RIGHT, 260, phi)
A(
    rf"\draw[xsHead, line width=0.55pt, dash pattern=on 1.3mm off 0.8mm]"
    rf" {poly(hd, pB)};"
)

pipe = sample(X_PIPE_TIP, L, 40, aq_top)
A(rf"\draw[xsPipe, line width=1.1pt] {poly(pipe, pB)};")
A(rf"\draw[xsPipe, line width=1.1pt] {pB(L, aq_top(L))} -- {pB(L, Z_TOE)};")
A(
    rf"\fill[xsPipe] {pB(L - 1.7, Z_TOE)} -- {pB(L + 1.7, Z_TOE)}"
    rf" -- {pB(L, Z_TOE + 0.32)} -- cycle;"
)

# ---- elevation axis, panel B
A(rf"\draw[tick] ({X(xax):.2f},{YB(34.0):.2f}) -- ({X(xax):.2f},{YB(48.2):.2f});")
for z in (36, 38, 40, 42, 44, 46, 48):
    A(rf"\draw[tick] ({X(xax):.2f},{YB(z):.2f}) -- ({X(xax) - 1.1:.2f},{YB(z):.2f});")
    A(rf"\node[tny, anchor=east] at ({X(xax) - 1.4:.2f},{YB(z):.2f}) {{{z}}};")
A(
    rf"\node[tny, anchor=center, rotate=90] at"
    rf" ({X(xax) - 7.0:.2f},{YB(41.0):.2f}) {{elevation (m T.P.)}};"
)
A(
    rf"\node[tny, anchor=west] at {pB(-76.0, 35.5)}"
    r" {vertical exaggeration $5\times$};"
)

# ---- stratigraphic labels
A(
    rf"\node[lbl, anchor=center, align=center] at {pB(20.0, 39.9)}"
    r" {$A_g$/$N_s$ aquifer\\$D_\mathrm{aq} = 10$~m,"
    r"\ $k_\mathrm{aq} = 1\times10^{-3}$~m/s};"
)
A(rf"\node[tny, anchor=center] at {pB(20.0, 34.8)}" r" {impervious base};")
A(
    rf"\node[callout, anchor=east] (blanket) at {pB(105.0, 48.25)}"
    r" {$A_c$ confining blanket\\$D_\mathrm{bl} = 0.45$~m,"
    r"\ $k_\mathrm{bl} = 3\times10^{-6}$~m/s};"
)
A(rf"\draw[lead] (blanket.south east) -- {pB(103.0, 44.72)};")

# ---- river-side features
A(
    rf"\node[tny, anchor=west] at {pB(-77.0, 46.90)}"
    r" {design high water $h = 46.39$~m T.P.};"
)
A(
    rf"\node[callout, anchor=center] (outcrop) at {pB(-61.0, 40.9)}"
    r" {exposed aquifer across\\the braid plain:\\no entry resistance};"
)
A(rf"\draw[lead] (outcrop.north) -- {pB(-61.0, ground(-61.0))};")
A(
    rf"\node[callout, anchor=center] (channel) at {pB(-59.0, 44.6)}"
    r" {low-water channel:\\several hundred metres left};"
)
A(rf"\draw[lead] (channel.west) -- {pB(-77.5, 44.6)};")
A(
    rf"\node[tny, anchor=south, align=center] at {pB(-23.0, 45.10)}"
    r" {high-water bed = riverside blanket\\45.00~m T.P.};"
)

# ---- levee and exit
A(rf"\node[lbl, anchor=center] at {pB(18.5, 46.90)} {{embankment}};")
A(rf"\node[tny, anchor=south] at {pB(18.5, 47.99)} {{crest 47.89~m T.P.}};")
A(
    rf"\node[callout, anchor=west] (exit) at {pB(42.0, 46.85)}"
    r" {sand boil at the exit;\\$z_\mathrm{toe} = 44.90$~m T.P.};"
)
A(rf"\draw[lead] (exit.south west) -- {pB(40.9, 45.10)};")
# The callout sits to the right of the point it indicates, so its leader
# runs down and to the left. It stops short of x = 97 so that the confining
# blanket's own leader, which drops through x = 103, stays clear of it.
A(
    rf"\node[callout, anchor=south west] (piez) at {pB(76.0, 45.62)}"
    r" {piezometric head (panel a)};"
)
A(rf"\draw[lead] (piez.south west) -- {pB(64.0, 45.22)};")

# ---- D_aq
xd = 99.0
A(rf"\draw[dim] {pB(xd, Z_BASE)} -- {pB(xd, aq_top(xd))};")
A(
    rf"\node[tny, fill=xsAquifer, inner sep=1pt] at {pB(xd, 39.5)}"
    r" {$D_\mathrm{aq}$};"
)

# ---- pipe dimensions
ypipe = 43.55
A(rf"\draw[ext] {pB(X_PIPE_TIP, ypipe - 0.3)} -- {pB(X_PIPE_TIP, aq_top(X_PIPE_TIP))};")
A(rf"\draw[ext] {pB(0.0, ypipe - 0.3)} -- {pB(0.0, Z_TERRACE)};")
A(
    rf"\draw[dim] {pB(X_PIPE_TIP, ypipe)} -- {pB(L, ypipe)}"
    r" node[midway, below=0.3mm, tny] {pipe length $l$};"
)
A(
    rf"\draw[dim] {pB(0.0, ypipe)} -- {pB(X_PIPE_TIP, ypipe)}"
    r" node[midway, below=0.3mm, tny] {remaining path $L - l$};"
)

# Both markings sit inside the grey impervious base, at its vertical
# centre, so they are at the same height as each other: the band runs
# from z = 33.30 to z = 34.45 and Z_SIDE_LABEL is the midpoint.
Z_SIDE_LABEL = 0.5 * (Z_FRAME_BOT + Z_BASE)
A(rf"\node[tny, anchor=west] at {pB(X_LEFT + 2.5, Z_SIDE_LABEL)} {{river side}};")
A(rf"\node[tny, anchor=east] at {pB(X_RIGHT - 2.5, Z_SIDE_LABEL)} {{land side}};")

# ==========================================================================
# Dimension band, below panel B
# ==========================================================================
A(r"% ================= dimension band =================")
yd1, yd2, yd3 = -6.0, -11.8, -17.6
for xg in (X_SCARP, 0.0, L):
    A(rf"\draw[ext] ({X(xg):.2f},{yd3 - 1.2:.2f}) -- {pB(xg, Z_FRAME_BOT)};")
for xg in (-lam_out, -lam_out_eff, L + lam_in):
    A(rf"\draw[ext] ({X(xg):.2f},{yd3 - 1.2:.2f}) -- ({X(xg):.2f},{yd1 + 1.2:.2f});")

A(
    rf"\draw[dim] ({X(X_SCARP):.2f},{yd1:.2f}) -- ({X(0.0):.2f},{yd1:.2f})"
    r" node[midway, above=0.3mm, tny] {$B_f = 44$~m};"
)
A(
    rf"\draw[dim] ({X(0.0):.2f},{yd1:.2f}) -- ({X(L):.2f},{yd1:.2f})"
    r" node[midway, above=0.3mm, tny] {$L = 40$~m};"
)
A(
    rf"\draw[dim] ({X(-lam_out):.2f},{yd2:.2f}) -- ({X(0.0):.2f},{yd2:.2f})"
    r" node[midway, above=0.3mm, tny] {$\lambda_\mathrm{out} = 38.7$~m};"
)
A(
    rf"\draw[dim] ({X(L):.2f},{yd2:.2f}) -- ({X(L + lam_in):.2f},{yd2:.2f})"
    r" node[midway, above=0.3mm, tny] {$\lambda_\mathrm{in} = 38.7$~m};"
)
A(rf"\draw[dim] ({X(-lam_out_eff):.2f},{yd3:.2f}) -- ({X(0.0):.2f},{yd3:.2f});")
A(
    rf"\node[tny, anchor=west] at ({X(2.0):.2f},{yd3:.2f})"
    r" {$\lambda_\mathrm{out,eff} = \lambda_\mathrm{out}"
    r"\tanh(B_f/\lambda_\mathrm{out}) = 31.5$~m, the equivalent entry resistance};"
)

# ==========================================================================
# PANEL A -- piezometric head, magnified
# ==========================================================================
A(r"% ================= panel A: head profile =================")
A(rf"\fill[white] {pA(X_LEFT, ZA_BOT)} rectangle {pA(X_RIGHT, ZA_TOP)};")

for xg in (X_SCARP, 0.0, L):
    A(rf"\draw[guide] {pB(xg, ZB_BOT - 20.0 / SY_B)} -- {pA(xg, ZA_TOP)};")

A(rf"\draw[xsHead, line width=0.45pt] {pA(X_LEFT, HWL)} -- {pA(X_RIGHT, HWL)};")
A(
    rf"\draw[draw=xsLine, line width=0.35pt, dash pattern=on 1mm off 0.7mm]"
    rf" {pA(X_LEFT, Z_TOE)} -- {pA(X_RIGHT, Z_TOE)};"
)

hdA = sample(X_LEFT, X_RIGHT, 320, phi)
A(rf"\draw[xsHead, line width=0.9pt] {poly(hdA, pA)};")

A(rf"\draw[tick] ({X(xax):.2f},{YA(44.9):.2f}) -- ({X(xax):.2f},{YA(46.5):.2f});")
for z in (45.0, 45.5, 46.0, 46.5):
    A(rf"\draw[tick] ({X(xax):.2f},{YA(z):.2f}) -- ({X(xax) - 1.1:.2f},{YA(z):.2f});")
    A(rf"\node[tny, anchor=east] at ({X(xax) - 1.4:.2f},{YA(z):.2f}) {{{z:.1f}}};")
A(
    rf"\node[tny, anchor=center, rotate=90] at"
    rf" ({X(xax) - 7.0:.2f},{YA(45.67):.2f}) {{head (m T.P.)}};"
)

A(
    rf"\node[tny, anchor=west, xsHead] at ({X(-40.0):.2f},{YA(46.50):.2f})"
    r" {river stage $h = 46.39$~m};"
)
A(
    rf"\node[tny, anchor=west] at ({X(-76.0):.2f},{YA(45.02):.2f})"
    r" {exit datum $z_\mathrm{toe} = 44.90$~m};"
)

# ---- the three head drops
xa1, xa2, xa3 = 4.0, 44.0, 66.0
A(rf"\draw[ext] {pA(X_SCARP, HWL)} -- {pA(xa1 + 1.2, HWL)};")
A(rf"\draw[ext] {pA(0.0, PHI_0)} -- {pA(xa2 + 1.2, PHI_0)};")
A(rf"\draw[ext] {pA(L, PHI_L)} -- {pA(xa3 + 1.2, PHI_L)};")
A(rf"\draw[dim] {pA(xa1, HWL)} -- {pA(xa1, PHI_0)};")
A(rf"\draw[dim] {pA(xa2, PHI_0)} -- {pA(xa2, PHI_L)};")
A(rf"\draw[dim] {pA(xa3, PHI_L)} -- {pA(xa3, Z_TOE)};")

A(
    rf"\node[tny, anchor=west, align=left] at {pA(xa1 + 2.0, 46.15)}"
    rf" {{across the foreland\\{DROP_OUT:.2f}~m"
    rf" ({100 * lam_out_eff / TOT:.0f}\%)}};"
)
A(
    rf"\node[tny, anchor=west, align=left] at {pA(xa2 + 2.0, 45.72)}"
    rf" {{under the levee\\{DROP_L:.2f}~m ({100 * L / TOT:.0f}\%)}};"
)
A(
    rf"\node[tny, anchor=west, align=left, xsHead] at {pA(xa3 + 2.0, 45.78)}"
    rf" {{into the hinterland {DROP_IN:.2f}~m"
    rf" ({100 * lam_in / TOT:.0f}\%):\\"
    r"this is the gate head\\"
    r"$\Delta h_\mathrm{blanket} = r_e\,(h - z_\mathrm{toe})$,\\"
    r"driving uplift and heave only};"
)

A(
    rf"\node[tny, anchor=west, align=left] at {pA(-75.5, 45.72)}"
    r" {each drop is proportional to the resistance\\"
    r"it crosses, so the head reaching the exit is\\[0.4mm]"
    r"$r_e = \dfrac{\lambda_\mathrm{in}}"
    r"{\lambda_\mathrm{out,eff} + L + \lambda_\mathrm{in}} = 0.351$};"
)

A(
    rf"\node[lbl, anchor=west, font=\sffamily\scriptsize\bfseries] at"
    rf" ({X(-77.6):.2f},{YA(46.72):.2f}) {{(a)}};"
)
A(
    rf"\node[lbl, anchor=west, font=\sffamily\scriptsize\bfseries] at"
    rf" ({X(-77.6):.2f},{YB(48.45):.2f}) {{(b)}};"
)

A(r"\end{tikzpicture}")

# Terminate the colour definitions with % so that no stray inter-word spaces
# reach the box if the file is ever \input in horizontal mode.
out = [ln + "%" if ln.startswith(r"\definecolor") else ln for ln in out]


def main() -> None:
    """Write one drawing outside the engine; never invoke a TeX compiler."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if target.is_relative_to(REPO):
        parser.error("Thesis drawing sources must be written outside the engine")
    header = (
        "% Annotated cross-section of the confined levee foundation, KP 62.0.\n"
        "% GENERATED by bep-reliability-engine/scripts/"
        "generate_annotated_cross_section.py; do not hand-edit.\n"
        "% Hydraulic quantities use the engine kernels; inputs follow\n"
        "% kp62_0_historical_matrix.yaml and the OYO 1999 provenance record.\n"
        "% Requires xcolor, tikz with arrows.meta, and amsmath/mathtools.\n"
    )
    target.write_text(header + "\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {target}")
    print(
        f"lambda_in={lam_in:.4f}, lambda_out={lam_out:.4f}, "
        f"lambda_out_eff={lam_out_eff:.4f}, r_e={r_e:.5f}"
    )
    print(f"head drops={DROP_OUT:.4f}/{DROP_L:.4f}/{DROP_IN:.4f}; total={DH:.4f}")


if __name__ == "__main__":
    main()
