import { ENCOUNTER_BY_ID, explainError } from '@/game/quests.js';

// Film order. A reel waits for its answer and plays only after the reel before it.
export const REEL_IDS = ['token_info', 'security', 'holders', 'traders', 'kline', 'smart_money', 'kol', 'agent', 'verdict'];

export const VERDICT_WORD = { APE: 'ENTER', REJECT: 'PASS', NEED_MORE_DATA: 'HOLD' };
export const VERDICT_TONE = { APE: 'ape', REJECT: 'reject', NEED_MORE_DATA: 'wait' };

export const SOURCE_LABEL = {
  token_info: 'Identity',
  security: 'Gatekeeper',
  holders: 'Holders',
  traders: 'Tape',
  kline: 'Chart',
  smart_money: 'Smart wallets',
  kol: 'KOL voices',
};

// What one reel knows right now. pending = still developing; ok = developed; error = no footage.
export function reelData(state, id) {
  if (id === 'agent') {
    const s = state.agent?.status;
    return { status: s === 'ok' ? 'ok' : s === 'error' ? 'error' : 'pending', error: state.agent?.error, sources: state.sources };
  }
  if (id === 'verdict') {
    const done = state.phase === 'done' || state.phase === 'blocked';
    return { status: done ? 'ok' : 'pending', result: state.result, sources: state.sources };
  }
  const src = state.sources[id];
  return { status: !src ? 'pending' : src.ok ? 'ok' : 'error', preview: src?.preview, error: src?.error, sources: state.sources };
}

export const isReady = (state, id) => reelData(state, id).status !== 'pending';

// The subtitle under each reel: the story while developing, the finding once it lands.
export function subtitleFor(id, data) {
  if (id === 'verdict') return data.result?.verdict_reason ?? ENCOUNTER_BY_ID.verdict.story;
  if (data.status === 'error') return explainError(data.error);
  const encounter = ENCOUNTER_BY_ID[id];
  if (data.status === 'pending') return encounter.story;
  if (id === 'agent') return 'The judge has ruled. Sealing the verdict.';
  const outcome = encounter.outcome(data.preview);
  return `${outcome.headline}. ${outcome.detail}`;
}
