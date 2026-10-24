#!/usr/bin/env python3
"""Fetch every GMGN source for one token in parallel, capped so GMGN's limiter does not ban the IP."""
import datetime
import json
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 45
FALLBACK_BAN = 300  # GMGN bans last at most 5 min
CONCURRENCY = 1  # a burst tripped RATE_LIMIT_BANNED on a live run, so GMGN calls run one at a time
SPACING = 2.0  # seconds between call starts, well under the 20-unit leaky bucket for these weights
RESET_RE = re.compile(r'resets at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) GMT([+-])(\d{2}):(\d{2})')

_gate = threading.Semaphore(CONCURRENCY)
_slot_lock = threading.Lock()
_next_slot = [0.0]
cooldown = {'until': 0.0, 'reason': ''}  # GMGN says stop sending before `until` (epoch seconds)


def _pace() -> None:
    with _slot_lock:
        now = time.monotonic()
        start = max(now, _next_slot[0])
        _next_slot[0] = start + SPACING
    if start > now:
        time.sleep(start - now)


def _remember_ban(text: str) -> None:
    if 'RATE_LIMIT' not in text:
        return
    m = RESET_RE.search(text)
    if m:
        offset = datetime.timedelta(hours=int(m[3]), minutes=int(m[4])) * (-1 if m[2] == '-' else 1)
        tz = datetime.timezone(offset)
        until = datetime.datetime.strptime(m[1], '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz).timestamp()
    else:
        until = time.time() + FALLBACK_BAN  # shortcut: no reset time in message, assume worst-case ban, upgrade if GMGN reports reset_at reliably
    if until > cooldown['until']:
        cooldown.update(until=until, reason=text.strip().splitlines()[-1][:200])


def gmgn(args: list[str]) -> dict:
    if time.time() < cooldown['until']:
        return {'ok': False, 'ms': 0, 'error': f"not sent: GMGN cooldown active. {cooldown['reason']}"}
    with _gate:
        _pace()
        started = time.monotonic()
        try:
            r = subprocess.run(['gmgn-cli', *args, '--raw'], capture_output=True, text=True, timeout=TIMEOUT)
        except (OSError, subprocess.TimeoutExpired) as e:
            return {'ok': False, 'ms': _ms(started), 'error': str(e)}
    if r.returncode != 0:
        text = (r.stderr or r.stdout).strip()
        _remember_ban(text)
        return {'ok': False, 'ms': _ms(started), 'error': text[-400:]}
    try:
        return {'ok': True, 'ms': _ms(started), 'data': json.loads(r.stdout)}
    except json.JSONDecodeError:
        return {'ok': False, 'ms': _ms(started), 'error': 'gmgn-cli returned non-JSON output'}


def _ms(started: float) -> int:
    return round((time.monotonic() - started) * 1000)


def jobs(chain: str, address: str) -> dict[str, list[str]]:
    base = ['--chain', chain]
    token = [*base, '--address', address]
    return {
        'token_info': ['token', 'info', *token],
        'security': ['token', 'security', *token],
        'holders': ['token', 'holders', *token, '--limit', '100'],
        'traders': ['token', 'traders', *token],
        'kline': ['market', 'kline', *token, '--resolution', '15m'],
        'smart_money': ['track', 'smartmoney', *base, '--limit', '200'],
        'kol': ['track', 'kol', *base, '--limit', '200'],
    }


def gather(chain: str, address: str, on_done=None) -> dict[str, dict]:
    plan = jobs(chain, address)
    with ThreadPoolExecutor(max_workers=len(plan)) as pool:
        futures = {pool.submit(gmgn, args): name for name, args in plan.items()}
        done = {}
        for f in as_completed(futures):  # report each source as it lands, not when the slowest finishes
            name = futures[f]
            done[name] = f.result()
            if on_done:
                on_done(name, done[name])
    return {name: done[name] for name in plan}
