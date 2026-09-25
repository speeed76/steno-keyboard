"""Turns dictionary translations into keyboard output, following Plover's syntax.

Supported translation syntax (the subset used by Plover's default dictionary):

  plain words          "the", "in the"          separated from the previous word by a space
  {^} {^^}             attach the next output with no space
  {^ing} {pre^} {^-^}  affixes: attach on the side(s) marked with ^
  {.} {?} {!}          sentence punctuation, attached, capitalizes the next word
  {,} {:} {;}          punctuation, attached
  {-|} {>} {<}         capitalize / lowercase / uppercase the next word
  {&a}                 glue (fingerspelling, numbers): glued text attaches to glued text
  {#Return} {#ctrl(c)} key combinations, sent as key presses
  {^\\n^} {^\\t^}        newline / tab
  {PLOVER:...} {:...}  commands: ignored

Suffixes ({^ing}, {^ed}, {^s}, ...) get the most common English orthography
rules (make+ing -> making, carry+ed -> carried, box+s -> boxes).

Output is a list of operations so it can be undone exactly:
  ("text", s)  type s
  ("del", s)   s was deleted with backspaces (s is remembered for undo)
  ("keys", s)  press a key combination (cannot be undone)
"""

# Formatting state is an immutable tuple so translations can snapshot it:
# (attach_next, case_next, glue_prev, last_word)
INITIAL_STATE = (True, None, False, "")

_SENTENCE_END = (".", "?", "!")
_MID_PUNCT = (",", ":", ";")
_VOWELS = "aeiou"


def _is_alpha(s):
    return bool(s) and all(("a" <= c <= "z") or ("A" <= c <= "Z") for c in s)


def orthography(word, suffix):
    """Return (chars_to_delete, text_to_add) for joining suffix onto word."""
    if not (_is_alpha(word) and _is_alpha(suffix) and len(word) >= 2):
        return 0, suffix
    w = word.lower()
    last, prev = w[-1], w[-2]
    first = suffix[0].lower()
    consonant_y = last == "y" and prev not in _VOWELS
    if suffix.lower() == "s":
        if consonant_y:
            return 1, "ies"
        if last in "sxz" or w.endswith("ch") or w.endswith("sh"):
            return 0, "es"
        return 0, suffix
    if consonant_y and first != "i":
        return 1, "i" + suffix
    if last == "e" and first in _VOWELS + "y":
        if first == "e":
            return 1, suffix  # agree+ed -> agreed, bake+ed -> baked
        if prev in "eyo" and first == "i":
            return 0, suffix  # seeing, dyeing, hoeing
        if prev in "cg" and first in "ao":
            return 0, suffix  # noticeable, courageous
        return 1, suffix  # make+ing -> making
    return 0, suffix


def _split(translation):
    """Split a translation into ("text", s) and ("meta", s) atoms."""
    atoms = []
    buf = ""
    i = 0
    n = len(translation)
    while i < n:
        c = translation[i]
        if c == "\\" and i + 1 < n and translation[i + 1] in "{}":
            buf += translation[i + 1]
            i += 2
            continue
        if c == "{":
            end = translation.find("}", i + 1)
            if end != -1:
                if buf.strip():
                    atoms.append(("text", buf.strip()))
                buf = ""
                atoms.append(("meta", translation[i + 1:end]))
                i = end + 1
                continue
        buf += c
        i += 1
    if buf.strip():
        atoms.append(("text", buf.strip()))
    return atoms


def _apply_case(word, case):
    if not word or case is None:
        return word
    if case == "cap":
        return word[0].upper() + word[1:]
    if case == "lower":
        return word[0].lower() + word[1:]
    return word.upper()


def _last_word(tail, added):
    text = tail + added
    cut = max(text.rfind(" "), text.rfind("\n"), text.rfind("\t"))
    return text[cut + 1:][-32:]


def render(translation, state):
    """Render a translation. Returns (ops, new_state)."""
    attach, case, glue, tail = state
    ops = []

    def add(kind, value):
        if ops and ops[-1][0] == kind and kind != "keys":
            ops[-1] = (kind, ops[-1][1] + value)
        else:
            ops.append((kind, value))

    def word(text, left=False, right=False, is_glue=False, suffix=False):
        nonlocal attach, case, glue, tail
        joined = attach or left
        if not joined:
            add("text", " ")
            tail = ""
        if suffix and joined and tail:
            n_del, text = orthography(tail, text)
            if n_del:
                add("del", tail[-n_del:])
                tail = tail[:-n_del]
        else:
            text = _apply_case(text, case)
            case = None
        add("text", text)
        tail = _last_word(tail, text)
        attach = right
        glue = is_glue

    for kind, value in _split(translation):
        if kind == "text":
            word(value)
            continue
        m = value
        if m == "":
            continue
        if m.startswith("#"):
            ops.append(("keys", m[1:]))
        elif m in _SENTENCE_END:
            word(m, left=True)
            case = "cap"
        elif m in _MID_PUNCT:
            word(m, left=True)
        elif m == "-|":
            case = "cap"
        elif m == ">":
            case = "lower"
        elif m == "<":
            case = "upper"
        elif m.startswith("&"):
            word(m[1:], left=glue, is_glue=True)
        elif m.startswith("PLOVER:") or m.startswith(":") or m.startswith("*"):
            continue
        elif "^" in m:
            left = m.startswith("^")
            text = m[1:] if left else m
            right = text.endswith("^")
            if right:
                text = text[:-1]
            if text:
                word(text, left=left, right=right, suffix=left and not right)
            else:
                attach = True
        # anything else is an unsupported meta: ignore it, like an empty {}

    return ops, (attach, case, glue, tail)


def inverse(ops):
    """Operations that undo ops (key presses cannot be undone and are skipped)."""
    out = []
    for kind, value in reversed(ops):
        if kind == "text":
            out.append(("del", value))
        elif kind == "del":
            out.append(("text", value))
    return out
