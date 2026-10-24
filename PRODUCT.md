# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Active memecoin traders on desktop and mobile, working mid-session. They copy a token contract address from a chart, feed or wallet page and want a fast verdict before buying. They are not usually careful or deliberate; the desk has to do the thinking for them in seconds.

## Product Purpose
Memecoin Research Desk turns a pasted contract address into a guarded verdict: ENTER (APE), PASS (REJECT) or HOLD (NEED_MORE_DATA). It runs GMGN evidence (token info, security, holders, traders, K-line, smart money, KOL mentions) through deterministic hard guards and a scoring agent. Success is a clear verdict the user trusts, with the evidence one tap away.

## Positioning
A guarded verdict built from on-chain evidence, where hard risk guards can override any agent opinion. A neighboring tool could show charts or holder lists; it cannot truthfully show a verdict where a honeypot or a rat-trader concentration is a hard stop regardless of the score.

## Operating Context
- Input is copy-paste only: a contract address is copied from elsewhere and pasted anywhere on the page. Typing is not the flow.
- EVM addresses do not reveal their chain, so the user taps BSC, Base or Ethereum after pasting. Solana addresses are detected automatically.
- A scan runs for roughly 20 to 60 seconds, with progressive evidence arriving reel by reel.
- Sessions are repeated and quick. The desk is reopened many times a day, often with another tab or chart open alongside.

## Capabilities and Constraints
- Local Python server (`scripts/ui_server.py`) serving a React 19 + Vite + Tailwind v4 front end; data comes from the gmgn-cli and a Kilo AI gateway.
- Verdict vocabulary is fixed in the product: ENTER / PASS / HOLD map to APE / REJECT / NEED_MORE_DATA.
- Scan results stream over SSE; a scan can end blocked by a hard guard.
- Progress (XP, ranks, badges) is stored per browser only; no accounts.
- Sound is optional and off by default.
- Undecided: whether the 3D intro (Three.js) stays in its current form.

## Brand Commitments
- Product name: "Memecoin Research Desk" (short mark "MR").
- Verdict words ENTER / PASS / HOLD are user-facing vocabulary and should not change without a product decision.
- The game layer (reels, XP, ranks, badges) is part of the product identity, but it is secondary to the verdict. The user asked for it to be quieter, not removed.

## Evidence on Hand
- Live data flows through GMGN and the Kilo gateway; no screenshots or testimonials are approved for use.
- The current idle desk and scan results are the only UI references. The repo README screenshot (`docs/assets/desk.png`) shows the current design.
- Absences to respect: no customer quotes, no performance or profit claims, no invented benchmarks.

## Product Principles
- The verdict leads. Evidence supports it; the game decorates around it, never ahead of it.
- Hard guards are shown as hard guards. A PASS from a guard must read differently from a PASS from the score.
- Built for speed. Every state (idle, scanning, verdict, blocked, error) must be readable in a glance on a phone.
- No claims the data cannot back. Risk language stays factual and sourced.

## Accessibility & Inclusion
Colour is never the only carrier of verdict meaning (words and icons accompany ENTER / PASS / HOLD). Reduced motion is respected. Mobile use is a first-class requirement, not a fallback.
