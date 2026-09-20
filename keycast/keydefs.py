"""Keyboard layout definitions and pynput -> canonical id normalization.

A *canonical id* is a stable string identifying a physical key regardless of
modifiers (e.g. the physical "2" key is always ``"2"`` even when Shift turns it
into ``"@"``). On Windows we prefer the virtual-key code (``vk``) for this,
falling back to the character for other platforms / edge cases.
"""

from __future__ import annotations

try:
    from pynput import keyboard as _kb
except Exception:  # pragma: no cover - allows importing layout without pynput
    _kb = None


# --------------------------------------------------------------------------- #
# Canonical id -> human friendly display name (for the top overlay).
# --------------------------------------------------------------------------- #
DISPLAY_NAMES = {
    "ctrl_l": "Ctrl",
    "ctrl_r": "Ctrl",
    "alt_l": "Alt",
    "alt_r": "Alt",
    "shift_l": "Shift",
    "shift_r": "Shift",
    "win_l": "Win",
    "win_r": "Win",
    "menu": "Menu",
    "caps": "Caps",
    "tab": "Tab",
    "enter": "Enter",
    "backspace": "Back",
    "space": "Space",
    "esc": "Esc",
    "ins": "Ins",
    "del": "Del",
    "home": "Home",
    "end": "End",
    "pgup": "PgUp",
    "pgdn": "PgDn",
    "up": "\u2191",
    "down": "\u2193",
    "left": "\u2190",
    "right": "\u2192",
    "printscreen": "PrtSc",
    "scrolllock": "ScrLk",
    "pause": "Pause",
    "numlock": "Num",
    "mouse_left": "L-Click",
    "mouse_right": "R-Click",
    "mouse_middle": "M-Click",
    "scroll_up": "Scroll\u2191",
    "scroll_down": "Scroll\u2193",
}


def display_name(canonical: str) -> str:
    """Return a friendly label for the top overlay."""
    if canonical in DISPLAY_NAMES:
        return DISPLAY_NAMES[canonical]
    if len(canonical) == 1:
        return canonical.upper()
    return canonical.capitalize()


# --------------------------------------------------------------------------- #
# Normalization
# --------------------------------------------------------------------------- #
_SPECIAL_KEY_MAP = {}
if _kb is not None:
    K = _kb.Key
    # (pynput attribute name, canonical id). Not every member exists on every
    # platform (e.g. macOS lacks `insert`, `scroll_lock`, ...), so we look each
    # one up defensively.
    _PAIRS = [
        ("ctrl", "ctrl_l"), ("ctrl_l", "ctrl_l"), ("ctrl_r", "ctrl_r"),
        ("alt", "alt_l"), ("alt_l", "alt_l"), ("alt_r", "alt_r"),
        ("alt_gr", "alt_r"),
        ("shift", "shift_l"), ("shift_l", "shift_l"), ("shift_r", "shift_r"),
        ("cmd", "win_l"), ("cmd_l", "win_l"), ("cmd_r", "win_r"),
        ("caps_lock", "caps"),
        ("tab", "tab"), ("space", "space"), ("enter", "enter"),
        ("backspace", "backspace"), ("esc", "esc"),
        ("up", "up"), ("down", "down"), ("left", "left"), ("right", "right"),
        ("insert", "ins"), ("delete", "del"),
        ("home", "home"), ("end", "end"),
        ("page_up", "pgup"), ("page_down", "pgdn"),
        ("print_screen", "printscreen"), ("scroll_lock", "scrolllock"),
        ("pause", "pause"), ("num_lock", "numlock"), ("menu", "menu"),
    ]
    for _i in range(1, 13):
        _PAIRS.append((f"f{_i}", f"f{_i}"))

    for _attr, _cid in _PAIRS:
        _member = getattr(K, _attr, None)
        if _member is not None:
            _SPECIAL_KEY_MAP[_member] = _cid


# Virtual-key codes (Windows) -> canonical id. Letters/digits are handled
# programmatically; this table covers OEM/symbol/numpad keys.
_VK_MAP = {
    0xBA: ";",
    0xBB: "=",
    0xBC: ",",
    0xBD: "-",
    0xBE: ".",
    0xBF: "/",
    0xC0: "`",
    0xDB: "[",
    0xDC: "\\",
    0xDD: "]",
    0xDE: "'",
    # numpad
    0x6A: "num_mul",
    0x6B: "num_add",
    0x6D: "num_sub",
    0x6E: "num_dec",
    0x6F: "num_div",
}
for _n in range(10):
    _VK_MAP[0x60 + _n] = f"num{_n}"

# Character fallback for shifted symbols -> base physical key.
_CHAR_TO_BASE = {
    "~": "`", "!": "1", "@": "2", "#": "3", "$": "4", "%": "5",
    "^": "6", "&": "7", "*": "8", "(": "9", ")": "0", "_": "-",
    "+": "=", "{": "[", "}": "]", "|": "\\", ":": ";", '"': "'",
    "<": ",", ">": ".", "?": "/",
}


