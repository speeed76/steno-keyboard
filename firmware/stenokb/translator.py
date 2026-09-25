"""Stroke-to-text translation with longest-match multi-stroke lookup and undo.

Mirrors Plover's behaviour: every new stroke is tried together with the
strokes of the most recent translations, longest outline first. When a longer
outline matches, the output of the translations it absorbs is taken back and
replaced. The undo stroke (``*`` / ``=undo``) reverses the last translation and
restores whatever that translation had replaced.
"""

from .formatting import INITIAL_STATE, render, inverse
from .stroke import STAR, stroke_digits, stroke_to_str

UNDO = "=undo"


class Translation:
    __slots__ = ("strokes", "english", "ops", "state_before", "state_after", "replaced")

    def __init__(self, strokes, english, ops, state_before, state_after, replaced):
        self.strokes = strokes
        self.english = english
        self.ops = ops
        self.state_before = state_before
        self.state_after = state_after
        self.replaced = replaced


class Translator:
    def __init__(self, dictionary, emit, history_size=40):
        """dictionary: object with lookup(outline) and max_strokes.
        emit: callable receiving a list of output operations (see formatting.py)."""
        self.dictionary = dictionary
        self.emit = emit
        self.history_size = history_size
        self.reset()

    def reset(self):
        self.history = []
        self.state = INITIAL_STATE

    def stroke(self, stroke):
        match = self._longest_match(stroke)
        if match is None:
            english = self._untranslated(stroke)
            absorbed = []
            strokes = (stroke,)
        else:
            absorbed, strokes, english = match
        if english == UNDO:
            self.undo()
            return
        ops = []
        if absorbed:
            for t in reversed(absorbed):
                ops.extend(inverse(t.ops))
            del self.history[-len(absorbed):]
            self.state = absorbed[0].state_before
        before = self.state
        new_ops, self.state = render(english, before)
        ops.extend(new_ops)
        self.history.append(Translation(strokes, english, new_ops, before, self.state, absorbed))
        if len(self.history) > self.history_size:
            self.history.pop(0)
        self.emit(ops)

    def undo(self):
        if not self.history:
            self.emit([("keys", "BackSpace")])
            return
        t = self.history.pop()
        ops = inverse(t.ops)
        for r in t.replaced:
            ops.extend(op for op in r.ops if op[0] != "keys")
            self.history.append(r)
        self.state = t.replaced[-1].state_after if t.replaced else t.state_before
        self.emit(ops)

    def _longest_match(self, stroke):
        """Find the longest outline ending in stroke. Returns (absorbed, strokes, english)."""
        limit = self.dictionary.max_strokes
        # candidates[k] = strokes of the last k translations + this stroke
        candidates = []
        strokes = (stroke,)
        candidates.append(([], strokes))
        n = 0
        for t in reversed(self.history):
            n += 1
            strokes = t.strokes + strokes
            if len(strokes) > limit:
                break
            candidates.append((self.history[-n:], strokes))
        for absorbed, outline in reversed(candidates):
            english = self.dictionary.lookup(outline)
            if english is not None:
                return absorbed, outline, english
        return None

    @staticmethod
    def _untranslated(stroke):
        if stroke == STAR:
            return UNDO
        digits = stroke_digits(stroke)
        if digits is not None:
            return "{&" + digits + "}"
        return stroke_to_str(stroke)
