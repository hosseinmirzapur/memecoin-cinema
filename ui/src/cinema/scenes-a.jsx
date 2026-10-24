import { useState } from 'react';
import { motion } from 'framer-motion';
import { age, count, num, pct, price, usd } from '@/format.js';
import { Layer, Stamp } from './shared.jsx';

const float = { duration: 4, repeat: Infinity, ease: 'easeInOut' };

// 1. The passport. The token introduces itself; tap to turn it over.
export function IdentityScene({ data }) {
  const [back, setBack] = useState(false);
  const p = data.preview ?? {};
  const pending = data.status === 'pending';
  return (
    <>
      <Layer depth={-4} className="bg-[radial-gradient(ellipse_at_top,rgba(245,182,66,0.35),transparent_60%)]" />
      <Layer depth={6} className="grid place-items-center">
        <motion.button
          type="button"
          onClick={() => setBack((b) => !b)}
          disabled={pending}
          animate={pending ? { y: [0, -10, 0] } : { y: 0 }}
          transition={float}
          aria-label="Turn the passport over"
          className="relative aspect-[1.6] h-[72%] cursor-pointer [perspective:1200px] disabled:cursor-default"
        >
          <motion.div
            animate={{ rotateY: back ? 180 : 0 }}
            transition={{ duration: 0.8, ease: [0.2, 0.7, 0.2, 1] }}
            className="relative size-full [transform-style:preserve-3d]"
          >
            <div className="absolute inset-0 flex flex-col justify-between rounded-2xl border border-[#f5b642]/50 bg-[linear-gradient(135deg,#3a2a10,#120d06_60%)] p-8 text-left shadow-[0_30px_80px_-20px_#000] [backface-visibility:hidden]">
              <p className="font-mono text-[11px] tracking-[0.35em] text-[#f5b642] uppercase">Token passport</p>
              <div>
                <p className="font-display text-6xl font-semibold text-[#ece6d8] sm:text-7xl">{p.symbol ?? '???'}</p>
                <p className="mt-2 font-mono text-sm text-[#ece6d8]/70">{p.name ?? (pending ? 'reading the badge…' : 'unnamed')}</p>
              </div>
              <p className="font-mono text-xs text-[#ece6d8]/60">Issued {age(p.creation_timestamp)} ago · tap to turn over</p>
            </div>
            <div className="absolute inset-0 flex flex-col justify-between rounded-2xl border border-[#f5b642]/50 bg-[linear-gradient(225deg,#3a2a10,#120d06_60%)] p-8 text-left [transform:rotateY(180deg)] [backface-visibility:hidden]">
              <p className="font-mono text-[11px] tracking-[0.35em] text-[#f5b642] uppercase">On the back</p>
              <dl className="grid grid-cols-2 gap-4 font-mono text-sm text-[#ece6d8]">
                <div><dt className="text-[#ece6d8]/50">Liquidity</dt><dd className="text-lg">{usd(p.liquidity)}</dd></div>
                <div><dt className="text-[#ece6d8]/50">Holders</dt><dd className="text-lg">{count(p.holder_count)}</dd></div>
                <div><dt className="text-[#ece6d8]/50">Price 24h ago</dt><dd className="text-lg">{price(p.price_24h)}</dd></div>
              </dl>
              <p className="font-mono text-xs text-[#ece6d8]/60">Tap to turn back</p>
            </div>
          </motion.div>
        </motion.button>
      </Layer>
      {data.status === 'ok' && <Stamp text="verified" tone="ape" rotate={-12} className="top-[16%] right-[12%]" />}
    </>
  );
}

