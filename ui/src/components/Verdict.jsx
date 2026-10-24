import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle2, CircleHelp, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

const TONE = { APE: 'ape', REJECT: 'reject', NEED_MORE_DATA: 'wait' };
const WORD = { APE: 'Enter', REJECT: 'Pass', NEED_MORE_DATA: 'Hold' };
const WORD_COLOR = { ape: 'text-ape', reject: 'text-reject', wait: 'text-wait' };
const RULE = { ape: 'border-ape', reject: 'border-reject', wait: 'border-wait' };
const ICON = { ape: CheckCircle2, reject: XCircle, wait: CircleHelp };

const list = {
  hidden: {},
  show: { transition: { staggerChildren: 0.05, delayChildren: 0.2 } },
};
const item = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.3, ease: 'easeOut' } },
};

function Column({ title, items, accent, icon: Icon }) {
  if (!items?.length) return null;
  return (
    <section className="min-w-0">
      <h3 className={cn('mb-3 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest', accent)}>
        <Icon className="size-3.5" /> {title}
      </h3>
      <motion.ul variants={list} initial="hidden" animate="show" className="flex flex-col gap-2">
        {items.map((text) => (
          <motion.li key={text} variants={item} className="text-sm leading-relaxed text-foreground/90">
            {text}
          </motion.li>
        ))}
      </motion.ul>
    </section>
  );
}

// Score on a 0-100 scale with the same bands the old orb used: avoid, hold, enter.
function ScoreScale({ score, tone }) {
  return (
    <div className="flex w-full flex-col gap-2">
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">Score</span>
        <span className="font-display text-3xl font-semibold tabular-nums">
          {score}
          <span className="font-mono text-xs text-muted-foreground"> /100</span>
        </span>
      </div>
      <div className="relative h-1.5 overflow-hidden rounded-full bg-muted" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={score}>
        <motion.div
          className={cn('h-full rounded-full', tone === 'ape' && 'bg-ape', tone === 'reject' && 'bg-reject', tone === 'wait' && 'bg-wait')}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
        />
      </div>
      <div className="flex justify-between font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        <span>avoid</span>
        <span>hold</span>
        <span>enter</span>
      </div>
    </div>
  );
}

export default function Verdict({ data }) {
  const tone = TONE[data.verdict] ?? 'wait';
  const Icon = ICON[tone];
  const hasScore = Number.isFinite(data.score);
  const agentError = data.agent && !data.agent.ok ? data.agent.error : null;

  return (
    <Card aria-live="polite">
      <CardContent className="grid p-0 md:grid-cols-[minmax(0,1fr)_minmax(0,22rem)]">
        <div className="flex min-w-0 flex-col gap-6 p-6 md:p-8">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="accent">{data.chain.toUpperCase()}</Badge>
            <Badge variant={tone}>
              <Icon className="size-3" /> {WORD[data.verdict]}
            </Badge>
          </div>

          <h2 className={cn('font-display text-6xl leading-none font-semibold tracking-tight sm:text-7xl', WORD_COLOR[tone])}>
            {WORD[data.verdict] ?? data.verdict}
          </h2>

          <p className="max-w-prose text-sm leading-relaxed text-muted-foreground">{data.verdict_reason}</p>

          {agentError && (
            <p className="flex items-start gap-2 border-l border-wait pl-3 font-mono text-xs text-wait">
              <AlertTriangle className="mt-0.5 size-3.5 shrink-0" /> Scoring agent: {agentError}
            </p>
          )}

          <div className="grid gap-6 sm:grid-cols-2">
            <Column title="Why" items={data.reasons} accent="text-ape" icon={CheckCircle2} />
            <Column title="Still missing" items={data.missing} accent="text-wait" icon={CircleHelp} />
          </div>
        </div>

        <div className={cn('flex flex-col gap-6 border-t p-6 md:border-t-0 md:border-l md:p-8', RULE[tone])}>
          {hasScore && <ScoreScale score={data.score} tone={tone} />}
          <Column title="Guards and top risks" items={data.risks} accent="text-reject" icon={XCircle} />
        </div>
      </CardContent>
    </Card>
  );
}
