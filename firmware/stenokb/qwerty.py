"""Layered QWERTY keyboard logic (hardware independent)."""


class Qwerty:
    def __init__(self, layers, hid, on_steno=None):
        """layers: {"base"|"lower"|"raise"|"adjust": {key_number: action}}.
        hid: object with press(*names) and release(*names).
        on_steno: called when a STENO key is pressed."""
        self.layers = layers
        self.hid = hid
        self.on_steno = on_steno
        self.lower = False
        self.raise_ = False
        self.active = {}  # key_number -> action it was pressed with

    def _layer(self):
        if self.lower and self.raise_:
            return "adjust"
        if self.lower:
            return "lower"
        if self.raise_:
            return "raise"
        return "base"

    def action_for(self, key):
        action = self.layers[self._layer()].get(key)
        if action == "_":
            action = self.layers["base"].get(key)
        return action

    def press(self, key):
        action = self.action_for(key)
        if action is None:
            return
        self.active[key] = action
        if action == "LOWER":
            self.lower = True
        elif action == "RAISE":
            self.raise_ = True
        elif action == "STENO":
            if self.on_steno:
                self.on_steno()
        else:
            self.hid.press(*action.split("+"))

    def release(self, key):
        action = self.active.pop(key, None)
        if action is None:
            return
        if action == "LOWER":
            self.lower = False
        elif action == "RAISE":
            self.raise_ = False
        elif action != "STENO":
            self.hid.release(*action.split("+"))

    def release_all(self):
        for key in list(self.active):
            self.release(key)
        self.lower = self.raise_ = False
