# Steno/QWERTY dual-mode keyboard

A 42-key keyboard (3×12 + 6 thumb keys) that works as a normal QWERTY keyboard
or as a steno machine that translates chords **on the keyboard itself**, so the
computer needs no Plover install.

## Status

| Part | State |
|---|---|
| PCB (`hardware/`) | in progress: Ergogen layout, then KiCad routing |
| Firmware (`firmware/`) | **draft, never run on hardware.** The steno engine works on a desktop against Plover's real dictionary; USB and matrix code is untested |
| Dictionary compiler (`tools/build_dictionary.py`) | works: Plover `main.json` → 2.8 MB binary file |

## Hardware constraint found so far

Plover's default dictionary is still ~2.6 MB after compiling to a compact
binary format. A standard Raspberry Pi Pico (2 MB flash, ~1 MB free under
CircuitPython) **cannot hold it**. The PCB uses the standard Pico footprint,
but fit a module with ≥4 MB of flash (Raspberry Pi Pico 2) or, better, 16 MB.
