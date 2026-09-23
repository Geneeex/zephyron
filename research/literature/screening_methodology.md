# Search, screening and focused review audit

This is a reproducible literature-scoping workflow supporting an engineering design manuscript. It is not a systematic review, a meta-analysis, a bibliometric census, or a claim to have read thousands of full texts.

## Broad metadata retrieval

Database: Crossref public REST API, `/works`, `query.bibliographic` parameter. Each query requested the first 500 relevance-ranked records, with publication-date filter 1995-01-01 through 2026-09-16. Retrieval occurred 2026-09-15 18:23–18:24 UTC, equivalent to 2026-09-16 00:23–00:24 in Asia/Dhaka. Exact request URLs, timestamps and provider result totals are stored in `search_log.json`; the public repository omits raw responses and abstract text, while preserving bibliographic records and the original flags.

| Query | Returned |
|---|---:|
| disaster rescue ground robot | 500 |
| mobile robot environmental monitoring gas sensing | 500 |
| robot radiological nuclear inspection mapping | 500 |
| mobile robot water quality monitoring | 500 |
| low cost modular mobile robot architecture | 500 |
| mobile manipulator disaster response intervention | 500 |
| rough terrain unmanned ground vehicle navigation field | 500 |
| search rescue robot human robot interaction field validation | 500 |
| gas source localization mobile robot | 500 |
| robotics subterranean exploration autonomous navigation | 500 |

Provider-reported total results are broad search-match counts, often much larger than relevant robotics literature. They are NOT screened-paper counts. The actual retrieved set contains 5,000 rows. Deduplication uses lowercase DOI where available and a normalized title otherwise, retaining 4,858 unique records and removing 142 duplicate rows. Query provenance is retained per record. The resulting machine-readable corpus is available as `deduplicated_records.json` and `.csv`.

## Automated metadata flagging

The original retrieval script applied two case-insensitive regular expressions to title plus available abstract. A candidate must match both a robot/platform term and a mission/application term.

Robot/platform expression: `robot|rover|unmanned ground|\bugv\b|mobile platform`.

Mission expression: `rescue|disaster|environment|gas|radiation|radiological|nuclear|water quality|monitor|inspection|hazard|subterranean|field|terrain|navigation|manipulat|modular|low.cost`.

This flags 1,630 candidates and leaves 3,228 records unflagged. Only 802 unique records contain an abstract in the retrieved metadata. These are machine flags, not human eligibility decisions or quality ratings. Unflagged papers are not scientifically excluded: missing abstracts, language, synonyms and platform terminology can cause false negatives. Generic words such as “field” can cause false positives.

## Focused full-text review

A separate targeted discovery process used primary publisher pages, DOI records, author manuscripts, Europe PMC full-text XML and arXiv. Thirty closely related source records were collected; 25 accessible sources received targeted reading of relevant methods, results, discussion and limitations. `evidence.json` states the exact reviewed version and page/section locators. It records supported claims, transfer limits and proposed design implications. This manual set complements the broad scoping search; it is not represented as a complete eligibility funnel from the 1,630 candidates.

Five attempted sources are not included in the focused evidence: the 2013 Fukushima response report, Murphy's 2004 rescue-robot article, the CSIRO subterranean-team article, the RGB-D multi-sensor SLAM article and HeRo. Full-text access attempts were blocked, incomplete or otherwise unsuccessful. They should not be presented as deeply reviewed or used for unverified detailed claims. The public repository retains only the 25-source focused evidence ledger.

Version qualifications: the German Rescue Robotics Center evidence was read in its 2022 preprint; its journal issue is 2024, following online publication in December 2023. CERBERUS is cited as 2024 and ResQbot as 2018 despite legacy citation-key suffixes. SMARTmBOT, Next-Best-Smell and Schwaiger's reviewed 2024 version are identified as preprints. These distinctions prevent a citation key or accessible manuscript from being mistaken for publication status.

## Limits and interpretation

Coverage depends on one metadata database, finite top-ranked retrieval, query wording and available abstracts. No completeness, inter-rater agreement or formal study-quality assessment is claimed. The focused review is purposive and access-constrained. It prioritizes primary sources that expose useful design mechanisms and evaluation limitations, rather than creating a statistical estimate across the whole research field.

The earlier Zephyron description was identified by the user as AI-written without proper dimensions or measurements. It is used only as concept/function context. Its numerical specifications and alleged results are excluded entirely from scientific evidence. Published results on other robots, declared design assumptions, analytical calculations, simulation results and future physical measurements must be kept distinct.

## Reused figures

The six source images actually used in the manuscript are included under `assets/`. See `assets/figure_licenses.json` and the repository-level `THIRD_PARTY_NOTICES.md` for authors, original figure numbers, licenses and modifications. The unused Schwaiger image is excluded. These images report other platforms, not Zephyron measurements.
