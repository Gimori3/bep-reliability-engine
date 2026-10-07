# 4TU.ResearchData deposit package for v1.3.0

Prepared 2026-10-07. **Not submitted or published.** It replaces the v1.2.0
package (`docs/release-v1.2.0-deposit.md`) in the same unpublished draft with
reserved DOI `10.4121/8ffa1f3e-942e-4852-b02a-a259b9d6d00d`; do not create a
second deposit. The DOI returned 404 on 6 October 2026, consistent with
reservation. The thesis title page and Appendix D cite Version 1.3.0 and this
DOI.

Why 1.3.0: the final thesis quotes engine work made after the v1.2.0 tag
(ADR-0055 and the gravel-grading, 2016-initiation and why-no-piping studies),
so its statement that all calculations used the cited release needs a release
that contains that work. No production input or result changed.

## Release order

1. Merge `develop` into `main` (the pull request text is in the Pol close-out
   report). `main` is protected; the merge is the owner's.
2. Create the annotated tag `v1.3.0` on the merge commit and publish the
   GitHub release from it (notes: the `[1.3.0]` section of `CHANGELOG.md`).
3. Check that the tag's tree equals the tree recorded in
   `RELEASE-MANIFEST.json`: `git rev-parse v1.3.0^{tree}`. If it does, the
   prepared archive is the tagged content and can be uploaded as is. If it does
   not (something else was merged), regenerate the archive from the tag with
   `git -c core.autocrlf=false archive --format=zip --prefix=bep-reliability-engine-v1.3.0/ -o bep-reliability-engine-v1.3.0.zip v1.3.0`
   and update the manifest's size and SHA-256. Keep `core.autocrlf=false`: on
   Windows the default conversion writes CRLF into the archive, so its files
   would no longer equal the repository's.
4. Upload the deposit (steps below).

## Files to upload

* `bep-reliability-engine-v1.3.0.zip`: `git archive` of the release commit,
  with a single `bep-reliability-engine-v1.3.0/` root directory.
* `RELEASE-MANIFEST.json`: release commit and tree, archive SHA-256 and scope.
* `README-DEPOSIT.md`: archive contents, installation, validation and input
  access conditions.

The local delivery directory is `D:/repositories/pol_feedback_2026-10-06/deposit-v1.3.0/`.
The archive contains tracked source, tests, processed input tables, figures,
documentation and compact evidence. It excludes machine-local agent files,
the thesis source and PDF, credentials, third-party raw data, reference PDFs
and untracked production arrays. Its raw-data README names the restricted
inputs and their provenance; this is a software and evidence deposit, not a
claim that all original data are open or that the full production pipeline is
executable without them. MIT is the repository licence; it grants no rights to
excluded third-party sources. Remove the v1.2.0 files from the draft before
uploading these, so the deposit carries one version.

## Metadata to paste

**Title:** bep-reliability-engine v1.3.0: computational evidence for time-dependent
backward erosion piping reliability of the Tokachi and Satsunai levees

**Author:** Gijs Morten Rietman. ORCID:
https://orcid.org/0009-0008-9443-696X. Affiliation: Delft University of Technology.
This is the author list in `CITATION.cff`; supervisors are not added as authors
without an authorship decision.

**Type:** Software. **Version:** 1.3.0. **Language:** English.
**Licence:** MIT. **Access:** Open for the uploaded software and evidence.

**Description:**

Source code and supporting computational evidence for the MSc thesis
*Time-Dependent Reliability Assessment of Levees against Backward Erosion
Piping in a High-Gradient River System: A Case Study of Tokachi River Levees
at Obihiro, Japan* by Gijs Morten Rietman, Delft University of Technology,
2026. The engine evaluates a steady-state Sellmeijer criterion and the
transient Pol piping criterion on shared Latin-hypercube samples, updates the
fragility against the observed 2016 typhoon survival, and composes piping with
overflow and fluvial scour into annual system failure probability under
historical and +4 K climate ensembles. Version 1.3.0 records the revision after
the supervisor's comments on the Green Light thesis: the two criteria are
compared on one driving head and one set of exit conditions, so their
difference is the effect of finite flood duration, and companion studies cover
a gravel allowance and grading resistance, the evidence of the 2016 flood on
initiation, and why the investigated sections showed no piping in 2016.
Probabilities are conditional on the stated model, soil, geometry, loading and
drainage assumptions. Restricted third-party raw inputs and large machine-local
production arrays are excluded; the archive documents their provenance and the
requirements for full reruns. The Bayesian package's internal 0.1.0
provenance stamp intentionally differs from the 1.3.0 distribution version.

**Keywords:** backward erosion piping; levee reliability; flood risk; Monte
Carlo simulation; Latin hypercube sampling; Bayesian updating; fragility
curves; time-dependent piping; climate change; Tokachi River; Satsunai River;
hydraulic engineering.

**Related identifiers / references:**

* Release, identical software version:
  https://github.com/Gimori3/bep-reliability-engine/releases/tag/v1.3.0
* Development repository:
  https://github.com/Gimori3/bep-reliability-engine
* Related thesis: Gijs Morten Rietman (2026), *Time-Dependent Reliability
  Assessment of Levees against Backward Erosion Piping in a High-Gradient
  River System*, MSc thesis, Delft University of Technology. Add its public
  identifier as `IsSupplementTo` when it exists; do not use the private
  Overleaf URL. (The v1.2.0 package gave the title as "... River Systems";
  the thesis title is singular.)

No grant number or additional creator is inferred. Retain verified funding
information already present in the author's draft, if any.

## Exact author steps

1. Open https://data.4tu.nl, click **Log in**, select Delft University of
   Technology and authenticate with your own account.
2. Open **My datasets** / **Dashboard** and edit the existing unpublished
   draft. Check that the **DOI reservation** field is exactly
   `10.4121/8ffa1f3e-942e-4852-b02a-a259b9d6d00d`. Stop if it differs.
3. In **Files**, delete any v1.2.0 files, then upload the three files above.
   Confirm the displayed archive name and size against `RELEASE-MANIFEST.json`.
4. Replace the title, version and description with the metadata above. Check
   Software, MIT, English and open access, the creator and ORCID, and the
   reserved DOI. Set the related links to the v1.3.0 release and the
   repository.
5. Click **Save draft**, then preview the record and verify the files, author,
   version, licence and access conditions.
6. When you intend to make the archive permanent, accept the deposit agreement
   and click **Submit for review**. Respond to any curator request.
7. Once published, open the DOI and check that it resolves to v1.3.0 with
   these files. The thesis already describes the archive as available; nothing
   in it needs to change.

These steps follow the repository's public instructions as checked for v1.2.0
on 2026-09-27 ([4TU FAQ](https://community.data.4tu.nl/frequently-asked-questions/),
[metadata review guidelines](https://data.4tu.nl/s/documents/Metadata_review_guidelines_June_2021.pdf));
the authenticated draft's field names cannot be inspected from here.
