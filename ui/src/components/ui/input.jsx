import { cn } from '@/lib/utils';

export function Input({ className, type = 'text', ...props }) {
  return (
    <input
      data-slot="input"
      type={type}
      className={cn(
        'h-11 w-full min-w-0 rounded-md border border-input bg-background px-3 font-mono text-sm outline-none transition-colors placeholder:text-muted-foreground/60 focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30 aria-invalid:border-destructive',
        className,
      )}
      {...props}
    />
  );
}
