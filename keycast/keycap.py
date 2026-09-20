"""A single keyboard key widget with active-state highlighting."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from . import theme


class KeyCap(QWidget):
    """Renders one physical key. Call :meth:`set_active` to highlight it."""

    def __init__(self, spec: dict, parent=None):
        super().__init__(parent)
        self.canonical = spec["id"]
        self.label = spec.get("label", "")
        self.sub = spec.get("sub")
        self.kind = spec.get("kind", "std")
        self._active = False
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumSize(20, 20)

    def set_active(self, active: bool):
        if active != self._active:
            self._active = active
            self.update()

    # ------------------------------------------------------------------ #
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        radius = min(8.0, rect.height() * 0.22)

        if self._active:
            bg = QColor(theme.HL_BG)
            border = QColor(theme.HL_BORDER)
            text_color = QColor(theme.HL_TEXT)
            sub_color = QColor(theme.HL_TEXT)
        else:
            bg = QColor(theme.KEY_BG_MOD if self.kind == "mod" else theme.KEY_BG)
            border = QColor(theme.KEY_BORDER)
            text_color = QColor(theme.KEY_TEXT)
            sub_color = QColor(theme.KEY_SUB_TEXT)

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # Subtle glow when active.
        if self._active:
            glow = QColor(theme.HL_GLOW)
            glow.setAlpha(90)
            p.setPen(QPen(glow, 3.0))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)

        p.setPen(QPen(border, 1.2))
        p.setBrush(bg)
        p.drawPath(path)

        # Text
        h = rect.height()
        main_size = max(8.0, min(h * 0.34, 22.0))
        font = QFont("Segoe UI", int(main_size))
        font.setPixelSize(int(main_size))
        font.setBold(self._active)
        p.setFont(font)
        p.setPen(text_color)

        if self.sub:
            # Two-line layout: sub symbol on top, main below.
            sub_size = max(7.0, main_size * 0.72)
            sub_font = QFont("Segoe UI")
            sub_font.setPixelSize(int(sub_size))
            sub_font.setBold(self._active)
            p.setFont(sub_font)
            p.setPen(sub_color)
            top_rect = rect.adjusted(6, rect.height() * 0.12, -6, -rect.height() * 0.45)
            p.drawText(top_rect, Qt.AlignLeft | Qt.AlignVCenter, self.sub)

            p.setFont(font)
            p.setPen(text_color)
            bot_rect = rect.adjusted(6, rect.height() * 0.42, -6, -rect.height() * 0.1)
            p.drawText(bot_rect, Qt.AlignLeft | Qt.AlignVCenter, self.label)
        else:
            p.drawText(rect, Qt.AlignCenter, self.label)

        p.end()
