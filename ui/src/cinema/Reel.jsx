import { useEffect, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion, useSpring } from 'framer-motion';
import { ENCOUNTER_BY_ID } from '@/game/quests.js';
import { subtitleFor } from './reelData.js';
import { IdentityScene, HoldersScene, KlineScene, SecurityScene, TradersScene } from './scenes-a.jsx';
import { RadarScene, SpotlightScene, TrialScene, VaultScene } from './scenes-b.jsx';

// One scene per GMGN call. Each one is interactive; the registry keeps the reel code generic.
const SCENES = {
  token_info: IdentityScene,
  security: SecurityScene,
  holders: HoldersScene,
  traders: TradersScene,
  kline: KlineScene,
  smart_money: RadarScene,
  kol: SpotlightScene,
  agent: TrialScene,
  verdict: VaultScene,
};

const GRAIN =
  "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")";

// A generated clip dropped at public/reels/<id>.mp4 plays under the scene. Without one, the scene carries the frame alone.
function Clip({ id }) {
  const [failed, setFailed] = useState(false);
  if (failed) return null;
  return (
    <video
      src={`/reels/${id}.mp4`}
      autoPlay
      muted
      loop
      playsInline
      onError={() => setFailed(true)}
      className="absolute inset-0 size-full object-cover opacity-50"
    />
  );
}

export default function Reel({ id, data, number, total }) {
  const reduce = useReducedMotion();
  const mx = useSpring(0, { stiffness: 90, damping: 22 });
  const my = useSpring(0, { stiffness: 90, damping: 22 });
  const [titled, setTitled] = useState(true);
  const encounter = ENCOUNTER_BY_ID[id];
  const Scene = SCENES[id];
  const typed = useTypedLine(subtitleFor(id, data));

  useEffect(() => {
    const timer = setTimeout(() => setTitled(false), 2600);
    return () => clearTimeout(timer);
  }, []);

  const move = (e) => {
    if (reduce) return;
    const r = e.currentTarget.getBoundingClientRect();
    mx.set(((e.clientX - r.left) / r.width) * 2 - 1);
    my.set(((e.clientY - r.top) / r.height) * 2 - 1);
  };
  const rest = () => {
    mx.set(0);
    my.set(0);
  };

  return (
    <motion.div
      style={{ '--px': mx, '--py': my }}
      onPointerMove={move}
      onPointerLeave={rest}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
      className="absolute inset-0 overflow-hidden bg-black"
    >
      <Clip id={id} />
      <div className="absolute inset-0 scale-[1.04]">
        <Scene data={data} />
      </div>

      {data.status === 'error' && (
        <div className="absolute top-[8%] right-[6%] z-20 rounded border-[3px] border-[#ff4d6d] px-4 py-1 font-mono text-lg font-bold tracking-[0.3em] text-[#ff4d6d] uppercase">
          no footage
        </div>
      )}

      <div className="pointer-events-none absolute inset-0 z-10 bg-[radial-gradient(ellipse_at_center,transparent_45%,#000_100%)]" />
      <motion.div
        aria-hidden="true"
        animate={reduce ? undefined : { opacity: [0.1, 0.16, 0.1] }}
        transition={{ duration: 0.4, repeat: Infinity }}
        className="pointer-events-none absolute inset-0 z-20 mix-blend-overlay"
        style={{ backgroundImage: GRAIN }}
      />

      <div className="absolute inset-x-0 bottom-0 z-20 bg-gradient-to-t from-black via-black/70 to-transparent px-[8%] pt-16 pb-[4%] text-center">
        <p className="min-h-[2.4em] font-display text-xl leading-snug text-[#ece6d8] sm:text-2xl md:text-3xl">{typed}</p>
      </div>

      <AnimatePresence>
        {titled && (
          <motion.div
            key="title"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, filter: 'blur(10px)' }}
            transition={{ duration: 0.8 }}
            className="absolute inset-0 z-30 grid place-items-center bg-black"
          >
            <div className="px-6 text-center">
              <p className="font-mono text-xs tracking-[0.4em] text-[#f5b642] uppercase">
                Reel {number} of {total}
              </p>
              <motion.h2
                initial={{ letterSpacing: '0.5em', opacity: 0 }}
                animate={{ letterSpacing: '0.04em', opacity: 1 }}
                transition={{ duration: 1.6, ease: 'easeOut' }}
                className="mt-4 font-display text-3xl font-semibold text-balance text-[#ece6d8] sm:text-5xl md:text-6xl"
              >
                {encounter.name}
              </motion.h2>
              <p className="mt-4 font-mono text-sm text-[#ece6d8]/60">{encounter.story}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Types the subtitle out one step at a time.
function useTypedLine(text) {
  const [shown, setShown] = useState('');
  useEffect(() => {
    let i = 0;
    setShown('');
    const id = setInterval(() => {
      i += 2;
      setShown(text.slice(0, i));
      if (i >= text.length) clearInterval(id);
    }, 22);
    return () => clearInterval(id);
  }, [text]);
  return shown;
}
