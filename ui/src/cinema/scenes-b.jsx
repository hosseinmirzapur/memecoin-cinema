import { useState } from 'react';
import { motion } from 'framer-motion';
import { count } from '@/format.js';
import { Figure, Layer, Stamp } from './shared.jsx';
import { VERDICT_WORD, VERDICT_TONE, SOURCE_LABEL } from './reelData.js';

// 6. The radar room. Each blip is a smart wallet that touched the coin; tap one to pin it.
export function RadarScene({ data }) {
  const [pinned, setPinned] = useState(null);
  const hits = Math.min(12, Number(data.preview?.mentions ?? 0));
  const scanned = count(data.preview?.scanned);
  const landed = data.status === 'ok';
  return (
    <>
      <Layer depth={-3} className="bg-[radial-gradient(circle_at_center,rgba(92,225,255,0.12),transparent_60%)]" />
      <Layer depth={4} className="flex items-center justify-center gap-[8%]">
        <div className="relative aspect-square h-[78%] overflow-hidden rounded-full border border-[#5ce1ff]/30 bg-[radial-gradient(circle,#0a1a22,#03070a)] shadow-[0_0_80px_-20px_#5ce1ff]">
          {[0.33, 0.66].map((r) => (
            <div key={r} className="absolute inset-0 m-auto rounded-full border border-[#5ce1ff]/15" style={{ width: `${r * 100}%`, height: `${r * 100}%` }} />
          ))}
          <motion.div
            className="absolute inset-0 rounded-full bg-[conic-gradient(from_0deg,rgba(92,225,255,0.55),transparent_30%)]"
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          />
          {landed &&
            Array.from({ length: hits }, (_, i) => {
              const angle = (i * 137.5 * Math.PI) / 180;
              const radius = 18 + ((i * 29) % 34);
              const x = 50 + Math.cos(angle) * radius;
              const y = 50 + Math.sin(angle) * radius;
              return (
                <motion.button
                  key={i}
                  type="button"
                  onClick={() => setPinned(i)}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.4 + i * 0.18 }}
                  aria-label={`Smart wallet hit ${i + 1}`}
                  className={`absolute size-3 -translate-x-1/2 -translate-y-1/2 rounded-full ${pinned === i ? 'bg-[#ffb020] shadow-[0_0_18px_#ffb020]' : 'bg-[#2ee59d] shadow-[0_0_14px_#2ee59d]'}`}
                  style={{ left: `${x}%`, top: `${y}%` }}
                />
              );
            })}
        </div>
        <div className="flex flex-col gap-3 font-mono text-[#ece6d8]">
          <p className="font-display text-7xl font-semibold tabular-nums">{landed ? hits : '···'}</p>
          <p className="text-xs tracking-[0.25em] text-[#ece6d8]/60 uppercase">smart-wallet hits</p>
          <p className="text-xs text-[#ece6d8]/50">{landed ? `of ${scanned} wallets scanned` : 'sweeping the feed'}</p>
        </div>
      </Layer>
    </>
  );
}

// 7. The spotlight. Every lit silhouette is a known voice posting about the coin.
export function SpotlightScene({ data }) {
  const mentions = Math.min(9, Number(data.preview?.mentions ?? 0));
  const landed = data.status === 'ok';
  return (
    <>
      <Layer depth={-3} className="bg-[linear-gradient(180deg,#05060a,#0b0a08)]" />
      <Layer depth={2} className="flex items-end justify-center">
        <div className="absolute top-0 left-1/2 h-[90%] w-[46%] -translate-x-1/2 bg-[linear-gradient(180deg,rgba(255,176,32,0.45),rgba(255,176,32,0.05))] [clip-path:polygon(38%_0,62%_0,100%_100%,0_100%)]" />
      </Layer>
      <Layer depth={5} className="flex items-end justify-center gap-[3%] pb-[4%]">
        {Array.from({ length: 9 }, (_, i) => {
          const lit = landed && i < mentions;
          return (
            <div key={i} className={`transition-all duration-700 ${lit ? 'text-[#ffb020] drop-shadow-[0_0_12px_#ffb020]' : 'text-[#1a1d26]'}`}>
              <Figure className={i % 2 ? 'scale-90' : ''} />
            </div>
          );
        })}
      </Layer>
      <p className="absolute top-[10%] right-[8%] text-right font-mono text-[#ece6d8]">
        <span className="block font-display text-6xl font-semibold text-[#ffb020] tabular-nums">{landed ? count(data.preview?.mentions) : '···'}</span>
        <span className="text-xs tracking-[0.25em] text-[#ece6d8]/60 uppercase">KOL mentions</span>
      </p>
    </>
  );
}

