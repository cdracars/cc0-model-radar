# CC0 Model Radar

Read-only discovery tool for finding MakerWorld models marked CC0 that do not appear to have a corresponding Printables listing.

The tool produces candidates for human review. It does not log in, bypass CAPTCHAs, download model files, or upload/re-publish models.

## Status

Early MVP. MakerWorld page layouts and access controls can change, so results are explicitly marked as candidates rather than proof that a model is absent from Printables.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m cc0_model_radar --limit 25 --output reports/cc0-candidates.csv
```

When MakerWorld blocks plain HTTP requests, use browser mode. The first setup
also installs the Chromium browser used by Playwright:

```bash
pip install -r requirements.txt
playwright install chromium
python -m cc0_model_radar --browser --limit 25 --output reports/cc0-candidates.csv
```

For troubleshooting a browser run, keep candidates that failed license
verification instead of dropping them:

```bash
python -m cc0_model_radar --browser --include-unverified --limit 5
```

The report will show whether MakerWorld returned a block page or whether the
page simply did not expose recognizable CC0 text.

Browser mode uses a fresh, unauthenticated browser session. It loads public
pages only, does not solve CAPTCHAs, log in, download model files, or upload
anything. Keep the delay conservative and stop if MakerWorld presents a block
page.

To use saved MakerWorld HTML while developing or when a network blocks MakerWorld:

```bash
python -m cc0_model_radar --makerworld-html fixtures/makerworld-cc0.html --limit 25
```

## Matching policy

The matcher checks Printables by title and creator, then classifies results as:

- `not_found`: no plausible Printables result was found;
- `possible_match`: a result needs human review;
- `matched`: the result has a direct source link or a very strong title/creator match;
- `unknown`: the source could not be queried.

The report includes the evidence URLs and timestamps so a candidate can be reviewed before any re-upload decision.

## Scope and safety

- Public pages only.
- No authentication or CAPTCHA handling.
- Conservative request delay.
- No model-file downloads.
- No automatic publishing.
- Respect each site's terms, robots guidance, rate limits, and creator licensing.

