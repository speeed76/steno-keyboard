"""Hardware configuration. Must match the PCB (hardware/ergogen/config.yaml)."""

# Matrix wiring: diodes point from column (anode) to row (cathode).
ROW_PINS = ("GP6", "GP7", "GP8", "GP9")
COL_PINS = (
    "GP0", "GP1", "GP2", "GP3", "GP4", "GP5",          # left half, outer -> inner
    "GP21", "GP20", "GP19", "GP18", "GP17", "GP16",    # right half, inner -> outer
)
COLUMNS_TO_ANODES = True

# SPDT slide switch: common pin to GPIO, one throw to GND. Set to None if not fitted.
# Switch closed (pin reads low) = steno mode.
MODE_SWITCH_PIN = "GP22"

# Mode indicator: on-board LED lit in steno mode (None to disable).
LED_PIN = "LED"

DEBOUNCE_SECONDS = 0.005

# Dictionaries, searched in order: the first one with a translation wins.
# *.json files are loaded into RAM (keep them small); *.stnd files are compiled
# with tools/build_dictionary.py and read from flash.
DICTIONARIES = (
    "/dictionaries/user.json",
    "/dictionaries/main.stnd",
)

# Mode at power-up when no mode switch is fitted: "steno" or "qwerty".
DEFAULT_MODE = "qwerty"