// 8. The trial. Each answer walks onto the bench as evidence. The judge rules once all are in.
export function TrialScene({ data }) {
  const [struck, setStruck] = useState(false);
  const sources = Object.values(data.sources ?? {});
  const ruled = data.status === 'ok';
  const broke = data.status === 'error';
  return (
    <>
      <Layer depth={-3} className="bg-[radial-gradient(ellipse_at_top,rgba(255,77,109,0.1),transparent_60%)]" />
      <Layer depth={3} className="flex flex-col items-center justify-end gap-6 pb-[8%]">
        <div className="flex flex-wrap justify-center gap-2 px-[10%]">
          {sources.map((s, i) => (
            <motion.span
              key={s.name}
              initial={{ x: -320, opacity: 0, rotate: -6 }}
              animate={{ x: 0, opacity: 1, rotate: (i % 2 ? 2 : -2) }}
              transition={{ delay: i * 0.12, type: 'spring', stiffness: 180, damping: 18 }}
              className={`rounded border px-3 py-2 font-mono text-[11px] tracking-widest uppercase ${s.ok ? 'border-[#2ee59d]/50 bg-[#2ee59d]/10 text-[#2ee59d]' : 'border-[#ff4d6d]/50 bg-[#ff4d6d]/10 text-[#ff4d6d]'}`}
            >
              {SOURCE_LABEL[s.name] ?? s.name}
            </motion.span>
          ))}
        </div>
        <button
          type="button"
          onClick={() => setStruck(true)}
          disabled={!ruled}
          aria-label="Strike the gavel"
          className="group flex flex-col items-center gap-2 disabled:cursor-default cursor-pointer"
        >
          <motion.span
            animate={{ rotate: struck ? -28 : 0, y: struck ? 6 : 0 }}
            transition={{ type: 'spring', stiffness: 400, damping: 12 }}
            className="block h-6 w-28 origin-right rounded bg-[#c9a36a]"
          />
          <span className="h-3 w-[32rem] max-w-[80vw] rounded-sm bg-[#3a2a1a] shadow-[0_8px_24px_#000]" />
        </button>
        <p className="font-mono text-[11px] tracking-[0.3em] text-[#ece6d8]/60 uppercase">
          {broke ? 'mistrial · the scoring agent did not answer' : ruled ? 'ruling in · strike the gavel' : 'the court is in session'}
        </p>
      </Layer>
      {ruled && struck && <Stamp text="order" tone="accent" rotate={-4} className="top-[14%] left-[10%]" />}
      {broke && <Stamp text="mistrial" tone="reject" rotate={-8} className="top-[14%] left-[10%]" />}
    </>
  );
}

// 9. The vault. Sealed until the ruling. Tap the wheel and the verdict is revealed.
export function VaultScene({ data }) {
  const [open, setOpen] = useState(false);
  const verdict = data.result?.verdict;
  const ready = data.status === 'ok' && verdict;
  const word = VERDICT_WORD[verdict] ?? 'HOLD';
  const tone = VERDICT_TONE[verdict] ?? 'wait';
  const colour = { ape: 'text-[#2ee59d]', reject: 'text-[#ff4d6d]', wait: 'text-[#ffb020]' }[tone];
  return (
    <>
      <Layer depth={-2} className="bg-[radial-gradient(ellipse_at_center,rgba(245,182,66,0.12),transparent_60%)]" />
      <Layer depth={4} className="flex items-center justify-center">
        <div className="relative flex h-[78%] aspect-square items-center justify-center rounded-full border-[10px] border-[#3a3f4c] bg-[radial-gradient(circle,#2b303c,#0b0d12)] shadow-[0_0_80px_-10px_#000]">
          <motion.div
            animate={{ scale: open ? 1.9 : 1, opacity: open ? 0 : 1 }}
            transition={{ duration: 1.2, ease: [0.7, 0, 0.2, 1] }}
            className="absolute inset-0 rounded-full bg-[#0b0d12]"
          />
          <button
            type="button"
            onClick={() => ready && setOpen(true)}
            disabled={!ready || open}
            aria-label="Turn the vault wheel"
            className="relative grid size-28 place-items-center rounded-full border-4 border-[#c9a36a] bg-[#2a2115] font-mono text-xs tracking-widest text-[#c9a36a] uppercase enabled:cursor-pointer enabled:hover:scale-105 disabled:opacity-70"
          >
            {ready ? (open ? 'open' : 'turn') : 'sealed'}
          </button>
        </div>
        <motion.div
          initial={false}
          animate={{ opacity: open ? 1 : 0, scale: open ? 1 : 0.8 }}
          transition={{ delay: 0.9, duration: 0.6 }}
          className="absolute left-[60%] max-w-md"
        >
          <p className={`font-display text-8xl leading-none font-semibold ${colour}`}>{word}</p>
          <p className="mt-4 text-sm leading-relaxed text-[#ece6d8]/80">{data.result?.verdict_reason}</p>
        </motion.div>
      </Layer>
    </>
  );
}
