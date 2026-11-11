#!/usr/bin/env python3
"""Bounded, intentional memory allocation for a disposable Linux container."""
import argparse
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mib', type=int, default=192)
    parser.add_argument('--hold-seconds', type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.mib <= 256:
        parser.error('--mib must be between 1 and 256')
    if not 0 <= args.hold_seconds <= 30:
        parser.error('--hold-seconds must be between 0 and 30')
    print(f'Allocating {args.mib} MiB...', flush=True)
    data = bytearray(args.mib * 1024 * 1024)
    for offset in range(0, len(data), 4096):
        data[offset] = 1
    print('Allocation completed.', flush=True)
    time.sleep(args.hold_seconds)
    print('Finished.', flush=True)


if __name__ == '__main__':
    main()
