const BASE58 = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
const EVM = /^0x[0-9a-fA-F]{40}$/;

// Mirrors scripts/validate_address.py; the server re-checks, this only gives early feedback.
export function addressError(chain, address) {
  const a = address.trim();
  if (chain === 'sol') return BASE58.test(a) ? null : 'Solana addresses are 32–44 base58 characters.';
  return EVM.test(a) ? null : 'EVM addresses are 0x followed by 40 hex characters.';
}

export function pct(value, digits = 1) {
  return Number.isFinite(value) ? `${(value * 100).toFixed(digits)}%` : '—';
}

export function signedPct(value, digits = 1) {
  return Number.isFinite(value) ? `${value >= 0 ? '+' : ''}${(value * 100).toFixed(digits)}%` : '—';
}

export function num(value, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : '—';
}

export function count(value) {
  return Number.isFinite(value) ? Math.round(value).toLocaleString('en-US') : '—';
}

// Small token prices need scientific notation or the digits vanish (1e-6 style).
export function price(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n === 0) return '—';
  return n < 0.001 ? `$${n.toExponential(3)}` : `$${n.toPrecision(4)}`;
}

export function usd(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return '—';
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

export function age(unixSeconds) {
  const n = Number(unixSeconds);
  if (!Number.isFinite(n) || n <= 0) return '—';
  const hours = (Date.now() / 1000 - n) / 3600;
  if (hours < 48) return `${Math.max(0, Math.round(hours))}h`;
  return `${Math.round(hours / 24)}d`;
}