// 2. The gate. Pull the lever to test whether the door lets you out again.
export function SecurityScene({ data }) {
  const [pulled, setPulled] = useState(false);
  const p = data.preview ?? {};
  const landed = data.status === 'ok';
  const trap = landed && p.honeypot === true;
  const open = pulled && landed && !trap;
  return (
    <>
      <Layer depth={-3} className="bg-[radial-gradient(circle_at_50%_0%,rgba(92,225,255,0.18),transparent_55%)]" />
      <Layer depth={5} className="flex items-end justify-center pb-[6%]">
        <div className="relative h-[66%] w-[30%] overflow-hidden rounded-t-xl border border-white/10 bg-[#0d1119] shadow-[inset_0_0_80px_#000]">
          <motion.div
            animate={{ y: open ? '-102%' : '0%' }}
            transition={{ duration: 1.1, ease: [0.7, 0, 0.2, 1] }}
            className="absolute inset-0 bg-[repeating-linear-gradient(0deg,#2b3446_0_18px,#161c28_18px_36px)]"
          />
          <div className="absolute inset-x-0 bottom-0 flex h-[22%] flex-col items-center justify-center gap-1 bg-black/70 font-mono text-xs text-[#ece6d8]">
            <span>{data.status === 'pending' ? 'testing the sell path…' : `rug ${num(p.rug_ratio)} · top10 ${pct(p.top10_holder_rate)}`}</span>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setPulled((v) => !v)}
          disabled={!landed}
          aria-pressed={pulled}
          aria-label="Pull the lever to test the sell path"
          className="absolute bottom-[26%] left-[calc(50%+15%)] flex h-44 w-14 items-end justify-center disabled:cursor-default cursor-pointer"
        >
          <motion.span animate={{ rotate: pulled ? 58 : -18 }} transition={{ type: 'spring', stiffness: 200, damping: 14 }} className="block h-40 w-2.5 origin-bottom rounded-full bg-[#c9d3e6]">
            <span className="absolute -top-2 -left-2 block size-6 rounded-full bg-[#5ce1ff] shadow-[0_0_24px_#5ce1ff]" />
          </motion.span>
        </button>
        {landed && !pulled && <p className="absolute right-[16%] bottom-[20%] font-mono text-xs tracking-widest text-[#5ce1ff] uppercase">pull the lever →</p>}
      </Layer>
      {trap && pulled && <Stamp text="trap" tone="reject" rotate={-10} className="top-[18%] left-[18%]" />}
      {open && <Stamp text="door open" tone="ape" rotate={-6} className="top-[18%] left-[18%]" />}
    </>
  );
}

// 3. The whale hunt. Every coin is a slice of supply; tap a pile to see whose it is.
export function HoldersScene({ data }) {
  const [focus, setFocus] = useState('top10');
  const p = data.preview ?? {};
  const ok = data.status === 'ok' && p.ok !== false;
  const top10 = ok ? Math.min(1, p.top10_share ?? 0) : 0;
  const largest = ok ? Math.min(1, p.largest_share ?? 0) : 0;
  const coins = Math.round(top10 * 40);
  const largestCoins = Math.round(largest * 40);
  const piles = [
    { id: 'top10', label: 'Top 10', n: coins, value: pct(p.top10_share), tone: 'bg-[#5ce1ff]' },
    { id: 'largest', label: 'Largest wallet', n: largestCoins, value: pct(p.largest_share), tone: 'bg-[#ff4d6d]' },
  ];
  return (
    <>
      <Layer depth={-2} className="bg-[radial-gradient(ellipse_at_bottom,rgba(255,176,32,0.15),transparent_60%)]" />
      <Layer depth={4} className="flex items-end justify-center gap-[14%] pb-[7%]">
        {piles.map((pile, i) => (
          <button
            key={pile.id}
            type="button"
            onClick={() => setFocus(pile.id)}
            aria-pressed={focus === pile.id}
            className={`flex flex-col items-center gap-2 transition-opacity ${focus === pile.id ? 'opacity-100' : 'opacity-40 hover:opacity-70'}`}
          >
            <div className="flex h-[280px] flex-col-reverse items-center gap-1">
              {Array.from({ length: pile.n }, (_, c) => (
                <motion.span
                  key={c}
                  initial={{ y: -260, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3 + c * 0.035, type: 'spring', stiffness: 160, damping: 14 }}
                  className={`block h-3 w-28 rounded-[50%] border border-black/40 shadow-[inset_0_-2px_0_rgba(0,0,0,.35)] ${pile.tone}`}
                />
              ))}
            </div>
            <span className="font-mono text-[11px] tracking-widest text-[#ece6d8]/80 uppercase">{pile.label}</span>
            <span className="font-display text-3xl font-semibold text-[#ece6d8]">{ok ? pile.value : '—'}</span>
          </button>
        ))}
      </Layer>
      <p className="absolute top-[10%] left-[8%] max-w-xs font-mono text-xs leading-relaxed text-[#ece6d8]/60">
        Each coin stands for 2.5% of supply. Tap a pile.
      </p>
      {ok && focus === 'largest' && largest > 0.1 && <Stamp text="whale" tone="reject" rotate={-9} className="top-[14%] right-[12%]" />}
    </>
  );
}

