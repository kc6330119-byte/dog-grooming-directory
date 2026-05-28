# dog-grooming-directory
National dog grooming directory — Collins Digital Media

## Maintenance — whenever you refresh listing data

Two steps keep the AdSense/SEO content remediation intact (see `CLAUDE.md` for full detail):

1. **Re-run `scripts/extract_gsc_protected.py` against a fresh GSC Performance export** so newly-ranking pages stay grandfathered past the quality gate (otherwise a page already earning Google traffic could be noindexed on the next build).
2. **Re-run `generate_fact_descriptions.py` (dry run, then `--apply`)** so new listings get the same fact-grounded descriptions as the rest. The calibration scripts (`analyze_fact_coverage.py`, `calibrate_gate.py`) are committed for re-checking join coverage and the gate threshold.
