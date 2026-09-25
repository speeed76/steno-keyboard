"""Collects steno chords: a stroke is every key pressed until all are released."""

from .stroke import BIT


class ChordCollector:
    def __init__(self, keymap):
        """keymap: {key_number: steno key name, or "MODE"}."""
        self.keymap = keymap
        self.down = set()
        self.chord = set()

    def reset(self):
        self.down = set()
        self.chord = set()

    def press(self, key):
        if key in self.keymap:
            self.down.add(key)
            self.chord.add(key)

    def release(self, key):
        """Returns the finished chord (a set of key numbers) or None."""
        if key not in self.down:
            return None
        self.down.discard(key)
        if self.down:
            return None
        chord, self.chord = self.chord, set()
        return chord

    def to_stroke(self, chord):
        """Steno bitmask for a chord; 0 if it contains no steno keys."""
        mask = 0
        for key in chord:
            mask |= BIT.get(self.keymap[key], 0)
        return mask

    def is_mode_chord(self, chord):
        return len(chord) > 0 and all(self.keymap[k] == "MODE" for k in chord)
