#!/usr/bin/env python3
"""Local control panel for the research scripts. Listens on 127.0.0.1 by default.

Run: python3 scripts/ui_server.py [--port 8765] [--host 127.0.0.1]   then open http://127.0.0.1:8765
Containers pass --host 0.0.0.0; the Host header check still limits requests to loopback names.
"""
import argparse, json, mimetypes, subprocess, sys, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_address import validate_solana, validate_evm
from research import research as run_research

DIST = ROOT / 'ui' / 'dist'  # built by `make ui-build` from the React app in ui/src
RULES = ROOT / 'agents.md'
FAST = ROOT / 'scripts' / 'fast_review.py'
HOLDERS = ROOT / '.agents' / 'skills' / 'gmgn-holder-analysis' / 'analyze.py'
TESTS = ROOT / 'tests'
TIMEOUT = 180
EVM_CHAINS = ('bsc', 'base', 'eth')
ALLOWED_HOSTS = ('127.0.0.1', 'localhost')


def check_address(chain, address):
    if chain not in ('sol', 'auto') + EVM_CHAINS:
        raise ValueError(f'unsupported chain: {chain}')
    if chain == 'sol':
        ok = validate_solana(address)
    elif chain in EVM_CHAINS:
        ok = validate_evm(address)
    else:
        ok = validate_solana(address) or validate_evm(address)
    if not ok:
        raise ValueError(f'invalid address for chain {chain}')


def run_cmd(argv, cwd=ROOT):
    shown = ' '.join(str(a) for a in argv)
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT, cwd=cwd)
    except subprocess.TimeoutExpired:
        return {'ok': False, 'code': None, 'cmd': shown, 'stdout': '', 'stderr': f'timed out after {TIMEOUT}s'}
    except FileNotFoundError as e:
        return {'ok': False, 'code': None, 'cmd': shown, 'stdout': '', 'stderr': str(e)}
    return {'ok': r.returncode == 0, 'code': r.returncode, 'cmd': shown,
            'stdout': r.stdout, 'stderr': r.stderr}


def review(body):
    chain = str(body.get('chain', '')).lower()
    address = str(body.get('address', '')).strip()
    if chain == 'auto':
        raise ValueError('fast review needs a fixed chain (sol/bsc/base/eth)')
    check_address(chain, address)
    return run_cmd([sys.executable, str(FAST), chain, address])


def holders(body):
    chain = str(body.get('chain', 'auto')).lower()
    address = str(body.get('address', '')).strip()
    lang = str(body.get('lang', 'en'))
    if lang not in ('en', 'zh'):
        raise ValueError(f'unsupported language: {lang}')
    check_address(chain, address)
    return run_cmd([sys.executable, str(HOLDERS), address, chain, lang])


def tests(_body):
    return run_cmd([sys.executable, '-m', 'unittest', 'discover', '-s', str(TESTS), '-v'])


def research(body):
    return run_research(str(body.get('chain', '')).lower(), str(body.get('address', '')).strip())


ROUTES = {'/api/research': research, '/api/review': review, '/api/holders': holders, '/api/tests': tests}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, text, ctype):
        data = text if isinstance(text, bytes) else text.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False), 'application/json; charset=utf-8')

    def _host_ok(self):
        return self.headers.get('Host', '').split(':')[0] in ALLOWED_HOSTS

    def _asset(self, rel):
        target = (DIST / rel).resolve()
        if DIST.resolve() not in target.parents or not target.is_file():
            return self._json(404, {'error': 'not found'})
        return self._send(200, target.read_bytes(), mimetypes.guess_type(target.name)[0] or 'application/octet-stream')

    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {'error': 'forbidden host'})
        path = self.path.split('?', 1)[0]  # query strings (e.g. ?intro) must not break routing
        if path == '/':
            if not (DIST / 'index.html').is_file():
                return self._json(503, {'error': 'UI not built: run make ui-build'})
            return self._asset('index.html')
        if path.startswith('/assets/'):
            return self._asset(path.lstrip('/'))
        if path == '/api/rules':
            return self._send(200, RULES.read_text(encoding='utf-8'), 'text/plain; charset=utf-8')
        if path == '/api/config':
            return self._json(200, run_cmd(['gmgn-cli', 'config', '--check']))
        if path.startswith('/api/'):
            return self._json(404, {'error': 'not found'})
        self._asset(path.lstrip('/'))  # built files such as /models/*.glb; _asset guards the path

    def _body(self) -> dict:
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
        if not isinstance(body, dict):
            raise ValueError('body must be a JSON object')
        return body

    def _stream_research(self) -> None:
        # Server-Sent Events: one 'source' frame per GMGN call as it lands, then 'agent', then 'done' (or 'error').
        try:
            body = self._body()
        except ValueError as e:
            return self._json(400, {'error': str(e)})
        chain, address = str(body.get('chain', '')).lower(), str(body.get('address', '')).strip()
        started = False

        def send(kind: str, payload: dict) -> None:
            nonlocal started
            if not started:
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Accel-Buffering', 'no')
                self.end_headers()
                started = True
            self.wfile.write(f'event: {kind}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n'.encode('utf-8'))
            self.wfile.flush()

        self.close_connection = True
        try:
            send('done', run_research(chain, address, on_event=send))
        except ValueError as e:  # bad address or chain is refused before any frame is sent
            if not started:
                return self._json(400, {'error': str(e)})
            send('error', {'error': str(e)})
        except (BrokenPipeError, ConnectionResetError):
            pass  # viewer left the page
        except Exception:
            traceback.print_exc()
            if not started:
                return self._json(500, {'error': 'scan failed, see server log'})
            send('error', {'error': 'scan failed, see server log'})

    def do_POST(self):
        # Custom header blocks cross-site form posts: browsers cannot send it without a CORS preflight, which we never answer.
        if not self._host_ok() or self.headers.get('X-Ui') != '1':
            return self._json(403, {'error': 'forbidden'})
        if self.path == '/api/research/stream':
            return self._stream_research()
        route = ROUTES.get(self.path)
        if route is None:
            return self._json(404, {'error': 'not found'})
        try:
            result = route(self._body())
        except (json.JSONDecodeError, ValueError) as e:
            return self._json(400, {'error': str(e)})
        self._json(200, result)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--port', type=int, default=8765)
    p.add_argument('--host', default='127.0.0.1')
    args = p.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f'Research console: http://127.0.0.1:{args.port}  (Ctrl+C to stop)')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.server_close()


if __name__ == '__main__':
    main()
