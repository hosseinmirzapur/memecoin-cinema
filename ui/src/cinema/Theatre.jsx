import { useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ENCOUNTER_BY_ID } from '@/game/quests.js';
import Reel from './Reel.jsx';
import { REEL_IDS, VERDICT_WORD, isReady, reelData } from './reelData.js';
import { useReelQueue } from './useReelQueue.js';

// The screen plays the scan one reel at a time. Viewers can jump to any reel that has developed.
export default function Theatre({ state }) {
  const reduce = useReducedMotion();
  const queue = useReelQueue(REEL_IDS, (id) => isReady(state, id));
  const [picked, setPicked] = useState(null);
  const liveId = queue.finished ? null : REEL_IDS[queue.index];
  const shownId = picked ?? liveId;
  const data = shownId ? reelData(state, shownId) : null;
  const shownNumber = shownId ? REEL_IDS.indexOf(shownId) + 1 : REEL_IDS.length;
  const developing = shownId && shownId === liveId && data.status === 'pending';

  return (
    <section aria-label="Scan film" className="flex flex-col gap-4">
      <div className="flex items-center justify-between font-mono text-[11px] tracking-[0.3em] text-muted-foreground uppercase">
        <span>Now showing · {state.address?.slice(0, 6)}…{state.address?.slice(-4)}</span>
        <span className="flex items-center gap-2">
          {picked ? (
            <button type="button" onClick={() => setPicked(null)} className="text-[#5ce1ff] underline-offset-4 hover:underline">
              back to live
            </button>
          ) : (
            <>
              <span className="size-1.5 rounded-full bg-[#ff4d6d] shadow-[0_0_8px_#ff4d6d]" />
              {queue.finished ? 'the end' : 'live'}
            </>
          )}
        </span>
      </div>

      <div className="relative mx-auto aspect-[4/3] w-full overflow-hidden sm:aspect-[2.39/1] rounded-md border border-white/10 bg-black shadow-[0_0_140px_-30px_rgba(92,225,255,0.3)]">
        <AnimatePresence mode="wait">
          {developing ? (
            <Leader key="leader" name={ENCOUNTER_BY_ID[shownId].name} number={shownNumber} />
          ) : shownId ? (
            <Reel key={shownId} id={shownId} data={data} number={shownNumber} total={REEL_IDS.length} />
          ) : (
            <Credits key="credits" state={state} />
          )}
        </AnimatePresence>
        {!reduce && <Curtain />}
      </div>

      <div className="mx-auto flex w-full justify-center gap-[0.6%] px-2" aria-hidden="true">
        {Array.from({ length: 14 }, (_, i) => (
          <div key={i} className="h-8 w-full max-w-14 rounded-t-2xl bg-[#07080c] shadow-[inset_0_2px_0_rgba(255,255,255,0.04)]" />
        ))}
      </div>

      <ol className="flex flex-wrap justify-center gap-2" aria-label="Reels">
        {REEL_IDS.map((id, i) => {
          const d = reelData(state, id);
          const playable = d.status !== 'pending' || id === liveId;
          const active = shownId === id;
          return (
            <li key={id}>
              <button
                type="button"
                onClick={() => setPicked(id)}
                disabled={!playable}
                aria-current={active ? 'true' : undefined}
                className={cn(
                  'flex items-center gap-2 rounded-full border px-3 py-1.5 font-mono text-[11px] tracking-wide transition-colors',
                  active ? 'border-[#5ce1ff] text-[#5ce1ff]' : 'border-border text-muted-foreground',
                  playable ? 'hover:border-[#5ce1ff]/60 hover:text-foreground' : 'opacity-40',
                )}
              >
                <span
                  className={cn(
                    'size-1.5 rounded-full',
                    d.status === 'ok' && 'bg-[#2ee59d]',
                    d.status === 'error' && 'bg-[#ff4d6d]',
                    d.status === 'pending' && 'bg-[#ffb020] animate-pulse',
                  )}
                />
                {i + 1}. {ENCOUNTER_BY_ID[id].name}
              </button>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

// The film leader: a countdown-style ring while the next reel is still developing.
function Leader({ name, number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 grid place-items-center bg-[#050608]"
    >
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2.4, repeat: Infinity, ease: 'linear' }}
          className="mx-auto size-16 rounded-full border-2 border-[#5ce1ff]/25 border-t-[#5ce1ff]"
        />
        <p className="mt-6 font-mono text-xs tracking-[0.35em] text-muted-foreground uppercase">
          Reel {number} · developing · {name}
        </p>
      </div>
    </motion.div>
  );
}

// Credits: the verdict word on the last frame. Evidence and the holder ledger sit below the screen.
function Credits({ state }) {
  const word = VERDICT_WORD[state.result?.verdict] ?? 'HOLD';
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 grid place-items-center bg-black">
      <div className="text-center">
        <p className="font-mono text-xs tracking-[0.4em] text-muted-foreground uppercase">The end</p>
        <p className="mt-4 font-display text-7xl font-semibold text-[#ece6d8]">{word}</p>
      </div>
    </motion.div>
  );
}

// Curtain: velvet parts once when the house opens. Skipped for reduced motion.
function Curtain() {
  const half = 'h-full w-1/2 bg-[linear-gradient(90deg,#3d0a12,#7a1422_40%,#4a0b15)] shadow-[inset_0_0_60px_rgba(0,0,0,0.6)]';
  return (
    <div className="pointer-events-none absolute inset-0 z-40 flex">
      <motion.div initial={{ x: 0 }} animate={{ x: '-100%' }} transition={{ duration: 1.8, delay: 0.4, ease: [0.7, 0, 0.2, 1] }} className={half} />
      <motion.div initial={{ x: 0 }} animate={{ x: '100%' }} transition={{ duration: 1.8, delay: 0.4, ease: [0.7, 0, 0.2, 1] }} className={half} />
    </div>
  );
}
