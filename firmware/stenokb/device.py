"""CircuitPython-only glue: USB HID output and dictionary loading."""

import os

from adafruit_hid.keycode import Keycode

from .dictionary import BinaryDictionary, DictionaryStack, MemoryDictionary
from .keys import parse_combo
from .stroke import STAR


def keycode(name):
    return getattr(Keycode, name)


class HidKeys:
    """press/release by Keycode name, for the QWERTY engine."""

    def __init__(self, keyboard):
        self.keyboard = keyboard

    def press(self, *names):
        self.keyboard.press(*[keycode(n) for n in names])

    def release(self, *names):
        self.keyboard.release(*[keycode(n) for n in names])


class StenoOutput:
    """Executes the translator's output operations over USB HID."""

    def __init__(self, keyboard, layout):
        self.keyboard = keyboard
        self.layout = layout

    def __call__(self, ops):
        for kind, value in ops:
            if kind == "text":
                self._type(value)
            elif kind == "del":
                # Only characters that were actually typed need erasing.
                for ch in value:
                    if self._typeable(ch):
                        self.keyboard.send(Keycode.BACKSPACE)
            elif kind == "keys":
                for press in parse_combo(value):
                    self.keyboard.send(*[keycode(n) for n in press])

    def _typeable(self, ch):
        try:
            self.layout.keycodes(ch)
            return True
        except ValueError:
            return False

    def _type(self, text):
        # Characters outside the US layout cannot be typed over plain HID; skip them.
        self.layout.write("".join(ch for ch in text if self._typeable(ch)))


def _exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def load_dictionaries(paths):
    dictionaries = []
    for path in paths:
        if not _exists(path):
            print("dictionary not found:", path)
            continue
        if path.endswith(".json"):
            d = MemoryDictionary.from_json(path)
        else:
            d = BinaryDictionary(path)
        print("loaded", path, len(d), "entries")
        dictionaries.append(d)
    # Undo is always available, even without any dictionary.
    dictionaries.append(MemoryDictionary({(STAR,): "=undo"}))
    return DictionaryStack(dictionaries)
