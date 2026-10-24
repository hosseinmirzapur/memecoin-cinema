import { cva } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wider whitespace-nowrap',
  {
    variants: {
      variant: {
        default: 'border-border bg-secondary text-secondary-foreground',
        ape: 'border-ape/40 bg-ape/10 text-ape',
        reject: 'border-reject/40 bg-reject/10 text-reject',
        wait: 'border-wait/40 bg-wait/10 text-wait',
        accent: 'border-accent/40 bg-accent/10 text-accent',
      },
    },
    defaultVariants: { variant: 'default' },
  },
);

export function Badge({ className, variant, ...props }) {
  return <span data-slot="badge" className={cn(badgeVariants({ variant }), className)} {...props} />;
}
