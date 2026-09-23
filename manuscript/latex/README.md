# Zephyron Overleaf source project

Upload `Zephyron_Overleaf.zip` using **New Project > Upload Project** in Overleaf.
Set the main document to `main.tex`, the compiler to **pdfLaTeX**, and use a
current TeX Live release. Recompile twice if citation cross-references are not
yet resolved. No BibTeX or Biber run is required: the verified, numbered IEEE
bibliography is editable in `references.tex` and is linked by citation keys.
Official Overleaf guidance: https://www.overleaf.com/learn/latex/Kb/Uploading_a_project
and https://docs.overleaf.com/getting-started/recompiling-your-project/selecting-a-tex-live-version-and-latex-compiler.

The package uses common LaTeX packages; newtx text/math fonts are selected when
available, with a Times-compatible fallback. Tectonic can also compile this
standard LaTeX source.

For this delivery, compilation was verified locally with **Tectonic 0.17.0**
(a XeTeX-derived engine): 49 pages, no overflowing boxes, undefined citations
or missing glyphs. A separate pdfLaTeX executable was not run. The pdfLaTeX
setting above is the recommended Overleaf configuration for this portable,
ASCII LaTeX source and its common packages. The private compilation and
full-page visual review are recorded in the accompanying research QA files;
no compiler output is included in this upload archive.

The TeX project is self-contained and uses only relative image paths, with no
external image fetches. Original local paths occur only in provenance metadata. `assets/` contains the exact manuscript image bytes, including three
unmodified author-supplied rover photographs. `reference_metadata.json` retains
the overlaid primary-source metadata behind all 59 numbered IEEE references.
`source_manifest.json` records source and asset hashes, figure order and counts.

This is the LaTeX companion to the final editable Word manuscript: 38 figures,
34 numbered equations, six tables, two executable-reference-code listings and
59 references, in the same order and with the same scientific content. Layout
and page breaks naturally differ between Word and LaTeX. It uses a single
column, Letter paper, 11-point serif type and a page-number-only footer. The
Conclusion ends the main body and is followed by References. The exact target
journal has not yet been identified, so no journal-specific template compliance
is claimed.

The machine-learning architectures are proposed and untrained in this study.
The code listings implement tested deterministic validation primitives, not
trained detectors or measured model performance. The selected engineering
baseline and scenario calculations must not be confused with field trials.

Canva's 15 native page images were available only at preview resolution
(596 x 335 pixels). Their original bytes are retained here; larger raster size
would not add detail. Replace those assets with high-resolution native exports
before a submission requiring higher-resolution artwork, keeping captions,
figure order and attribution unchanged. Other supplied image-source credits
and licensing qualifications remain in their full figure captions.

This source-only distribution intentionally contains no compiled PDF. Overleaf
creates a preview in your project when you compile it. The Word file is supplied
separately. Do not add private compiler output to the delivery archive.
