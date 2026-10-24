import { AnimatePresence, motion } from 'framer-motion';

// Rewards pop in the corner: XP, badges, rank-ups. Each one leaves on its own timer.
export default function Toasts({ toasts }) {
  return (
    <div role="status" aria-live="polite" className="pointer-events-none fixed right-4 bottom-4 z-50 flex w-72 flex-col gap-2">
      <AnimatePresence initial={false}>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            layout
            initial={{ opacity: 0, x: 40, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 40 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="rounded-md border border-border bg-card p-3"
          >
            <p className="font-mono text-[10px] tracking-widest text-wait uppercase">{t.kicker}</p>
            <p className="font-display text-sm font-semibold">{t.title}</p>
            <p className="text-xs text-muted-foreground">{t.text}</p>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
