import { motion } from 'framer-motion';
import { Activity, Plus, Trophy, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { rankFor } from '@/game/progress.js';

export default function Hud({ progress, sound, onSound, onIntro, onNew, showNew, canIntro }) {
  const rank = rankFor(progress.scans);

  return (
    <header className="flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <span className="grid size-9 place-items-center rounded-lg bg-accent font-display text-sm font-semibold text-accent-foreground">MR</span>
        <div>
          <p className="font-display text-base leading-none font-semibold">Memecoin Research Desk</p>
          <p className="mt-1 font-mono text-[11px] text-muted-foreground">GMGN evidence · guarded verdict</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="flex min-w-52 items-center gap-3 rounded-full border border-border bg-card px-4 py-2">
          <Trophy className="size-4 shrink-0 text-wait" />
          <div className="flex-1">
            <p className="font-mono text-[11px] tracking-wide">
              {rank.title} · {progress.xp} XP{rank.next && <span className="text-muted-foreground"> · {rank.toNext} scans to {rank.next}</span>}
            </p>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted">
              <motion.div className="h-full rounded-full bg-wait" initial={false} animate={{ width: `${rank.progress * 100}%` }} transition={{ duration: 0.8, ease: 'easeOut' }} />
            </div>
          </div>
        </div>
        {showNew && (
          <Button variant="accent" size="sm" onClick={onNew}>
            <Plus /> Scan another
          </Button>
        )}
        <Button variant="ghost" size="sm" onClick={onSound} aria-pressed={sound} aria-label={sound ? 'Mute sound' : 'Turn sound on'}>
          {sound ? <Volume2 /> : <VolumeX />}
        </Button>
        <Button variant="outline" size="sm" onClick={onIntro} disabled={!canIntro} title="Replay the intro">
          <Activity /> Intro
        </Button>
      </div>
    </header>
  );
}
