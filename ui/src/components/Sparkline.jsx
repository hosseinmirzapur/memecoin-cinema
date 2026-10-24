import { motion } from 'framer-motion';

// Price path for the last closes (15m candles). viewBox scales with the card.
export default function Sparkline({ closes }) {
  if (!closes?.length || closes.length < 2) {
    return <div className="grid h-24 place-items-center rounded-lg bg-muted font-mono text-xs text-muted-foreground">no candles</div>;
  }
  const lo = Math.min(...closes);
  const hi = Math.max(...closes);
  const span = hi - lo || 1;
  const step = 300 / (closes.length - 1);
  const points = closes.map((c, i) => `${(i * step).toFixed(1)},${(84 - ((c - lo) / span) * 76).toFixed(1)}`);
  const up = closes.at(-1) >= closes[0];
  const stroke = up ? 'var(--ape)' : 'var(--reject)';

  return (
    <svg
      className="h-24 w-full rounded-lg bg-muted"
      viewBox="0 0 300 88"
      preserveAspectRatio="none"
      role="img"
      aria-label="Recent 15m closes"
    >
      <motion.polyline
        points={points.join(' ')}
        fill="none"
        stroke={stroke}
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.1, ease: 'easeOut' }}
      />
    </svg>
  );
}
