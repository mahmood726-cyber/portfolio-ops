Mahmood Ahmad
Tahir Heart Institute
author@example.com

Protocol: PortfolioOps - Multi-Signal Operational Readiness Audit

This protocol describes a snapshot-first fusion study using bundled outputs from `ResearchConstellation`, `DrivePulse`, `TriageWorkbench`, and `FAIRPortfolio`. Eligible records are all 134 indexed portfolio projects preserved across those bundled snapshots. The primary estimand is the proportion of projects classified as operationally backed, defined as projects with a resolved lifecycle state, code signals, publish signals, and FAIR proxy maturity of at least 60. Secondary outputs will report mean readiness, readiness at 70/100 or higher, triage-resolved rows, action queues, and tier-level readiness means. The build process will emit `ops-readiness.json`, `data.json`, `data.js`, and a static dashboard for browser review. The readiness model will combine explicit statuses, medium- and high-confidence triage resolutions, live path and git evidence, test and manuscript signals, Pages signals, and FAIR-inspired maturity scores. Anticipated limitations include upstream snapshot lag, heuristic weighting, duplicated path effects, and the inability of a high readiness score to certify scientific validity.

Outside Notes

Type: protocol
Primary estimand: proportion of projects classified as operationally backed
App: PortfolioOps v0.1
Code: repository root, scripts/build_portfolio_ops.py, ops-readiness.json, and data-source/
Date: 2026-03-30
Validation: DRAFT

References

1. Wilkinson MD, Dumontier M, Aalbersberg IJJ, et al. The FAIR Guiding Principles for scientific data management and stewardship. Sci Data. 2016;3:160018.
2. Sandve GK, Nekrutenko A, Taylor J, Hovig E. Ten simple rules for reproducible computational research. PLoS Comput Biol. 2013;9:e1003285.
3. Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement. BMJ. 2021;372:n71.

AI Disclosure

This protocol was drafted from versioned local artifacts and deterministic build logic. AI was used as a drafting and implementation assistant under author supervision, with the author retaining responsibility for scope, methods, and reporting choices.
