import { lazy, Suspense } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle2, CircleHelp, XCircle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

// Three.js loads only when a verdict with a score is on screen.
const VerdictOrb = lazy(() => import('@/scene/VerdictOrb'));

const TONE = { APE: 'ape', REJECT: 'reject', NEED_MORE_DATA: 'wait' };
const WORD = { APE: 'Enter', REJECT: 'Pass', NEED_MORE_DATA: 'Hold' };
const WORD_COLOR = { ape: 'text-ape', reject: 'text-reject', wait: 'text-wait' };
const ICON = { ape: CheckCircle2, reject: XCircle, wait: CircleHelp };

const list = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06, delayChildren: 0.25 } },
};
const item = {
  hidden: { opacity: 0, x: -6 },
  show: { opacity: 1, x: 0, transition: { duration: 0.35, ease: 'easeOut' } },
};

function Column({ title, items, accent, icon: Icon }) {
  if (!items?.length) return null;
  return (
    <section className="min-w-0">
      <h3 className={cn('mb-3 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest', accent)}>
        <Icon className="size-3.5" /> {title}
      </h3>
      <motion.ul variants={list} initial="hidden" animate="show" className="flex flex-col gap-2.5">
        {items.map((text) => (
          <motion.li key={text} variants={item} className="border-l border-border pl-3 text-sm leading-relaxed text-foreground/90">
            {text}
          </motion.li>
        ))}
      </motion.ul>
    </section>
  );
}

export default function Verdict({ data }) {
  const tone = TONE[data.verdict] ?? 'wait';
  const Icon = ICON[tone];
  const hasScore = Number.isFinite(data.score);
  const agentError = data.agent && !data.agent.ok ? data.agent.error : null;

  return (
    <Card className="relative overflow-hidden" aria-live="polite">
      <div
        className={cn(
          'pointer-events-none absolute -top-40 -right-40 size-[480px] rounded-full opacity-[0.12] blur-3xl',
          tone === 'ape' && 'bg-ape',
          tone === 'reject' && 'bg-reject',
          tone === 'wait' && 'bg-wait',
        )}
      />
      <CardContent className="relative grid gap-8 p-6 md:grid-cols-[minmax(0,1fr)_auto] md:p-8">
        <div className="flex min-w-0 flex-col gap-5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="accent">{data.chain.toUpperCase()}</Badge>
            <Badge variant={tone}>
              <Icon className="size-3" /> {WORD[data.verdict]}
            </Badge>
          </div>

          <motion.h2
            key={data.verdict}
            initial={{ opacity: 0, y: 14, filter: 'blur(6px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            transition={{ duration: 0.6, ease: [0.2, 0.7, 0.2, 1] }}
            className={cn('font-display text-6xl leading-none font-semibold tracking-tight sm:text-7xl', WORD_COLOR[tone])}
          >
            {WORD[data.verdict] ?? data.verdict}
          </motion.h2>

          <p className="max-w-prose text-sm leading-relaxed text-muted-foreground">{data.verdict_reason}</p>

          {agentError && (
            <p className="flex items-start gap-2 rounded-lg border border-wait/30 bg-wait/5 p-3 font-mono text-xs text-wait">
              <AlertTriangle className="mt-0.5 size-3.5 shrink-0" /> Scoring agent: {agentError}
            </p>
          )}

          <div className="grid gap-6 pt-2 sm:grid-cols-2">
            <Column title="Why" items={data.reasons} accent="text-ape" icon={CheckCircle2} />
            <Column title="Top risks" items={data.risks} accent="text-reject" icon={XCircle} />
            <Column title="Still missing" items={data.missing} accent="text-wait" icon={CircleHelp} />
          </div>
        </div>

        {hasScore && (
          <div className="flex flex-col items-center gap-3 self-start md:pt-2">
            <div className="relative">
              <Suspense fallback={<Skeleton className="aspect-square w-[260px] rounded-full" />}>
                <VerdictOrb score={data.score} tone={tone} />
              </Suspense>
              <div className="pointer-events-none absolute inset-0 grid place-items-center">
                <div className="text-center">
                  <p className="font-display text-4xl font-semibold tabular-nums">{data.score}</p>
                  <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">of 100</p>
                </div>
              </div>
            </div>
            <div className="flex w-full justify-between font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              <span>avoid</span>
              <span>hold</span>
              <span>enter</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
