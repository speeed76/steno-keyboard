"""Physical layout and keymaps. Edit this file to customize the keyboard.

The board is a 4 x 12 switch matrix: three 12-key rows plus six thumb keys
(row 3, columns 3-8). A key's number is ``row * 12 + column``, the same
numbering CircuitPython's ``keypad.KeyMatrix`` reports.

    col:   0     1     2     3     4     5   |   6     7     8     9    10    11
    row 0 [ ]   [ ]   [ ]   [ ]   [ ]   [ ]  |  [ ]   [ ]   [ ]   [ ]   [ ]   [ ]
    row 1 [ ]   [ ]   [ ]   [ ]   [ ]   [ ]  |  [ ]   [ ]   [ ]   [ ]   [ ]   [ ]
    row 2 [ ]   [ ]   [ ]   [ ]   [ ]   [ ]  |  [ ]   [ ]   [ ]   [ ]   [ ]   [ ]
    row 3                   [ ]   [ ]   [ ]  |  [ ]   [ ]   [ ]
"""

ROWS = 4
COLS = 12
THUMB_COLS = range(3, 9)


def key_number(row, col):
    return row * COLS + col


def physical_keys():
    """All key numbers that exist on the board."""
    keys = []
    for row in range(3):
        for col in range(COLS):
            keys.append(key_number(row, col))
    for col in THUMB_COLS:
        keys.append(key_number(3, col))
    return keys


def _grid(rows):
    """Turn per-row lists (12, 12, 12 and 6 entries) into {key_number: value}."""
    out = {}
    for row, values in enumerate(rows):
        first = THUMB_COLS[0] if row == 3 else 0
        for i, value in enumerate(values):
            if value is not None:
                out[key_number(row, first + i)] = value
    return out


# ---------------------------------------------------------------------------
# Steno mode. The standard steno layout on a 40% board, as on a Planck/Georgi:
#
#    #   #   #   #   #   #  |  #   #   #   #   #   #      <- number bar
#   ( ) S-  T-  P-  H-  *   |  *  -F  -P  -L  -T  -D
#   ( ) S-  K-  W-  R-  *   |  *  -R  -B  -G  -S  -Z
#               ( ) A-  O-  | -E  -U  ( )
#
# The left pinky rests on column 1 so S- is pressed with one finger on either
# row. "MODE" (top-left key, pressed on its own) switches to QWERTY.
# ---------------------------------------------------------------------------
STENO = _grid([
    ["MODE", "#", "#", "#", "#", "#", "#", "#", "#", "#", "#", "#"],
    [None, "S-", "T-", "P-", "H-", "*", "*", "-F", "-P", "-L", "-T", "-D"],
    [None, "S-", "K-", "W-", "R-", "*", "*", "-R", "-B", "-G", "-S", "-Z"],
    [None, "A-", "O-", "-E", "-U", None],
])

# ---------------------------------------------------------------------------
# QWERTY mode. Names are adafruit_hid Keycode attributes; "A+B" presses a
# combination. Special values:
#   LOWER / RAISE  momentary layers (both together = ADJUST)
#   STENO          switch to steno mode
#   _              transparent: use the key from the base layer
#   None           no action
# ---------------------------------------------------------------------------
_ = "_"
S = "LEFT_SHIFT+"

BASE = _grid([
    ["ESCAPE", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "BACKSPACE"],
    ["TAB", "A", "S", "D", "F", "G", "H", "J", "K", "L", "SEMICOLON", "QUOTE"],
    ["LEFT_SHIFT", "Z", "X", "C", "V", "B", "N", "M", "COMMA", "PERIOD", "FORWARD_SLASH", "ENTER"],
    ["LEFT_CONTROL", "LOWER", "SPACEBAR", "SPACEBAR", "RAISE", "LEFT_ALT"],
])

LOWER = _grid([
    ["GRAVE_ACCENT", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "ZERO", "DELETE"],
    [_, "F1", "F2", "F3", "F4", "F5", "LEFT_ARROW", "DOWN_ARROW", "UP_ARROW", "RIGHT_ARROW", "MINUS", "EQUALS"],
    [_, "F6", "F7", "F8", "F9", "F10", "HOME", "PAGE_DOWN", "PAGE_UP", "END", "BACKSLASH", _],
    ["LEFT_GUI", _, _, _, _, _],
])

RAISE = _grid([
    [S + "GRAVE_ACCENT", S + "ONE", S + "TWO", S + "THREE", S + "FOUR", S + "FIVE",
     S + "SIX", S + "SEVEN", S + "EIGHT", S + "NINE", S + "ZERO", "DELETE"],
    [_, "F11", "F12", None, None, None,
     "LEFT_BRACKET", "RIGHT_BRACKET", S + "LEFT_BRACKET", S + "RIGHT_BRACKET", S + "MINUS", S + "EQUALS"],
    [_, None, None, None, None, None,
     S + "NINE", S + "ZERO", S + "COMMA", S + "PERIOD", S + "BACKSLASH", _],
    [_, _, _, _, _, "LEFT_GUI"],
])

ADJUST = _grid([
    ["STENO", None, None, None, None, None, None, None, None, None, None, "PRINT_SCREEN"],
    ["CAPS_LOCK", None, None, None, None, None, None, None, None, None, None, "INSERT"],
    [_, None, None, None, None, None, None, None, None, None, None, _],
    [_, _, _, _, _, _],
])

LAYERS = {"base": BASE, "lower": LOWER, "raise": RAISE, "adjust": ADJUST}
