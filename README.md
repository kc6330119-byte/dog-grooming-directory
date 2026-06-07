# dog-grooming-directory
National dog grooming directory — Collins Digital Media

## Maintenance — whenever you refresh listing data

Two steps keep the AdSense/SEO content remediation intact (see `CLAUDE.md` for full detail):

1. **Re-run `scripts/extract_gsc_protected.py` against a fresh GSC Performance export** so newly-ranking pages stay grandfathered past the quality gate (otherwise a page already earning Google traffic could be noindexed on the next build). It **merges** by default (preserves the existing list, adds the export's click-earners) — **do not use `--overwrite`** during a traffic dip: a single export is a 28-day snapshot, and overwriting drops temporarily-suppressed pages and re-inflates the thin indexed surface. See `CLAUDE.md` for the full rationale.
2. **Re-run `generate_fact_descriptions.py` (dry run, then `--apply`)** so new listings get the same fact-grounded descriptions as the rest. The calibration scripts (`analyze_fact_coverage.py`, `calibrate_gate.py`) are committed for re-checking join coverage and the gate threshold.
