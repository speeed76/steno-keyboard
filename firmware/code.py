"""Dual-mode steno/QWERTY keyboard firmware (CircuitPython, RP2040/RP2350).

QWERTY mode: a layered 42-key keyboard.
Steno mode: chords are translated on the keyboard itself using the dictionaries
in /dictionaries and typed out as ordinary keystrokes, so the computer needs no
steno software.
"""

import time

import board
import digitalio
import keypad
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS

from stenokb import config, layout
from stenokb.chord import ChordCollector
from stenokb.device import HidKeys, StenoOutput, load_dictionaries
from stenokb.qwerty import Qwerty
from stenokb.translator import Translator


def pin(name):
    return getattr(board, name)


keyboard = Keyboard(usb_hid.devices)
steno_out = StenoOutput(keyboard, KeyboardLayoutUS(keyboard))

matrix = keypad.KeyMatrix(
    row_pins=[pin(p) for p in config.ROW_PINS],
    column_pins=[pin(p) for p in config.COL_PINS],
    columns_to_anodes=config.COLUMNS_TO_ANODES,
    interval=config.DEBOUNCE_SECONDS,
)

mode_switch = None
if config.MODE_SWITCH_PIN:
    mode_switch = digitalio.DigitalInOut(pin(config.MODE_SWITCH_PIN))
    mode_switch.switch_to_input(pull=digitalio.Pull.UP)

led = None
if config.LED_PIN and hasattr(board, config.LED_PIN):
    led = digitalio.DigitalInOut(pin(config.LED_PIN))
    led.switch_to_output()

translator = Translator(load_dictionaries(config.DICTIONARIES), steno_out)
chords = ChordCollector(layout.STENO)
state = {"mode": None}


def set_mode(mode):
    if mode == state["mode"]:
        return
    qwerty.release_all()
    keyboard.release_all()
    chords.reset()
    translator.reset()
    state["mode"] = mode
    if led:
        led.value = mode == "steno"
    print("mode:", mode)


qwerty = Qwerty(layout.LAYERS, HidKeys(keyboard), on_steno=lambda: set_mode("steno"))


def switch_mode():
    return "steno" if not mode_switch.value else "qwerty"


last_switch = switch_mode() if mode_switch else None
set_mode(last_switch or config.DEFAULT_MODE)

event = keypad.Event()
while True:
    if mode_switch:
        position = switch_mode()
        if position != last_switch:
            last_switch = position
            set_mode(position)

    if not matrix.events.get_into(event):
        time.sleep(0.001)
        continue

    key = event.key_number
    if state["mode"] == "qwerty":
        if event.pressed:
            qwerty.press(key)
        else:
            qwerty.release(key)
        continue

    if event.pressed:
        chords.press(key)
        continue
    chord = chords.release(key)
    if not chord:
        continue
    if chords.is_mode_chord(chord):
        set_mode("qwerty")
        continue
    stroke = chords.to_stroke(chord)
    if stroke:
        translator.stroke(stroke)
