import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

const TONES = {
  accent: 'border-[#5ce1ff] text-[#5ce1ff]',
  ape: 'border-[#2ee59d] text-[#2ee59d]',
  reject: 'border-[#ff4d6d] text-[#ff4d6d]',
  wait: 'border-[#ffb020] text-[#ffb020]',
};

// Parallax: the pointer drives --px and --py (-1..1). Deeper layers move further, so the frame reads as depth.
export function Layer({ depth = 0, className, children }) {
  return (
    <div
      className={cn('absolute inset-0', className)}
      style={{ transform: `translate3d(calc(var(--px, 0) * ${depth}px), calc(var(--py, 0) * ${depth * 0.6}px), 0)` }}
    >
      {children}
    </div>
  );
}

// A rubber stamp that slams onto the frame. Used for the moment a fact lands.
export function Stamp({ text, tone = 'accent', rotate = -8, delay = 0.25, className }) {
  return (
    <motion.div
      initial={{ scale: 2.4, opacity: 0, rotate: rotate - 6 }}
      animate={{ scale: 1, opacity: 1, rotate }}
      transition={{ delay, type: 'spring', stiffness: 240, damping: 15 }}
      className={cn(
        'pointer-events-none absolute rounded-md border-[3px] px-5 py-1.5 font-mono text-2xl font-bold tracking-[0.3em] uppercase',
        TONES[tone],
        className,
      )}
    >
      {text}
    </motion.div>
  );
}

// A stand-in silhouette for a person in the scene. Colour comes from the parent's text colour.
export function Figure({ className }) {
  return (
    <div className={cn('flex flex-col items-center', className)} aria-hidden="true">
      <div className="size-7 rounded-full bg-current" />
      <div className="h-20 w-14 rounded-t-[2rem] bg-current" />
    </div>
  );
}
