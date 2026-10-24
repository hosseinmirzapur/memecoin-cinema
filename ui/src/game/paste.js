// Finds a contract address anywhere in pasted text, so a copied line like "CA: <address>" works too.
const EVM = /0x[0-9a-fA-F]{40}(?![0-9a-fA-F])/;
const SOLANA = /(?<![1-9A-HJ-NP-Za-km-z])[1-9A-HJ-NP-Za-km-z]{32,44}(?![1-9A-HJ-NP-Za-km-z])/;

// Returns { chain, address }. EVM addresses come back with chain null: the viewer picks BSC, Base or Ethereum.
export function findAddress(text) {
  const t = String(text ?? '');
  const evm = t.match(EVM);
  if (evm) return { chain: null, address: evm[0] };
  const sol = t.match(SOLANA);
  if (sol) return { chain: 'sol', address: sol[0] };
  return null;
}

export const isMac = () => /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || '');
