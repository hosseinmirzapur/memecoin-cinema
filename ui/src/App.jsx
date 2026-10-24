import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { FileText, RotateCcw } from 'lucide-react';
import Evidence from './components/Evidence.jsx';
import Hud from './components/Hud.jsx';
import Portal from './components/Portal.jsx';
import Toasts from './components/Toasts.jsx';
import Verdict from './components/Verdict.jsx';
import Theatre from './cinema/Theatre.jsx';
import { holderReport } from './api.js';
import { useScan } from './hooks/useScan.js';
import { findAddress } from './game/paste.js';
import { awardScan, BADGES, loadProgress, rankFor } from './game/progress.js';
import { cue, setSoundOn, soundOn } from './game/sound.js';
import { explainError } from './game/quests.js';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

// The 3D intro pulls in Three.js; load it only when it will actually play.
const IntroReel = lazy(() => import('./scene/IntroReel.jsx'));

const INTRO_KEY = 'mrd.intro-seen';

// Storage is a convenience only: a private window or blocked storage just means the intro may repeat.
function introSeen() {
  try {
    return sessionStorage.getItem(INTRO_KEY) === '1';
  } catch {
    return false;
  }
}

function markIntroSeen() {
  try {
    sessionStorage.setItem(INTRO_KEY, '1');
  } catch {
    /* storage unavailable: the intro may show again, which is harmless */
  }
}

export default function App() {
  const reduce = useReducedMotion();
  const [intro, setIntro] = useState(() => !reduce && !introSeen());
  const [sound, setSound] = useState(soundOn);
  const [progress, setProgress] = useState(loadProgress);
  const [toasts, setToasts] = useState([]);
  const [draft, setDraft] = useState(null);
  const [hint, setHint] = useState('');
  const [holders, setHolders] = useState(null);
  const toastId = useRef(0);
  const awarded = useRef(null);

  const onEvent = useCallback((kind, payload) => cue(kind, payload), []);
  const { state, start, reset } = useScan(onEvent);
  const busy = state.phase === 'running';

  const toast = useCallback((t) => {
    const id = ++toastId.current;
    setToasts((list) => [...list, { ...t, id }]);
    setTimeout(() => setToasts((list) => list.filter((x) => x.id !== id)), 4200);
  }, []);

  // Rewards land once per finished scan. Blocked scans do not count.
  useEffect(() => {
    if (state.phase !== 'done' || awarded.current === state.result) return;
    awarded.current = state.result;
    const before = loadProgress();
    const got = awardScan(before, state.result);
    setProgress(got.progress);
    toast({ kicker: 'Scan cleared', title: `+${got.xp} XP`, text: `${got.progress.scans} scans logged` });
    for (const id of got.unlocked) toast({ kicker: 'Badge unlocked', title: BADGES[id].title, text: BADGES[id].text });
    const rank = rankFor(got.progress.scans).title;
    if (rankFor(before.scans).title !== rank) toast({ kicker: 'Rank up', title: rank, text: 'Keep scanning to climb.' });
  }, [state.phase, state.result, toast]);

  const handlePaste = useCallback(
    (text) => {
      if (busy) {
        setHint('A scan is running. Wait for the credits, or start over with Scan another.');
        return;
      }
      if (text == null) {
        setHint('The browser blocked clipboard access. Press Ctrl+V or ⌘V here instead.');
        return;
      }
      const found = findAddress(text);
      if (!found) {
        setHint('No contract address in that. Copy a token address and paste again.');
        return;
      }
      setHint('');
      setHolders(null);
      if (found.chain) start(found.chain, found.address);
      else setDraft(found.address);
    },
    [busy, start],
  );

  // Paste works anywhere on the page: the viewer never has to click into a field.
  useEffect(() => {
    const onPaste = (e) => handlePaste(e.clipboardData?.getData('text') ?? '');
    window.addEventListener('paste', onPaste);
    return () => window.removeEventListener('paste', onPaste);
  }, [handlePaste]);

  const choose = (chain) => {
    const address = draft;
    setDraft(null);
    setHolders(null);
    start(chain, address);
  };

  const newScan = () => {
    reset();
    setDraft(null);
    setHint('');
    setHolders(null);
  };

  const toggleSound = () => {
    const next = !sound;
    setSoundOn(next);
    setSound(next);
  };

  const endIntro = useCallback(() => {
    markIntroSeen();
    setIntro(false);
  }, []);

  const showHolders = async () => {
    setHolders({ status: 'loading' });
    try {
      const res = await holderReport(state.chain, state.address);
      setHolders(res.ok ? { status: 'done', text: res.stdout } : { status: 'error', error: res.stderr || 'holder report failed' });
    } catch (err) {
      setHolders({ status: 'error', error: err.message });
    }
  };

  const finished = state.phase === 'done' && state.result;

  return (
    <>
      <AnimatePresence>
        {intro && (
          <Suspense fallback={null} key="intro">
            <IntroReel onDone={endIntro} />
          </Suspense>
        )}
      </AnimatePresence>

      <div className="mx-auto flex min-h-dvh max-w-[1200px] flex-col gap-8 px-4 py-6 md:px-8 md:py-8">
        <Hud
          progress={progress}
          sound={sound}
          onSound={toggleSound}
          onIntro={() => setIntro(true)}
          canIntro={!reduce}
          onNew={newScan}
          showNew={state.phase !== 'idle'}
        />

        <AnimatePresence mode="wait">
          {state.phase === 'idle' && (
            <motion.div key="portal" exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.25 }}>
              <Portal
                draft={draft}
                hint={hint}
                onPaste={handlePaste}
                onChoose={choose}
                onCancel={() => setDraft(null)}
              />
            </motion.div>
          )}

          {state.phase !== 'idle' && (
            <motion.div key="theatre" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-6">
              <Theatre key={state.run} state={state} />

              {state.phase === 'error' && (
                <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-reject/40 bg-reject/10 p-4 text-sm text-reject">
                  <span>{explainError(state.error)}</span>
                  <Button variant="outline" size="sm" onClick={() => start(state.chain, state.address)}>
                    <RotateCcw /> Retry scan
                  </Button>
                </div>
              )}

              {state.phase === 'blocked' && (
                <p role="alert" className="rounded-xl border border-reject/40 bg-reject/10 p-4 text-sm text-reject">
                  {state.result.verdict_reason}
                </p>
              )}

              {finished && (
                <motion.div key={state.result.address} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-6">
                  <Verdict data={state.result} />
                  <Evidence signals={state.result.signals} sources={state.result.sources} />
                  <div className="flex flex-col gap-3">
                    <Button variant="outline" onClick={showHolders} disabled={holders?.status === 'loading'} className="self-start">
                      <FileText /> {holders?.status === 'loading' ? 'Opening the holder ledger…' : 'Side quest: full holder ledger'}
                    </Button>
                    {holders?.status === 'done' && (
                      <Card>
                        <CardContent className="max-h-[560px] overflow-auto p-5">
                          <pre className={cn('font-mono text-xs leading-relaxed whitespace-pre-wrap text-foreground/90')}>{holders.text}</pre>
                        </CardContent>
                      </Card>
                    )}
                    {holders?.status === 'error' && <p role="alert" className="text-sm text-reject">{holders.error}</p>}
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <Toasts toasts={toasts} />
    </>
  );
}
