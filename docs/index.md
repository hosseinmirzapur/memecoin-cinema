# Memecoin Research Workspace

This folder stores the evolving setup for fast token research and the `APE` / `REJECT` workflow.

## Current State
- Unified research guideline: `agents.md`
- GMGN skills installed and config verified: `gmgn-cli config --check`
- Research-only mode active: no trading, orders, or token creation yet

## Iteration Log
Use this section to track accepted changes.

### Iteration 1
- Date: 2026-08-27
- Change: Created `agents.md` as the single source of truth.
- Rationale: Fast, deterministic, CLI-backed GMGN research workflow.
- Result: Baseline workflow and rubric established.

### Iteration 2
- Date: 2026-08-27
- Change: Integrated first YouTube transcript.
- Rationale: Capture real operator setup guidance and safety rules.
- Result: Added `transcripts/memecoin-blueprint-ep1.md` and distilled terminal/filter/mindset insights.

### Iteration 3
- Date: 2026-08-27
- Change: Integrated second YouTube transcript.
- Rationale: Add concrete filter thresholds, fee presets, and bundle-detection heuristics.
- Result: Added `transcripts/memecoin-blueprint-ep2.md` and updated `agents.md` rubric with bundle checks.

### Iteration 4
- Date: 2026-08-27
- Change: Integrated third YouTube transcript.
- Rationale: Add scanning workflow, narrative checks, coin-type filters, and wallet-tracking rules.
- Result: Added `transcripts/memecoin-blueprint-ep3.md` and updated `agents.md` with community/tweet/profile coin rules.

### Iteration 5
- Date: 2026-08-27
- Change: Integrated day 4 scalping transcript.
- Rationale: Add updated filters, chart patterns, and scalping strategies for new pairs/final stretch/graduated coins.
- Result: Added `transcripts/memecoin-blueprint-day4.md` and updated `agents.md` with scalping workflow.

### Iteration 6
- Date: 2026-08-27
- Change: Integrated challenge video transcript.
- Rationale: Add small-account building strategy, trade management rules, and position sizing guidance.
- Result: Added `transcripts/challenge-1sol-to-20sol.md` and updated `agents.md` with challenge-derived rules.

### Iteration 7
- Date: 2026-08-27
- Change: Integrated mindset/psychology transcript.
- Rationale: Add emotional management, discipline rules, and wallet-tracker usage guidance.
- Result: Added `transcripts/mindset-psychology.md` and updated `agents.md` with psychology protocol.

### Iteration 8
- Date: 2026-08-27
- Change: Integrated full strategy/scalping transcript.
- Rationale: Add portfolio-based position sizing, additional filters, and community token checks.
- Result: Added `transcripts/full-strategy-scalping.md` and updated `agents.md` with sizing and filter rules.

### Iteration 9
- Date: 2026-08-27
- Change: Integrated low portfolio strategy transcript.
- Rationale: Add beginner filters, community checks, originality rules, and 40% dip emphasis.
- Result: Added `transcripts/low-portfolio-strategy.md` and updated `agents.md` with additional filters and big four checks.

### Iteration 10
- Date: 2026-08-27
- Change: Integrated Nova Trade live session transcript.
- Rationale: Capture platform-specific features, cashback impact, and real-time trading observations.
- Result: Added `transcripts/nova-trade-live.md` and updated `agents.md` with platform and alpha-signal notes.

### Iteration 11
- Date: 2026-08-27
- Change: Integrated rug avoidance and filters transcript.
- Rationale: Add quick rug checks, fee settings by balance, final-stretch filters, and tracked-wallet avoidance rules.
- Result: Added `transcripts/rug-avoidance-filters.md` and updated `agents.md` with rug-avoidance checklist.

### Iteration 12
- Date: 2026-08-27
- Change: Integrated 100x spotting transcript.
- Rationale: Add about-to-graduate filters, meta tracking, breakout patterns, and wallet-tracking guidance for good calls.
- Result: Added `transcripts/spotting-100x.md` and updated `agents.md` with about-to-graduate and breakout rules.

### Iteration 13
- Date: 2026-08-27
- Change: Integrated discipline and low balance strategy transcript.
- Rationale: Add mindset rules, risk management, position sizing, and scalping strategies for low portfolios.
- Result: Added `transcripts/discipline-low-balance.md` and updated `agents.md` with discipline protocol and scalping rules.

## Decision Rubric Summary
- Critical red flag => `REJECT`
- Multiple medium risks => `REJECT`
- Favorable risk/benefit => `APE`
- Missing required fields => `NEED_MORE_DATA`

## Agent Packaging
- Packaged skill files:
  - `.agents/skills/memecoin-research-agent/SKILL.md`
  - `~/.jcode/skills/memecoin-research-agent/SKILL.md`
- Purpose: convert the unified `agents.md` workflow into a reusable local research mode.
- Default behavior: research-only; no trading, orders, or token creation.
- Composition: uses installed GMGN skills and local scripts as runtime helpers.
- Current loading status: verified as loadable after Jcode restart; use slash command `/memecoin-research-agent` or ask to load the skill.
- Usage contract:
  - Input: chain, contract address, language, optional time window.
  - Output: structured findings and `APE` / `REJECT` verdict.
  - Live trading: explicitly disabled unless later approved and enabled.

## Next Steps
1. Verify skill loading behavior in Jcode.
2. Use the skill for live token reviews and iterate on speed/format.
3. Extend docs if activation changes or additional local skills are added.