def normalize_key(key) -> str | None:
    """Translate a pynput key event into a canonical id.

    Returns ``None`` if the key cannot be mapped.
    """
    if _kb is None:
        return None

    # Special keys (modifiers, function keys, navigation, ...)
    if isinstance(key, _kb.Key):
        return _SPECIAL_KEY_MAP.get(key)

    # Character keys (KeyCode)
    vk = getattr(key, "vk", None)
    if vk is not None:
        if 0x41 <= vk <= 0x5A:  # A-Z
            return chr(vk).lower()
        if 0x30 <= vk <= 0x39:  # 0-9 (top row)
            return chr(vk)
        if vk in _VK_MAP:
            return _VK_MAP[vk]

    ch = getattr(key, "char", None)
    if ch:
        if ch in _CHAR_TO_BASE:
            return _CHAR_TO_BASE[ch]
        low = ch.lower()
        if low.isalpha() or low.isdigit():
            return low
        if low in "`-=[]\\;',./":
            return low
    return None


# --------------------------------------------------------------------------- #
# Physical keyboard layout (TKL / tenkeyless).
#
# Each row is a list of items. An item is either:
#   {"id": <canonical>, "label": <str>, "sub": <str|None>, "w": <float>, "kind": <str>}
# or a spacer:
#   {"spacer": <float>}
#
# ``w`` is the relative width in key units. ``kind`` drives styling:
#   "std" | "mod" (modifier) | "accent".
# --------------------------------------------------------------------------- #
def _k(cid, label, w=1.0, sub=None, kind="std"):
    return {"id": cid, "label": label, "sub": sub, "w": w, "kind": kind}


def _sp(w):
    return {"spacer": w}


KEYBOARD_ROWS = [
    # Function row
    [
        _k("esc", "Esc"),
        _sp(1.0),
        _k("f1", "F1"), _k("f2", "F2"), _k("f3", "F3"), _k("f4", "F4"),
        _sp(0.5),
        _k("f5", "F5"), _k("f6", "F6"), _k("f7", "F7"), _k("f8", "F8"),
        _sp(0.5),
        _k("f9", "F9"), _k("f10", "F10"), _k("f11", "F11"), _k("f12", "F12"),
        _sp(0.5),
        _k("printscreen", "PrtSc"), _k("scrolllock", "ScrLk"), _k("pause", "Pause"),
    ],
    # Number row
    [
        _k("`", "`", sub="~"),
        _k("1", "1", sub="!"), _k("2", "2", sub="@"), _k("3", "3", sub="#"),
        _k("4", "4", sub="$"), _k("5", "5", sub="%"), _k("6", "6", sub="^"),
        _k("7", "7", sub="&"), _k("8", "8", sub="*"), _k("9", "9", sub="("),
        _k("0", "0", sub=")"), _k("-", "-", sub="_"), _k("=", "=", sub="+"),
        _k("backspace", "Back", w=2.0, kind="mod"),
        _sp(0.5),
        _k("ins", "Ins"), _k("home", "Home"), _k("pgup", "PgUp"),
    ],
    # QWERTY row
    [
        _k("tab", "Tab", w=1.5, kind="mod"),
        _k("q", "Q"), _k("w", "W"), _k("e", "E"), _k("r", "R"), _k("t", "T"),
        _k("y", "Y"), _k("u", "U"), _k("i", "I"), _k("o", "O"), _k("p", "P"),
        _k("[", "[", sub="{"), _k("]", "]", sub="}"),
        _k("\\", "\\", w=1.5, sub="|"),
        _sp(0.5),
        _k("del", "Del"), _k("end", "End"), _k("pgdn", "PgDn"),
    ],
    # Home row
    [
        _k("caps", "Caps", w=1.75, kind="mod"),
        _k("a", "A"), _k("s", "S"), _k("d", "D"), _k("f", "F"), _k("g", "G"),
        _k("h", "H"), _k("j", "J"), _k("k", "K"), _k("l", "L"),
        _k(";", ";", sub=":"), _k("'", "'", sub='"'),
        _k("enter", "Enter", w=2.25, kind="accent"),
        _sp(3.5),
    ],
    # Shift row
    [
        _k("shift_l", "Shift", w=2.25, kind="mod"),
        _k("z", "Z"), _k("x", "X"), _k("c", "C"), _k("v", "V"), _k("b", "B"),
        _k("n", "N"), _k("m", "M"),
        _k(",", ",", sub="<"), _k(".", ".", sub=">"), _k("/", "/", sub="?"),
        _k("shift_r", "Shift", w=2.75, kind="mod"),
        _sp(1.5),
        _k("up", "\u2191"),
        _sp(1.0),
    ],
    # Bottom modifier row
    [
        _k("ctrl_l", "Ctrl", w=1.25, kind="mod"),
        _k("win_l", "Win", w=1.25, kind="mod"),
        _k("alt_l", "Alt", w=1.25, kind="mod"),
        _k("space", "Space", w=6.25),
        _k("alt_r", "Alt", w=1.25, kind="mod"),
        _k("win_r", "Win", w=1.25, kind="mod"),
        _k("menu", "Menu", w=1.25, kind="mod"),
        _k("ctrl_r", "Ctrl", w=1.25, kind="mod"),
        _sp(0.5),
        _k("left", "\u2190"), _k("down", "\u2193"), _k("right", "\u2192"),
    ],
]
