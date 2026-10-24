#!/usr/bin/env python3
"""Run with: python3 -m unittest discover -s tests"""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_address import validate_solana, validate_evm

ANALYZE = ROOT / '.agents' / 'skills' / 'gmgn-holder-analysis' / 'analyze.py'
SOL = 'So11111111111111111111111111111111111111112'
EVM = '0x' + 'ab' * 20

# Fake gmgn-cli: prints $STUB_JSON, or an empty holder list by default.
STUB = '''#!/usr/bin/env python3
import os, sys
if os.environ.get('STUB_FAIL'):
    sys.stderr.write('HTTP 429 RATE_LIMIT_BANNED')
    sys.exit(1)
sys.stdout.write(os.environ.get('STUB_JSON', '{"list": []}'))
'''

HOLDERS = {'list': [
    {'address': f'W{i}', 'addr_type': 0, 'amount_percentage': p, 'balance': 1000 * p,
     'usd_value': 100.0, 'buy_tx_count_cur': 2, 'sell_tx_count_cur': 0,
     'unrealized_pnl': 0.1, 'profit': 5, 'native_balance': 0, 'native_transfer': {}}
    for i, p in enumerate([0.05, 0.2, 0.1])
]}


class ValidateAddressTest(unittest.TestCase):
    def test_solana_accepts_base58(self):
        self.assertTrue(validate_solana(SOL))

    def test_solana_rejects_bad_length_and_characters(self):
        self.assertFalse(validate_solana('abc'))
        self.assertFalse(validate_solana('0' + SOL[1:]))  # '0' is not base58

    def test_evm_accepts_hex(self):
        self.assertTrue(validate_evm(EVM))

    def test_evm_rejects_missing_prefix_wrong_length_and_non_hex(self):
        self.assertFalse(validate_evm(EVM[2:]))
        self.assertFalse(validate_evm(EVM[:-1]))
        self.assertFalse(validate_evm('0x' + 'g' * 40))


class AnalyzeScriptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        stub = Path(self.tmp.name) / 'gmgn-cli'
        stub.write_text(STUB)
        stub.chmod(0o755)
        self.env = {**os.environ, 'PATH': self.tmp.name + os.pathsep + os.environ['PATH']}

    def tearDown(self):
        self.tmp.cleanup()

    def run_analyze(self, *args, stub_json=None, fail=False):
        env = dict(self.env)
        if stub_json is not None:
            env['STUB_JSON'] = json.dumps(stub_json)
        if fail:
            env['STUB_FAIL'] = '1'
        return subprocess.run([sys.executable, str(ANALYZE), *args],
                              capture_output=True, text=True, env=env, timeout=60)

    def test_no_args_prints_usage(self):
        r = self.run_analyze()
        self.assertEqual(r.returncode, 1)
        self.assertIn('Usage', r.stderr)

    def test_bad_address_is_rejected(self):
        r = self.run_analyze('not-an-address', 'sol')
        self.assertEqual(r.returncode, 1)
        self.assertIn('not a valid', r.stderr)

    def test_auto_chain_fails_loudly_when_no_chain_matches(self):
        r = self.run_analyze(EVM, 'auto')
        self.assertEqual(r.returncode, 1)
        self.assertIn('no chain found', r.stderr)

    def test_gmgn_failure_is_one_clean_error_line(self):
        r = self.run_analyze(EVM, 'base', 'en', fail=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn('RATE_LIMIT_BANNED', r.stderr)
        self.assertNotIn('Traceback', r.stderr)

    def test_report_runs_with_holders(self):
        r = self.run_analyze(EVM, 'base', 'en', stub_json=HOLDERS)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('Holder Chip Analysis', r.stdout)
        self.assertIn('OUTPUT COMPLETE', r.stdout)


if __name__ == '__main__':
    unittest.main()
