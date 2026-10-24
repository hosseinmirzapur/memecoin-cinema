import {
  Bot,
  CandlestickChart,
  Coins,
  Fish,
  Megaphone,
  PackageOpen,
  Radar,
  Shield,
  ArrowLeftRight,
} from 'lucide-react';
import { age, count, num, pct, usd } from '@/format.js';

// Each GMGN call is an encounter with its own relic (3D), story line and outcome wording.
// `outcome` turns the source's preview into the headline and detail shown on its card.
export const ENCOUNTERS = [
  {
    id: 'token_info',
    name: 'The Identity',
    story: 'Checking the badge. Who is this coin, and how old is it?',
    icon: Coins,
    relic: 'coin',
    xp: 10,
    tone: 'accent',
    outcome: (p) => ({
      headline: p?.symbol ? `${p.symbol} · ${p.name ?? 'unnamed'}` : 'Identity unclear',
      detail: `Liquidity ${usd(p?.liquidity)} · ${count(p?.holder_count)} holders · age ${age(p?.creation_timestamp)}`,
    }),
  },
  {
    id: 'security',
    name: 'The Gatekeeper',
    story: 'Can you sell it, or did the door lock behind you?',
    icon: Shield,
    relic: 'shield',
    xp: 15,
    tone: 'ape',
    outcome: (p) =>
      p?.honeypot === true
        ? { headline: 'Trap: contract blocks selling', detail: 'Honeypot flag set. Walk away.', tone: 'reject' }
        : { headline: 'Door open: sell check passed', detail: `Rug ratio ${num(p?.rug_ratio)} · top 10 ${pct(p?.top10_holder_rate)}`, tone: 'ape' },
  },
  {
    id: 'holders',
    name: 'The Whale Hunt',
    story: 'Who owns the bag? One whale can empty the room.',
    icon: Fish,
    relic: 'whale',
    xp: 15,
    tone: 'accent',
    outcome: (p) =>
      p?.ok === false
        ? { headline: 'No holder data', detail: p.reason ?? 'GMGN returned no holders', tone: 'wait' }
        : {
            headline: `Top 10 hold ${pct(p?.top10_share)}`,
            detail: `Largest wallet ${pct(p?.largest_share)} · rat traders ${pct(p?.rat_trader_share)}`,
          },
  },
  {
    id: 'traders',
    name: 'The Tape',
    story: 'Bots and snipers leave footprints. Reading the last trades.',
    icon: ArrowLeftRight,
    relic: 'tape',
    xp: 10,
    tone: 'wait',
    outcome: (p) => ({
      headline: `${count(p?.count)} recent trades read`,
      detail: 'Bot and sniper footprints checked',
    }),
  },
  {
    id: 'kline',
    name: 'The Chart Run',
    story: 'Candles show what already happened, not what happens next.',
    icon: CandlestickChart,
    relic: 'candles',
    xp: 10,
    tone: 'ape',
    outcome: (p) =>
      p?.ok === false
        ? { headline: 'Not enough candles', detail: `No pattern read yet · ${p.usable ?? 0} of 8 needed`, tone: 'wait' }
        : { headline: p.pattern, detail: `Score ${count(p.score)}/100 · drawdown ${pct(p.metrics?.drawdown, 0)}` },
  },
  {
    id: 'smart_money',
    name: 'The Radar',
    story: 'Are the smart wallets sniffing around?',
    icon: Radar,
    relic: 'radar',
    xp: 10,
    tone: 'accent',
    outcome: (p) => ({
      headline: `${count(p?.mentions)} smart-wallet hits`,
      detail: `${count(p?.scanned)} wallets scanned`,
    }),
  },
  {
    id: 'kol',
    name: 'The Spotlight',
    story: 'Are known voices talking about it?',
    icon: Megaphone,
    relic: 'spotlight',
    xp: 10,
    tone: 'wait',
    outcome: (p) => ({
      headline: `${count(p?.mentions)} KOL mentions`,
      detail: `${count(p?.scanned)} KOL posts scanned`,
    }),
  },
  {
    id: 'agent',
    name: 'The Oracle',
    story: 'Boss fight. The scoring agent weighs every clue at once.',
    icon: Bot,
    relic: 'oracle',
    xp: 25,
    tone: 'reject',
    outcome: () => ({ headline: 'Verdict delivered', detail: 'Scoring agent finished' }),
  },
];

export const CHEST = {
  id: 'verdict',
  name: 'The Chest',
  story: 'Loot time. Your verdict is ready.',
  icon: PackageOpen,
  relic: 'chest',
  tone: 'accent',
};

export const ENCOUNTER_BY_ID = Object.fromEntries([...ENCOUNTERS, CHEST].map((e) => [e.id, e]));

// Tailwind classes per tone. Spelled out in full so the compiler keeps them.
export const TONE_TEXT = { accent: 'text-accent', ape: 'text-ape', reject: 'text-reject', wait: 'text-wait' };
export const TONE_BG = { accent: 'bg-accent/15', ape: 'bg-ape/15', reject: 'bg-reject/15', wait: 'bg-wait/15' };
export const TONE_HEX = { accent: '#5ce1ff', ape: '#2ee59d', reject: '#ff4d6d', wait: '#ffb020' };

// GMGN errors arrive as raw CLI text; say what it means for the viewer.
export function explainError(text) {
  if (!text) return 'No answer from GMGN';
  if (/RATE_LIMIT_BANNED/.test(text)) return 'GMGN banned us for a few minutes. Try again soon.';
  if (/RATE_LIMIT_EXCEEDED|rate limit/i.test(text)) return 'GMGN rate limit hit. Pacing slows down.';
  if (/cooldown/i.test(text)) return 'Waiting out a GMGN cooldown.';
  return text.length > 90 ? `${text.slice(0, 90)}…` : text;
}