// 4. The tape. The trades roll past; the count stops the reel.
export function TradersScene({ data }) {
  const [paused, setPaused] = useState(false);
  const total = count(data.preview?.count);
  const landed = data.status === 'ok';
  return (
    <>
      <Layer depth={-2} className="bg-[linear-gradient(180deg,rgba(255,176,32,0.08),transparent)]" />
      <Layer depth={3} className="flex flex-col items-center justify-center gap-8">
        <div
          onPointerEnter={() => setPaused(true)}
          onPointerLeave={() => setPaused(false)}
          className="relative h-24 w-[72%] overflow-hidden rounded-xl border border-[#ffb020]/30 bg-black/60"
        >
          <motion.div
            animate={paused || landed ? {} : { x: ['0%', '-50%'] }}
            transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
            className="flex h-full w-max items-center gap-3 px-4"
          >
            {Array.from({ length: 48 }, (_, i) => (
              <span key={i} style={{ height: 16 + ((i * 37) % 5) * 8 }} className={`block w-1.5 rounded-full ${i % 3 ? 'bg-[#2ee59d]/70' : 'bg-[#ff4d6d]/70'}`} />
            ))}
          </motion.div>
        </div>
        <div className="text-center">
          <p className="font-display text-7xl font-semibold text-[#ffb020] tabular-nums">{landed ? total : '···'}</p>
          <p className="mt-2 font-mono text-xs tracking-[0.35em] text-[#ece6d8]/60 uppercase">trades read · hover to pause the tape</p>
        </div>
      </Layer>
    </>
  );
}

// 5. The chart run. A sketch of the pattern, drawn from the slope and drawdown the server measured.
export function KlineScene({ data }) {
  const p = data.preview ?? {};
  const m = p.metrics ?? {};
  const ok = data.status === 'ok' && p.ok !== false;
  const slope = Number.isFinite(m.slope) ? m.slope : 0;
  const drop = Number.isFinite(m.drawdown) ? m.drawdown : 0;
  const points = Array.from({ length: 60 }, (_, i) => {
    const t = i / 59;
    const trend = -slope * t * 220;
    const wiggle = Math.sin(t * 17) * 14 * (1 + (Number.isFinite(m.volatility) ? m.volatility * 6 : 0));
    const crash = t > 0.75 ? drop * 260 * (t - 0.75) * 4 : 0;
    return `${40 + t * 1120},${150 + trend + wiggle + crash}`;
  }).join(' ');
  return (
    <>
      <Layer depth={-2} className="bg-[radial-gradient(ellipse_at_center,rgba(46,229,157,0.1),transparent_65%)]" />
      <Layer depth={4} className="flex flex-col items-center justify-center gap-4">
        <svg viewBox="0 0 1200 300" className="w-[80%] overflow-visible" aria-hidden="true">
          <line x1="40" y1="290" x2="1160" y2="290" stroke="#ffffff22" />
          {ok && (
            <motion.polyline
              points={points}
              fill="none"
              stroke={slope >= 0 ? '#2ee59d' : '#ff4d6d'}
              strokeWidth="5"
              strokeLinejoin="round"
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 2.4, ease: 'easeInOut' }}
              style={{ filter: 'drop-shadow(0 0 10px currentColor)' }}
            />
          )}
        </svg>
        <p className="font-mono text-[11px] tracking-[0.25em] text-[#ece6d8]/50 uppercase">
          {ok ? `sketch from measured metrics · score ${num(p.score, 0)}/100 · not the real price` : 'waiting for candles'}
        </p>
      </Layer>
      {ok && <Stamp text={p.pattern ?? 'pattern'} tone={slope >= 0 ? 'ape' : 'reject'} rotate={-5} className="top-[12%] right-[10%] text-xl" />}
    </>
  );
}
