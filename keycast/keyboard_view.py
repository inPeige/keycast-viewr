"""The virtual keyboard: lays out KeyCap widgets and drives highlighting."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget

from . import theme
from .keydefs import KEYBOARD_ROWS
from .keycap import KeyCap

# Integer scale for QLayout stretch factors (which must be ints).
_SCALE = 100


class KeyboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._caps: dict[str, list[KeyCap]] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(6)

        for row in KEYBOARD_ROWS:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(6)
            for item in row:
                if "spacer" in item:
                    row_layout.addStretch(int(item["spacer"] * _SCALE))
                    continue
                cap = KeyCap(item)
                self._caps.setdefault(item["id"], []).append(cap)
                row_layout.addWidget(cap, int(item.get("w", 1.0) * _SCALE))
            outer.addLayout(row_layout, 1)

    # ------------------------------------------------------------------ #
    def set_key_active(self, canonical: str, active: bool):
        for cap in self._caps.get(canonical, ()):
            cap.set_active(active)

    def clear_all(self):
        for caps in self._caps.values():
            for cap in caps:
                cap.set_active(False)
