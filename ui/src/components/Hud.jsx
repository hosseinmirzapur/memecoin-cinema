import { Activity, Plus, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { rankFor } from '@/game/progress.js';

export default function Hud({ progress, sound, onSound, onIntro, onNew, showNew, canIntro }) {
  const rank = rankFor(progress.scans);

  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
      <div className="flex items-baseline gap-3">
        <span className="font-display text-base font-semibold tracking-tight">Memecoin Research Desk</span>
        <span className="font-mono text-[11px] text-muted-foreground">
          {rank.title} · {progress.xp} XP
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
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
