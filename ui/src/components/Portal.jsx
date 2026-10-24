import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { ClipboardPaste } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ENCOUNTERS } from '@/game/quests.js';
import { isMac } from '@/game/paste.js';

const CHAINS = [
  ['bsc', 'BSC'],
  ['base', 'Base'],
  ['eth', 'Ethereum'],
];

const short = (address) => `${address.slice(0, 6)}…${address.slice(-4)}`;

// Copy-paste is the only input. EVM addresses do not say which chain they live on, so the viewer taps one.
export default function Portal({ draft, hint, onPaste, onChoose, onCancel }) {
  const reduce = useReducedMotion();

  const readClipboard = async () => {
    try {
      onPaste(await navigator.clipboard.readText());
    } catch {
      onPaste(null);
    }
  };

  return (
    <section className="flex flex-col gap-8 py-4 md:py-10">
      <h1 className="max-w-2xl font-display text-3xl leading-tight font-semibold tracking-tight sm:text-4xl">
        Paste a contract address. Get the verdict.
      </h1>

      <div className="flex flex-col gap-5 rounded-md border border-border bg-card p-5 md:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col gap-1">
            <span className="font-mono text-xs text-muted-foreground">Input</span>
            <span className="text-sm text-foreground/90">Copy a token address from a chart, feed or wallet, then paste it here.</span>
          </div>
          <Button size="lg" onClick={readClipboard} className="sm:shrink-0">
            <ClipboardPaste /> Paste from clipboard
          </Button>
        </div>
        <p className="border-t border-dashed border-border pt-4 font-mono text-[11px] tracking-wider text-muted-foreground uppercase">
          or press {isMac() ? '⌘V' : 'Ctrl+V'} anywhere
        </p>

        <AnimatePresence mode="wait">
          {draft ? (
            <motion.div
              key="pick"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col gap-4 border-t border-dashed border-border pt-4"
            >
              <p className="font-display text-lg">
                Which chain is <span className="font-mono text-base">{short(draft)}</span> on?
              </p>
              <div className="flex flex-wrap gap-2">
                {CHAINS.map(([id, label]) => (
                  <Button key={id} variant="outline" className="min-w-28" onClick={() => onChoose(id)}>
                    {label}
                  </Button>
                ))}
                <Button variant="ghost" onClick={onCancel}>
                  Cancel
                </Button>
              </div>
            </motion.div>
          ) : (
            hint && (
              <motion.p
                key={hint}
                role="status"
                animate={reduce ? undefined : { x: [0, -8, 8, -5, 5, 0] }}
                transition={{ duration: 0.45 }}
                className="border-l border-reject pl-3 text-sm text-reject"
              >
                {hint}
              </motion.p>
            )
          )}
        </AnimatePresence>
      </div>

      <div className="flex flex-col gap-3">
        <p className="font-mono text-[11px] tracking-widest text-muted-foreground uppercase">Scan route</p>
        <ol className="flex flex-wrap gap-x-5 gap-y-2" aria-label="Your scan route">
          {ENCOUNTERS.map((e, i) => {
            const Icon = e.icon;
            return (
              <li key={e.id} className="flex items-center gap-2 font-mono text-[12px] text-muted-foreground">
                <span className="tabular-nums">{String(i + 1).padStart(2, '0')}</span>
                <Icon className="size-3.5" /> {e.name}
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}
