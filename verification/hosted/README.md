# Checking mathematics on GitHub

This check compares the mathematical expressions in a pinned Git commit with their actual rendering on public GitHub pages. It uses an anonymous Chromium session and inspects both 1440-pixel and 760-pixel viewports. Source compilation supplies the reference expression; the captured GitHub MathML supplies the observed expression.

The comparison retains subscripts, superscripts, fractions, relations and meaningful token structure. It detects missing formula hosts, absent operands, unsupported TeX and table-cell collisions. Screenshots support a separate review of legibility and page layout. Mathematical equivalence and scientific correctness require reading the source arguments.

## Reproduce the capture

Requirements are Node.js 18 or later, Python 3.10 or later, Git, Playwright and MathJax. The workflow pins Playwright 1.56.1 and mathjax-full 3.2.1. Install rendering dependencies outside the source checkout, then run from the repository root:

```bash
npm install --prefix /absolute/math-runtime playwright@1.56.1 mathjax-full@3.2.1
/absolute/math-runtime/node_modules/.bin/playwright install chromium
export NODE_PATH=/absolute/math-runtime/node_modules
node verification/hosted/probe_hosted_math.cjs --root . --repository GoGoKo699/Quantum-Gauge-Reconstruction --revision FULL_COMMIT_SHA --page README.md --output /absolute/new-probe-directory
node verification/hosted/capture_hosted_math.cjs --root . --repository GoGoKo699/Quantum-Gauge-Reconstruction --revision FULL_COMMIT_SHA --output /absolute/new-capture-directory
```

Replace the illustrative absolute paths and `FULL_COMMIT_SHA` with the intended environment and complete observed commit identifier. Output directories must be new and empty, so an unsuccessful attempt is retained. The source checkout must contain the exact Git objects; uncommitted working files are not the source of the comparison.

The probe checks one representative page and reports runtime or source issues. The full collector inventories every tracked Markdown page by default, captures every expression at both widths, and writes `hosted-report.json`, per-page records, HTML and screenshots. A passing probe is not a full repository check. The source and capture comparison is implemented in [check_rendered_math.py](check_rendered_math.py).

## Read-only automation

The [workflow](../../.github/workflows/hosted-math.yml) runs on pull requests and manual dispatch. It checks out the exact pull-request head, pins its actions by commit, uses a `contents: read` token, and performs no source writes. Its artifact includes failed diagnostics as well as completed captures. Workflow artifacts expire after 14 days and should not be treated as permanent scientific storage.

The final review must inspect the saved screenshots against the corresponding source. A structural match alone does not establish that a long expression is comfortable to read on every display, or that future GitHub renderer versions will behave identically.
