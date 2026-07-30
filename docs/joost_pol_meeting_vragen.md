# Questionnaire for Joost Pol: Piping Model Validation

> **SUPERSEDED -- ANSWERED (header added 2026-07-31; content unchanged).** The
> questions below were put to Joost Pol at the 2026-07-06/07 meeting and are
> retained as the record of what was asked. They were answered; the answers are
> in [`docs/validation/pol-meeting-2026-07-07-dispositions.md`](validation/pol-meeting-2026-07-07-dispositions.md)
> and were landed as **ADR-0026**, **ADR-0027** and **ADR-0028**.
>
> Note in particular that Tier 1 question 1 describes the implementation as
> computing `H_erosion = r_e(h - h_e) - 0.3 D_bl`. Pol's answer was that this is
> **wrong**: after heave ruptures the blanket the exit is unfiltered, so r_e must
> not appear in the erosion head (confirmed in writing 2026-07-08, "Ja klopt";
> see [`docs/validation/head-datum-re-convention-CLOSED.md`](validation/head-datum-re-convention-CLOSED.md)).
> The engine was changed accordingly by ADR-0027, and ADR-0028 removed r_e from
> the static comparator too. **Do not read the premises below as descriptions of
> the current engine.**

## Tier 1: Essential questions on reference frames and calibration

### 1. The head datum for the erosion-driving head and the $0.3D_{bl}$ crack-resistance

**Context:**
In SIE 2024 (Eq. 6), the erosion-driving head is defined as $H = h - h_e - 0.3D_{bl}$, where the crack-resistance of the blanket is subtracted directly from the raw outer water level $h$. However, in Eq. 10, the aquifer head arriving at the landside levee toe $u_{it}(t)$ is attenuated by the response factor $r_e$. In my implementation, I compute the erosion-driving head as $H_{erosion} = r_e(h - h_e) - 0.3D_{bl}$. Thus, the $0.3D_{bl}$ loss is applied after the $r_e$ attenuation to the head that has actually arrived at the exit point, rather than directly to the raw outer level. This matters substantially because $r_e$ in my model is around **0.6**, meaning my erosion head is roughly **40%** lower and progression is much slower. Additionally, I treat $r_e$ not as a fixed **0.6** but as a stochastic variable based on USACE/TAW leakage lengths.

**Question:**
Is my physical interpretation correct that the $0.3D_{bl}$ crack-resistance should be subtracted from the effective ($r_e$-attenuated) head at the exit point instead of directly from the raw outer water level? And do you consider modeling $r_e$ stochastically based on local seepage lengths to be a legitimate extension of your method?

**Answer:**
Joost Pol clarified that the response factor $r_e$ should no longer be taken into account after heave has occurred. Furthermore, he agreed that treating $r_e$ as a stochastic variable based on USACE/TAW leakage paths is the correct and appropriate approach for this research.

### 2. The $C_e$ prior distribution and discrepancies in calibration values

**Context:**
The parameter $C_e$ is one of my most important stochastic Monte Carlo variables. The progression rate $dl/dt = 89 \cdot C_e(k_{aq}(H-H_{eq})/L)^{0.81}$ scales directly and linearly with it. However, I found different values in your papers. In the base case of the reliability analysis (SIE 2024, Table 2), the prior is specified as a Lognormal distribution with a mean of **0.055**. In the calibration paper (CG 2024, Table 1), the calibrated experimental values are much lower: between **0.007** and **0.030**, with an average of **0.016**, and **0.014** for the large-scale FPH experiment. In that same paper (CG 2024), there is also an internal discrepancy for test B25-245: Table 1 gives $C_e$ as **0.010**, but the caption for Figure 5 lists **0.014**. In my current model, I use a Lognormal distribution with a mean of **0.014** and a COV of **0.50**, specifically so I can use this distribution via a Bayesian update with historical 2016 data to absorb the uncertainty between laminar and turbulent flow.

**Questions:**
Why is the mean of the prior in the reliability study (**0.055**) roughly four times higher than your experimentally calibrated values (**0.014**)? Which value actually belongs in a real field-scale reliability analysis, and what is the correct reference value for B25-245? Furthermore, is it legitimate to use $C_e$ as a stochastic variable to absorb the laminar versus turbulent model uncertainty?

