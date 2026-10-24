// Local progression. Per-viewer convenience only: a blocked storage just means the ranks reset.
const KEY = 'mrd.progress';
const EMPTY = { scans: 0, xp: 0, badges: [] };

export const RANKS = [
  [0, 'Rookie'],
  [3, 'Scout'],
  [8, 'Analyst'],
  [20, 'Alpha Hunter'],
  [50, 'Oracle'],
];

export const BADGES = {
  first_scan: { title: 'First Blood', text: 'Finished your first scan.' },
  clean_sweep: { title: 'Clean Sweep', text: 'All seven GMGN sources answered.' },
  trap_spotted: { title: 'Trap Spotter', text: 'Caught a honeypot before it caught you.' },
  whale_seen: { title: 'Whale Watcher', text: 'Found one wallet holding over 10% of supply.' },
  chest_hoarder: { title: 'Chest Hoarder', text: 'Opened ten chests.' },
};

export function loadProgress() {
  try {
    return { ...EMPTY, ...JSON.parse(localStorage.getItem(KEY)) };
  } catch {
    return { ...EMPTY };
  }
}

function saveProgress(progress) {
  try {
    localStorage.setItem(KEY, JSON.stringify(progress));
  } catch {
    /* storage unavailable: progress lasts for this page only */
  }
}

export function rankFor(scans) {
  let index = 0;
  RANKS.forEach(([min], i) => {
    if (scans >= min) index = i;
  });
  const [min, title] = RANKS[index];
  const next = RANKS[index + 1] ?? null;
  const span = next ? next[0] - min : 1;
  return { title, next: next?.[1] ?? null, progress: next ? (scans - min) / span : 1, toNext: next ? next[0] - scans : 0 };
}

// Rewards for one finished scan. Returns the new progress, the XP gained and any badges just unlocked.
export function awardScan(progress, result) {
  const sourcesOk = (result.sources ?? []).filter((s) => s.ok).length;
  const xp = sourcesOk * 10 + (result.agent?.ok ? 25 : 0) + 50;
  const next = { ...progress, scans: progress.scans + 1, xp: progress.xp + xp, badges: [...progress.badges] };
  const unlocked = [];
  const earn = (id, earned) => {
    if (earned && !next.badges.includes(id)) {
      next.badges.push(id);
      unlocked.push(id);
    }
  };
  earn('first_scan', true);
  earn('clean_sweep', sourcesOk === (result.sources ?? []).length && sourcesOk > 0);
  earn('trap_spotted', result.signals?.security?.honeypot === true);
  earn('whale_seen', result.signals?.holders?.ok === true && result.signals.holders.largest_share > 0.1);
  earn('chest_hoarder', next.scans >= 10);
  saveProgress(next);
  return { progress: next, xp, unlocked };
}
