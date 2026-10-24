#!/usr/bin/env python3
import subprocess
import sys
from validate_address import validate_solana, validate_evm

REQUIRED_CHAINS = {'sol', 'bsc', 'base', 'eth'}

def run(args: list[str]) -> str:
    result = subprocess.run(['gmgn-cli', *args], text=True, capture_output=True, check=False, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f'Command failed: gmgn-cli {" ".join(args)}\n{result.stderr}')
    return result.stdout.strip()

def validate_address(chain: str, address: str) -> bool:
    chain = chain.lower()
    if chain == 'sol':
        return validate_solana(address)
    elif chain in ('bsc', 'base', 'eth'):
        return validate_evm(address)
    return False

def main():
    if len(sys.argv) < 3 or sys.argv[1] in ('--help', '-h'):
        print('Usage: fast_review.py <chain> <address>')
        print('Chains: sol, bsc, base, eth')
        sys.exit(0 if sys.argv[1:] and sys.argv[1] in ('--help', '-h') else 1)

    chain = sys.argv[1].lower()
    address = sys.argv[2]

    if chain not in REQUIRED_CHAINS:
        print(f'ERROR: unsupported chain: {chain}')
        sys.exit(1)

    if not validate_address(chain, address):
        print(f'ERROR: invalid address for chain {chain}')
        sys.exit(1)

    print(f'## Token Review: {chain} {address}\n')

    # Step 1: token info
    print('Running GMGN token info...')
    token_info = run(['token', 'info', '--chain', chain, '--address', address, '--raw'])
    print(token_info)

    # Step 2: security
    print('\nRunning GMGN token security...')
    security = run(['token', 'security', '--chain', chain, '--address', address, '--raw'])
    print(security)

    # Step 3: holders
    print('\nRunning GMGN token holders...')
    holders = run(['token', 'holders', '--chain', chain, '--address', address, '--raw'])
    print(holders)

    # Step 4: traders
    print('\nRunning GMGN token traders...')
    traders = run(['token', 'traders', '--chain', chain, '--address', address, '--raw'])
    print(traders)

    # Step 5: market kline
    print('\nRunning GMGN market kline...')
    kline = run(['market', 'kline', '--chain', chain, '--address', address, '--resolution', '15m', '--raw'])
    print(kline)

    print('\nReview complete.')

if __name__ == '__main__':
    main()
