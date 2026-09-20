"""Global keyboard & mouse listener that emits Qt signals.

pynput runs its listener callbacks on background threads, so we forward every
event through Qt signals. When a signal is connected across threads Qt uses a
queued connection automatically, marshalling the call onto the GUI thread -
which is required for safely touching widgets.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from . import keydefs

try:
    from pynput import keyboard as kb
    from pynput import mouse as ms
except Exception:  # pragma: no cover
    kb = None
    ms = None


class InputBridge(QObject):
    """Owns the pynput listeners and re-emits events as Qt signals."""

    keyPressed = Signal(str)      # canonical id
    keyReleased = Signal(str)     # canonical id
    buttonPressed = Signal(str)   # mouse_left / mouse_right / mouse_middle
    buttonReleased = Signal(str)
    scrolled = Signal(str)        # scroll_up / scroll_down
    mouseMoved = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._kb_listener = None
        self._mouse_listener = None
        # De-bounce auto-repeat: track keys we already reported as down.
        self._down = set()

    # ------------------------------------------------------------------ #
    def start(self):
        if kb is None or ms is None:
            raise RuntimeError(
                "pynput is not available. Install it with 'pip install pynput'."
            )
        self._kb_listener = kb.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        self._mouse_listener = ms.Listener(
            on_click=self._on_click, on_scroll=self._on_scroll, on_move=self._on_move
        )
        self._kb_listener.start()
        self._mouse_listener.start()

    def stop(self):
        for listener in (self._kb_listener, self._mouse_listener):
            if listener is not None:
                try:
                    listener.stop()
                except Exception:
                    pass
        self._kb_listener = None
        self._mouse_listener = None

    # ------------------------------------------------------------------ #
    # Keyboard callbacks (background thread)
    # ------------------------------------------------------------------ #
    def _on_press(self, key):
        cid = keydefs.normalize_key(key)
        if not cid or cid in self._down:
            return  # unknown key or auto-repeat
        self._down.add(cid)
        self.keyPressed.emit(cid)

    def _on_release(self, key):
        cid = keydefs.normalize_key(key)
        if not cid:
            return
        self._down.discard(cid)
        self.keyReleased.emit(cid)

    # ------------------------------------------------------------------ #
    # Mouse callbacks (background thread)
    # ------------------------------------------------------------------ #
    _BUTTON_MAP = {}

    def _button_id(self, button):
        if ms is None:
            return None
        name = getattr(button, "name", "")
        return {
            "left": "mouse_left",
            "right": "mouse_right",
            "middle": "mouse_middle",
        }.get(name)

    def _on_click(self, x, y, button, pressed):
        cid = self._button_id(button)
        if cid is None:
            return
        if pressed:
            self.buttonPressed.emit(cid)
        else:
            self.buttonReleased.emit(cid)

    def _on_scroll(self, x, y, dx, dy):
        if dy > 0:
            self.scrolled.emit("scroll_up")
        elif dy < 0:
            self.scrolled.emit("scroll_down")

    def _on_move(self, x, y):
        self.mouseMoved.emit(int(x), int(y))
