# 4TU.ResearchData deposit package for v1.2.0

Prepared 2026-09-27. **Not submitted or published.** Use the existing draft
with reserved DOI `10.4121/8ffa1f3e-942e-4852-b02a-a259b9d6d00d`; do not create
a second deposit. The public DOI and DataCite lookups return 404, consistent
with reservation. The private draft cannot be verified without the author's
4TU account. All repository and thesis copies of the DOI agree.

## Files to upload

* `bep-reliability-engine-v1.2.0.zip`: `git archive` of the annotated release
  tag, with a single `bep-reliability-engine-v1.2.0/` root directory.
* `RELEASE-MANIFEST.json`: release commit, archive SHA-256 and scope.
* `README-DEPOSIT.md`: archive contents, installation, validation and input
  access conditions.

The local delivery directory is `D:/repositories/g6-closeout/deposit/`.
The archive contains tracked source, tests, processed input tables, figures,
documentation and compact evidence. It excludes machine-local agent files,
the thesis source/PDF, credentials, third-party raw data, reference PDFs and
untracked production arrays. Its raw-data README names the restricted inputs
and their provenance; this is a software/evidence deposit, not a claim that
all original data are open or that the full production pipeline is executable
without them. MIT is the repository licence; it grants no rights to excluded
third-party sources.

## Metadata to paste

**Title:** bep-reliability-engine v1.2.0: computational evidence for time-dependent
backward erosion piping reliability of the Tokachi and Satsunai levees

**Author:** Gijs Morten Rietman. ORCID:
https://orcid.org/0009-0008-9443-696X. Affiliation: Delft University of Technology.
This is the author list in `CITATION.cff`; supervisors are not added as authors
without an authorship decision.

**Type:** Software. **Version:** 1.2.0. **Language:** English.
**Licence:** MIT. **Access:** Open for the uploaded software and evidence.

**Description:**

Source code and supporting computational evidence for the MSc thesis
*Time-Dependent Reliability Assessment of Levees against Backward Erosion
Piping in High-Gradient River Systems* by Gijs Morten Rietman, Delft University
of Technology, 2026. The engine evaluates steady-state Sellmeijer and transient
Pol piping criteria on shared Latin-hypercube samples, updates fragility
against the observed 2016 typhoon survival, and composes piping with overflow
and fluvial scour into annual system failure probability under historical
and +4 K climate ensembles. Version 1.2.0 records the revision following the
Green Light meeting: aquifer-derived matrix grain sizes and regenerated
results, uniformity and internal-stability sensitivities, the annual
consequences of the piping criterion, the measured-berm companion at drained
sections, hydraulic-loading sensitivities, and an assumption-to-conclusion
synthesis. Probabilities are conditional on the stated model, soil, geometry,
loading and drainage assumptions. Restricted third-party raw inputs and large
machine-local production arrays are excluded; the archive documents their
provenance and the requirements for full reruns. The Bayesian package's
internal 0.1.0 provenance stamp intentionally differs from the 1.2.0
distribution version.

**Keywords:** backward erosion piping; levee reliability; flood risk; Monte
Carlo simulation; Latin hypercube sampling; Bayesian updating; fragility
curves; climate change; Tokachi River; Satsunai River; hydraulic engineering.

**Related identifiers / references:**

* Release, identical software version:
  https://github.com/Gimori3/bep-reliability-engine/releases/tag/v1.2.0
* Development repository:
  https://github.com/Gimori3/bep-reliability-engine
* Related thesis: Gijs Morten Rietman (2026), *Time-Dependent Reliability
  Assessment of Levees against Backward Erosion Piping in High-Gradient River
  Systems*, MSc thesis, Delft University of Technology. The public thesis
  repository URL/DOI is not yet available in the project record. Keep this
  bibliographic relationship in the description now; add the public identifier
  as `IsSupplementTo` when it exists. Do not use the private Overleaf URL.

No grant number or additional creator is inferred. Retain verified funding
information already present in the author's draft, if any.

## Exact author steps

1. Open https://data.4tu.nl, click **Log in**, select Delft University of
   Technology and authenticate with your own account.
2. Open **My datasets** / **Dashboard** and edit the existing unpublished
   draft. Check the **DOI reservation** field is exactly
   `10.4121/8ffa1f3e-942e-4852-b02a-a259b9d6d00d`. Stop if it differs; neither
   public lookup can verify a private reservation.
3. In **Files**, upload the three files above. Use the prepared archive as the
   snapshot rather than connecting the moving default GitHub branch. Confirm
   the displayed archive name and size against `RELEASE-MANIFEST.json`.
4. Paste the metadata above into the corresponding fields. Select Software,
   MIT, English and open access. Check the existing creator/ORCID and retain
   the reserved DOI. Add the GitHub release and repository as related links.
5. Click **Save draft**, then preview the record and verify the files, author,
   version, licence and access conditions. The related thesis's title is
   provided; its public URL can be added later.
6. When you intend to make the archive permanent, accept the deposit agreement
   and click **Submit for review** (the repository's publication workflow).
   Respond to any curator request. This action is the author's, not an action
   already performed by this close-out.
7. Once published, open the DOI and check it resolves to this version and the
   correct files. Update the README/thesis wording from reserved to published;
   add the public thesis identifier when issued.

The authenticated draft's current field names cannot be inspected here. These
steps use the repository's current public instructions: [4TU FAQ](https://community.data.4tu.nl/frequently-asked-questions/)
and [metadata review guidelines](https://data.4tu.nl/s/documents/Metadata_review_guidelines_June_2021.pdf),
checked on 2026-09-27. The guidelines confirm that a reserved DOI becomes active
only on publication and that a publication identifier can be added later.
