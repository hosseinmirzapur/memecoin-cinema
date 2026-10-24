import { motion } from 'framer-motion';
import Sparkline from './Sparkline.jsx';
import { age, count, num, pct, price, signedPct, usd } from '../format.js';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

const FLAG = { ok: 'bg-ape', warn: 'bg-wait', bad: 'bg-reject' };
const VALUE = { ok: 'text-foreground', warn: 'text-wait', bad: 'text-reject' };

// Yellow/red flags use the same thresholds the server guards use (scripts/research.py).
const flagRate = (v, warn, bad) => (!Number.isFinite(v) ? null : v > bad ? 'bad' : v > warn ? 'warn' : 'ok');

function Row({ label, flag, children }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-t border-dashed border-border py-2 first:border-0 first:pt-0">
      <dt className="shrink-0 text-xs text-muted-foreground">{label}</dt>
      <dd className={cn('flex min-w-0 items-center justify-end gap-2 text-right font-mono text-[13px] tabular-nums break-words', VALUE[flag] ?? 'text-foreground')}>
        {flag && <i className={cn('size-1.5 shrink-0 rounded-full', FLAG[flag])} aria-hidden="true" />}
        {children}
      </dd>
    </div>
  );
}

const panel = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.2, 0.7, 0.2, 1] } },
};

function Panel({ title, note, children, className }) {
  return (
    <motion.div variants={panel} whileHover={{ y: -2 }} transition={{ type: 'spring', stiffness: 400, damping: 30 }} className={cn('min-w-0', className)}>
      <Card className="h-full transition-colors hover:border-muted-foreground/30">
        <CardHeader className="flex-row items-baseline justify-between gap-3">
          <CardTitle>{title}</CardTitle>
          {note && <CardDescription className="text-right font-mono text-[11px]">{note}</CardDescription>}
        </CardHeader>
        <CardContent>
          <dl className="flex flex-col">{children}</dl>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function Evidence({ signals, sources }) {
  const { token = {}, security = {}, holders = {}, kline = {}, smart_money: smart = {}, kol = {} } = signals;
  const m = kline.metrics ?? {};
  const failed = sources.filter((s) => !s.ok);

  return (
    <motion.div
      initial="hidden"
      animate="show"
      transition={{ staggerChildren: 0.07, delayChildren: 0.1 }}
      className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
    >
      <Panel title="Token" note={token.name || null}>
        <Row label="Price">{price(token.price_usd)}</Row>
        <Row label="24h price">{price(token.price_24h)}</Row>
        <Row label="Liquidity">{usd(token.liquidity)}</Row>
        <Row label="Holders">{count(token.holder_count)}</Row>
        <Row label="Age">{age(token.creation_timestamp)}</Row>
      </Panel>

      <Panel title="Security" note="GMGN token security">
        <Row label="Honeypot" flag={security.honeypot ? 'bad' : security.honeypot === false ? 'ok' : null}>
          {security.honeypot ? 'yes: blocks selling' : 'no'}
        </Row>
        <Row label="Rug ratio" flag={flagRate(security.rug_ratio, 0.1, 0.3)}>{num(security.rug_ratio)}</Row>
        <Row label="Top 10 holders" flag={flagRate(security.top10_holder_rate, 0.2, 0.5)}>{pct(security.top10_holder_rate)}</Row>
        <Row label="Dev status" flag={security.creator_token_status === 'creator_hold' ? 'warn' : null}>
          {security.creator_token_status ?? '—'}
        </Row>
        <Row label="Snipers">{count(security.sniper_count)}</Row>
        <Row label="Smart wallets">{count(security.smart_wallets)}</Row>
      </Panel>

      <Panel title="Holders" note={holders.ok ? `top ${holders.holders_fetched} · supply basis` : null}>
        {holders.ok ? (
          <>
            <Row label="Top 10" flag={flagRate(holders.top10_share, 0.4, 0.5)}>{pct(holders.top10_share)}</Row>
            <Row label="Top 20">{pct(holders.top20_share)}</Row>
            <Row label="Largest wallet" flag={flagRate(holders.largest_share, 0.05, 0.1)}>{pct(holders.largest_share)}</Row>
            <Row label="Snipers" flag={flagRate(holders.sniper_share, 0.1, 0.2)}>{pct(holders.sniper_share)}</Row>
            <Row label="Rat traders" flag={flagRate(holders.rat_trader_share, 0.02, 0.05)}>{pct(holders.rat_trader_share)}</Row>
            <Row label="Bundlers" flag={flagRate(holders.bundler_share, 0.1, 0.2)}>{pct(holders.bundler_share)}</Row>
            <Row label="Dev / creator">{pct(holders.dev_share)}</Row>
            <Row label="Airdrop, never bought">{pct(holders.airdrop_share)}</Row>
          </>
        ) : (
          <Row label="Status">{holders.reason ?? 'unavailable'}</Row>
        )}
      </Panel>

      <Panel title="Chart" note={kline.ok ? `${kline.bars} × ${kline.resolution}` : null} className="md:col-span-2 xl:col-span-2">
        {kline.ok ? (
          <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <div className="flex flex-col gap-3">
              <div className="flex items-baseline justify-between">
                <span className="font-display text-xl font-semibold">{kline.pattern}</span>
                <span className="font-mono text-2xl tabular-nums">
                  {kline.score}
                  <span className="text-xs text-muted-foreground">/100</span>
                </span>
              </div>
              <Sparkline closes={kline.closes} />
            </div>
            <dl className="flex flex-col">
              <Row label="Slope">{signedPct(m.slope)}</Row>
              <Row label="Drawdown">{pct(m.drawdown)}</Row>
              <Row label="Volatility">{pct(m.volatility)}</Row>
              <Row label="Volume ratio">{Number.isFinite(m.vol_ratio) ? `${num(m.vol_ratio)}×` : '—'}</Row>
            </dl>
          </div>
        ) : (
          <Row label="Status">{kline.reason ?? 'unavailable'}</Row>
        )}
      </Panel>

      <Panel title="Smart money & KOL" note="recent feed, by address">
        <Row label="Smart money trades">{count(smart.mentions)} of {count(smart.scanned)} scanned</Row>
        <Row label="KOL trades">{count(kol.mentions)} of {count(kol.scanned)} scanned</Row>
      </Panel>

      <Panel title="GMGN sources" note={failed.length ? `${failed.length} failed` : 'all answered'}>
        {sources.map((s) => (
          <Row key={s.name} label={s.name.replace('_', ' ')} flag={s.ok ? 'ok' : 'bad'}>
            {s.ok ? (
              <Badge variant="ape" className="normal-case tracking-normal">{s.ms} ms</Badge>
            ) : (
              <span className="line-clamp-2 break-words text-reject">{s.error?.split('\n')[0]?.slice(0, 120) ?? 'failed'}</span>
            )}
          </Row>
        ))}
      </Panel>
    </motion.div>
  );
}
