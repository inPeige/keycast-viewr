"""Main application window: top overlay + bottom (keyboard + mouse)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .keydefs import display_name
from .keyboard_view import KeyboardView
from .mouse_view import MouseView
from .overlay_view import OverlayView

# Modifier grouping / ordering for the top combo.
_MOD_ORDER = {"ctrl": 0, "alt": 1, "shift": 2, "win": 3}
_MOUSE_IDS = {"mouse_left", "mouse_right", "mouse_middle"}


def _base(cid: str) -> str:
    if cid.endswith("_l") or cid.endswith("_r"):
        return cid[:-2]
    return cid


class MainWindow(QMainWindow):
    def __init__(self, bridge, parent=None):
        super().__init__(parent)
        self.bridge = bridge
        self.setWindowTitle("KeyCast Viewer")
        self.setMinimumSize(720, 380)
        self.resize(1000, 560)
        self.setStyleSheet(f"background: {theme.BG_WINDOW};")

        # Active input tracking (cid -> monotonic sequence number).
        self._active_order: dict[str, int] = {}
        self._seq = 0

        # --- Widgets -------------------------------------------------- #
        self.overlay = OverlayView()
        self.keyboard = KeyboardView()
        self.mouse = MouseView()

        bottom = QWidget()
        bottom.setStyleSheet(f"background: {theme.BG_WINDOW};")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(10, 6, 10, 10)
        bottom_layout.setSpacing(10)
        bottom_layout.addWidget(self.keyboard, 5)
        bottom_layout.addWidget(self.mouse, 1)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.overlay)
        splitter.addWidget(bottom)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 5)
        splitter.setSizes([180, 420])
        splitter.setHandleWidth(4)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)
        self.setCentralWidget(container)

        # Timer to refresh overlay after a transient scroll token.
        self._scroll_refresh = QTimer(self)
        self._scroll_refresh.setSingleShot(True)
        self._scroll_refresh.setInterval(260)
        self._scroll_refresh.timeout.connect(self._refresh_overlay)

        self._connect_bridge()

        # --- Floating overlay behavior ------------------------------- #
        # Stay above other apps by default and never steal keyboard focus,
        # so you can keep operating whatever app you're using while this
        # window remains visible on top instead of being sent to the back.
        self._on_top = True
        self._float_applied = False
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self._apply_window_flags()

    # ------------------------------------------------------------------ #
    def _connect_bridge(self):
        b = self.bridge
        b.keyPressed.connect(self._on_key_pressed)
        b.keyReleased.connect(self._on_key_released)
        b.buttonPressed.connect(self._on_button_pressed)
        b.buttonReleased.connect(self._on_button_released)
        b.scrolled.connect(self._on_scrolled)

    # ------------------------------------------------------------------ #
    # Slots
    # ------------------------------------------------------------------ #
    def _on_key_pressed(self, cid: str):
        self.keyboard.set_key_active(cid, True)
        self._add_active(cid)
        self._refresh_overlay()

    def _on_key_released(self, cid: str):
        self.keyboard.set_key_active(cid, False)
        self._remove_active(cid)
        self._refresh_overlay()

    def _on_button_pressed(self, cid: str):
        self.mouse.set_button_active(cid, True)
        self._add_active(cid)
        self._refresh_overlay()

    def _on_button_released(self, cid: str):
        self.mouse.set_button_active(cid, False)
        self._remove_active(cid)
        self._refresh_overlay()

    def _on_scrolled(self, direction: str):
        self.mouse.flash_scroll(direction)
        tokens = self._compute_tokens()
        tokens.append(display_name(direction))
        self.overlay.set_combo(tokens)
        self._scroll_refresh.start()

    # ------------------------------------------------------------------ #
    def _add_active(self, cid: str):
        if cid not in self._active_order:
            self._active_order[cid] = self._seq
            self._seq += 1

    def _remove_active(self, cid: str):
        self._active_order.pop(cid, None)

    def _compute_tokens(self) -> list[str]:
        mods = []
        others = []
        for cid, seq in sorted(self._active_order.items(), key=lambda kv: kv[1]):
            base = _base(cid)
            name = display_name(cid)
            if base in _MOD_ORDER:
                mods.append((_MOD_ORDER[base], name))
            else:
                others.append((seq, name))
        mods.sort(key=lambda t: t[0])

        tokens: list[str] = []
        seen = set()
        for _, name in mods:
            if name not in seen:
                seen.add(name)
                tokens.append(name)
        for _, name in others:
            tokens.append(name)
        return tokens

    def _refresh_overlay(self):
        self.overlay.set_combo(self._compute_tokens())

    # ------------------------------------------------------------------ #
    # Context menu: always-on-top toggle + quit.
    # ------------------------------------------------------------------ #
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        top_action = QAction("Always on top", self, checkable=True)
        top_action.setChecked(self._on_top)
        top_action.triggered.connect(self._toggle_on_top)
        menu.addAction(top_action)
        menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)
        menu.exec(event.globalPos())

    def _apply_window_flags(self):
        flags = self.windowFlags()
        # Never take keyboard focus -> your typing keeps going to the app
        # you're actually using; this window just stays visible on top.
        flags |= Qt.WindowDoesNotAcceptFocus
        if self._on_top:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def _toggle_on_top(self, checked: bool):
        self._on_top = checked
        self._apply_window_flags()
        self.show()  # WA_ShowWithoutActivating keeps focus on the other app

    def showEvent(self, event):
        super().showEvent(event)
        # Best-effort macOS enhancement: float across all Spaces and above
        # fullscreen apps. No-ops on Windows or if pyobjc isn't installed.
        if not self._float_applied:
            try:
                from .macos_overlay import make_window_float
                self._float_applied = make_window_float(self)
            except Exception:
                self._float_applied = False

    def closeEvent(self, event):
        try:
            self.bridge.stop()
        except Exception:
            pass
        super().closeEvent(event)
