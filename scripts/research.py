#!/usr/bin/env python3
"""Research one token: GMGN sources in parallel -> signals -> Kilo scoring agent -> hard guards.

Usage: python3 scripts/research.py <sol|bsc|base|eth> <address>
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_address import validate_solana, validate_evm
from gmgn_data import gather
from signals import kline_metrics, holder_metrics, track_mentions, security_flags
import kilo_agent

EVM_CHAINS = ('bsc', 'base', 'eth')
ENV_FILE = Path(__file__).resolve().parent.parent / '.env'


def load_env_file() -> None:
    # Real environment wins over .env so an exported key still overrides the file.
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())


load_env_file()

def token_summary(token: dict) -> dict:
    price = token.get('price') if isinstance(token.get('price'), dict) else {}
    return {'symbol': token.get('symbol'), 'name': token.get('name'), 'price_usd': price.get('price'),
            'price_24h': price.get('price_24h'), 'liquidity': token.get('liquidity'),
            'holder_count': token.get('holder_count'), 'creation_timestamp': token.get('creation_timestamp')}




def traders_count(payload) -> dict:
    rows = payload if isinstance(payload, list) else (payload or {}).get('list') or (payload or {}).get('traders') or []
    return {'count': len(rows) if isinstance(rows, list) else 0}


def preview(name: str, data, address: str) -> dict | None:
    """Short facts for the live feed. Cosmetic only: a bad payload must not break the scan."""
    try:
        if name == 'token_info':
            return token_summary(data)
        if name == 'security':
            return {k: v for k, v in security_flags(data).items() if k != 'raw'}
        if name == 'holders':
            return holder_metrics(data)
        if name == 'traders':
            return traders_count(data)
        if name == 'kline':
            return kline_metrics(data)
        return track_mentions(data, address)  # smart_money and kol
    except Exception:
        return None


def check_address(chain: str, address: str) -> None:
    if chain == 'sol':
        ok = validate_solana(address)
    elif chain in EVM_CHAINS:
        ok = validate_evm(address)
    else:
        raise ValueError(f'unsupported chain: {chain}')
    if not ok:
        raise ValueError(f'invalid address for chain {chain}')


def guards(sec: dict, holders: dict, kline: dict) -> tuple[list[str], list[str]]:
    """Return (hard, soft). Hard flags force REJECT; soft flags count toward the medium-risk rule."""
    hard, soft = [], []
    if sec['honeypot']:
        hard.append('honeypot: contract blocks selling')
    if sec['rug_ratio'] is not None and sec['rug_ratio'] > 0.3:
        hard.append(f"rug_ratio {sec['rug_ratio']:.2f} above 0.30")
    if holders.get('ok'):
        if holders['largest_share'] > 0.10:
            hard.append(f"largest wallet holds {holders['largest_share']:.1%} of supply (above 10%)")
        if holders['rat_trader_share'] > 0.05:
            hard.append(f"rat traders hold {holders['rat_trader_share']:.1%} of supply (above 5%)")
        if holders['top10_share'] > 0.50:
            soft.append(f"top 10 wallets hold {holders['top10_share']:.1%} of supply")
        if holders['sniper_share'] + holders['rat_trader_share'] + holders['bundler_share'] > 0.30:
            soft.append('sniper + rat-trader + bundler share above 30% of supply')
    if sec['creator_token_status'] == 'creator_hold':
        soft.append('dev still holds tokens')
    if kline.get('ok') and kline['pattern'] in ('Breakdown', 'Distribution at highs', 'Slow bleed'):
        soft.append(f"chart pattern: {kline['pattern']}")
    return hard, soft


def decide(agent_verdict: str, hard: list[str], soft: list[str]) -> tuple[str, str]:
    if hard:
        return 'REJECT', 'hard guard: ' + '; '.join(hard)
    if agent_verdict == 'APE' and len(soft) >= 2:
        return 'REJECT', 'multiple medium risks override APE'
    return agent_verdict, 'agent verdict'


def research(chain: str, address: str, env=None, on_event=None) -> dict:
    """on_event(kind, payload) gets 'source' as each GMGN call lands and 'agent' around the scoring call."""
    env = os.environ if env is None else env
    chain = chain.lower()
    check_address(chain, address)

    def emit(kind: str, **payload) -> None:
        if on_event:
            on_event(kind, payload)

    def source_done(name: str, res: dict) -> None:
        emit('source', name=name, ok=res['ok'], ms=res['ms'], error=res.get('error'),
             preview=preview(name, res.get('data'), address) if res['ok'] else None)

    raw = gather(chain, address, source_done)
    sources = [{'name': k, 'ok': v['ok'], 'ms': v['ms'], 'error': v.get('error')} for k, v in raw.items()]

    def data(name):
        return raw[name]['data'] if raw[name]['ok'] else None

    if not any(raw[k]['ok'] for k in ('token_info', 'security', 'holders', 'kline')):
        return {'ok': False, 'chain': chain, 'address': address, 'verdict': 'NEED_MORE_DATA',
                'verdict_reason': 'no core GMGN source answered', 'sources': sources}

    token = data('token_info') or {}
    sec = security_flags(data('security'))
    holders = holder_metrics(data('holders'))
    kline = kline_metrics(data('kline'))
    smart = track_mentions(data('smart_money'), address)
    kol = track_mentions(data('kol'), address)
    hard, soft = guards(sec, holders, kline)

    facts = {
        'token': token_summary(token),
        'security': sec,
        'holders': holders, 'kline': kline, 'smart_money': smart, 'kol': kol,
        'sources_failed': [s['name'] for s in sources if not s['ok']],
    }
    agent = {'ok': False, 'error': 'KILO_API_KEY not set: GMGN data shown, scoring skipped'}
    if env.get('KILO_API_KEY'):
        emit('agent', status='start', model=kilo_agent.MODEL)
        try:
            agent = {'ok': True, 'model': kilo_agent.MODEL, **kilo_agent.score(env['KILO_API_KEY'], chain, address, facts)}
        except (RuntimeError, ValueError, TypeError) as e:
            agent = {'ok': False, 'model': kilo_agent.MODEL, 'error': str(e)}
    emit('agent', status='ok' if agent['ok'] else 'error', error=agent.get('error'))

    verdict, why = decide(agent.get('verdict', 'NEED_MORE_DATA'), hard, soft)
    if not agent['ok'] and not hard:
        why = agent['error']  # no agent verdict: say why, not "agent verdict"
    score = min(agent.get('score', 0), 20) if hard else agent.get('score')
    risks = list(dict.fromkeys(hard + soft + agent.get('risks', [])))[:6]
    return {
        'ok': True, 'chain': chain, 'address': address, 'verdict': verdict, 'verdict_reason': why,
        'score': score, 'reasons': agent.get('reasons', []), 'risks': risks,
        'missing': agent.get('missing', []) or facts['sources_failed'], 'agent': {k: v for k, v in agent.items() if k not in ('reasons', 'risks', 'missing')},
        'signals': {'token': facts['token'], 'security': {k: v for k, v in sec.items() if k != 'raw'},
                    'holders': holders, 'kline': kline, 'smart_money': smart, 'kol': kol},
        'sources': sources,
    }


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: research.py <sol|bsc|base|eth> <address>', file=sys.stderr)
        sys.exit(1)
    try:
        print(json.dumps(research(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=2))
    except ValueError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
