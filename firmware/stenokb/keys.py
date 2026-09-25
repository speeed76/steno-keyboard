"""Parses Plover key combinations ({#...}) into adafruit_hid Keycode names.

Plover uses X11 keysym names: ``{#Return}``, ``{#control(z)}``,
``{#shift(alt(Tab))}``, several combos separated by spaces.
"""

MODIFIERS = {
    "shift": "LEFT_SHIFT", "shift_l": "LEFT_SHIFT", "shift_r": "RIGHT_SHIFT",
    "control": "LEFT_CONTROL", "ctrl": "LEFT_CONTROL",
    "control_l": "LEFT_CONTROL", "control_r": "RIGHT_CONTROL",
    "alt": "LEFT_ALT", "alt_l": "LEFT_ALT", "alt_r": "RIGHT_ALT", "option": "LEFT_ALT",
    "super": "LEFT_GUI", "super_l": "LEFT_GUI", "super_r": "RIGHT_GUI",
    "windows": "LEFT_GUI", "command": "LEFT_GUI", "meta": "LEFT_GUI",
}

KEYS = {
    "return": "ENTER", "enter": "ENTER", "kp_enter": "KEYPAD_ENTER",
    "backspace": "BACKSPACE", "tab": "TAB", "iso_left_tab": "TAB",
    "escape": "ESCAPE", "space": "SPACEBAR", "delete": "DELETE", "insert": "INSERT",
    "up": "UP_ARROW", "down": "DOWN_ARROW", "left": "LEFT_ARROW", "right": "RIGHT_ARROW",
    "home": "HOME", "end": "END", "page_up": "PAGE_UP", "prior": "PAGE_UP",
    "page_down": "PAGE_DOWN", "next": "PAGE_DOWN",
    "caps_lock": "CAPS_LOCK", "print": "PRINT_SCREEN", "pause": "PAUSE",
    "minus": "MINUS", "equal": "EQUALS", "bracketleft": "LEFT_BRACKET",
    "bracketright": "RIGHT_BRACKET", "backslash": "BACKSLASH", "semicolon": "SEMICOLON",
    "apostrophe": "QUOTE", "grave": "GRAVE_ACCENT", "comma": "COMMA",
    "period": "PERIOD", "slash": "FORWARD_SLASH",
    "0": "ZERO", "1": "ONE", "2": "TWO", "3": "THREE", "4": "FOUR",
    "5": "FIVE", "6": "SIX", "7": "SEVEN", "8": "EIGHT", "9": "NINE",
}
for _i in range(1, 25):
    KEYS["f%d" % _i] = "F%d" % _i
for _c in "abcdefghijklmnopqrstuvwxyz":
    KEYS[_c] = _c.upper()


def _key(name):
    return KEYS.get(name.lower())


def parse_combo(text):
    """Return a list of presses; each press is a list of Keycode names held together.

    Unknown key names are skipped."""
    presses = []
    i = 0
    n = len(text)
    held = []  # stack of modifier names for open "mod(" groups

    def token():
        nonlocal i
        start = i
        while i < n and text[i] not in "() \t":
            i += 1
        return text[start:i]

    while i < n:
        c = text[i]
        if c in " \t":
            i += 1
            continue
        if c == ")":
            if held:
                held.pop()
            i += 1
            continue
        name = token()
        if i < n and text[i] == "(":
            i += 1
            mod = MODIFIERS.get(name.lower()) or _key(name)
            held.append(mod)
            continue
        key = _key(name) or MODIFIERS.get(name.lower())
        if key:
            presses.append([m for m in held if m] + [key])
    return presses
