"""Top overlay that shows the current key/mouse combo, enlarged (e.g. Alt + A)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from . import theme


class OverlayView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumHeight(90)
        self._tokens: list[str] = []
        self._linger = QTimer(self)
        self._linger.setSingleShot(True)
        self._linger.setInterval(750)
        self._linger.timeout.connect(self._clear)

    def set_combo(self, tokens: list[str]):
        """Display the given tokens. Empty list lingers briefly then clears."""
        if tokens:
            self._linger.stop()
            self._tokens = list(tokens)
        else:
            # Keep the last combo visible for a moment for readability.
            if self._tokens:
                self._linger.start()
        self.update()

    def _clear(self):
        self._tokens = []
        self.update()

    # ------------------------------------------------------------------ #
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        area = QRectF(self.rect())

        if not self._tokens:
            p.setPen(QColor(theme.KEY_SUB_TEXT))
            f = QFont("Segoe UI")
            f.setPixelSize(max(14, int(area.height() * 0.18)))
            p.setFont(f)
            p.drawText(area, Qt.AlignCenter, "Press any key\u2026")
            p.end()
            return

        cap_h = min(area.height() * 0.62, 130.0)
        font_px = max(16.0, cap_h * 0.46)
        font = QFont("Segoe UI Semibold", int(font_px))
        font.setPixelSize(int(font_px))
        font.setBold(True)
        fm = QFontMetricsF(font)

        plus_font = QFont("Segoe UI")
        plus_px = font_px * 0.8
        plus_font.setPixelSize(int(plus_px))
        fm_plus = QFontMetricsF(plus_font)

        h_pad = font_px * 0.55
        gap = font_px * 0.55
        plus_w = fm_plus.horizontalAdvance("+") + gap * 2

        # Measure total width.
        cap_widths = []
        for tok in self._tokens:
            w = max(cap_h * 0.85, fm.horizontalAdvance(tok) + 2 * h_pad)
            cap_widths.append(w)
        total = sum(cap_widths) + plus_w * (len(self._tokens) - 1)

        x = area.center().x() - total / 2
        y = area.center().y() - cap_h / 2

        for i, tok in enumerate(self._tokens):
            w = cap_widths[i]
            rect = QRectF(x, y, w, cap_h)
            radius = cap_h * 0.2
            path = QPainterPath()
            path.addRoundedRect(rect, radius, radius)

            glow = QColor(theme.HL_GLOW)
            glow.setAlpha(70)
            p.setPen(QPen(glow, 4.0))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)

            p.setPen(QPen(QColor(theme.OVL_BORDER), 2.0))
            p.setBrush(QColor(theme.OVL_BG))
            p.drawPath(path)

            p.setFont(font)
            p.setPen(QColor(theme.OVL_TEXT))
            p.drawText(rect, Qt.AlignCenter, tok)

            x += w
            if i < len(self._tokens) - 1:
                plus_rect = QRectF(x, y, plus_w, cap_h)
                p.setFont(plus_font)
                p.setPen(QColor(theme.OVL_PLUS))
                p.drawText(plus_rect, Qt.AlignCenter, "+")
                x += plus_w

        p.end()
