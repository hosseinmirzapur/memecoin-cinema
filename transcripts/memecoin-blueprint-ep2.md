# Memecoin Blueprint - Episode 2 Transcript

Date: 2026-08-27
Source: YouTube transcript provided by user
Topic: Filters, fees, and bundle detection for memecoin trading

## Key Insights
- New pairs filter: market cap min 6,000, token age max 6 minutes
- Soon/final stretch filter: token age max 30, protraders min 20, market cap min 8,500
- Migrated filter: protraders min 100, market cap min 30,000
- Fee presets: pyo 0.00001, tip 0.000001, MEV off, buy slippage 20%, sell slippage 50%
- Bundle detection is critical - 4 main checks:
  1. Holder distribution: avoid if top holder >4% of supply
  2. Similar SOL balances among top holders
  3. Common funding source/timing for top holder wallets
  4. Uniform trading terminal among top holders
- Additional bundle signals:
  - Identical token percentages among top holders
  - Top holders buying same coins in history
  - Many fresh wallets in top 10 holders
  - Bubble map clusters showing multi-wallet ownership
- Fresh wallets indicator: leaf icon shows recently created wallets buying

## Applied Changes
- Added concrete filter thresholds to research workflow
- Added bundle detection rules to decision rubric
- Added fee/slippage reference for execution context
- Added bubble map and fresh wallet checks to holder analysis
