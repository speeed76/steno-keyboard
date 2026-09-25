"""Steno dictionaries that work within a microcontroller's RAM budget.

A Plover ``main.json`` is ~4 MB of text with ~150k entries; parsed into Python
objects it needs tens of megabytes, while an RP2040 has 264 KB of RAM. So the
big dictionary is compiled on the host (``tools/build_dictionary.py``) into a
hash-bucketed binary file that the firmware searches directly on flash: each
lookup is two small seeks and reads, and RAM use stays constant.

File layout (all integers little-endian)::

    header   16 bytes  b"STND", u8 version, u8 max_strokes, u16 reserved,
                       u32 bucket_count (power of two), u32 entry_count
    table    (bucket_count + 1) * u32  offset of each bucket in the data area
    data     entries, grouped by bucket:
               u8 stroke_count, stroke_count * 3 bytes (24-bit stroke masks),
               u8 text_length, text_length bytes of UTF-8 translation
"""

import struct

MAGIC = b"STND"
VERSION = 1
HEADER = struct.Struct("<4sBBHII")
MAX_TEXT = 255


def outline_key(strokes):
    """Serialize an outline (sequence of stroke masks) to the bytes used on disk."""
    out = bytearray(3 * len(strokes))
    for i, s in enumerate(strokes):
        out[3 * i] = s & 0xFF
        out[3 * i + 1] = (s >> 8) & 0xFF
        out[3 * i + 2] = (s >> 16) & 0xFF
    return bytes(out)


def fnv1a(data):
    h = 0x811C9DC5
    for b in data:
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return h


class MemoryDictionary:
    """A dictionary held in RAM: for small user dictionaries and for tests."""

    def __init__(self, entries=None):
        self._entries = {}
        self.max_strokes = 1
        if entries:
            for outline, text in entries.items():
                self.add(outline, text)

    def add(self, outline, text):
        outline = tuple(outline)
        self._entries[outline] = text
        if len(outline) > self.max_strokes:
            self.max_strokes = len(outline)

    def lookup(self, outline):
        return self._entries.get(tuple(outline))

    def __len__(self):
        return len(self._entries)

    @classmethod
    def from_json(cls, path_or_file):
        """Load a Plover-style JSON dictionary ({"STROKE/STROKE": "text"})."""
        import json
        from .stroke import parse_outline, StrokeError

        if hasattr(path_or_file, "read"):
            data = json.load(path_or_file)
        else:
            with open(path_or_file, "r") as f:
                data = json.load(f)
        d = cls()
        for steno, text in data.items():
            try:
                d.add(parse_outline(steno), text)
            except StrokeError:
                pass
        return d


class BinaryDictionary:
    """Reads a compiled dictionary straight from flash, one bucket at a time."""

    def __init__(self, path):
        self._file = open(path, "rb")
        header = self._file.read(HEADER.size)
        magic, version, max_strokes, _, buckets, count = HEADER.unpack(header)
        if magic != MAGIC or version != VERSION:
            raise ValueError("%s is not a compiled steno dictionary (v%d)" % (path, VERSION))
        self.max_strokes = max_strokes
        self._mask = buckets - 1
        self._count = count
        self._data_start = HEADER.size + 4 * (buckets + 1)
        self._pair = bytearray(8)

    def __len__(self):
        return self._count

    def lookup(self, outline):
        n = len(outline)
        if n == 0 or n > self.max_strokes:
            return None
        key = outline_key(outline)
        bucket = fnv1a(key) & self._mask
        f = self._file
        f.seek(HEADER.size + 4 * bucket)
        f.readinto(self._pair)
        start, end = struct.unpack("<II", self._pair)
        if start == end:
            return None
        f.seek(self._data_start + start)
        data = f.read(end - start)
        i = 0
        while i < len(data):
            count = data[i]
            i += 1
            this_key = data[i:i + 3 * count]
            i += 3 * count
            tlen = data[i]
            i += 1
            if count == n and this_key == key:
                return str(data[i:i + tlen], "utf-8")
            i += tlen
        return None

    def close(self):
        self._file.close()


class DictionaryStack:
    """Several dictionaries searched in order; the first one with an entry wins."""

    def __init__(self, dictionaries):
        self.dictionaries = list(dictionaries)
        self.max_strokes = max([d.max_strokes for d in self.dictionaries] or [1])

    def lookup(self, outline):
        for d in self.dictionaries:
            text = d.lookup(outline)
            if text is not None:
                return text
        return None
