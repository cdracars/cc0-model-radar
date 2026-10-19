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

To use an installed Chromium-based browser such as Opera instead of the
Playwright-managed Chromium binary:

```bash
python -m cc0_model_radar --browser --browser-path "$(command -v opera)" --limit 25
```

Use a visible browser window when a site blocks headless automation:

```bash
python -m cc0_model_radar --browser --headed --browser-path "$(command -v opera)" --limit 25
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

The matcher compares titles (token overlap) against Printables results and
classifies each candidate as:

- `matched`: a direct Printables search result has a very strong title match;
- `possible_match`: a result needs human review (direct search, or any hit from the search fallback);
- `likely_not_found`: Printables could not be searched directly, and the search fallback explicitly reported zero indexed Printables models; manual review is still required;
- `unknown`: neither Printables nor the search fallback gave a usable answer (blocked, challenge page, rate-limited, or an unrecognized page).

An empty or challenge page is never treated as proof of absence. When the
direct Printables search returns no parseable results, the tool falls back to
the search engine instead of reporting `not_found`.

The report includes the evidence URLs so a candidate can be reviewed before any re-upload decision.

If Printables blocks direct access, the tool automatically uses a public
search-results fallback for `site:printables.com/model/` queries. Search
results are leads, not proof that a model is absent from Printables.

## Scope and safety

- Public pages only.
- No authentication or CAPTCHA handling.
- Conservative request delay.
- No model-file downloads.
- No automatic publishing.
- Respect each site's terms, robots guidance, rate limits, and creator licensing.

