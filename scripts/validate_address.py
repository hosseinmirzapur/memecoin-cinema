#!/usr/bin/env python3
import re
import sys

def validate_solana(address: str) -> bool:
    if not (32 <= len(address) <= 44):
        return False
    return bool(re.fullmatch(r'[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]+', address))

def validate_evm(address: str) -> bool:
    if not address.startswith('0x'):
        return False
    if len(address) != 42:
        return False
    return bool(re.fullmatch(r'0x[0-9a-fA-F]{40}', address))

def main():
    if len(sys.argv) != 3:
        print('Usage: validate_address.py <chain> <address>')
        sys.exit(1)

    chain = sys.argv[1].lower()
    address = sys.argv[2]

    if chain == 'sol':
        ok = validate_solana(address)
    elif chain in ('bsc', 'base', 'eth'):
        ok = validate_evm(address)
    else:
        print(f'ERROR: unsupported chain: {chain}')
        sys.exit(1)

    if ok:
        print('VALID')
        sys.exit(0)
    print('INVALID')
    sys.exit(1)

if __name__ == '__main__':
    main()
