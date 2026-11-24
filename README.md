# Tier 1 Trauma — Tier 1 FFL Weekly Dispatch

Public-facing weekly fantasy football dispatch, scoreboard triage, holiday-themed awards, standings, playoff bracket tracker, and Max PF draft order for all 12 managers in **Tier 1 Dynasty** (Sleeper League `1398719645564796928`).

## Live Site
**https://blakehenderson45-svg.github.io/tier1-trauma/**

## Features
- **Automated Tuesday Morning Updates**: Runs via GitHub Actions (`.github/workflows/tuesday-dispatch.yml`) every Tuesday at 6:30 AM PT (14:30 UTC) after Monday Night Football & overnight stat corrections settle.
- **100% League-Wide & Unbiased**: Built for all 12 leaguemates equally — no single-manager highlighting or personalization.
- **Weekly Holiday Theme Mixups**: Every week pairs the signature **Tier 1 Trauma** medical/gridiron tone with a timely holiday/seasonal edition (Labor Day Intake, Harvest Moon, Autumn Equinox, Oktoberfest, Halloween Bloodbath, Thanksgiving Carving, Black Friday Clearance, Holiday Playoff Intake, Christmas Trauma Ward, New Year's Championship Flatline, etc.).
- **Full Season Archive**: Switch seamlessly between Week 1 through the latest completed week, with deep-linking (`?week=11`).
- **Interactive Box-Score Triage**: Click any matchup to inspect top starters and bench malpractice.
- **Standings, All-Play Matrix & Anti-Tanking Draft Order**: Sortable standings with playoff cut-line, all-play luck metrics, playoff seedings, and Max PF rookie draft order (`1.01`–`1.12`).
- **Season Team Pulse**: Click any of the 12 franchises to explore their week-by-week scoring sparkline and lineup efficiency.

## Local Refresh
```bash
python3 scripts/generate_dispatch.py
```