**Answer:**
Joost Pol recommends using a $C_e$ mean of **0.055** for the levee reliability calculations. The lower values (**0.010** and **0.014**) were based on small-scale experiments, whereas **0.055** was determined later by incorporating large-scale experiments and is the recommended value for practical applications. He acknowledged the inconsistencies noted in the papers, is currently looking into their exact origins, and will provide further clarification later. For now, the recommendation is to treat it as a stochastic parameter using a Lognormal distribution with $\mu = 0.055$ and $\sigma = 0.043$.

### 3. Field-scale conservatism of the equilibrium-head ($H_{eq}$) end-anchor

**Context:**
The progression ODE requires an equilibrium curve $H_{eq}(l)$ that is piecewise-linear with anchor points at $(0,0)$, $(l_c,H_c)$, and $(L, 0.9H_c)$. The **0.9** factor at the exit is described in both papers as a conservative estimate based on DgFlow FEM simulations at lab scale ($L=3$ to **30 meters**). When I cross-checked this against your own $L=3$ meter simulation in CG 2024 (the S2-2 run), the effective post-critical equilibrium head was roughly $1.01$ to $1.04H_c$. Using the conservative **0.9** anchor artificially inflates the post-critical progression rate by a factor of roughly **1.95** in that $L=3$ meter case. My model computes for a field scale with seepage lengths of **40 to 70 meters**.

**Question:**
Does this significant conservatism in the **0.9** factor persist when we scale up to seepage lengths of tens of meters in the field? How much of the resulting gap between a static failure probability and a transient failure probability should I attribute to this simplified $H_{eq}$ schematization rather than a genuine physical temporal effect?

**Answer:**
Joost confirmed that the **0.9** factor is intended to be conservative. In particular, deriving the equilibrium curve from the simplified relation used in the pipe progression model, rather than from direct numerical simulations, adds to this conservatism. He acknowledged that the simplified equilibrium curve is far from perfect and is strictly based on the specific cases he assessed numerically. I told him I would look back into my calculations on how exactly I found the $1.01$ to $1.04H_c$ values and the resulting 1.95 inflation factor, and that I would come back to him with these calculations to show the issue.

---

## Tier 2: Validation of extensions and physical theory

### 4. The mandatory $k_{aq}$ and $d_{70}$ coupling

**Context:**
While setting up the stochastic variables, I ran into the coupling between permeability ($k_{aq}$) and grain size ($d_{70}$). In the geotechnical dataset, I found too few paired records ($N=6$ total, and only $N=1$ at the governing cross-section) to establish a reliable correlation. I ultimately resolved this by decoupling them and using a two-soil model: a matrix for $d_{70}$ and a framework for $k_{aq}$, effectively computing with a correlation of $\rho = 0$.

**Question:**
How do you typically handle the relationship between grain size and permeability in gravelly aquifers in your work? Do you endorse this two-population interpretation where we assume no correlation, or would you physically expect a genuine correlation that I am currently missing in this model?

**Answer:**
He noted that in practice, the correlation between $k_{aq}$ and $d_{70}$ is often very unclear and difficult to establish, leading to them frequently being decoupled in real-world applications. Given the very limited number of measurements available in this dataset, he agreed that decoupling them is the only viable and practical option.

### 5. The correct scale exponent ($\alpha$) for field-scale confined aquifers

**Context:**
Your critical-head formula has a scale factor with an exponent ($\alpha$) on the dimensionless group $d_{70}^3/(\kappa L)$. There are three different exponents in play. The classical 2D Sellmeijer formula uses $\alpha = -1/3$. In CG 2024, you describe that the 3D DgFlow simulations show a stronger scale effect with $\alpha = -1/2$. At the same time, you cite hole-exit experiments (Van Beek 2015, Allan 2018) that bracket a weaker effect in the range of **-0.2 to -0.45**. In my framework, I am constantly comparing the static response with the transient response at field scale.

**Question:**
Which of these three exponents (-1/3, -1/2, or the experimental band) do you recommend using for a field-scale failure mechanism in a confined aquifer? Does this choice depend on the expected exit geometry (hole-type versus plane-type exit) in the field?

