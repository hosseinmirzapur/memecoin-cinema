#!/usr/bin/env python3
"""Deterministic signals from raw GMGN payloads. Follows gmgn-kline-pattern and gmgn-holder-analysis rules."""
import json


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _mean(xs):
    return sum(xs) / len(xs)


def kline_metrics(payload: dict | None) -> dict:
    candles = []
    for r in (payload or {}).get('list') or []:
        t, o = _num(r.get('time')), _num(r.get('open'))
        c, h, lo = _num(r.get('close')), _num(r.get('high')), _num(r.get('low'))
        if None in (t, c, h, lo) or min(c, h, lo) <= 0:
            continue
        candles.append({'t': t, 'o': o or c, 'c': c, 'h': h, 'l': lo, 'v': _num(r.get('volume')) or 0.0})
    candles.sort(key=lambda x: x['t'])
    if len(candles) < 8:
        return {'ok': False, 'usable': len(candles), 'reason': f'not enough candles to read a pattern ({len(candles)} usable)'}

    C = [x['c'] for x in candles]
    H = [x['h'] for x in candles]
    L = [x['l'] for x in candles]
    V = [x['v'] for x in candles]
    n = len(C)
    skipped = []

    sma9, sma21 = _mean(C[-9:]), _mean(C[-21:])
    trend = 'up' if sma9 > sma21 else 'down' if sma9 < sma21 else 'flat'

    if n >= 24 and _mean(C[-24:-19]) != 0:
        base = _mean(C[-24:-19])
        slope = (_mean(C[-5:]) - base) / base
    else:
        slope = (C[-1] - C[0]) / C[0]

    volatility = _mean([(x['h'] - x['l']) / x['c'] for x in candles[-14:]])
    peak = max(H)
    drawdown = (peak - C[-1]) / peak
    low = min(L)
    up_from_low = (C[-1] - low) / low if low > 0 else None
    vol_base = _mean(V[-21:-1]) if n > 1 else 0.0
    vol_ratio = V[-1] / vol_base if vol_base > 0 else None
    if vol_ratio is None:
        skipped.append('vol_ratio: recent volume is zero, volume rules skipped')
    if up_from_low is None:
        skipped.append('up_from_low: lowest low is zero, low-based rules skipped')

    metrics = {'trend': trend, 'slope': slope, 'volatility': volatility, 'drawdown': drawdown,
               'vol_ratio': vol_ratio, 'up_from_low': up_from_low}

    pattern = _classify(metrics)
    score, evidence = _score(metrics, C, V, candles, n)
    return {'ok': True, 'pattern': pattern, 'score': score, 'metrics': metrics, 'evidence': evidence,
            'skipped': skipped, 'bars': n, 'resolution': '15m', 'closes': C[-60:]}


def _classify(m: dict) -> str:
    s, d, v, fl, t = m['slope'], m['drawdown'], m['volatility'], m['up_from_low'], m['trend']
    rules = [
        (s > 0.25 and d < 0.12, 'Vertical run-up'),
        (s > 0.08 and d < 0.25, 'Uptrend channel'),
        (d > 0.55 and s < -0.10, 'Breakdown'),
        (d > 0.55 and s > 0.02, 'Bounce off the lows'),
        (d > 0.35 and abs(s) < 0.08, 'Distribution at highs'),
        (s < -0.20, 'Slow bleed'),
        (abs(s) < 0.05 and v < 0.05 and fl is not None and fl < 0.20, 'Basing at lows'),
        (abs(s) < 0.08 and v > 0.08, 'Wide chop'),
    ]
    for matched, name in rules:
        if matched:
            return name
    return {'up': 'Bullish consolidation', 'down': 'Bearish consolidation'}.get(t, 'Sideways consolidation')


