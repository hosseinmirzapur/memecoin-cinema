import { cn } from '@/lib/utils';

export function Card({ className, ...props }) {
  return <div data-slot="card" className={cn('rounded-xl border border-border bg-card text-card-foreground', className)} {...props} />;
}

export function CardHeader({ className, ...props }) {
  return <div data-slot="card-header" className={cn('flex flex-col gap-1 p-5 pb-3', className)} {...props} />;
}

export function CardTitle({ className, ...props }) {
  return <h3 data-slot="card-title" className={cn('text-sm font-semibold leading-none tracking-tight', className)} {...props} />;
}

export function CardDescription({ className, ...props }) {
  return <p data-slot="card-description" className={cn('text-xs text-muted-foreground', className)} {...props} />;
}

export function CardContent({ className, ...props }) {
  return <div data-slot="card-content" className={cn('px-5 pb-5', className)} {...props} />;
}
