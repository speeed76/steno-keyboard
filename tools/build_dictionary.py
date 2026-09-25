#!/usr/bin/env python3
"""Compile Plover JSON dictionaries into the keyboard's binary format.

    python3 tools/build_dictionary.py main.json [more.json ...] -o main.stnd

Later dictionaries override earlier ones for the same outline. The output is
read directly from flash by the firmware (see firmware/stenokb/dictionary.py).
"""

import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "firmware"))

from stenokb.dictionary import HEADER, MAGIC, MAX_TEXT, VERSION, fnv1a, outline_key  # noqa: E402
from stenokb.stroke import StrokeError, parse_outline  # noqa: E402

PLOVER_MAIN_URL = "https://raw.githubusercontent.com/openstenoproject/plover/main/plover/assets/main.json"


def load_entries(paths, warn=print):
    entries = {}
    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        bad = 0
        for steno, text in data.items():
            try:
                outline = parse_outline(steno)
            except StrokeError:
                bad += 1
                continue
            if len(text.encode("utf-8")) > MAX_TEXT:
                bad += 1
                continue
            entries[outline] = text
        if bad:
            warn("%s: skipped %d entries (unparseable steno or text > %d bytes)" % (path, bad, MAX_TEXT))
    return entries


def compile_entries(entries, entries_per_bucket=4):
    buckets = 1
    while buckets * entries_per_bucket < len(entries):
        buckets *= 2
    grouped = [[] for _ in range(buckets)]
    for outline, text in entries.items():
        key = outline_key(outline)
        grouped[fnv1a(key) & (buckets - 1)].append((outline, key, text.encode("utf-8")))

    table = bytearray()
    data = bytearray()
    for group in grouped:
        table += struct.pack("<I", len(data))
        for outline, key, text in group:
            data.append(len(outline))
            data += key
            data.append(len(text))
            data += text
    table += struct.pack("<I", len(data))

    max_strokes = max((len(o) for o in entries), default=1)
    header = HEADER.pack(MAGIC, VERSION, max_strokes, 0, buckets, len(entries))
    return bytes(header + table + data)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dictionaries", nargs="+", help="Plover JSON dictionaries (later ones win)")
    parser.add_argument("-o", "--output", default="main.stnd", help="output file (default: main.stnd)")
    args = parser.parse_args(argv)

    entries = load_entries(args.dictionaries, warn=lambda m: print("warning:", m, file=sys.stderr))
    blob = compile_entries(entries)
    with open(args.output, "wb") as f:
        f.write(blob)
    print("%s: %d entries, %.2f MB" % (args.output, len(entries), len(blob) / 1e6))


if __name__ == "__main__":
    main()
