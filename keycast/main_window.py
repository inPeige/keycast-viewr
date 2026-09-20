"""Main application window: top (mouse + enlarged combo) over keyboard.

Background is a single semi-transparent rounded panel so the whole thing reads
as one translucent overlay you can see the desktop through.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QAction, QActionGroup, QColor, QPainter, QPainterPath, QPen
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
# Mouse/scroll ids never appear as text in the top combo (they light up the
# mouse graphic instead).
_MOUSE_IDS = {"mouse_left", "mouse_right", "mouse_middle", "scroll_up", "scroll_down"}


def _base(cid: str) -> str:
    if cid.endswith("_l") or cid.endswith("_r"):
        return cid[:-2]
    return cid


class Backdrop(QWidget):
    """Paints the unified semi-transparent rounded background."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._alpha = 205  # 0-255

    def set_alpha(self, alpha: int):
        self._alpha = max(0, min(255, alpha))
        self.update()

    def alpha(self) -> int:
        return self._alpha

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)
        col = QColor(theme.BG_WINDOW)
        col.setAlpha(self._alpha)
        p.fillPath(path, col)
        p.setPen(QPen(QColor(255, 255, 255, 20), 1.0))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        p.end()


class MainWindow(QMainWindow):
    def __init__(self, bridge, parent=None):
        super().__init__(parent)
        self.bridge = bridge
        self.setWindowTitle("KeyCast Viewer")
        self.setMinimumSize(720, 340)
        self.resize(980, 480)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Active keyboard input tracking (cid -> monotonic sequence number).
        self._active_order: dict[str, int] = {}
        self._seq = 0

        # --- Widgets -------------------------------------------------- #
        self.overlay = OverlayView()
        self.keyboard = KeyboardView()
        self.mouse = MouseView()
        self.mouse.setMaximumWidth(168)

        # Top row: compact mouse on the left, enlarged combo filling the rest.
        top = QWidget()
        top.setAttribute(Qt.WA_TranslucentBackground, True)
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(14, 10, 14, 4)
        top_layout.setSpacing(14)
        top_layout.addWidget(self.mouse, 0)
        top_layout.addWidget(self.overlay, 1)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(top)
        splitter.addWidget(self.keyboard)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 5)
        splitter.setSizes([190, 360])
        splitter.setHandleWidth(4)

        self._backdrop = Backdrop()
        root = QVBoxLayout(self._backdrop)
        root.setContentsMargins(10, 10, 10, 10)
        root.addWidget(splitter)
        self.setCentralWidget(self._backdrop)

        self._connect_bridge()

        # --- Floating overlay behavior ------------------------------- #
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
    # Keyboard -> top combo + keyboard highlight
    # ------------------------------------------------------------------ #
    def _on_key_pressed(self, cid: str):
        self.keyboard.set_key_active(cid, True)
        self._add_active(cid)
        self._refresh_overlay()

    def _on_key_released(self, cid: str):
        self.keyboard.set_key_active(cid, False)
        self._remove_active(cid)
        self._refresh_overlay()

    # ------------------------------------------------------------------ #
    # Mouse -> ONLY lights up the mouse graphic (no text in the combo)
    # ------------------------------------------------------------------ #
    def _on_button_pressed(self, cid: str):
        self.mouse.set_button_active(cid, True)

    def _on_button_released(self, cid: str):
        self.mouse.set_button_active(cid, False)

    def _on_scrolled(self, direction: str):
        self.mouse.flash_scroll(direction)

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
            if cid in _MOUSE_IDS:
                continue
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
    # Window flags / floating behavior
    # ------------------------------------------------------------------ #
    def _apply_window_flags(self):
        flags = self.windowFlags()
        flags |= Qt.WindowDoesNotAcceptFocus
        if self._on_top:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def _toggle_on_top(self, checked: bool):
        self._on_top = checked
        self._apply_window_flags()
        self.show()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._float_applied:
            try:
                from .macos_overlay import make_window_float
                self._float_applied = make_window_float(self)
            except Exception:
                self._float_applied = False

    # ------------------------------------------------------------------ #
    # Context menu: on-top toggle, background opacity, quit.
    # ------------------------------------------------------------------ #
    def contextMenuEvent(self, event):
        menu = QMenu(self)

        top_action = QAction("Always on top", self, checkable=True)
        top_action.setChecked(self._on_top)
        top_action.triggered.connect(self._toggle_on_top)
        menu.addAction(top_action)

        opacity_menu = menu.addMenu("背景透明度")
        group = QActionGroup(self)
        group.setExclusive(True)
        current = self._backdrop.alpha()
        for label, val in [
            ("不透明 100%", 255),
            ("85%", 216),
            ("70%", 180),
            ("55%", 140),
            ("40%", 102),
            ("25%", 64),
        ]:
            act = QAction(label, self, checkable=True)
            act.setChecked(abs(current - val) < 8)
            act.triggered.connect(lambda _=False, v=val: self._backdrop.set_alpha(v))
            group.addAction(act)
            opacity_menu.addAction(act)

        menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)
        menu.exec(event.globalPos())

    def closeEvent(self, event):
        try:
            self.bridge.stop()
        except Exception:
            pass
        super().closeEvent(event)