def _score(m: dict, C, V, candles, n) -> tuple[int, list[dict]]:
    s, d = m['slope'], m['drawdown']
    vr, fl = m['vol_ratio'], m['up_from_low']
    ev = []

    def add(delta, text):
        ev.append({'delta': delta, 'text': text})

    if m['trend'] == 'up':
        add(12, '9-bar average above 21-bar average: short-term bullish structure')
    elif m['trend'] == 'down':
        add(-12, '9-bar average below 21-bar average: short-term bearish structure')

    if s > 0.15:
        add(15, f'last 20 bars trend up, {s:+.1%}')
    elif s > 0.02:
        add(6, f'mild uptrend, {s:+.1%}')
    elif s < -0.15:
        add(-15, f'last 20 bars trend down, {s:+.1%}')
    elif s < -0.02:
        add(-6, f'slow bleed, {s:+.1%}')

    if vr is not None and vr > 3:
        last = candles[-1]
        if last['c'] > last['o']:
            add(8, f'latest bar {vr:.1f}x volume, closed green: volume-backed push up')
        elif last['c'] < last['o']:
            add(-10, f'latest bar {vr:.1f}x volume, closed red: volume-backed dump')
    if vr is not None and vr < 0.3:
        add(-5, f'volume shrank to {vr:.0%} of average: attention fading')

    if d > 0.60:
        add(-15, f'down {d:.0%} from range high: catching-a-knife risk')
    elif d > 0.30:
        add(-6, f'down {d:.0%} from range high')
    elif d < 0.05:
        add(8, 'trading right at the range high')

    if n > 40 and max(C[-20:]) > max(C[-40:-20]) * 1.02 and _mean(V[-20:]) < _mean(V[-40:-20]) * 0.7:
        add(-10, 'divergence: new price high on shrinking volume')

    score = max(0, min(100, 50 + sum(e['delta'] for e in ev)))
    return score, ev


def holder_metrics(payload: dict | None) -> dict:
    rows = (payload or {}).get('list') or []
    if not rows:
        return {'ok': False, 'reason': 'no holders returned'}
    wallets = [h for h in rows if h.get('addr_type', 0) == 0]
    share = lambda h: _num(h.get('amount_percentage')) or 0.0
    ranked = sorted(wallets, key=share, reverse=True)

    def tagged(h, *tags):
        return any(t in (h.get('maker_token_tags') or []) or t in (h.get('tags') or []) for t in tags)

    airdrop = [h for h in wallets if (_num(h.get('buy_tx_count_cur')) or 0) == 0 and (_num(h.get('balance')) or 0) > 0]
    return {
        'ok': True,
        'holders_fetched': len(rows),
        'top10_share': sum(share(h) for h in ranked[:10]),
        'top20_share': sum(share(h) for h in ranked[:20]),
        'largest_share': share(ranked[0]) if ranked else 0.0,
        'sniper_share': sum(share(h) for h in wallets if tagged(h, 'sniper')),
        'rat_trader_share': sum(share(h) for h in wallets if tagged(h, 'rat_trader')),
        'bundler_share': sum(share(h) for h in wallets if tagged(h, 'bundler')),
        'dev_share': sum(share(h) for h in wallets if tagged(h, 'dev_team', 'creator')),
        'airdrop_share': sum(share(h) for h in airdrop),
        'basis': 'share of total supply (not float-rebased)',
    }


def track_mentions(payload: dict | None, address: str) -> dict:
    rows = (payload or {}).get('list') or []
    needle = address.lower()
    hits = [r for r in rows if needle in json.dumps(r, ensure_ascii=False).lower()]
    return {'ok': True, 'scanned': len(rows), 'mentions': len(hits)}


def security_flags(payload: dict | None) -> dict:
    p = payload or {}
    honeypot = str(p.get('is_honeypot', '')).lower() in ('yes', 'true', '1')
    return {
        'honeypot': honeypot,
        'rug_ratio': _num(p.get('rug_ratio')),
        'top10_holder_rate': _num(p.get('top_10_holder_rate')),
        'creator_token_status': p.get('creator_token_status'),
        'sniper_count': _num(p.get('sniper_count')),
        'smart_wallets': _num(p.get('smart_wallets')),
        'raw': p,
    }
