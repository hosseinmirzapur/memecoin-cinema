# Skill Iteration 1: Fast Token Review Wrapper

## Goal
Create a deterministic, fast-path token review workflow that can be invoked with a single command or skill call.

## Problem
Current workflow requires manually chaining multiple `gmgn-cli` commands. This is slower and less repeatable for quick `APE` / `REJECT` decisions.

## Proposed Solution
Add a new workspace skill or helper that runs the canonical research pipeline in the minimum viable order:
1. Validate address format.
2. Run `gmgn-cli token info`.
3. Run `gmgn-cli token security`.
4. Run holder-analysis script.
5. Run `gmgn-cli market kline --resolution 15m`.
6. Output structured findings and verdict.

## Acceptance Criteria
- Input: chain, token address, optional language and time window.
- Output: structured `APE` / `REJECT` / `NEED_MORE_DATA` result.
- Speed: complete within target time window without unnecessary extra calls.
- No trading, orders, or token creation.
- Auth handled via existing `gmgn-cli config --check` flow.

## Status
- Proposed
- Not implemented
