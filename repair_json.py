#!/usr/bin/env python3
"""
Repair corrupted JSON log files that contain multiple concatenated arrays.
Sugarscape.py opens logs in append mode, so re-runs produce files like:
  [partial][complete][complete][partial][complete]

This script finds the first complete run (timestep 0 → 5000) and writes it
back as a clean single JSON array, with a backup of the original.
"""
import json
import os
import shutil
import sys

SEEDS = [687, 651, 876, 72, 634, 128, 619, 991, 984, 829, 719, 518]
DIR   = "data/four_peak_utilitarian"
LABEL = "four_peak_utilitarian"
TARGET_TIMESTEPS = 5000


def find_segments(lines):
    """Return list of (start, end) line indices for each closed array segment.

    Arrays are concatenated at the top level (not nested). Each `[` starts
    a new segment; each `]` or `][` ends the MOST RECENTLY opened one.
    Unclosed segments (interrupted runs) are discarded.
    """
    segments = []
    stack = []  # start-line indices of unclosed segments

    for i, l in enumerate(lines):
        s = l.strip()
        if s == '[':
            stack.append(i)
        elif s == '][':
            if stack:
                segments.append((stack.pop(), i))
            stack.append(i)   # '][\n' also opens the next segment
        elif s == ']':
            if stack:
                segments.append((stack.pop(), i))

    return segments


def extract_segment(lines, start, end):
    """Extract lines[start..end] (inclusive) as a single valid JSON string."""
    chunk = list(lines[start:end + 1])   # include the close line
    # If segment starts with '][', strip the leading ']'
    if chunk[0].lstrip().startswith(']'):
        chunk[0] = '[\n'
    # Normalise the closing line to plain ']'
    chunk[-1] = ']\n'
    # Remove trailing comma from last data entry if present
    if len(chunk) >= 2 and chunk[-2].rstrip().endswith(','):
        chunk[-2] = chunk[-2].rstrip()[:-1] + '\n'
    return ''.join(chunk)


def is_complete(data):
    return (
        isinstance(data, list)
        and len(data) > 0
        and data[-1].get('timestep', 0) == TARGET_TIMESTEPS
    )


def repair_file(seed):
    path = os.path.join(DIR, f"{LABEL}_{seed}.json")
    backup = path + ".bak"

    with open(path) as f:
        lines = f.readlines()

    segments = find_segments(lines)
    print(f"  seed={seed}: {len(segments)} segment(s) found")

    for i, (start, end) in enumerate(segments):
        text = extract_segment(lines, start, end)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"    segment {i}: parse error — {e}")
            continue

        if is_complete(data):
            timesteps = len(data)
            print(f"    segment {i} (lines {start}-{end}): complete, {timesteps} timesteps — using this")
            shutil.copy2(path, backup)
            with open(path, 'w') as f:
                f.write(text)
            print(f"    wrote clean file (backup: {backup})")
            return True
        else:
            last_t = data[-1].get('timestep', '?') if data else '?'
            print(f"    segment {i} (lines {start}-{end}): partial (last timestep={last_t}), skipping")

    print(f"  [ERROR] No complete segment found for seed={seed}")
    return False


def main():
    seeds = list(map(int, sys.argv[1:])) if len(sys.argv) > 1 else SEEDS
    ok, fail = 0, 0
    for seed in seeds:
        print(f"\nProcessing seed={seed}")
        if repair_file(seed):
            ok += 1
        else:
            fail += 1
    print(f"\n{'='*50}")
    print(f"  Repaired: {ok}/{len(seeds)}")
    if fail:
        print(f"  Failed:   {fail}")


if __name__ == "__main__":
    main()
