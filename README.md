# PortfolioOps

PortfolioOps is a new standalone project that fuses the earlier portfolio layers into one operational view.

## Why this exists

The C-drive portfolio now has:

- declared portfolio metadata from `ResearchConstellation`
- live folder telemetry from `DrivePulse`
- status recommendations from `TriageWorkbench`
- maturity scores from `FAIRPortfolio`

What it still lacked was one project that combines those signals and turns them into a concrete operating queue.

## What it does

- merges portfolio, live-scan, triage, and FAIR snapshots
- computes a per-project readiness score
- distinguishes explicit status, triage-resolved status, and still-unresolved rows
- highlights operationally backed projects
- exposes a primary action for each project
- serves the result as a static dashboard and E156 bundle

## Outputs

- `ops-readiness.json` - merged readiness model
- `data.json` and `data.js` - dashboard payloads
- `index.html` - static operating dashboard
- `e156-submission/` - paper, protocol, metadata, and reader page

## Rebuild

Run:

`python C:\Users\user\PortfolioOps\scripts\build_portfolio_ops.py`

## Scope note

This project is an operating heuristic, not a definitive project-truth system. It is only as good as the bundled upstream snapshots it fuses.