**Answer:**
He agreed with the observations and stated that since the model is 2D and based on Sellmeijer's work, the most pragmatic choice is to assume $\alpha = -1/3$. While the scale exponent remains a major point of discussion in the field with ongoing research, diving deeper into it would be out of scope for this project. He recommends explicitly addressing this in the Discussion chapter, noting that the 2D assumption (and thus the use of $\alpha = -1/3$) is well-supported by the fact that the blanket layers at the site are quite thin (less than 1 meter).

### 6. Under-prediction of the critical pipe length ($l_c$) compared to 3D models

**Context:**
To determine the peak moment in the $H_{eq}$ curve, I use the formula $l_c = 0.5L \tanh(2D_{aq}/L)$ from SIE 2024 (Eq. 13). The paper states this agrees well with 2D numerical models. However, when I check this formula against your 3D DgFlow hole-exit simulations from CG 2024, it consistently under-predicts the simulated critical pipe length by a factor of **1.5 to 2.2**. The real 3D critical pipe length is thus substantially longer than the 2D tanh formula predicts.

**Question:**
Is this under-prediction relative to the 3D DgFlow simulations a known limitation? Is there a corrected or 3D-calibrated version of this formula for hole-type exits that is more appropriate for real field levees?

**Answer:**
He confirmed this is a known limitation and that there is currently no corrected or 3D-calibrated version of the formula for hole-type exits that is better suited for real levees. In deep aquifers, the factor can approach 1/2, and 3D lab experiments frequently show values between 1/3 and 1/2. He advises sticking to the 2D formula (again, justified by the presence of thin blanket layers) and addressing the differences between 2D and 3D models in the Discussion section.

### 7. Compound-event memory during multiple high-water peaks

**Context:**
My model includes compound events where successive typhoon peaks occur. I assume full system memory ($r_l = 0$), meaning there is no pipe healing or recovery in between peaks. The grown pipe length is fully retained. This assumption carries the entire Bayesian calibration step in Phase 2.

**Question:**
Is the assumption of zero recovery between peaks consistent with how you intended the memory model to behave? Do the large-scale experiments support the claim that no pipe healing occurs during the relatively short period between individual typhoon peaks?

**Answer:**
Yes, he confirmed that assuming zero recovery (full system memory) between successive peaks is a reasonable and sound assumption for this model.

---

## Tier 3: Edge cases, definitions, and wrap-up

### 8. The interpretation of the flood-fighting term $t_{ff}/I_{ff}$ in the erosion indicator

**Context:**
Your erosion indicator $I_{er}$ in SIE 2024 (Eq. 7) uses the time limit $t < t_{uh} + t_{ff}/I_{ff}$. The published text states that when organized flood fighting fails ($I_{ff} = 0$), this term "becomes 1". Mathematically, dividing by zero should send the limit to infinity, meaning there is no time limit on erosion at all. In my implementation, I have omitted this entire clause for now, making the limit state an unconditional upper bound (a conservative approach) that gives no credit for flood fighting.

**Question:**
Should the term $t_{ff}/I_{ff}$ mathematically go to infinity when flood fighting fails, or does the text "becomes 1" have a specific physical meaning I am overlooking? Is omitting this clause a correct and safe conservative assumption for my model?

**Answer:**
He noted that organized flood fighting would likely be very difficult or impossible in such flashy rivers during typhoons. Therefore, he agrees that completely omitting the flood-fighting clause is the better and safer approach for this model.

### 9. Framing the low failure probabilities (raw-tail-with-binomial-CI)

**Context:**
At a number of cross-sections in my model, the transient failure probability remains extremely low across all attainable water levels. I want to present this as a substantive finding: these levees are significantly safer against through-progression than the static benchmark implies. I support this using a raw-tail-with-binomial-CI approach, rather than treating it as a fitting gap.

**Question:**
Do you agree that such a low transient failure probability is fundamentally a real finding compared to the static benchmark? Does this framing and the use of raw tail data with a binomial confidence interval sound like a solid scientific approach to you?

**Answer:**
Joost Pol advised against putting too much effort into this specific framing. He noted that from a practical standpoint, extremely small failure probabilities do not carry much meaningful information, and therefore highlighting them as a major substantive finding might not be necessary.
