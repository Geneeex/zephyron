# Manuscript files and paper record

The associated preprint is [arXiv:2609.25709](https://arxiv.org/abs/2609.25709), first submitted on 22 September 2026. The author order is Sabik Bin Sultan, Shafi Bin Sultan and Safwan Sadad. The arXiv record lists DOI `10.48550/arXiv.2609.25709`; at the metadata check it described DataCite registration as pending, so the arXiv URL is the direct access link.

This repository contains the latest locally verified author-side manuscript files:

- `manuscript/word/Zephyron_Research_Manuscript.docx` — 46 pages in the reviewed Word layout.
- `manuscript/latex/` — complete LaTeX source, bibliography, 40 image assets and upload instructions; 49 pages with the verified Tectonic layout.
- `manuscript/assembled_manuscript.md` — supporting manuscript text source. The title-page author block is supplied by the formatted Word/LaTeX files.
- `manuscript/artifact_verification.json` — file hashes and scope of the existing author revision.

These are editable supporting author manuscripts. They have not been compared byte for byte against the uploaded arXiv TeX archive, and they should not be described as the exact archived source version. The arXiv record is authoritative for the deposited preprint.

The author update changed only the author block and metadata; later pages were verified pixel-identical to the preceding reviewed files. Word and LaTeX naturally paginate differently. The manuscripts contain 38 numbered figures, 34 displayed equations, six tables, two executable-reference-code listings and 59 IEEE references. Only page numbers remain in the footer.

## Word

Open the `.docx` in Word. Native equations and text remain editable; figures are embedded. The file is about 38 MB and should be added with Git or GitHub Desktop, not the browser uploader.

## Overleaf

Create a ZIP containing the contents of `manuscript/latex/`, with `main.tex` at the ZIP root, and use **New Project > Upload Project**. The supplied standalone Overleaf ZIP can also be uploaded directly. Select `main.tex` as the main document and use the README's compiler settings. The source was verified locally with Tectonic 0.17.0; a separate pdfLaTeX binary was not run. No BibTeX or Biber step is needed because `references.tex` supplies the keyed IEEE bibliography.

No PDF is distributed in this repository. A local TeX compilation or Overleaf creates its own preview; the `.gitignore` keeps compilation products out of commits.
