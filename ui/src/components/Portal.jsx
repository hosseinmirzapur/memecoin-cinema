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
    <section className="flex flex-col items-center gap-8 py-6 text-center md:py-12">
      <div className="relative grid size-40 place-items-center">
        {!reduce &&
          [0, 1].map((i) => (
            <motion.span
              key={i}
              className="absolute inset-0 rounded-full border border-accent/40"
              animate={{ scale: [0.55, 1.3], opacity: [0.8, 0] }}
              transition={{ duration: 2.6, repeat: Infinity, delay: i * 1.3, ease: 'easeOut' }}
            />
          ))}
        <motion.div
          animate={reduce ? undefined : { y: [0, -6, 0] }}
          transition={{ duration: 3.2, repeat: Infinity, ease: 'easeInOut' }}
          className="grid size-20 place-items-center rounded-2xl border border-accent/50 bg-accent/10 text-accent shadow-[0_0_40px_-8px_var(--color-accent)]"
        >
          <ClipboardPaste className="size-9" />
        </motion.div>
      </div>

      <div className="flex max-w-2xl flex-col gap-3">
        <h1 className="font-display text-4xl leading-tight font-semibold tracking-tight sm:text-5xl">Paste a contract. Get the verdict.</h1>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Copy any token address from a chart, a post or a wallet page, then paste it here. Nothing to type.
        </p>
      </div>

      <Button size="lg" onClick={readClipboard}>
        <ClipboardPaste /> Paste from clipboard
      </Button>
      <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
        or press {isMac() ? '⌘V' : 'Ctrl+V'} anywhere
      </p>

      <AnimatePresence mode="wait">
        {draft ? (
          <motion.div
            key="pick"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-4"
          >
            <p className="font-display text-xl">
              Which chain is <span className="font-mono text-base text-accent">{short(draft)}</span> on?
            </p>
            <div className="flex flex-wrap justify-center gap-3">
              {CHAINS.map(([id, label]) => (
                <Button key={id} variant="outline" className="min-w-28" onClick={() => onChoose(id)}>
                  {label}
                </Button>
              ))}
            </div>
            <button type="button" onClick={onCancel} className="font-mono text-xs text-muted-foreground underline-offset-4 hover:underline">
              cancel
            </button>
          </motion.div>
        ) : (
          hint && (
            <motion.p
              key={hint}
              role="status"
              animate={reduce ? undefined : { x: [0, -8, 8, -5, 5, 0] }}
              transition={{ duration: 0.45 }}
              className="rounded-lg border border-reject/40 bg-reject/10 px-4 py-2 text-sm text-reject"
            >
              {hint}
            </motion.p>
          )
        )}
      </AnimatePresence>

      <ol className="flex flex-wrap justify-center gap-2" aria-label="Your scan route">
        {ENCOUNTERS.map((e, i) => {
          const Icon = e.icon;
          return (
            <motion.li
              key={e.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.06 }}
              className="flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 font-mono text-[11px] text-muted-foreground"
            >
              <Icon className="size-3.5 text-accent" /> {e.name}
            </motion.li>
          );
        })}
      </ol>
    </section>
  );
}
