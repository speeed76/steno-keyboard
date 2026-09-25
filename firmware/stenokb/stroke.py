"""Steno stroke encoding shared by the firmware and the host-side tools.

A stroke is stored as an integer bitmask over the 23 keys of the standard
English steno layout, in steno order. The same module runs under CPython
(dictionary compiler, tests) and CircuitPython (on the keyboard), so it only
uses the language subset both support.
"""

# Steno order. Index in this tuple == bit position in a stroke bitmask.
KEYS = (
    "#",
    "S-", "T-", "K-", "P-", "W-", "H-", "R-",
    "A-", "O-", "*", "-E", "-U",
    "-F", "-R", "-P", "-B", "-L", "-G", "-T", "-S", "-D", "-Z",
)

NUM_KEYS = len(KEYS)
BIT = {k: 1 << i for i, k in enumerate(KEYS)}

NUMBER_BAR = BIT["#"]
STAR = BIT["*"]
LEFT_MASK = sum(BIT[k] for k in KEYS[1:8])
VOWEL_MASK = BIT["A-"] | BIT["O-"] | BIT["-E"] | BIT["-U"]
RIGHT_MASK = sum(BIT[k] for k in KEYS[13:])

# Keys that turn into digits while the number bar is held.
NUMBERS = {
    "S-": "1", "T-": "2", "P-": "3", "H-": "4", "A-": "5",
    "O-": "0", "-F": "6", "-P": "7", "-L": "8", "-T": "9",
}
_DIGIT_TO_KEY = {v: k for k, v in NUMBERS.items()}

_FIRST_RIGHT = KEYS.index("-E")  # first key that can only be on the right


class StrokeError(ValueError):
    pass


def _letter(key):
    return key.replace("-", "")


def parse_stroke(text):
    """Parse one stroke in RTF/CRE notation ("STKPW-R", "1-9", "#S") to a bitmask."""
    mask = 0
    pos = 0  # index into KEYS; keys must appear in steno order
    for ch in text:
        if ch == "-":
            if pos > _FIRST_RIGHT:
                raise StrokeError("misplaced '-' in %r" % text)
            pos = _FIRST_RIGHT
            continue
        if ch == "#":
            mask |= NUMBER_BAR
            continue
        if ch in _DIGIT_TO_KEY:
            key = _DIGIT_TO_KEY[ch]
            idx = KEYS.index(key)
            if idx < pos:
                raise StrokeError("out of order digit %r in %r" % (ch, text))
            mask |= NUMBER_BAR | BIT[key]
            pos = idx + 1
            continue
        idx = pos
        while idx < NUM_KEYS and _letter(KEYS[idx]) != ch:
            idx += 1
        if idx == NUM_KEYS:
            raise StrokeError("cannot place %r in stroke %r" % (ch, text))
        mask |= 1 << idx
        pos = idx + 1
    if mask == 0:
        raise StrokeError("empty stroke %r" % text)
    return mask


def parse_outline(text):
    """Parse a multi-stroke outline ("PHAO/-PBLG") into a tuple of bitmasks."""
    return tuple(parse_stroke(s) for s in text.split("/"))


def stroke_to_str(mask):
    """Render a bitmask in normalized RTF/CRE notation (digits when # is held)."""
    numbers = bool(mask & NUMBER_BAR)
    out = []
    used_digit = False
    for i in range(1, NUM_KEYS):
        if not mask & (1 << i):
            continue
        key = KEYS[i]
        if numbers and key in NUMBERS:
            out.append((i, NUMBERS[key]))
            used_digit = True
        else:
            out.append((i, _letter(key)))
    text = ""
    has_middle = bool(mask & (VOWEL_MASK | STAR))
    for i, letter in out:
        if i >= 13 and not has_middle and "-" not in text:
            text += "-"
        text += letter
    if numbers and not used_digit:
        text = "#" + text
    return text or "#"


def stroke_digits(mask):
    """Return the digits a number-bar stroke types, or None if it is not purely numeric."""
    if not mask & NUMBER_BAR:
        return None
    digits = ""
    for i in range(1, NUM_KEYS):
        if mask & (1 << i):
            key = KEYS[i]
            if key not in NUMBERS:
                return None
            digits += NUMBERS[key]
    return digits or None
